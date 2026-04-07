"""Go-ethereum Transition tool interface."""

import json
import re
import shlex
import shutil
import subprocess
import textwrap
from functools import cache
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional

from execution_testing.exceptions import (
    BlockException,
    ExceptionBase,
    ExceptionMapper,
    TransactionException,
    UndefinedException,
)
from execution_testing.fixtures import (
    BlockchainEngineFixture,
    BlockchainFixture,
    FixtureFormat,
    StateFixture,
)
from execution_testing.forks import Fork

from ..cli_types import (
    BlockTestResult,
    EngineTestResult,
    FixtureTestResult,
    StateTestResult,
)
from ..ethereum_cli import EthereumCLI
from ..fixture_consumer_tool import FixtureConsumerTool
from ..transition_tool import TransitionTool, dump_files_to_directory


class GethExceptionMapper(ExceptionMapper):
    """Translate between EEST exceptions and error strings returned by Geth."""

    mapping_substring: ClassVar[Dict[ExceptionBase, str]] = {
        TransactionException.SENDER_NOT_EOA: "sender not an eoa",
        TransactionException.GAS_ALLOWANCE_EXCEEDED: "gas limit reached",
        TransactionException.INSUFFICIENT_ACCOUNT_FUNDS: (
            "insufficient funds for gas * price + value"
        ),
        TransactionException.INTRINSIC_GAS_TOO_LOW: "intrinsic gas too low",
        TransactionException.INTRINSIC_GAS_BELOW_FLOOR_GAS_COST: (
            "insufficient gas for floor data gas cost"
        ),
        TransactionException.NONCE_IS_MAX: "nonce has max value",
        TransactionException.TYPE_3_TX_MAX_BLOB_GAS_ALLOWANCE_EXCEEDED: (
            "would exceed maximum allowance"
        ),
        TransactionException.INSUFFICIENT_MAX_FEE_PER_BLOB_GAS: (
            "max fee per blob gas less than block blob gas fee"
        ),
        TransactionException.INSUFFICIENT_MAX_FEE_PER_GAS: (
            "max fee per gas less than block base fee"
        ),
        TransactionException.PRIORITY_GREATER_THAN_MAX_FEE_PER_GAS: (
            "max priority fee per gas higher than max fee per gas"
        ),
        TransactionException.TYPE_1_TX_PRE_FORK: (
            "transaction type not supported"
        ),
        TransactionException.TYPE_2_TX_PRE_FORK: (
            "transaction type not supported"
        ),
        TransactionException.TYPE_3_TX_PRE_FORK: (
            "transaction type not supported"
        ),
        TransactionException.TYPE_3_TX_INVALID_BLOB_VERSIONED_HASH: (
            "has invalid hash version"
        ),
        # This message is the same as TYPE_3_TX_MAX_BLOB_GAS_ALLOWANCE_EXCEEDED
        TransactionException.TYPE_3_TX_BLOB_COUNT_EXCEEDED: (
            "blob transaction has too many blobs"
        ),
        TransactionException.TYPE_3_TX_ZERO_BLOBS: (
            "blob transaction missing blob hashes"
        ),
        TransactionException.TYPE_3_TX_WITH_FULL_BLOBS: (
            "unexpected blob sidecar in transaction at index"
        ),
        TransactionException.TYPE_3_TX_CONTRACT_CREATION: (
            "input string too short for common.Address, "
            "decoding into (types.BlobTx).To"
        ),
        TransactionException.TYPE_4_EMPTY_AUTHORIZATION_LIST: (
            "EIP-7702 transaction with empty auth list"
        ),
        TransactionException.TYPE_4_TX_CONTRACT_CREATION: (
            "input string too short for common.Address, "
            "decoding into (types.SetCodeTx).To"
        ),
        TransactionException.GAS_LIMIT_EXCEEDS_MAXIMUM: (
            "transaction gas limit too high"
        ),
        TransactionException.TYPE_4_TX_PRE_FORK: (
            "transaction type not supported"
        ),
        TransactionException.INITCODE_SIZE_EXCEEDED: (
            "max initcode size exceeded"
        ),
        TransactionException.NONCE_MISMATCH_TOO_LOW: "nonce too low",
        TransactionException.NONCE_MISMATCH_TOO_HIGH: "nonce too high",
        BlockException.INCORRECT_BLOB_GAS_USED: "blob gas used mismatch",
        BlockException.INCORRECT_EXCESS_BLOB_GAS: "invalid excessBlobGas",
        BlockException.INVALID_VERSIONED_HASHES: (
            "invalid number of versionedHashes"
        ),
        BlockException.INVALID_REQUESTS: "invalid requests hash",
        BlockException.SYSTEM_CONTRACT_CALL_FAILED: (
            "system call failed to execute:"
        ),
        BlockException.INVALID_BLOCK_HASH: "blockhash mismatch",
        BlockException.RLP_BLOCK_LIMIT_EXCEEDED: (
            "block RLP-encoded size exceeds maximum"
        ),
        BlockException.INVALID_BAL_EXTRA_ACCOUNT: (
            "BAL change not reported in computed"
        ),
        BlockException.INVALID_BAL_MISSING_ACCOUNT: (
            "additional mutations compared to BAL"
        ),
        BlockException.INVALID_BLOCK_ACCESS_LIST: "unequal",
        BlockException.INVALID_BASEFEE_PER_GAS: "invalid baseFee",
        BlockException.INVALID_BLOCK_TIMESTAMP_OLDER_THAN_PARENT: (
            "invalid timestamp"
        ),
        BlockException.INVALID_GASLIMIT: "invalid gas limit",
        BlockException.INVALID_BLOCK_NUMBER: "invalid block number",
        BlockException.EXTRA_DATA_TOO_BIG: "invalid extradata length",
        BlockException.INVALID_RECEIPTS_ROOT: "invalid receipt root hash",
        BlockException.INVALID_LOG_BLOOM: "invalid bloom",
        BlockException.INVALID_STATE_ROOT: "invalid merkle root",
        BlockException.GAS_USED_OVERFLOW: "bal validation failure",
    }
    mapping_regex: ClassVar[Dict[ExceptionBase, str]] = {
        TransactionException.TYPE_3_TX_MAX_BLOB_GAS_ALLOWANCE_EXCEEDED: (
            r"blob gas used \d+ exceeds maximum allowance \d+"
        ),
        BlockException.BLOB_GAS_USED_ABOVE_LIMIT: (
            r"blob gas used \d+ exceeds maximum allowance \d+"
        ),
        BlockException.INVALID_GAS_USED_ABOVE_LIMIT: (
            r"invalid gasUsed: have \d+, gasLimit \d+"
        ),
        BlockException.INVALID_DEPOSIT_EVENT_LAYOUT: (
            r"invalid requests hash|failed to parse deposit logs"
        ),
        # Geth does not validate the sizes or offsets of the deposit
        # contract logs. As a workaround we have set
        # INVALID_DEPOSIT_EVENT_LAYOUT equal to INVALID_REQUESTS.
        #
        # Although this is out of spec, it is understood that this
        # will not cause an issue so long as the mainnet/testnet
        # deposit contracts don't change.
        #
        # The offsets are checked second and the sizes are checked
        # third within the `is_valid_deposit_event_data` function:
        # https://eips.ethereum.org/EIPS/eip-6110#block-validity
        #
        # EELS definition for `is_valid_deposit_event_data`:
        # https://github.com/ethereum/execution-specs/blob/5ddb904fa7ba27daeff423e78466744c51e8cb6a/src/ethereum/forks/prague/requests.py#L51
        # BAL Exceptions: TODO - review once all clients completed.
        BlockException.INVALID_BAL_EXTRA_ACCOUNT: (
            r"invalid block access list:"
        ),
        BlockException.INVALID_BAL_HASH: (r"invalid block access list:"),
        BlockException.INVALID_BAL_MISSING_ACCOUNT: (
            r"computed state diff contained mutated accounts "
            r"which weren't reported in BAL|"
            r"invalid block access list:"
        ),
        BlockException.INVALID_BLOCK_ACCESS_LIST: (
            r"difference between computed state diff and "
            r"BAL entry for account|invalid block access list:"
        ),
        BlockException.INCORRECT_BLOCK_FORMAT: (r"invalid block access list:"),
        BlockException.BLOCK_ACCESS_LIST_GAS_LIMIT_EXCEEDED: (
            r"block access list exceeds gas limit"
        ),
        BlockException.GAS_USED_OVERFLOW: (r"gas limit reached"),
        TransactionException.INTRINSIC_GAS_TOO_LOW: (
            r"insufficient gas for floor data gas cost"
        ),
    }


