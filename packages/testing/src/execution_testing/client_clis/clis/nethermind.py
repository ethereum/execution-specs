"""Interfaces for Nethermind CLIs."""

import json
import re
import shlex
import subprocess
import textwrap
from functools import cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from execution_testing.exceptions import (
    BlockException,
    ExceptionMapper,
    TransactionException,
)
from execution_testing.fixtures import (
    BlockchainEngineFixture,
    BlockchainFixture,
    FixtureFormat,
    StateFixture,
)

from ..cli_types import FixtureTestResult
from ..ethereum_cli import EthereumCLI
from ..file_utils import dump_files_to_directory
from ..fixture_consumer_tool import FixtureConsumerTool


class Nethtest(EthereumCLI):
    """Nethermind `nethtest` binary base class."""

    default_binary = Path("nethtest")
    # new pattern allows e.g. '1.2.3', in the past that was denied
    detect_binary_pattern = re.compile(
        r"^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?(\+[a-f0-9]{40})?$"
    )
    version_flag: str = "--version"
    cached_version: Optional[str] = None

    @classmethod
    def detect_binary(cls, binary_output: str) -> bool:
        """
        Detect nethtest from version output, checking each line.
        Handles the 'Using launch settings...' prefix from dotnet run.
        """
        for line in binary_output.splitlines():
            line = line.strip()
            if line and cls.detect_binary_pattern.match(line):
                return True
        return False

    @classmethod
    def from_binary_path(
        cls,
        binary_path: Path,
        **kwargs: Any,
    ) -> "Nethtest":
        """
        Create a Nethtest instance, handling .csproj/.dll paths that need
        dotnet to run.
        """
        binary = binary_path
        suffix = binary.suffix.lower()

        # Try dotnet run for .csproj or .dll files
        if suffix in (".csproj", ".dll") or (
            binary.is_dir() and list(binary.glob("*.csproj"))
        ):
            try:
                if binary.is_dir():
                    csproj = list(binary.glob("*.csproj"))[0]
                else:
                    csproj = binary
                result = subprocess.run(
                    ["dotnet", "run", "--no-build", "-c", "Release",
                     "--project", str(csproj), "--", "--version"],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                    timeout=30,
                )
                if result.returncode == 0 and cls.detect_binary(result.stdout):
                    instance = cls(binary=binary, **kwargs)
                    instance._needs_dotnet = True
                    return instance
            except Exception:
                pass

        # Fall back to direct execution
        try:
            result = subprocess.run(
                [str(binary), "--version"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                timeout=10,
            )
            output = result.stdout.strip()
            if cls.detect_binary(output):
                return cls(binary=binary, **kwargs)
        except Exception:
            pass

        raise Exception(f"Could not detect nethtest at {binary}")

    def __init__(
        self,
        binary: Path,
        trace: bool = False,
        exception_mapper: ExceptionMapper | None = None,
    ):
        """Initialize the Nethtest class."""
        self.binary = binary
        self.trace = trace
        self.exception_mapper = exception_mapper if exception_mapper else None
        # Detect if binary needs dotnet to run (.csproj, .dll, or directory with .csproj)
        self._needs_dotnet = self._detect_dotnet(binary)

    @staticmethod
    def _detect_dotnet(binary: Path) -> bool:
        """Check if the binary needs dotnet to run."""
        if binary.suffix in (".csproj", ".dll"):
            return True
        # Check if it's a directory containing a .csproj
        if binary.is_dir() and list(binary.glob("*.csproj")):
            return True
        # Check if the binary fails to run directly (needs .NET runtime)
        try:
            result = subprocess.run(
                [str(binary), "--version"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                timeout=5,
            )
            if "must install .NET" in result.stdout or "must install .NET" in result.stderr:
                return True
        except Exception:
            pass
        return False

    def _build_base_command(self, args: List[str]) -> List[str]:
        """Build a command, wrapping with dotnet if needed."""
        if self._needs_dotnet:
            # Find the .csproj file
            binary_path = self.binary
            if binary_path.is_dir():
                csproj = list(binary_path.glob("*.csproj"))
                if csproj:
                    binary_path = csproj[0]
            return [
                "dotnet", "run", "--no-build", "-c", "Release",
                "--project", str(binary_path), "--",
            ] + args
        return [str(self.binary)] + args

    def _run_command(self, command: List[str]) -> subprocess.CompletedProcess:
        try:
            return subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            raise Exception("Command failed with non-zero status.") from e
        except Exception as e:
            raise Exception("Unexpected exception calling evm tool.") from e

    def _consume_debug_dump(
        self,
        command: Tuple[str, ...],
        result: subprocess.CompletedProcess,
        debug_output_path: Path,
    ) -> None:
        # our assumption is that each command element is a string
        assert all(isinstance(x, str) for x in command), (
            f"Not all elements of 'command' list are strings: {command}"
        )

        # ensure that flags with spaces are wrapped in double-quotes
        consume_direct_call = " ".join(shlex.quote(arg) for arg in command)

        consume_direct_script = textwrap.dedent(
            f"""\
            #!/bin/bash
            {consume_direct_call}
            """
        )

        dump_files_to_directory(
            debug_output_path,
            {
                "consume_direct_args.py": command,
                "consume_direct_returncode.txt": result.returncode,
                "consume_direct_stdout.txt": result.stdout,
                "consume_direct_stderr.txt": result.stderr,
                "consume_direct.sh+x": consume_direct_script,
            },
        )

    @cache  # noqa
    def help(self, subcommand: str | None = None) -> str:
        """Return the help string, optionally for a subcommand."""
        help_command = [str(self.binary)]
        if subcommand:
            help_command.append(subcommand)
        help_command.append("--help")
        return self._run_command(help_command).stdout


class NethtestFixtureConsumer(
    Nethtest,
    FixtureConsumerTool,
    fixture_formats=[StateFixture, BlockchainFixture, BlockchainEngineFixture],
):
    """Nethermind implementation of the fixture consumer."""

    # Map fixture format to nethtest subcommand flags
    _format_to_flags: Dict[type, List[str]] = {
        StateFixture: ["--stateTest"],
        BlockchainFixture: ["--blockTest"],
        BlockchainEngineFixture: ["--engineTest"],
    }

    _dir_cache: Dict[str, Dict[str, Dict[str, Any]]] = {}

    def _get_dir_results(
        self,
        fixture_format: FixtureFormat,
        fixture_path: Path,
        debug_output_path: Optional[Path] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Run nethtest once per fixture directory and cache all results
        indexed by test name.
        """
        dir_path = fixture_path if fixture_path.is_dir() else fixture_path.parent
        flags = self._format_to_flags[type(fixture_format) if not isinstance(fixture_format, type) else fixture_format]
        cache_key = f"{flags[0]}:{dir_path}"

        if cache_key not in self._dir_cache:
            workers = getattr(self, "workers", 1)
            extra_args = flags + ["--jsonout", "--workers", str(workers), "--input", str(dir_path)]
            if debug_output_path:
                extra_args += ["--trace"]
            command = self._build_base_command(extra_args)

            result = self._run_command(command)

            if debug_output_path:
                self._consume_debug_dump(command, result, debug_output_path)

            if result.returncode != 0:
                raise Exception(
                    f"Unexpected exit code:\n{' '.join(command)}\n\n"
                    f"Error:\n{result.stderr}"
                )

            # nethtest may output non-JSON lines before the array
            stdout = result.stdout
            json_start = stdout.find("[")
            if json_start < 0:
                raise Exception(
                    f"No JSON array in nethtest output:\n{stdout[:500]}"
                )
            result_json = json.loads(stdout[json_start:])
            if not isinstance(result_json, list):
                raise Exception(
                    f"Unexpected result from nethtest: {result_json}"
                )

            indexed: Dict[str, Dict[str, Any]] = {}
            for r in result_json:
                validated = FixtureTestResult.model_validate(r).model_dump(
                    by_alias=True
                )
                indexed[validated["name"]] = validated

            self._dir_cache[cache_key] = indexed

        return self._dir_cache[cache_key]

    def _consume_test(
        self,
        fixture_format: FixtureFormat,
        label: str,
        fixture_path: Path,
        fixture_name: Optional[str] = None,
        debug_output_path: Optional[Path] = None,
    ) -> None:
        """Generic consume method using directory-level cache."""
        dir_results = self._get_dir_results(
            fixture_format=fixture_format,
            fixture_path=fixture_path,
            debug_output_path=debug_output_path,
        )
        if fixture_name:
            assert fixture_name in dir_results, (
                f"Test result for {fixture_name} missing"
            )
            result = dir_results[fixture_name]
            assert result["pass"], (
                f"{label} test failed: {result['error']}"
            )
        else:
            failures = [r for r in dir_results.values() if not r["pass"]]
            if failures:
                raise Exception(
                    f"{label} test failed: \n"
                    + "\n".join(f"{r['name']}: {r['error']}" for r in failures)
                )

    def consume_fixture(
        self,
        fixture_format: FixtureFormat,
        fixture_path: Path,
        fixture_name: Optional[str] = None,
        debug_output_path: Optional[Path] = None,
    ) -> None:
        """Execute the appropriate nethtest fixture consumer."""
        labels = {
            StateFixture: "State",
            BlockchainFixture: "Blockchain",
            BlockchainEngineFixture: "Engine",
        }
        label = labels.get(fixture_format, "Unknown")
        self._consume_test(fixture_format, label, fixture_path, fixture_name, debug_output_path)


class NethermindExceptionMapper(ExceptionMapper):
    """Nethermind exception mapper."""

    mapping_substring = {
        TransactionException.SENDER_NOT_EOA: "sender has deployed code",
        TransactionException.INTRINSIC_GAS_TOO_LOW: "intrinsic gas too low",
        TransactionException.INTRINSIC_GAS_BELOW_FLOOR_GAS_COST: (
            "intrinsic gas too low"
        ),
        TransactionException.INSUFFICIENT_MAX_FEE_PER_GAS: (
            "miner premium is negative"
        ),
        TransactionException.PRIORITY_GREATER_THAN_MAX_FEE_PER_GAS: (
            "InvalidMaxPriorityFeePerGas: Cannot be higher than maxFeePerGas"
        ),
        TransactionException.GAS_ALLOWANCE_EXCEEDED: (
            "Block gas limit exceeded"
        ),
        TransactionException.NONCE_IS_MAX: "NonceTooHigh",
        TransactionException.INITCODE_SIZE_EXCEEDED: (
            "max initcode size exceeded"
        ),
        TransactionException.NONCE_MISMATCH_TOO_LOW: (
            "transaction nonce is too low"
        ),
        TransactionException.NONCE_MISMATCH_TOO_HIGH: (
            "transaction nonce is too high"
        ),
        TransactionException.INSUFFICIENT_MAX_FEE_PER_BLOB_GAS: (
            "InsufficientMaxFeePerBlobGas: Not enough to cover blob gas fee"
        ),
        TransactionException.TYPE_1_TX_PRE_FORK: (
            "InvalidTxType: Transaction type in Custom is not supported"
        ),
        TransactionException.TYPE_2_TX_PRE_FORK: (
            "InvalidTxType: Transaction type in Custom is not supported"
        ),
        TransactionException.TYPE_3_TX_PRE_FORK: (
            "InvalidTxType: Transaction type in Custom is not supported"
        ),
        TransactionException.TYPE_3_TX_ZERO_BLOBS: (
            "blob transaction must have at least 1 blob"
        ),
        TransactionException.TYPE_3_TX_INVALID_BLOB_VERSIONED_HASH: (
            "InvalidBlobVersionedHashVersion: Blob version not supported"
        ),
        TransactionException.TYPE_3_TX_CONTRACT_CREATION: (
            "blob transaction of type create"
        ),
        TransactionException.TYPE_4_EMPTY_AUTHORIZATION_LIST: (
            "MissingAuthorizationList: Must be set"
        ),
        TransactionException.TYPE_4_TX_CONTRACT_CREATION: (
            "NotAllowedCreateTransaction: To must be set"
        ),
        TransactionException.TYPE_4_TX_PRE_FORK: (
            "InvalidTxType: Transaction type in Custom is not supported"
        ),
        BlockException.INCORRECT_BLOB_GAS_USED: (
            "HeaderBlobGasMismatch: "
            "Blob gas in header does not match calculated"
        ),
        BlockException.INVALID_REQUESTS: (
            "InvalidRequestsHash: Requests hash mismatch in block"
        ),
        BlockException.INVALID_GAS_USED_ABOVE_LIMIT: (
            "ExceededGasLimit: Gas used exceeds gas limit."
        ),
        BlockException.RLP_BLOCK_LIMIT_EXCEEDED: (
            "ExceededBlockSizeLimit: Exceeded block size limit"
        ),
        BlockException.INVALID_DEPOSIT_EVENT_LAYOUT: (
            "DepositsInvalid: Invalid deposit event layout:"
        ),
        BlockException.INVALID_BASEFEE_PER_GAS: (
            "InvalidBaseFeePerGas: Does not match calculated"
        ),
        BlockException.INVALID_BLOCK_TIMESTAMP_OLDER_THAN_PARENT: (
            "InvalidTimestamp: "
            "Timestamp in header cannot be lower than ancestor"
        ),
        BlockException.INVALID_BLOCK_NUMBER: (
            "InvalidBlockNumber: Block number does not match the parent"
        ),
        BlockException.EXTRA_DATA_TOO_BIG: (
            "InvalidExtraData: Extra data in header is not valid"
        ),
        BlockException.INVALID_GASLIMIT: (
            "InvalidGasLimit: Gas limit is not correct"
        ),
        BlockException.INVALID_RECEIPTS_ROOT: (
            "InvalidReceiptsRoot: Receipts root in header does not match"
        ),
        BlockException.INVALID_LOG_BLOOM: (
            "InvalidLogsBloom: Logs bloom in header does not match"
        ),
        BlockException.INVALID_STATE_ROOT: (
            "InvalidStateRoot: State root in header does not match"
        ),
        BlockException.GAS_USED_OVERFLOW: ("Block gas limit exceeded"),
        BlockException.BLOCK_ACCESS_LIST_GAS_LIMIT_EXCEEDED: (
            "BlockAccessListGasLimitExceeded:"
        ),
    }
    mapping_regex = {
        TransactionException.INSUFFICIENT_ACCOUNT_FUNDS: (
            r"insufficient sender balance|"
            r"insufficient MaxFeePerGas for sender balance"
        ),
        TransactionException.TYPE_3_TX_WITH_FULL_BLOBS: (
            r"Transaction \d+ is not valid"
        ),
        TransactionException.TYPE_3_TX_MAX_BLOB_GAS_ALLOWANCE_EXCEEDED: (
            r"BlockBlobGasExceeded: A block cannot have more than "
            r"\d+ blob gas, blobs count \d+, blobs gas used: \d+"
        ),
        TransactionException.TYPE_3_TX_BLOB_COUNT_EXCEEDED: (
            r"BlobTxGasLimitExceeded: Transaction's totalDataGas=\d+ "
            r"exceeded MaxBlobGas per transaction=\d+"
        ),
        TransactionException.GAS_LIMIT_EXCEEDS_MAXIMUM: (
            r"TxGasLimitCapExceeded: Gas limit \d+ \w+ cap of \d+\.?"
        ),
        BlockException.INCORRECT_EXCESS_BLOB_GAS: (
            r"HeaderExcessBlobGasMismatch: Excess blob gas in header "
            r"does not match calculated|Overflow in excess blob gas"
        ),
        BlockException.INVALID_BLOCK_HASH: (
            r"Invalid block hash 0x[0-9a-f]+ does not match "
            r"calculated hash 0x[0-9a-f]+"
        ),
        BlockException.SYSTEM_CONTRACT_EMPTY: (
            r"(Withdrawals|Consolidations)Empty: Contract is not deployed\."
        ),
        BlockException.SYSTEM_CONTRACT_CALL_FAILED: (
            r"(Withdrawals|Consolidations)Failed: Contract execution failed\."
        ),
        # BAL Exceptions — specific exceptions have unique patterns, but
        # INVALID_BLOCK_ACCESS_LIST and INCORRECT_BLOCK_FORMAT intentionally
        # overlap because the test framework requires `want in got` matching.
        BlockException.INVALID_BAL_HASH: (r"InvalidBlockLevelAccessListHash:"),
        BlockException.INVALID_BAL_MISSING_ACCOUNT: (
            r"InvalidBlockLevelAccessList:.*missing account"
        ),
        BlockException.INVALID_BAL_EXTRA_ACCOUNT: (
            r"InvalidBlockLevelAccessList:.*surplus changes"
            r"|could not be parsed as a block: "
            r"Error decoding block access list:"
        ),
        BlockException.INVALID_BLOCK_ACCESS_LIST: (
            r"InvalidBlockLevelAccessListHash:"
            r"|InvalidBlockLevelAccessList:"
            r"|could not be parsed as a block: "
            r"Error decoding block access list:"
        ),
        BlockException.INCORRECT_BLOCK_FORMAT: (
            r"could not be parsed as a block: "
            r"Error decoding block access list:"
        ),
        TransactionException.GAS_ALLOWANCE_EXCEEDED: (
            r"TxGasLimitCapExceeded:"
        ),
    }
