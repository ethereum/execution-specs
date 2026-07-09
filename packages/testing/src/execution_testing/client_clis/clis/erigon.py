"""Erigon execution client transition tool."""

import json
import re
import shlex
import shutil
import subprocess
import textwrap
from functools import cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from execution_testing.exceptions import (
    BlockException,
    ExceptionMapper,
    TransactionException,
)
from execution_testing.fixtures import (
    BlockchainFixture,
    FixtureFormat,
    StateFixture,
)

from ..ethereum_cli import EthereumCLI
from ..fixture_consumer_tool import FixtureConsumerTool


class ErigonExceptionMapper(ExceptionMapper):
    """Erigon exception mapper."""

    mapping_substring = {
        TransactionException.SENDER_NOT_EOA: "sender not an eoa",
        TransactionException.INITCODE_SIZE_EXCEEDED: (
            "max initcode size exceeded"
        ),
        TransactionException.INSUFFICIENT_ACCOUNT_FUNDS: (
            "insufficient funds for gas * price + value"
        ),
        TransactionException.NONCE_IS_MAX: "nonce has max value",
        TransactionException.INTRINSIC_GAS_TOO_LOW: "intrinsic gas too low",
        TransactionException.INTRINSIC_GAS_BELOW_FLOOR_GAS_COST: (
            "intrinsic gas too low"
        ),
        TransactionException.INSUFFICIENT_MAX_FEE_PER_GAS: (
            "fee cap less than block base fee"
        ),
        TransactionException.PRIORITY_GREATER_THAN_MAX_FEE_PER_GAS: (
            "tip higher than fee cap"
        ),
        TransactionException.INSUFFICIENT_MAX_FEE_PER_BLOB_GAS: (
            "max fee per blob gas too low"
        ),
        TransactionException.NONCE_MISMATCH_TOO_LOW: "nonce too low",
        TransactionException.NONCE_MISMATCH_TOO_HIGH: "nonce too high",
        TransactionException.GAS_ALLOWANCE_EXCEEDED: "gas limit reached",
        TransactionException.INVALID_CHAINID: "invalid chain id for signer",
        TransactionException.INVALID_SIGNATURE_VRS: (
            "invalid transaction v, r, s values"
        ),
        TransactionException.TYPE_3_TX_PRE_FORK: (
            "blob txn is not supported by signer"
        ),
        TransactionException.TYPE_3_TX_INVALID_BLOB_VERSIONED_HASH: (
            "invalid blob versioned hash, must start with "
            "VERSIONED_HASH_VERSION_KZG"
        ),
        TransactionException.TYPE_3_TX_BLOB_COUNT_EXCEEDED: (
            "blob transaction has too many blobs"
        ),
        TransactionException.TYPE_3_TX_ZERO_BLOBS: (
            "a blob stx must contain at least one blob"
        ),
        TransactionException.TYPE_3_TX_WITH_FULL_BLOBS: (
            "rlp: expected String or Byte"
        ),
        TransactionException.TYPE_3_TX_CONTRACT_CREATION: (
            "wrong size for To: 0"
        ),
        TransactionException.TYPE_3_TX_MAX_BLOB_GAS_ALLOWANCE_EXCEEDED: (
            "blobs/blobgas exceeds max"
        ),
        TransactionException.TYPE_4_EMPTY_AUTHORIZATION_LIST: (
            "SetCodeTransaction without authorizations is invalid"
        ),
        TransactionException.TYPE_4_TX_CONTRACT_CREATION: (
            "wrong size for To: 0"
        ),
        TransactionException.TYPE_4_TX_PRE_FORK: (
            "setCode tx is not supported by signer"
        ),
        BlockException.INVALID_DEPOSIT_EVENT_LAYOUT: (
            "could not parse requests logs"
        ),
        BlockException.SYSTEM_CONTRACT_EMPTY: (
            "Syscall failure: Empty Code at"
        ),
        BlockException.SYSTEM_CONTRACT_CALL_FAILED: (
            "Unprecedented Syscall failure"
        ),
        BlockException.INVALID_REQUESTS: (
            "invalid requests root hash in header"
        ),
        BlockException.INVALID_BLOCK_HASH: "invalid block hash",
        BlockException.RLP_BLOCK_LIMIT_EXCEEDED: "block exceeds max rlp size",
        BlockException.INVALID_BASEFEE_PER_GAS: (
            "invalid block: invalid baseFee"
        ),
        BlockException.INVALID_BLOCK_TIMESTAMP_OLDER_THAN_PARENT: (
            "invalid block: timestamp older than parent"
        ),
        BlockException.INVALID_BLOCK_NUMBER: "invalid block number",
        BlockException.EXTRA_DATA_TOO_BIG: (
            "invalid block: extra-data longer than 32 bytes"
        ),
        BlockException.INVALID_GASLIMIT: "invalid block: invalid gas limit",
        BlockException.INVALID_STATE_ROOT: "invalid block: wrong trie root",
        BlockException.INVALID_RECEIPTS_ROOT: "receiptHash mismatch",
        BlockException.INVALID_LOG_BLOOM: "invalid bloom",
        BlockException.INCORRECT_BLOCK_FORMAT: "invalid block access list",
        BlockException.GAS_USED_OVERFLOW: "block gas used overflow",
    }
    mapping_regex = {
        BlockException.INVALID_BAL_HASH: (
            r"invalid block access list|block access list mismatch"
        ),
        BlockException.INVALID_BLOCK_ACCESS_LIST: (
            r"invalid block access list|block access list mismatch"
        ),
        BlockException.INCORRECT_BLOCK_FORMAT: (r"invalid block access list"),
        BlockException.BLOCK_ACCESS_LIST_GAS_LIMIT_EXCEEDED: (
            r"block access list too large"
        ),
        TransactionException.GAS_LIMIT_EXCEEDS_MAXIMUM: (
            r"gas limit too high"
        ),
        BlockException.INCORRECT_BLOB_GAS_USED: (
            r"blobGasUsed by execution: \d+, in header: \d+"
        ),
        BlockException.INCORRECT_EXCESS_BLOB_GAS: (
            r"invalid excessBlobGas: have \d+, want \d+"
        ),
        BlockException.INVALID_GAS_USED: (
            r"gas used by execution: \w+, in header: \w+"
        ),
        BlockException.INVALID_GAS_USED_ABOVE_LIMIT: (
            r"invalid gasUsed: have \d+, gasLimit \d+"
        ),
    }