class GethEvm(EthereumCLI):
    """go-ethereum `evm` base class."""

    default_binary = Path("evm")
    detect_binary_pattern = re.compile(r"^evm(.exe)? version\b")
    cached_version: Optional[str] = None
    trace: bool

    def __init__(
        self,
        binary: Optional[Path] = None,
        trace: bool = False,
    ):
        """Initialize the GethEvm class."""
        self.binary = binary if binary else self.default_binary
        self.trace = trace
        self._info_metadata: Optional[Dict[str, Any]] = {}

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
        # our assumption is that each command element is a string
        assert all(isinstance(x, str) for x in command), (
            f"Not all elements of 'command' list are strings: {command}"
        )
        assert len(command) > 0

        # replace last value with debug fixture path
        debug_fixture_path = str(debug_output_path / "fixtures.json")
        command[-1] = debug_fixture_path

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
        shutil.copyfile(fixture_path, debug_fixture_path)

    @cache  # noqa
    def help(self, subcommand: str | None = None) -> str:
        """Return the help string, optionally for a subcommand."""
        help_command = [str(self.binary)]
        if subcommand:
            help_command.append(subcommand)
        help_command.append("--help")
        return self._run_command(help_command).stdout


class GethTransitionTool(GethEvm, TransitionTool):
    """go-ethereum `evm` Transition tool interface wrapper class."""

    subcommand: Optional[str] = "t8n"
    trace: bool
    t8n_use_stream = True
    supports_opcode_count: ClassVar[bool] = True

    def __init__(
        self,
        *,
        exception_mapper: Optional[ExceptionMapper] = None,
        binary: Optional[Path] = None,
        trace: bool = False,
    ):
        """Initialize the GethTransitionTool class."""
        if not exception_mapper:
            exception_mapper = GethExceptionMapper()
        GethEvm.__init__(self, binary=binary, trace=trace)
        TransitionTool.__init__(
            self, binary=binary, exception_mapper=exception_mapper, trace=trace
        )
        help_command = [str(self.binary), str(self.subcommand), "--help"]
        result = self._run_command(help_command)
        self.help_string = result.stdout

    def is_fork_supported(self, fork: Fork) -> bool:
        """
        Return True if the fork is supported by the tool.

        If the fork is a transition fork, we want to check the fork it
        transitions to.
        """
        return fork.transition_tool_name() in self.help_string


