"""Ethrex execution client fixture consumer interface."""

import json
import re
import shlex
import shutil
import subprocess
import textwrap
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

from ..cli_types import (
    BlockTestResult,
    EngineTestResult,
    FixtureTestResult,
    StateTestResult,
)
from ..ethereum_cli import EthereumCLI
from ..file_utils import dump_files_to_directory
from ..fixture_consumer_tool import FixtureConsumerTool


class EthrexExceptionMapper(ExceptionMapper):
    """Translate between EEST exceptions and error strings returned by Ethrex."""

    mapping_substring: ClassVar[Dict[ExceptionBase, str]] = {
        BlockException.INVALID_GASLIMIT: (
            "Gas limit changed more than allowed from the parent"
        ),
        TransactionException.TYPE_3_TX_MAX_BLOB_GAS_ALLOWANCE_EXCEEDED: (
            "Exceeded MAX_BLOB_GAS_PER_BLOCK"
        ),
        BlockException.INVALID_DEPOSIT_EVENT_LAYOUT: (
            "Invalid deposit request layout"
        ),
        BlockException.INVALID_REQUESTS: (
            "Requests hash does not match the one in "
            "the header after executing"
        ),
        BlockException.INVALID_RECEIPTS_ROOT: (
            "Receipts Root does not match the one in "
            "the header after executing"
        ),
        BlockException.INVALID_STATE_ROOT: (
            "World State Root does not match the one in "
            "the header after executing"
        ),
        BlockException.GAS_USED_OVERFLOW: "Block gas used overflow",
        BlockException.INVALID_BLOCK_ACCESS_LIST: (
            "Block access list hash does not match the one in "
            "the header after executing"
        ),
        BlockException.INVALID_BAL_HASH: (
            "Block access list hash does not match the one in "
            "the header after executing"
        ),
        BlockException.INVALID_BAL_EXTRA_ACCOUNT: (
            "Block access list hash does not match the one in "
            "the header after executing"
        ),
        BlockException.INVALID_BAL_MISSING_ACCOUNT: (
            "Block access list hash does not match the one in "
            "the header after executing"
        ),
        BlockException.INCORRECT_BLOCK_FORMAT: (
            "not in strictly ascending order for"
        ),
        BlockException.BLOCK_ACCESS_LIST_GAS_LIMIT_EXCEEDED: (
            "Block access list exceeds gas limit"
        ),
        BlockException.INVALID_GAS_USED: (
            "Gas used doesn't match value in header"
        ),
        BlockException.INCORRECT_BLOB_GAS_USED: (
            "Blob gas used doesn't match value in header"
        ),
        BlockException.INVALID_BASEFEE_PER_GAS: (
            "Base fee per gas is incorrect"
        ),
    }
    mapping_regex: ClassVar[Dict[ExceptionBase, str]] = {
        TransactionException.PRIORITY_GREATER_THAN_MAX_FEE_PER_GAS: (
            r"(?i)priority fee.* is greater than max fee.*"
        ),
        TransactionException.TYPE_4_EMPTY_AUTHORIZATION_LIST: (
            r"(?i)empty authorization list"
        ),
        TransactionException.SENDER_NOT_EOA: (
            r"reject transactions from senders with deployed code|"
            r"Sender account .* shouldn't be a contract"
        ),
        TransactionException.NONCE_MISMATCH_TOO_LOW: (
            r"nonce \d+ too low, expected \d+|Nonce mismatch.*"
        ),
        TransactionException.NONCE_MISMATCH_TOO_HIGH: (
            r"Nonce mismatch.*"
        ),
        TransactionException.TYPE_3_TX_MAX_BLOB_GAS_ALLOWANCE_EXCEEDED: (
            r"blob gas used \d+ exceeds maximum allowance \d+"
        ),
        TransactionException.TYPE_3_TX_ZERO_BLOBS: (
            r"blob transactions present in pre-cancun payload|"
            r"empty blobs|"
            r"Type 3 transaction without blobs"
        ),
        TransactionException.TYPE_3_TX_INVALID_BLOB_VERSIONED_HASH: (
            r"blob version not supported|"
            r"Invalid blob versioned hash"
        ),
        TransactionException.TYPE_2_TX_PRE_FORK: (
            r"Type 2 transactions are not supported "
            r"before the London fork"
        ),
        TransactionException.TYPE_3_TX_PRE_FORK: (
            r"blob versioned hashes not supported|"
            r"Type 3 transactions are not supported "
            r"before the Cancun fork"
        ),
        TransactionException.TYPE_4_TX_CONTRACT_CREATION: (
            r"unexpected length|"
            r"Contract creation in type 4 transaction|"
            r"Error decoding field 'to' of type "
            r"primitive_types::H160: InvalidLength"
        ),
        TransactionException.TYPE_3_TX_CONTRACT_CREATION: (
            r"unexpected length|"
            r"Contract creation in type 3 transaction|"
            r"Error decoding field 'to' of type "
            r"primitive_types::H160: InvalidLength"
        ),
        TransactionException.TYPE_4_TX_PRE_FORK: (
            r"eip 7702 transactions present in pre-prague payload|"
            r"Type 4 transactions are not supported "
            r"before the Prague fork"
        ),
        TransactionException.INSUFFICIENT_ACCOUNT_FUNDS: (
            r"lack of funds \(\d+\) for max fee \(\d+\)|"
            r"Insufficient account funds"
        ),
        TransactionException.INTRINSIC_GAS_TOO_LOW: (
            r"gas floor exceeds the gas limit|"
            r"call gas cost exceeds the gas limit|"
            r"Transaction gas limit lower than the minimum "
            r"gas cost to execute the transaction|"
            r"Transaction gas limit lower than the gas cost "
            r"floor for calldata tokens"
        ),
        TransactionException.INTRINSIC_GAS_BELOW_FLOOR_GAS_COST: (
            r"Transaction gas limit lower than the gas cost "
            r"floor for calldata tokens"
        ),
        TransactionException.INSUFFICIENT_MAX_FEE_PER_GAS: (
            r"gas price is less than basefee|"
            r"Insufficient max fee per gas"
        ),
        TransactionException.INSUFFICIENT_MAX_FEE_PER_BLOB_GAS: (
            r"blob gas price is greater than "
            r"max fee per blob gas|"
            r"Insufficient max fee per blob gas.*"
        ),
        TransactionException.INITCODE_SIZE_EXCEEDED: (
            r"create initcode size limit|Initcode size exceeded.*"
        ),
        TransactionException.NONCE_IS_MAX: r"Nonce is max",
        TransactionException.GAS_ALLOWANCE_EXCEEDED: (
            r"Gas allowance exceeded.*"
        ),
        BlockException.GAS_USED_OVERFLOW: r"Block gas used overflow.*",
        TransactionException.TYPE_3_TX_BLOB_COUNT_EXCEEDED: (
            r"Blob count exceeded.*"
        ),
        TransactionException.GASLIMIT_PRICE_PRODUCT_OVERFLOW: (
            r"Invalid transaction: "
            r"Gas limit price product overflow.*"
        ),
        TransactionException.GAS_LIMIT_EXCEEDS_MAXIMUM: (
            r"Invalid transaction: "
            r"Transaction gas limit exceeds maximum.*"
        ),
        BlockException.INVALID_DEPOSIT_EVENT_LAYOUT: (
            r"Invalid deposit request layout|"
            r"BAL validation failed.*"
        ),
        BlockException.SYSTEM_CONTRACT_CALL_FAILED: (
            r"System call failed.*"
        ),
        BlockException.SYSTEM_CONTRACT_EMPTY: (
            r"System contract:.* has no code after deployment"
        ),
        BlockException.INCORRECT_BLOB_GAS_USED: (
            r"Blob gas used doesn't match value in header"
        ),
        BlockException.RLP_STRUCTURES_ENCODING: (
            r"Error decoding field '\D+' of type \w+.*"
        ),
        BlockException.INCORRECT_EXCESS_BLOB_GAS: (
            r".* Excess blob gas is incorrect"
        ),
        BlockException.INVALID_BLOCK_HASH: (
            r"Invalid block hash. Expected \w+, got \w+"
        ),
        BlockException.RLP_BLOCK_LIMIT_EXCEEDED: (
            r"Maximum block size exceeded.*"
        ),
        BlockException.INVALID_BAL_EXTRA_ACCOUNT: (
            r"Block access list accounts not in strictly "
            r"ascending order.*|"
            r"BAL validation failed: account .* "
            r"was never accessed.*"
        ),
        BlockException.INVALID_BAL_MISSING_ACCOUNT: (
            r"absent from BAL"
        ),
        BlockException.INVALID_BLOCK_ACCESS_LIST: (
            r"Block access list contains index \d+ "
            r"exceeding max valid index \d+|"
            r"Failed to RLP decode BAL|"
            r"Block access list .+ not in strictly "
            r"ascending order.*|"
            r"BAL validation failed for "
            r"(tx \d+|system_tx|withdrawal): .*|"
            r"BAL validation failed: .*|"
            r"Block access list slot .+ is in both "
            r"storage_changes and storage_reads.*"
        ),
        BlockException.INCORRECT_BLOCK_FORMAT: (
            r"Block access list hash does not match "
            r"the one in the header after executing|"
            r"Block access list contains index \d+ "
            r"exceeding max valid index \d+|"
            r"Failed to RLP decode BAL|"
            r"Block access list accounts not in strictly "
            r"ascending order.*"
        ),
    }