class ErigonEvm(EthereumCLI):
    """
    Erigon `evm` base class.

    Erigon's `evm` tool shares go-ethereum's command surface (`evm version`,
    `evm statetest`, `evm blocktest`, `evm t8n`) and prints an
    indistinguishable ``evm version <semver>...`` banner, so the version string
    alone cannot tell the two apart. ``detect_binary`` instead probes the
    binary itself: Erigon's `evm` exposes an ``enginextest`` subcommand (its
    engine-x test runner) that go-ethereum's `evm` does not, which is a stable,
    version-independent fingerprint.
    """

    default_binary = Path("evm")
    # Cheap pre-filter shared with go-ethereum; the binary probe in
    # `detect_binary` is what actually confirms Erigon.
    detect_binary_pattern = re.compile(r"^evm(\.exe)? version\b")
    # Erigon-only subcommand, used as the disambiguating fingerprint.
    erigon_marker = "enginextest"
    cached_version: Optional[str] = None
    trace: bool

    def __init__(
        self,
        binary: Optional[Path] = None,
        trace: bool = False,
    ):
        """Initialize the ErigonEvm class."""
        self.binary = binary if binary else self.default_binary
        self.trace = trace
        self._info_metadata: Optional[Dict[str, Any]] = {}

    @classmethod
    def detect_binary(
        cls, binary_output: str, binary: Optional[Path] = None
    ) -> bool:
        """
        Confirm the binary is Erigon's `evm`, not go-ethereum's.

        Both print ``evm version ...``; after that cheap check passes we probe
        the binary's ``--help`` for Erigon's ``enginextest`` subcommand.
        Without a binary to probe (or if the probe fails) we cannot positively
        identify Erigon, so we decline and let go-ethereum's consumer claim it.
        """
        if not super().detect_binary(binary_output, binary):
            return False
        if binary is None:
            return False
        try:
            help_output = subprocess.run(
                [str(binary), "--help"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=10,
            ).stdout
        except Exception:
            return False
        return cls.erigon_marker in help_output

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
        command: List[str],
        result: subprocess.CompletedProcess,
        fixture_path: Path,
        debug_output_path: Path,
    ) -> None:
        assert all(isinstance(x, str) for x in command), (
            f"Not all elements of 'command' list are strings: {command}"
        )
        assert len(command) > 0

        # the fixture path is always the last argument
        debug_fixture_path = str(debug_output_path / "fixtures.json")
        command[-1] = debug_fixture_path

        consume_direct_call = " ".join(shlex.quote(arg) for arg in command)
        consume_direct_script = textwrap.dedent(
            f"""\
            #!/bin/bash
            {consume_direct_call}
            """
        )
        from ..transition_tool import dump_files_to_directory

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
        shutil.copyfile(fixture_path, debug_fixture_path)

    @cache  # noqa
    def help(self, subcommand: str | None = None) -> str:
        """Return the help string, optionally for a subcommand."""
        help_command = [str(self.binary)]
        if subcommand:
            help_command.append(subcommand)
        help_command.append("--help")
        return self._run_command(help_command).stdout