class GethFixtureConsumer(
    GethEvm,
    FixtureConsumerTool,
    fixture_formats=[StateFixture, BlockchainFixture, BlockchainEngineFixture],
):
    """Geth's implementation of the fixture consumer."""

    _dir_cache: Dict[str, Dict[str, Dict[str, Any]]] = {}
    exception_mapper: ExceptionMapper = GethExceptionMapper()

    def _get_dir_results(
        self,
        subcommand: str,
        fixture_path: Path,
        debug_output_path: Optional[Path] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Run a subcommand once per fixture directory and cache all results
        indexed by test name. Subsequent calls for the same directory
        return from cache instantly.
        """
        dir_path = fixture_path if fixture_path.is_dir() else fixture_path.parent
        cache_key = f"{subcommand}:{dir_path}"

        if cache_key not in self._dir_cache:
            workers = getattr(self, "workers", 1)
            global_options: List[str] = []
            subcommand_options: List[str] = ["--workers", str(workers)]
            if debug_output_path:
                global_options += ["--verbosity", "100"]
                subcommand_options += ["--trace"]

            command = (
                [str(self.binary)]
                + global_options
                + [subcommand]
                + subcommand_options
                + [str(dir_path)]
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

            # Find JSON array start (geth may output debug info before it)
            stdout = result.stdout
            json_start = stdout.find("[")
            if json_start < 0:
                raise Exception(
                    f"No JSON array in evm {subcommand} output:\n{stdout[:500]}"
                )
            result_json = json.loads(stdout[json_start:])
            if not isinstance(result_json, list):
                raise Exception(
                    f"Unexpected result from evm {subcommand}: {result_json}"
                )

            result_model: type[FixtureTestResult] = {
                "statetest": StateTestResult,
                "blocktest": BlockTestResult,
                "enginetest": EngineTestResult,
            }.get(subcommand, FixtureTestResult)

            indexed: Dict[str, Dict[str, Any]] = {}
            for r in result_json:
                validated = result_model.model_validate(r).model_dump(
                    by_alias=True
                )
                indexed[validated["name"]] = validated

            self._dir_cache[cache_key] = indexed

        return self._dir_cache[cache_key]

    _fixture_cache: Dict[str, Dict[str, Any]] = {}

    def _get_fixture_json(self, fixture_path: Path) -> Dict[str, Any]:
        """Load and cache fixture JSON keyed by file path."""
        key = str(fixture_path)
        if key not in self._fixture_cache:
            file_path = fixture_path if fixture_path.is_file() else None
            if file_path is None:
                return {}
            self._fixture_cache[key] = json.loads(file_path.read_text())
        return self._fixture_cache[key]

    def _get_expected_exceptions(
        self,
        fixture_path: Path,
        fixture_name: str,
        subcommand: str,
    ) -> List[ExceptionBase]:
        """Extract expected exceptions from a fixture for a given test case."""
        fixture_json = self._get_fixture_json(fixture_path)
        test_data = fixture_json.get(fixture_name, {})
        exceptions: List[ExceptionBase] = []

        if subcommand == "enginetest":
            for payload in test_data.get("engineNewPayloads", []):
                ve = payload.get("validationError")
                if ve:
                    exceptions.extend(ExceptionBase.from_str(e) for e in ve.split("|"))
        elif subcommand == "blocktest":
            for block in test_data.get("blocks", []):
                ee = block.get("expectException")
                if ee:
                    exceptions.extend(ExceptionBase.from_str(e) for e in ee.split("|"))
        elif subcommand == "statetest":
            for fork_posts in test_data.get("post", {}).values():
                for post in fork_posts:
                    ee = post.get("expectException")
                    if ee:
                        exceptions.extend(ExceptionBase.from_str(e) for e in ee.split("|"))

        return exceptions

    def _check_exception(
        self,
        label: str,
        fixture_name: str,
        error: str,
        expected: List[ExceptionBase],
    ) -> None:
        """Map client error through ExceptionMapper and compare to expected."""
        mapped = self.exception_mapper.message_to_exception(error)
        if isinstance(mapped, UndefinedException):
            raise AssertionError(
                f"{label} test: unmapped error for {fixture_name}:\n"
                f"  expected: {expected}\n"
                f"  error: {error}\n"
                f"  mapper: {mapped.mapper_name}"
            )
        if not any(exc in expected for exc in mapped):
            raise AssertionError(
                f"{label} test: wrong exception for {fixture_name}:\n"
                f"  expected: {expected}\n"
                f"  got: {mapped}\n"
                f"  error: {error}"
            )

    def _consume_test(
        self,
        subcommand: str,
        label: str,
        fixture_path: Path,
        fixture_name: Optional[str] = None,
        debug_output_path: Optional[Path] = None,
    ) -> None:
        """Generic consume method using directory-level cache."""
        dir_results = self._get_dir_results(
            subcommand=subcommand,
            fixture_path=fixture_path,
            debug_output_path=debug_output_path,
        )
        if fixture_name:
            if fixture_name not in dir_results:
                raise Exception(
                    f"{label} test result missing: {fixture_name} "
                    f"(client may have skipped or crashed on this test)"
                )
            result = dir_results[fixture_name]
            expected = self._get_expected_exceptions(
                fixture_path, fixture_name, subcommand,
            )
            error = result.get("error", "")

            if expected and error:
                self._check_exception(
                    label, fixture_name, error, expected,
                )

            if not result["pass"]:
                raise AssertionError(
                    f"{label} test failed: {error}"
                )
        else:
            failures = [r for r in dir_results.values() if not r["pass"]]
            if failures:
                raise Exception(
                    f"{label} test failed: \n"
                    + "\n".join(f"{r['name']}: {r['error']}" for r in failures)
                )

    def consume_state_test(
        self,
        fixture_path: Path,
        fixture_name: Optional[str] = None,
        debug_output_path: Optional[Path] = None,
    ) -> None:
        """Consume a single state test."""
        self._consume_test("statetest", "State", fixture_path, fixture_name, debug_output_path)

    def consume_blockchain_test(
        self,
        fixture_path: Path,
        fixture_name: Optional[str] = None,
        debug_output_path: Optional[Path] = None,
    ) -> None:
        """Consume a single blockchain test."""
        self._consume_test("blocktest", "Blockchain", fixture_path, fixture_name, debug_output_path)

    def consume_engine_test(
        self,
        fixture_path: Path,
        fixture_name: Optional[str] = None,
        debug_output_path: Optional[Path] = None,
    ) -> None:
        """Consume a single engine test."""
        self._consume_test("enginetest", "Engine", fixture_path, fixture_name, debug_output_path)

    def consume_fixture(
        self,
        fixture_format: FixtureFormat,
        fixture_path: Path,
        fixture_name: Optional[str] = None,
        debug_output_path: Optional[Path] = None,
    ) -> None:
        """
        Execute the appropriate geth fixture consumer for the fixture at
        `fixture_path`.
        """
        if fixture_format == BlockchainFixture:
            self.consume_blockchain_test(
                fixture_path=fixture_path,
                fixture_name=fixture_name,
                debug_output_path=debug_output_path,
            )
        elif fixture_format == BlockchainEngineFixture:
            self.consume_engine_test(
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
