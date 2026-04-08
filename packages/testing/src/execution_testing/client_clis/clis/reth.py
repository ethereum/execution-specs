"""Reth execution client fixture consumer interface."""

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

from ..cli_types import (
    BlockTestResult,
    EngineTestResult,
    FixtureTestResult,
    StateTestResult,
)
from ..ethereum_cli import EthereumCLI
from ..file_utils import dump_files_to_directory
from ..fixture_consumer_tool import FixtureConsumerTool


class RethExceptionMapper(ExceptionMapper):
    """Translate between EEST exceptions and error strings returned by reth."""

    mapping_substring: ClassVar[Dict[ExceptionBase, str]] = {
        TransactionException.SENDER_NOT_EOA: (
            "reject transactions from senders with deployed code"
        ),
        TransactionException.INSUFFICIENT_ACCOUNT_FUNDS: "lack of funds",
        TransactionException.INITCODE_SIZE_EXCEEDED: (
            "create initcode size limit"
        ),
        TransactionException.INSUFFICIENT_MAX_FEE_PER_GAS: (
            "gas price is less than basefee"
        ),
        TransactionException.PRIORITY_GREATER_THAN_MAX_FEE_PER_GAS: (
            "priority fee is greater than max fee"
        ),
        TransactionException.GASLIMIT_PRICE_PRODUCT_OVERFLOW: "overflow",
        TransactionException.TYPE_3_TX_CONTRACT_CREATION: (
            "unexpected length"
        ),
        TransactionException.TYPE_3_TX_WITH_FULL_BLOBS: "unexpected list",
        TransactionException.TYPE_3_TX_INVALID_BLOB_VERSIONED_HASH: (
            "blob version not supported"
        ),
        TransactionException.TYPE_3_TX_ZERO_BLOBS: "empty blobs",
        TransactionException.TYPE_4_EMPTY_AUTHORIZATION_LIST: (
            "empty authorization list"
        ),
        TransactionException.TYPE_4_TX_CONTRACT_CREATION: (
            "unexpected length"
        ),
        TransactionException.TYPE_4_TX_PRE_FORK: (
            "eip 7702 transactions present in pre-prague payload"
        ),
        BlockException.INVALID_REQUESTS: (
            "mismatched block requests hash"
        ),
        BlockException.INVALID_RECEIPTS_ROOT: "receipt root mismatch",
        BlockException.INVALID_STATE_ROOT: (
            "mismatched block state root"
        ),
        BlockException.INVALID_BLOCK_HASH: "block hash mismatch",
        BlockException.INVALID_GAS_USED: "block gas used mismatch",
        BlockException.RLP_BLOCK_LIMIT_EXCEEDED: "block is too large: ",
        BlockException.INVALID_BASEFEE_PER_GAS: (
            "block base fee mismatch"
        ),
        BlockException.EXTRA_DATA_TOO_BIG: "invalid payload extra data",
        BlockException.INVALID_LOG_BLOOM: (
            "header bloom filter mismatch"
        ),
    }
    mapping_regex: ClassVar[Dict[ExceptionBase, str]] = {
        TransactionException.NONCE_MISMATCH_TOO_LOW: (
            r"nonce \d+ too low, expected \d+"
        ),
        TransactionException.NONCE_MISMATCH_TOO_HIGH: (
            r"nonce \d+ too high, expected \d+"
        ),
        TransactionException.INSUFFICIENT_MAX_FEE_PER_BLOB_GAS: (
            r"blob gas price \(\d+\) is greater than "
            r"max fee per blob gas \(\d+\)"
        ),
        TransactionException.INTRINSIC_GAS_TOO_LOW: (
            r"call gas cost \(\d+\) exceeds the gas limit \(\d+\)"
        ),
        TransactionException.INTRINSIC_GAS_BELOW_FLOOR_GAS_COST: (
            r"gas floor \(\d+\) exceeds the gas limit \(\d+\)"
        ),
        TransactionException.TYPE_3_TX_MAX_BLOB_GAS_ALLOWANCE_EXCEEDED: (
            r"blob gas used \d+ exceeds maximum allowance \d+"
        ),
        TransactionException.TYPE_3_TX_BLOB_COUNT_EXCEEDED: (
            r"too many blobs, have \d+, max \d+"
        ),
        TransactionException.TYPE_3_TX_PRE_FORK: (
            r"blob transactions present in pre-cancun payload|"
            r"empty blobs"
        ),
        TransactionException.GAS_ALLOWANCE_EXCEEDED: (
            r"transaction gas limit \w+ is more than blocks "
            r"available gas \w+"
        ),
        TransactionException.GAS_LIMIT_EXCEEDS_MAXIMUM: (
            r"transaction gas limit.*is greater than the cap"
        ),
        BlockException.SYSTEM_CONTRACT_CALL_FAILED: (
            r"failed to apply .* requests contract call"
        ),
        BlockException.INCORRECT_BLOB_GAS_USED: (
            r"blob gas used mismatch|"
            r"blob gas used \d+ is not a multiple of "
            r"blob gas per blob"
        ),
        BlockException.INCORRECT_EXCESS_BLOB_GAS: (
            r"excess blob gas \d+ is not a multiple of "
            r"blob gas per blob|"
            r"invalid excess blob gas"
        ),
        BlockException.INVALID_GAS_USED_ABOVE_LIMIT: (
            r"block used gas \(\d+\) is greater than "
            r"gas limit \(\d+\)"
        ),
        BlockException.INVALID_GASLIMIT: (
            r"child gas_limit \d+ max .* is .*|"
            r"child gas_limit \d+ is below the max allowed "
            r"decrease .*|"
            r"child gas limit \d+ is below the minimum "
            r"allowed limit"
        ),
        BlockException.INVALID_BLOCK_TIMESTAMP_OLDER_THAN_PARENT: (
            r"block timestamp \d+ is in the past compared to "
            r"the parent timestamp \d+"
        ),
        BlockException.INVALID_BLOCK_NUMBER: (
            r"block number \d+ does not match parent "
            r"block number \d+"
        ),
        BlockException.GAS_USED_OVERFLOW: (
            r"transaction gas limit \w+ is more than blocks "
            r"available gas \w+"
        ),
        # BAL Exceptions: TODO - review once all clients completed.
        BlockException.INVALID_BAL_EXTRA_ACCOUNT: (
            r"block access list hash mismatch"
        ),
        BlockException.INVALID_BAL_HASH: (
            r"block access list hash mismatch"
        ),
        BlockException.INVALID_BAL_MISSING_ACCOUNT: (
            r"block access list hash mismatch"
        ),
        BlockException.INVALID_BLOCK_ACCESS_LIST: (
            r"block access list hash mismatch"
        ),
        BlockException.INCORRECT_BLOCK_FORMAT: (
            r"block access list hash mismatch"
        ),
        # Reth does not validate the sizes or offsets of the deposit
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
        BlockException.INVALID_DEPOSIT_EVENT_LAYOUT: (
            r"failed to decode deposit requests from receipts|"
            r"mismatched block requests hash"
        ),
    }