class ErigonFixtureConsumer(
    ErigonEvm,
    FixtureConsumerTool,
    fixture_formats=[StateFixture, BlockchainFixture],
):
    """
    Erigon's implementation of the fixture consumer.

    Mirrors ``GethFixtureConsumer`` but passes ``--jsonout`` to ``statetest``
    and ``blocktest``: unlike go-ethereum, Erigon defaults to human-readable
    output and only emits the JSON result array (``[{name, pass, error, ...}]``
    on stdout) when ``--jsonout`` is given. Without it the consumer's
    ``json.loads`` fails on the first non-JSON line.
    """

    def consume_blockchain_test(
        self,
        fixture_path: Path,
        fixture_name: Optional[str] = None,
        debug_output_path: Optional[Path] = None,
    ) -> None:
        """Consume a single blockchain test."""
        subcommand = "blocktest"
        subcommand_options = ["--jsonout"]
        if debug_output_path:
            subcommand_options += ["--verbosity", "100"]

        if fixture_name:
            subcommand_options += ["--run", re.escape(fixture_name)]

        command = (
            [str(self.binary)]
            + [subcommand]
            + subcommand_options
            + [str(fixture_path)]
        )

        result = self._run_command(command)

        if debug_output_path:
            self._consume_debug_dump(
                command, result, fixture_path, debug_output_path
            )

        if result.returncode != 0:
            raise Exception(
                f"Unexpected exit code:\n{' '.join(command)}\n\n"
                f"Error:\n{result.stderr}"
            )

        result_json = json.loads(result.stdout)
        if not isinstance(result_json, list):
            raise Exception(
                f"Unexpected result from evm blocktest: {result_json}"
            )

        if any(not test_result["pass"] for test_result in result_json):
            exception_text = "Blockchain test failed: \n" + "\n".join(
                f"{test_result['name']}: " + test_result["error"]
                for test_result in result_json
                if not test_result["pass"]
            )
            raise Exception(exception_text)

    @cache  # noqa
    def consume_state_test_file(
        self,
        fixture_path: Path,
        debug_output_path: Optional[Path] = None,
    ) -> List[Dict[str, Any]]:
        """
        Consume an entire state test file.

        `evm statetest` executes every test in the file at once, so the result
        is cached and `consume_state_test` selects the requested test from it.
        """
        subcommand = "statetest"
        subcommand_options = ["--jsonout"]
        if debug_output_path:
            subcommand_options += ["--json"]

        command = (
            [str(self.binary)]
            + [subcommand]
            + subcommand_options
            + [str(fixture_path)]
        )
        result = self._run_command(command)

        if debug_output_path:
            self._consume_debug_dump(
                command, result, fixture_path, debug_output_path
            )

        if result.returncode != 0:
            raise Exception(
                f"Unexpected exit code:\n{' '.join(command)}\n\n"
                f"Error:\n{result.stderr}"
            )

        result_json = json.loads(result.stdout)
        if not isinstance(result_json, list):
            raise Exception(
                f"Unexpected result from evm statetest: {result_json}"
            )
        return result_json

    def consume_state_test(
        self,
        fixture_path: Path,
        fixture_name: Optional[str] = None,
        debug_output_path: Optional[Path] = None,
    ) -> None:
        """Consume a single state test from the cached file results."""
        file_results = self.consume_state_test_file(
            fixture_path=fixture_path,
            debug_output_path=debug_output_path,
        )
        if fixture_name:
            test_result = [
                test_result
                for test_result in file_results
                if test_result["name"] == fixture_name
            ]
            assert len(test_result) < 2, (
                f"Multiple test results for {fixture_name}"
            )
            assert len(test_result) == 1, (
                f"Test result for {fixture_name} missing"
            )
            assert test_result[0]["pass"], (
                f"State test failed: {test_result[0]['error']}"
            )
        else:
            if any(not test_result["pass"] for test_result in file_results):
                exception_text = "State test failed: \n" + "\n".join(
                    f"{test_result['name']}: " + test_result["error"]
                    for test_result in file_results
                    if not test_result["pass"]
                )
                raise Exception(exception_text)

    def consume_fixture(
        self,
        fixture_format: FixtureFormat,
        fixture_path: Path,
        fixture_name: Optional[str] = None,
        debug_output_path: Optional[Path] = None,
    ) -> None:
        """Dispatch to the appropriate Erigon fixture consumer."""
        if fixture_format == BlockchainFixture:
            self.consume_blockchain_test(
                fixture_path=fixture_path,
                fixture_name=fixture_name,
                debug_output_path=debug_output_path,
            )
        elif fixture_format == StateFixture:
            self.consume_state_test(
                fixture_path=fixture_path,
                fixture_name=fixture_name,
                debug_output_path=debug_output_path,
            )
        else:
            raise Exception(
                f"Fixture format {fixture_format.format_name} "
                f"not supported by {self.binary}"
            )
