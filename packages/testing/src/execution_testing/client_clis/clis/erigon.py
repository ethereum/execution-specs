"""Erigon execution client fixture consumer interface."""

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
    BlockchainEngineXFixture,
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


class ErigonExceptionMapper(ExceptionMapper):
    """Translate between EEST exceptions and error strings returned by Erigon."""

    mapping_substring: ClassVar[Dict[ExceptionBase, str]] = {
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
        BlockException.RLP_BLOCK_LIMIT_EXCEEDED: (
            "block exceeds max rlp size"
        ),
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
        BlockException.INVALID_GASLIMIT: (
            "invalid block: invalid gas limit"
        ),
        BlockException.INVALID_STATE_ROOT: (
            "invalid block: wrong trie root"
        ),
        BlockException.INVALID_RECEIPTS_ROOT: "receiptHash mismatch",
        BlockException.INVALID_LOG_BLOOM: "invalid bloom",
        BlockException.INVALID_BAL_MISSING_ACCOUNT: (
            "block access list mismatch"
        ),
        BlockException.INCORRECT_BLOCK_FORMAT: (
            "invalid block access list"
        ),
        BlockException.INVALID_BAL_EXTRA_ACCOUNT: (
            "invalid block access list"
        ),
        BlockException.GAS_USED_OVERFLOW: "block gas used overflow",
    }
    mapping_regex: ClassVar[Dict[ExceptionBase, str]] = {
        BlockException.INVALID_BLOCK_ACCESS_LIST: (
            r"invalid block access list|block access list mismatch"
        ),
        BlockException.INVALID_BAL_MISSING_ACCOUNT: (
            r"block access list mismatch"
        ),
        BlockException.INVALID_BAL_EXTRA_ACCOUNT: (
            r"invalid block access list"
        ),
        BlockException.INCORRECT_BLOCK_FORMAT: (
            r"invalid block access list"
        ),
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
    """Erigon `evm` base class."""

    default_binary = Path("evm")
    detect_binary_pattern = re.compile(r"^evm(.exe)? version\b")
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
                "Unexpected exception calling erigon evm tool."
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


class ErigonFixtureConsumer(
    ErigonEvm,
    FixtureConsumerTool,
    fixture_formats=[
        StateFixture,
        BlockchainFixture,
        BlockchainEngineFixture,
        BlockchainEngineXFixture,
    ],
):
    """Erigon's implementation of the fixture consumer.

    Uses the erigon `evm` binary with statetest, blocktest,
    enginetest, and enginextest subcommands. Requires `--jsonout`
    for JSON output. Supports both --type engine (use with -n8
    --bin-workers 8) and --type enginex (pre-alloc cached, faster
    with less parallelism).
    """

    dir_cache: Dict[str, Dict[str, Dict[str, Any]]] = {}
    fixture_cache: Dict[str, Dict[str, Any]] = {}
    exception_mapper: ExceptionMapper = ErigonExceptionMapper()

    def get_dir_results(
        self,
        subcommand: str,
        fixture_path: Path,
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
        cache_key = f"{subcommand}:{dir_path}"

        if cache_key not in self.dir_cache:
            workers = getattr(self, "workers", 1)
            global_options: List[str] = []
            subcommand_options: List[str] = [
                "--jsonout",
                "--workers",
                str(workers),
            ]
            if debug_output_path:
                global_options += ["--verbosity", "100"]

            command = (
                [str(self.binary)]
                + global_options
                + [subcommand]
                + subcommand_options
                + [str(dir_path)]
            )
            result = self.run_command(command)

            if debug_output_path:
                self.validate_debug_dump(
                    command, result, fixture_path, debug_output_path
                )

            if result.returncode != 0:
                raise Exception(
                    f"Unexpected exit code:\n"
                    f"{' '.join(command)}\n\n"
                    f"Error:\n{result.stderr}"
                )

            stdout = result.stdout
            json_start = stdout.find("[")
            if json_start < 0:
                raise Exception(
                    f"No JSON array in evm {subcommand} output:\n"
                    f"{stdout[:500]}"
                )
            result_json = json.loads(stdout[json_start:])
            if not isinstance(result_json, list):
                raise Exception(
                    f"Unexpected result from evm {subcommand}: "
                    f"{result_json}"
                )

            result_model: type[FixtureTestResult] = {
                "statetest": StateTestResult,
                "blocktest": BlockTestResult,
                "enginetest": EngineTestResult,
                "enginextest": EngineTestResult,
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
        debug_output_path: Optional[Path] = None,
    ) -> None:
        """Generic consume method using directory-level cache."""
        dir_results = self.get_dir_results(
            subcommand=subcommand,
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
            validate_test_result(
                self.fixture_cache, self.exception_mapper,
                label, fixture_name, dir_results[fixture_name],
                fixture_path,
                is_engine=subcommand in (
                    "enginetest", "enginextest",
                ),
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
        """Consume a single state test."""
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
        """Consume a single blockchain test."""
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
        """Consume a single engine test."""
        self.validate_test(
            "enginetest",
            "Engine",
            fixture_path,
            fixture_name,
            debug_output_path,
        )

    def consume_enginex_test(
        self,
        fixture_path: Path,
        fixture_name: Optional[str] = None,
        debug_output_path: Optional[Path] = None,
    ) -> None:
        """Consume a single engine test via enginextest (pre-alloc cached)."""
        self.validate_test(
            "enginextest",
            "EngineX",
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
        """Execute the appropriate erigon fixture consumer."""
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
        elif fixture_format == BlockchainEngineXFixture:
            self.consume_enginex_test(
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
