"""Go-ethereum Transition tool interface."""

import json
import re
import shutil
import subprocess
import textwrap
from functools import cache
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional

from ethereum_test_exceptions import (
    BlockException,
    EOFException,
    ExceptionBase,
    ExceptionMapper,
    TransactionException,
)
from ethereum_test_fixtures import BlockchainFixture, FixtureFormat, StateFixture
from ethereum_test_forks import Fork

from ..ethereum_cli import EthereumCLI
from ..fixture_consumer_tool import FixtureConsumerTool
from ..transition_tool import TransitionTool, dump_files_to_directory


class GethExceptionMapper(ExceptionMapper):
    """Translate between EEST exceptions and error strings returned by Geth."""

    mapping_substring: ClassVar[Dict[ExceptionBase, str]] = {
        TransactionException.SENDER_NOT_EOA: "sender not an eoa",
        TransactionException.INSUFFICIENT_ACCOUNT_FUNDS: (
            "insufficient funds for gas * price + value"
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
        TransactionException.PRIORITY_GREATER_THAN_MAX_FEE_PER_GAS: (
            "max priority fee per gas higher than max fee per gas"
        ),
        TransactionException.TYPE_3_TX_PRE_FORK: ("transaction type not supported"),
        TransactionException.TYPE_3_TX_INVALID_BLOB_VERSIONED_HASH: "has invalid hash version",
        # This message is the same as TYPE_3_TX_MAX_BLOB_GAS_ALLOWANCE_EXCEEDED
        TransactionException.TYPE_3_TX_BLOB_COUNT_EXCEEDED: "exceed maximum allowance",
        TransactionException.TYPE_3_TX_ZERO_BLOBS: "blob transaction missing blob hashes",
        TransactionException.TYPE_3_TX_WITH_FULL_BLOBS: (
            "unexpected blob sidecar in transaction at index"
        ),
        TransactionException.TYPE_3_TX_CONTRACT_CREATION: (
            "input string too short for common.Address, decoding into (types.BlobTx).To"
        ),
        TransactionException.TYPE_4_EMPTY_AUTHORIZATION_LIST: (
            "EIP-7702 transaction with empty auth list"
        ),
        TransactionException.TYPE_4_TX_CONTRACT_CREATION: (
            "input string too short for common.Address, decoding into (types.SetCodeTx).To"
        ),
        TransactionException.TYPE_4_TX_PRE_FORK: ("transaction type not supported"),
        TransactionException.INITCODE_SIZE_EXCEEDED: "max initcode size exceeded",
        TransactionException.NONCE_MISMATCH_TOO_LOW: "nonce too low",
        TransactionException.INVALID_DEPOSIT_EVENT_LAYOUT: "unable to parse deposit data",
        BlockException.INCORRECT_BLOB_GAS_USED: "blob gas used mismatch",
        BlockException.INCORRECT_EXCESS_BLOB_GAS: "invalid excessBlobGas",
        BlockException.INVALID_VERSIONED_HASHES: "invalid number of versionedHashes",
        BlockException.INVALID_REQUESTS: "invalid requests hash",
        BlockException.SYSTEM_CONTRACT_CALL_FAILED: "system call failed to execute:",
        BlockException.INVALID_BLOCK_HASH: "blockhash mismatch",
        # TODO EVMONE needs to differentiate when the section is missing in the header or body
        EOFException.MISSING_STOP_OPCODE: "err: no_terminating_instruction",
        EOFException.MISSING_CODE_HEADER: "err: code_section_missing",
        EOFException.MISSING_TYPE_HEADER: "err: type_section_missing",
        # TODO EVMONE these exceptions are too similar, this leeds to ambiguity
        EOFException.MISSING_TERMINATOR: "err: header_terminator_missing",
        EOFException.MISSING_HEADERS_TERMINATOR: "err: section_headers_not_terminated",
        EOFException.INVALID_VERSION: "err: eof_version_unknown",
        EOFException.INVALID_NON_RETURNING_FLAG: "err: invalid_non_returning_flag",
        EOFException.INVALID_MAGIC: "err: invalid_prefix",
        EOFException.INVALID_FIRST_SECTION_TYPE: "err: invalid_first_section_type",
        EOFException.INVALID_SECTION_BODIES_SIZE: "err: invalid_section_bodies_size",
        EOFException.INVALID_TYPE_SECTION_SIZE: "err: invalid_type_section_size",
        EOFException.INCOMPLETE_SECTION_SIZE: "err: incomplete_section_size",
        EOFException.INCOMPLETE_SECTION_NUMBER: "err: incomplete_section_number",
        EOFException.TOO_MANY_CODE_SECTIONS: "err: too_many_code_sections",
        EOFException.ZERO_SECTION_SIZE: "err: zero_section_size",
        EOFException.MISSING_DATA_SECTION: "err: data_section_missing",
        EOFException.UNDEFINED_INSTRUCTION: "err: undefined_instruction",
        EOFException.INPUTS_OUTPUTS_NUM_ABOVE_LIMIT: "err: inputs_outputs_num_above_limit",
        EOFException.UNREACHABLE_INSTRUCTIONS: "err: unreachable_instructions",
        EOFException.INVALID_RJUMP_DESTINATION: "err: invalid_rjump_destination",
        EOFException.UNREACHABLE_CODE_SECTIONS: "err: unreachable_code_sections",
        EOFException.STACK_UNDERFLOW: "err: stack_underflow",
        EOFException.MAX_STACK_INCREASE_ABOVE_LIMIT: "err: max_stack_increase_above_limit",
        EOFException.STACK_HIGHER_THAN_OUTPUTS: "err: stack_higher_than_outputs_required",
        EOFException.JUMPF_DESTINATION_INCOMPATIBLE_OUTPUTS: (
            "err: jumpf_destination_incompatible_outputs"
        ),
        EOFException.INVALID_MAX_STACK_INCREASE: "err: invalid_max_stack_increase",
        EOFException.INVALID_DATALOADN_INDEX: "err: invalid_dataloadn_index",
        EOFException.TRUNCATED_INSTRUCTION: "err: truncated_instruction",
        EOFException.TOPLEVEL_CONTAINER_TRUNCATED: "err: toplevel_container_truncated",
        EOFException.ORPHAN_SUBCONTAINER: "err: unreferenced_subcontainer",
        EOFException.CONTAINER_SIZE_ABOVE_LIMIT: "err: container_size_above_limit",
        EOFException.INVALID_CONTAINER_SECTION_INDEX: "err: invalid_container_section_index",
        EOFException.INCOMPATIBLE_CONTAINER_KIND: "err: incompatible_container_kind",
        EOFException.STACK_HEIGHT_MISMATCH: "err: stack_height_mismatch",
        EOFException.TOO_MANY_CONTAINERS: "err: too_many_container_sections",
        EOFException.INVALID_CODE_SECTION_INDEX: "err: invalid_code_section_index",
    }
    mapping_regex: ClassVar[Dict[ExceptionBase, str]] = {
        TransactionException.TYPE_3_TX_MAX_BLOB_GAS_ALLOWANCE_EXCEEDED: (
            r"blob gas used \d+ exceeds maximum allowance \d+"
        ),
        TransactionException.INTRINSIC_GAS_TOO_LOW: (
            r"intrinsic gas too low|insufficient gas for floor data gas cost"
        ),
        BlockException.BLOB_GAS_USED_ABOVE_LIMIT: (
            r"blob gas used \d+ exceeds maximum allowance \d+"
        ),
    }


class GethEvm(EthereumCLI):
    """go-ethereum `evm` base class."""

    default_binary = Path("evm")
    detect_binary_pattern = re.compile(r"^evm(.exe)? version\b")
    cached_version: Optional[str] = None

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
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
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
    ):
        debug_fixture_path = debug_output_path / "fixtures.json"
        consume_direct_call = " ".join(command[:-1]) + f" {debug_fixture_path}"
        consume_direct_script = textwrap.dedent(
            f"""\
            #!/bin/bash
            {consume_direct_call}
            """
        )
        dump_files_to_directory(
            str(debug_output_path),
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
        TransitionTool.__init__(self, binary=binary, exception_mapper=exception_mapper)
        help_command = [str(self.binary), str(self.subcommand), "--help"]
        result = self._run_command(help_command)
        self.help_string = result.stdout

    def is_fork_supported(self, fork: Fork) -> bool:
        """
        Return True if the fork is supported by the tool.

        If the fork is a transition fork, we want to check the fork it transitions to.
        """
        return fork.transition_tool_name() in self.help_string


class GethFixtureConsumer(
    GethEvm,
    FixtureConsumerTool,
    fixture_formats=[StateFixture, BlockchainFixture],
):
    """Geth's implementation of the fixture consumer."""

    def consume_blockchain_test(
        self,
        fixture_path: Path,
        fixture_name: Optional[str] = None,
        debug_output_path: Optional[Path] = None,
    ):
        """
        Consume a single blockchain test.

        The `evm blocktest` command takes the `--run` argument which can be used to select a
        specific fixture from the fixture file when executing.
        """
        subcommand = "blocktest"
        global_options = []
        subcommand_options = []
        if debug_output_path:
            global_options += ["--verbosity", "100"]
            subcommand_options += ["--trace"]

        if fixture_name:
            subcommand_options += ["--run", re.escape(fixture_name)]

        command = (
            [str(self.binary)]
            + global_options
            + [subcommand]
            + subcommand_options
            + [str(fixture_path)]
        )

        result = self._run_command(command)

        if debug_output_path:
            self._consume_debug_dump(command, result, fixture_path, debug_output_path)

        if result.returncode != 0:
            raise Exception(
                f"Unexpected exit code:\n{' '.join(command)}\n\n Error:\n{result.stderr}"
            )

        result_json = json.loads(result.stdout)
        if not isinstance(result_json, list):
            raise Exception(f"Unexpected result from evm blocktest: {result_json}")

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

        The `evm statetest` will always execute all the tests contained in a file without the
        possibility of selecting a single test, so this function is cached in order to only call
        the command once and `consume_state_test` can simply select the result that
        was requested.
        """
        subcommand = "statetest"
        global_options: List[str] = []
        subcommand_options: List[str] = []
        if debug_output_path:
            global_options += ["--verbosity", "100"]
            subcommand_options += ["--trace"]

        command = (
            [str(self.binary)]
            + global_options
            + [subcommand]
            + subcommand_options
            + [str(fixture_path)]
        )
        result = self._run_command(command)

        if debug_output_path:
            self._consume_debug_dump(command, result, fixture_path, debug_output_path)

        if result.returncode != 0:
            raise Exception(
                f"Unexpected exit code:\n{' '.join(command)}\n\n Error:\n{result.stderr}"
            )

        result_json = json.loads(result.stdout)
        if not isinstance(result_json, list):
            raise Exception(f"Unexpected result from evm statetest: {result_json}")
        return result_json

    def consume_state_test(
        self,
        fixture_path: Path,
        fixture_name: Optional[str] = None,
        debug_output_path: Optional[Path] = None,
    ):
        """
        Consume a single state test.

        Uses the cached result from `consume_state_test_file` in order to not call the command
        every time an select a single result from there.
        """
        file_results = self.consume_state_test_file(
            fixture_path=fixture_path,
            debug_output_path=debug_output_path,
        )
        if fixture_name:
            test_result = [
                test_result for test_result in file_results if test_result["name"] == fixture_name
            ]
            assert len(test_result) < 2, f"Multiple test results for {fixture_name}"
            assert len(test_result) == 1, f"Test result for {fixture_name} missing"
            assert test_result[0]["pass"], f"State test failed: {test_result[0]['error']}"
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
    ):
        """Execute the appropriate geth fixture consumer for the fixture at `fixture_path`."""
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
                f"Fixture format {fixture_format.format_name} not supported by {self.binary}"
            )