class EthrexCLI(EthereumCLI):
    """Ethrex base class for the ef_tests-* binaries.

    Uses a base binary path (e.g. `ef_tests`) and derives per-type
    binaries by appending `-statetest`, `-blocktest`, `-enginetest`.
    """

    default_binary = Path("ef_tests-statetest")
    detect_binary_pattern = re.compile(r"^ef_tests-statetest\b")
    version_flag: str = "--version"
    cached_version: Optional[str] = None
    trace: bool

    def __init__(
        self,
        binary: Optional[Path] = None,
        trace: bool = False,
    ):
        """Initialize the EthrexCLI class."""
        self.binary = binary if binary else self.default_binary
        self.trace = trace

    def _binary_for(self, test_type: str) -> Path:
        """Derive the binary path for a given test type.

        If binary is `ef_tests-statetest`, derives siblings like
        `ef_tests-blocktest`. If binary is a base like `ef_tests`,
        appends `-statetest` etc.
        """
        bin_str = str(self.binary)
        # Strip any existing suffix to get the base
        for suffix in (
            "-statetest",
            "-blocktest",
            "-enginetest",
        ):
            if bin_str.endswith(suffix):
                base = bin_str[: -len(suffix)]
                return Path(f"{base}-{test_type}")
        # Binary is the base itself
        return Path(f"{bin_str}-{test_type}")

    def _run_command(
        self, command: List[str]
    ) -> subprocess.CompletedProcess:
        """Run a command and return the result."""
        try:
            return subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            raise Exception(
                "Command failed with non-zero status."
            ) from e
        except Exception as e:
            raise Exception(
                "Unexpected exception calling ethrex tool."
            ) from e

    def _consume_debug_dump(
        self,
        command: List[str],
        result: subprocess.CompletedProcess,
        fixture_path: Path,
        debug_output_path: Path,
    ) -> None:
        """Dump debug output for a consume command."""
        assert all(isinstance(x, str) for x in command), (
            f"Not all elements of 'command' list are strings: "
            f"{command}"
        )
        assert len(command) > 0

        debug_fixture_path = str(
            debug_output_path / "fixtures.json"
        )

        consume_direct_call = " ".join(
            shlex.quote(arg) for arg in command
        )

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


