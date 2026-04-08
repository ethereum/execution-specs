"""Nimbus Transition tool and fixture consumer interfaces."""

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
)
from ..validate_helpers import validate_test_result
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
from ..file_utils import dump_files_to_directory
from ..fixture_consumer_tool import FixtureConsumerTool
from ..transition_tool import TransitionTool


class NimbusTransitionTool(TransitionTool):
    """Nimbus `evm` Transition tool interface wrapper class."""

    default_binary = Path("t8n")
    detect_binary_pattern = re.compile(r"^Nimbus-t8n\b")
    version_flag: str = "--version"

    binary: Path
    cached_version: Optional[str] = None
    trace: bool

    def __init__(
        self,
        *,
        binary: Optional[Path] = None,
        trace: bool = False,
    ):
        """Initialize the Nimbus Transition tool interface."""
        super().__init__(
            exception_mapper=NimbusExceptionMapper(),
            binary=binary,
            trace=trace,
        )
        args = [str(self.binary), "--help"]
        try:
            result = subprocess.run(args, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            raise Exception(
                f"evm process unexpectedly returned "
                f"a non-zero status code: {e}."
            ) from e
        except Exception as e:
            raise Exception(
                f"Unexpected exception calling evm tool: {e}."
            ) from e
        self.help_string = result.stdout

    def version(self) -> str:
        """Get `evm` binary version."""
        if self.cached_version is None:
            self.cached_version = re.sub(
                r"\x1b\[0m", "", super().version()
            ).strip()

        return self.cached_version

    def is_fork_supported(self, fork: Fork) -> bool:
        """
        Return True if the fork is supported by the tool.

        If the fork is a transition fork, we want to check the fork it
        transitions to.
        """
        return fork.transition_tool_name() in self.help_string


class NimbusExceptionMapper(ExceptionMapper):
    """
    Translate between EEST exceptions and error strings returned by Nimbus.
    """

    mapping_substring: ClassVar[Dict[ExceptionBase, str]] = {
        TransactionException.TYPE_4_TX_CONTRACT_CREATION: (
            "set code transaction must not be a create transaction"
        ),
        TransactionException.INSUFFICIENT_ACCOUNT_FUNDS: (
            "invalid tx: not enough cash to send"
        ),
        TransactionException.TYPE_3_TX_MAX_BLOB_GAS_ALLOWANCE_EXCEEDED: (
            "would exceed maximum allowance"
        ),
        TransactionException.INSUFFICIENT_MAX_FEE_PER_BLOB_GAS: (
            "max fee per blob gas less than block blob gas fee"
        ),
        TransactionException.INSUFFICIENT_MAX_FEE_PER_GAS: (
            "max fee per gas less than block base fee"
        ),
        TransactionException.TYPE_3_TX_PRE_FORK: (
            "blob tx used but field env.ExcessBlobGas missing"
        ),
        TransactionException.TYPE_3_TX_INVALID_BLOB_VERSIONED_HASH: (
            "invalid tx: one of blobVersionedHash has invalid version"
        ),
        # TODO: temp solution until mapper for nimbus is fixed
        TransactionException.GAS_LIMIT_EXCEEDS_MAXIMUM: (
            "zero gasUsed but transactions present"
        ),
        # This message is the same as TYPE_3_TX_MAX_BLOB_GAS_ALLOWANCE_EXCEEDED
        TransactionException.TYPE_3_TX_BLOB_COUNT_EXCEEDED: (
            "exceeds maximum allowance"
        ),
        TransactionException.TYPE_3_TX_ZERO_BLOBS: (
            "blob transaction missing blob hashes"
        ),
        TransactionException.INTRINSIC_GAS_TOO_LOW: (
            "zero gasUsed but transactions present"
        ),
        TransactionException.INTRINSIC_GAS_BELOW_FLOOR_GAS_COST: (
            "intrinsic gas too low"
        ),
        TransactionException.INITCODE_SIZE_EXCEEDED: (
            "max initcode size exceeded"
        ),
        BlockException.RLP_BLOCK_LIMIT_EXCEEDED: (
            # TODO:
            "ExceededBlockSizeLimit: Exceeded block size limit"
        ),
        BlockException.INVALID_BASEFEE_PER_GAS: "invalid baseFee",
        BlockException.INVALID_BLOCK_NUMBER: (
            "Blocks must be numbered consecutively"
        ),
        BlockException.INVALID_BLOCK_TIMESTAMP_OLDER_THAN_PARENT: (
            "Invalid timestamp"
        ),
        BlockException.INVALID_GASLIMIT: "invalid gas limit",
        BlockException.INVALID_GAS_USED_ABOVE_LIMIT: (
            "gasUsed should be non negative and smaller or equal gasLimit"
        ),
        BlockException.INVALID_BLOCK_HASH: "blockhash mismatch",
        BlockException.INVALID_STATE_ROOT: "stateRoot mismatch",
        BlockException.INVALID_RECEIPTS_ROOT: "receiptRoot mismatch",
        BlockException.INVALID_LOG_BLOOM: "bloom mismatch",
    }
    mapping_regex: ClassVar[Dict[ExceptionBase, str]] = {}


class NimbusCLI(EthereumCLI):
    """Nimbus base class for the evmstate / eest_* binaries."""

    default_binary = Path("evmstate")
    detect_binary_pattern = re.compile(r"^Nimbus-evmstate\b")
    version_flag: str = "--version"
    cached_version: Optional[str] = None
    trace: bool

    def __init__(
        self,
        binary: Optional[Path] = None,
        block_binary: Optional[Path] = None,
        engine_binary: Optional[Path] = None,
        trace: bool = False,
    ):
        """Initialize the NimbusCLI class."""
        self.binary = binary if binary else self.default_binary
        self.block_binary = block_binary
        self.engine_binary = engine_binary
        self.trace = trace

    def run_command(
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
                "Unexpected exception calling nimbus tool."
            ) from e

    def validate_debug_dump(
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

        validate_call = " ".join(
            shlex.quote(arg) for arg in command
        )

        validate_script = textwrap.dedent(
            f"""\
            #!/bin/bash
            {validate_call}
            """
        )
        dump_files_to_directory(
            debug_output_path,
            {
                "validate_args.py": command,
                "validate_returncode.txt": result.returncode,
                "validate_stdout.txt": result.stdout,
                "validate_stderr.txt": result.stderr,
                "validate.sh+x": validate_script,
            },
        )
        shutil.copyfile(fixture_path, debug_fixture_path)


class NimbusFixtureConsumer(
    NimbusCLI,
    FixtureConsumerTool,
    fixture_formats=[
        StateFixture,
        BlockchainFixture,
        BlockchainEngineFixture,
    ],
):
    """Nimbus fixture consumer.

    Uses three separate binaries:
    - evmstate for state tests
    - eest_blockchain for block tests
    - eest_engine for engine tests
    """

    dir_cache: Dict[str, Dict[str, Dict[str, Any]]] = {}
    fixture_cache: Dict[str, Dict[str, Any]] = {}
    exception_mapper: ExceptionMapper = NimbusExceptionMapper()

    def get_dir_results(
        self,
        test_type: str,
        fixture_path: Path,
        debug_output_path: Optional[Path] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Run the appropriate binary once per fixture directory
        and cache all results indexed by test name.
        """
        dir_path = (
            fixture_path
            if fixture_path.is_dir()
            else fixture_path.parent
        )
        cache_key = f"{test_type}:{dir_path}"

        if cache_key not in self.dir_cache:
            workers = getattr(self, "workers", 1)

            if test_type == "statetest":
                # evmstate <dir> — outputs JSON array by default
                command = [
                    str(self.binary),
                    str(dir_path),
                ]
            elif test_type == "blocktest":
                # eest_blockchain --fast --json <dir>
                binary = self.block_binary or self.binary
                command = [
                    str(binary),
                    "--fast",
                    "--json",
                    str(dir_path),
                ]
            elif test_type == "enginetest":
                # eest_engine --fast --json <dir>
                binary = self.engine_binary or self.binary
                command = [
                    str(binary),
                    "--fast",
                    "--json",
                    str(dir_path),
                ]
            else:
                raise Exception(
                    f"Unknown test type: {test_type}"
                )

            result = self.run_command(command)

            if debug_output_path:
                self.validate_debug_dump(
                    command,
                    result,
                    fixture_path,
                    debug_output_path,
                )

            # Nimbus exits non-zero when tests fail but still
            # outputs JSON results. Parse JSON first.
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
                # Nimbus may omit fork or use null for error;
                # normalize before Pydantic validation.
                if "fork" not in r:
                    r["fork"] = ""
                if r.get("error") is None:
                    r["error"] = ""
                validated = result_model.model_validate(
                    r
                ).model_dump(by_alias=True)
                indexed[validated["name"]] = validated

            self.dir_cache[cache_key] = indexed

        return self.dir_cache[cache_key]

    def validate_test(
        self,
        test_type: str,
        label: str,
        fixture_path: Path,
        fixture_name: Optional[str] = None,
        debug_output_path: Optional[Path] = None,
    ) -> None:
        """Generic consume method using directory-level cache."""
        dir_results = self.get_dir_results(
            test_type=test_type,
            fixture_path=fixture_path,
            debug_output_path=debug_output_path,
        )
        if fixture_name:
            if fixture_name not in dir_results:
                return  # silently pass — nimbus skips pre-Merge forks
            validate_test_result(
                self.fixture_cache, self.exception_mapper,
                label, fixture_name, dir_results[fixture_name],
                fixture_path,
                is_engine=test_type == "enginetest",
                is_block=test_type == "blocktest",
                is_state=test_type == "statetest",
                exception_check=getattr(self, "exception_check", True),
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
        """Consume a single state test via evmstate."""
        self.validate_test(
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
        """Consume a single blockchain test via eest_blockchain."""
        self.validate_test(
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
        """Consume a single engine test via eest_engine."""
        self.validate_test(
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
        """Execute the appropriate nimbus fixture consumer."""
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