class RethCLI(EthereumCLI):
    """Reth `ef-test-runner` base class."""

    default_binary = Path("ef-test-runner")
    detect_binary_pattern = re.compile(r"^ef-test-runner\b")
    version_flag: str = "--version"
    cached_version: Optional[str] = None
    trace: bool

    def __init__(
        self,
        binary: Optional[Path] = None,
        state_binary: Optional[Path] = None,
        trace: bool = False,
    ):
        """Initialize the RethCLI class."""
        self.binary = binary if binary else self.default_binary
        self.state_binary = state_binary
        self.trace = trace

    def run_command(
        self, command: List[str]
    ) -> subprocess.CompletedProcess:
        """Run a command and return the result."""
        import os
        env = os.environ.copy()
        env.setdefault("RAYON_NUM_THREADS", "4")
        try:
            return subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
            )
        except subprocess.CalledProcessError as e:
            raise Exception(
                "Command failed with non-zero status."
            ) from e
        except Exception as e:
            raise Exception(
                "Unexpected exception calling reth tool."
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
        command[-1] = debug_fixture_path

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


class RethFixtureConsumer(
    RethCLI,
    FixtureConsumerTool,
    fixture_formats=[
        StateFixture,
        BlockchainEngineFixture,
    ],
):
    """Reth's implementation of the fixture consumer.

    Uses two binaries:
    - ef-test-runner for block and engine tests
    - revme (revm) for state tests
    """

    dir_cache: Dict[str, Dict[str, Dict[str, Any]]] = {}
    fixture_cache: Dict[str, Dict[str, Any]] = {}
    exception_mapper: ExceptionMapper = RethExceptionMapper()

    def get_dir_results(
        self,
        subcommand: str,
        fixture_path: Path,
        binary: Optional[Path] = None,
        debug_output_path: Optional[Path] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Run a subcommand once per fixture directory and cache all
        results indexed by test name.
        """
        dir_path = (
            fixture_path
            if fixture_path.is_dir()
            else fixture_path.parent
        )
        effective_binary = binary if binary else self.binary
        cache_key = f"{subcommand}:{dir_path}"

        if cache_key not in self.dir_cache:
            command = [
                str(effective_binary),
                subcommand,
                "--json-array",
                str(dir_path),
            ]
            result = self.run_command(command)

            if debug_output_path:
                self.validate_debug_dump(
                    command,
                    result,
                    fixture_path,
                    debug_output_path,
                )

            if result.returncode != 0:
                raise Exception(
                    f"Unexpected exit code:\n"
                    f"{' '.join(command)}\n\n"
                    f"Error:\n{result.stderr}"
                )

            # Find JSON array start (binary may output info
            # before it)
            stdout = result.stdout
            json_start = stdout.rfind("[{")
            if json_start < 0:
                json_start = stdout.rfind("[")
            if json_start < 0:
                raise Exception(
                    f"No JSON array in {subcommand} output:\n"
                    f"{stdout[:500]}"
                )
            result_json = json.loads(stdout[json_start:])
            if not isinstance(result_json, list):
                raise Exception(
                    f"Unexpected result from {subcommand}: "
                    f"{result_json}"
                )

            result_model: type[FixtureTestResult] = {
                "statetest": StateTestResult,
                "blocktest": BlockTestResult,
                "enginetest": EngineTestResult,
            }.get(subcommand, FixtureTestResult)

            indexed: Dict[str, Dict[str, Any]] = {}
            for r in result_json:
                validated = result_model.model_validate(
                    r
                ).model_dump(by_alias=True)
                indexed[validated["name"]] = validated

            self.dir_cache[cache_key] = indexed

        return self.dir_cache[cache_key]

    def validate_test(
        self,
        subcommand: str,
        label: str,
        fixture_path: Path,
        fixture_name: Optional[str] = None,
        binary: Optional[Path] = None,
        debug_output_path: Optional[Path] = None,
    ) -> None:
        """Generic consume method using directory-level cache."""
        dir_results = self.get_dir_results(
            subcommand=subcommand,
            fixture_path=fixture_path,
            binary=binary,
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
            validate_test_result(
                self.fixture_cache, self.exception_mapper,
                label, fixture_name, dir_results[fixture_name],
                fixture_path,
                is_engine=subcommand == "enginetest",
                is_block=subcommand == "blocktest",
                is_state=subcommand == "statetest",
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
        """Consume a single state test via revme (revm)."""
        self.validate_test(
            "statetest",
            "State",
            fixture_path,
            fixture_name,
            binary=self.state_binary,
            debug_output_path=debug_output_path,
        )

    def consume_blockchain_test(
        self,
        fixture_path: Path,
        fixture_name: Optional[str] = None,
        debug_output_path: Optional[Path] = None,
    ) -> None:
        """Consume a single blockchain test via ef-test-runner."""
        self.validate_test(
            "blocktest",
            "Blockchain",
            fixture_path,
            fixture_name,
            debug_output_path=debug_output_path,
        )

    def consume_engine_test(
        self,
        fixture_path: Path,
        fixture_name: Optional[str] = None,
        debug_output_path: Optional[Path] = None,
    ) -> None:
        """Consume a single engine test via ef-test-runner."""
        self.validate_test(
            "enginetest",
            "Engine",
            fixture_path,
            fixture_name,
            debug_output_path=debug_output_path,
        )

    def consume_fixture(
        self,
        fixture_format: FixtureFormat,
        fixture_path: Path,
        fixture_name: Optional[str] = None,
        debug_output_path: Optional[Path] = None,
    ) -> None:
        """Execute the appropriate reth fixture consumer."""
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