class EthrexFixtureConsumer(
    EthrexCLI,
    FixtureConsumerTool,
    fixture_formats=[
        StateFixture,
        BlockchainFixture,
        BlockchainEngineFixture,
    ],
):
    """Ethrex's implementation of the fixture consumer.

    Uses separate binaries per test type:
    ef_tests-statetest, ef_tests-blocktest, ef_tests-enginetest.
    All use --path <dir> --json --workers N.
    """

    _dir_cache: Dict[str, Dict[str, Dict[str, Any]]] = {}
    _fixture_cache: Dict[str, Dict[str, Any]] = {}
    exception_mapper: ExceptionMapper = EthrexExceptionMapper()

    def _get_dir_results(
        self,
        test_type: str,
        fixture_path: Path,
        debug_output_path: Optional[Path] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Run a binary once per fixture directory and cache all
        results indexed by test name.
        """
        dir_path = (
            fixture_path
            if fixture_path.is_dir()
            else fixture_path.parent
        )
        cache_key = f"{test_type}:{dir_path}"

        if cache_key not in self._dir_cache:
            workers = getattr(self, "workers", 1)
            binary = self._binary_for(test_type)

            command = [
                str(binary),
                "--path",
                str(dir_path),
                "--json",
                "--workers",
                str(workers),
            ]
            result = self._run_command(command)

            if debug_output_path:
                self._consume_debug_dump(
                    command,
                    result,
                    fixture_path,
                    debug_output_path,
                )

            # Ethrex exits non-zero when any test fails, but still
            # outputs JSON results. Parse JSON first, only fail if missing.
            stdout = result.stdout
            json_start = stdout.find("[")
            if json_start < 0:
                raise Exception(
                    f"No JSON array in {test_type} output:\n"
                    f"{stdout[:500]}"
                )
            result_json = json.loads(stdout[json_start:])
            if not isinstance(result_json, list):
                raise Exception(
                    f"Unexpected result from {test_type}: "
                    f"{result_json}"
                )

            result_model: type[FixtureTestResult] = {
                "statetest": StateTestResult,
                "blocktest": BlockTestResult,
                "enginetest": EngineTestResult,
            }.get(test_type, FixtureTestResult)

            indexed: Dict[str, Dict[str, Any]] = {}
            for r in result_json:
                # Ethrex blocktest/enginetest may omit fork
                # and use null for error; normalize before
                # Pydantic validation.
                if "fork" not in r:
                    r["fork"] = ""
                if r.get("error") is None:
                    r["error"] = ""
                validated = result_model.model_validate(
                    r
                ).model_dump(by_alias=True)
                indexed[validated["name"]] = validated

            self._dir_cache[cache_key] = indexed

        return self._dir_cache[cache_key]

    def _get_fixture_json(
        self, fixture_path: Path
    ) -> Dict[str, Any]:
        """Load and cache fixture JSON keyed by file path."""
        key = str(fixture_path)
        if key not in self._fixture_cache:
            file_path = (
                fixture_path if fixture_path.is_file() else None
            )
            if file_path is None:
                return {}
            self._fixture_cache[key] = json.loads(
                file_path.read_text()
            )
        return self._fixture_cache[key]

    def _get_expected_exceptions(
        self,
        fixture_path: Path,
        fixture_name: str,
        test_type: str,
    ) -> List[ExceptionBase]:
        """Extract expected exceptions from a fixture."""
        fixture_json = self._get_fixture_json(fixture_path)
        test_data = fixture_json.get(fixture_name, {})
        exceptions: List[ExceptionBase] = []

        if test_type == "enginetest":
            for payload in test_data.get(
                "engineNewPayloads", []
            ):
                ve = payload.get("validationError")
                if ve:
                    exceptions.extend(
                        ExceptionBase.from_str(e)
                        for e in ve.split("|")
                    )
        elif test_type == "blocktest":
            for block in test_data.get("blocks", []):
                ee = block.get("expectException")
                if ee:
                    exceptions.extend(
                        ExceptionBase.from_str(e)
                        for e in ee.split("|")
                    )
        elif test_type == "statetest":
            for fork_posts in test_data.get(
                "post", {}
            ).values():
                for post in fork_posts:
                    ee = post.get("expectException")
                    if ee:
                        exceptions.extend(
                            ExceptionBase.from_str(e)
                            for e in ee.split("|")
                        )

        return exceptions

    def _check_exception(
        self,
        label: str,
        fixture_name: str,
        error: str,
        expected: List[ExceptionBase],
    ) -> None:
        """Map client error and compare to expected exceptions."""
        mapped = self.exception_mapper.message_to_exception(
            error
        )
        if isinstance(mapped, UndefinedException):
            raise AssertionError(
                f"{label} test: unmapped error for "
                f"{fixture_name}:\n"
                f"  expected: {expected}\n"
                f"  error: {error}\n"
                f"  mapper: {mapped.mapper_name}"
            )
        if not any(exc in expected for exc in mapped):
            raise AssertionError(
                f"{label} test: wrong exception for "
                f"{fixture_name}:\n"
                f"  expected: {expected}\n"
                f"  got: {mapped}\n"
                f"  error: {error}"
            )

    def _consume_test(
        self,
        test_type: str,
        label: str,
        fixture_path: Path,
        fixture_name: Optional[str] = None,
        debug_output_path: Optional[Path] = None,
    ) -> None:
        """Generic consume method using directory-level cache."""
        dir_results = self._get_dir_results(
            test_type=test_type,
            fixture_path=fixture_path,
            debug_output_path=debug_output_path,
        )
        if fixture_name:
            if fixture_name not in dir_results:
                raise Exception(
                    f"{label} test result missing: "
                    f"{fixture_name} "
                    f"(client may have skipped or crashed "
                    f"on this test)"
                )
            result = dir_results[fixture_name]
            expected = self._get_expected_exceptions(
                fixture_path,
                fixture_name,
                test_type,
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
            failures = [
                r
                for r in dir_results.values()
                if not r["pass"]
            ]
            if failures:
                raise Exception(
                    f"{label} test failed: \n"
                    + "\n".join(
                        f"{r['name']}: {r['error']}"
                        for r in failures
                    )
                )

    def consume_state_test(
        self,
        fixture_path: Path,
        fixture_name: Optional[str] = None,
        debug_output_path: Optional[Path] = None,
    ) -> None:
        """Consume a single state test."""
        self._consume_test(
            "statetest",
            "State",
            fixture_path,
            fixture_name,
            debug_output_path,
        )

    def consume_blockchain_test(
        self,
        fixture_path: Path,
        fixture_name: Optional[str] = None,
        debug_output_path: Optional[Path] = None,
    ) -> None:
        """Consume a single blockchain test."""
        self._consume_test(
            "blocktest",
            "Blockchain",
            fixture_path,
            fixture_name,
            debug_output_path,
        )

    def consume_engine_test(
        self,
        fixture_path: Path,
        fixture_name: Optional[str] = None,
        debug_output_path: Optional[Path] = None,
    ) -> None:
        """Consume a single engine test."""
        self._consume_test(
            "enginetest",
            "Engine",
            fixture_path,
            fixture_name,
            debug_output_path,
        )

    def consume_fixture(
        self,
        fixture_format: FixtureFormat,
        fixture_path: Path,
        fixture_name: Optional[str] = None,
        debug_output_path: Optional[Path] = None,
    ) -> None:
        """Execute the appropriate ethrex fixture consumer."""
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
                f"Fixture format "
                f"{fixture_format.format_name} "
                f"not supported by {self.binary}"
            )
