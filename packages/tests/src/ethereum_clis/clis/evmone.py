"""Evmone Transition tool interface."""

import json
import re
import shlex
import shutil
import subprocess
import tempfile
import textwrap
from functools import cache
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional

import pytest

from ethereum_clis.file_utils import dump_files_to_directory
from ethereum_clis.fixture_consumer_tool import FixtureConsumerTool
from ethereum_test_exceptions import (
    EOFException,
    ExceptionBase,
    ExceptionMapper,
    TransactionException,
)
from ethereum_test_fixtures.base import FixtureFormat
from ethereum_test_fixtures.blockchain import BlockchainFixture
from ethereum_test_fixtures.state import StateFixture
from ethereum_test_forks import Fork

from ..transition_tool import TransitionTool


class EvmOneTransitionTool(TransitionTool):
    """Evmone `evmone-t8n` Transition tool interface wrapper class."""

    default_binary = Path("evmone-t8n")
    detect_binary_pattern = re.compile(r"^evmone-t8n\b")
    t8n_use_stream = False

    binary: Path
    cached_version: Optional[str] = None
    trace: bool
    supports_opcode_count: ClassVar[bool] = True
    supports_blob_params: ClassVar[bool] = True

    def __init__(
        self,
        *,
        binary: Optional[Path] = None,
        trace: bool = False,
    ):
        """Initialize the Evmone Transition tool interface."""
        super().__init__(
            exception_mapper=EvmoneExceptionMapper(),
            binary=binary,
            trace=trace,
        )

    def is_fork_supported(self, fork: Fork) -> bool:
        """
        Return True if the fork is supported by the tool. Currently, evmone-t8n
        provides no way to determine supported forks.
        """
        del fork
        return True


class EvmoneFixtureConsumerCommon:
    """Common functionality for Evmone fixture consumers."""

    binary: Path
    version_flag: str = "--version"

    cached_version: Optional[str] = None

    def __init__(
        self,
        trace: bool = False,
    ):
        """Initialize the EvmoneFixtureConsumerCommon class."""
        del trace
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

    # TODO: copied from geth.py, needs to be deduplicated, but nethermind.py
    # also has its version
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

    def _skip_message(self, fixture_format: FixtureFormat) -> str:
        return f"Fixture format {fixture_format.format_name} not supported by {self.binary}"

    @cache  # noqa
    def consume_test_file(
        self,
        fixture_path: Path,
        debug_output_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Consume an entire state or blockchain test file.

        The `evmone-...test` will always execute all the tests contained in a
        file without the possibility of selecting a single test, so this
        function is cached in order to only call the command once and
        `consume_test` can simply select the result that was requested.
        """
        global_options: List[str] = []
        if debug_output_path:
            global_options += ["--trace"]

        with tempfile.NamedTemporaryFile() as tempfile_json:
            # `evmone` uses `gtest` and generates JSON output to a file,
            # c.f. https://google.github.io/googletest/advanced.html#generating-a-json-report
            # see there for the JSON schema.
            global_options += [
                "--gtest_output=json:{}".format(tempfile_json.name)
            ]
            command = [str(self.binary)] + global_options + [str(fixture_path)]
            result = self._run_command(command)

            if result.returncode not in [0, 1]:
                raise Exception(
                    f"Unexpected exit code:\n{' '.join(command)}\n\n Error:\n{result.stderr}"
                )

            try:
                output_data = json.load(tempfile_json)
            except json.JSONDecodeError as e:
                raise Exception(
                    f"Failed to parse JSON output from evmone-state/blockchaintest: {e}"
                ) from e

            if debug_output_path:
                self._consume_debug_dump(
                    command, result, fixture_path, debug_output_path
                )

            return output_data

    def _failure_msg(self, file_results: Dict[str, Any]) -> str:
        # Assumes only one test has run and there has been a failure,
        # as asserted before.
        failures = file_results["testsuites"][0]["testsuite"][0]["failures"]
        return ", ".join([f["failure"] for f in failures])

    def consume_test(
        self,
        fixture_path: Path,
        fixture_name: Optional[str] = None,
        debug_output_path: Optional[Path] = None,
    ) -> None:
        """
        Consume a single state or blockchain test.

        Uses the cached result from `consume_test_file` in order to not
        call the command every time an select a single result from there.
        """
        file_results = self.consume_test_file(
            fixture_path=fixture_path,
            debug_output_path=debug_output_path,
        )
        assert len(file_results["testsuites"]) < 2, (
            f"Multiple testsuites for {fixture_name}"
        )
        assert len(file_results["testsuites"]) == 1, (
            f"testsuite for {fixture_name} missing"
        )
        test_suite = file_results["testsuites"][0]["testsuite"]

        assert fixture_name is not None, (
            "fixture_name must be provided for evmone tests"
        )
        test_results = [
            test_result
            for test_result in test_suite
            if test_result["name"] == fixture_name
        ]
        assert len(test_results) < 2, (
            f"Multiple test results for {fixture_name}"
        )
        assert len(test_results) == 1, (
            f"Test result for {fixture_name} missing"
        )
        assert "failures" not in test_results[0], (
            f"Test failed: {test_results[0]['failures'][0]['failure']}"
        )


class EvmOneStateFixtureConsumer(
    EvmoneFixtureConsumerCommon,
    FixtureConsumerTool,
    fixture_formats=[StateFixture],
):
    """Evmone's implementation of the fixture consumer for state tests."""

    default_binary = Path("evmone-statetest")
    detect_binary_pattern = re.compile(r"^evmone-statetest\b")

    def __init__(
        self,
        binary: Optional[Path] = None,
        trace: bool = False,
    ):
        """Initialize the EvmOneStateFixtureConsumer class."""
        self.binary = binary if binary else self.default_binary
        super().__init__(trace=trace)

    def consume_fixture(
        self,
        fixture_format: FixtureFormat,
        fixture_path: Path,
        fixture_name: Optional[str] = None,
        debug_output_path: Optional[Path] = None,
    ) -> None:
        """
        Execute the appropriate fixture consumer for the fixture at
        `fixture_path`.
        """
        if fixture_format == StateFixture:
            self.consume_test(
                fixture_path=fixture_path,
                fixture_name=fixture_name,
                debug_output_path=debug_output_path,
            )
        else:
            pytest.skip(self._skip_message(fixture_format))


class EvmOneBlockchainFixtureConsumer(
    EvmoneFixtureConsumerCommon,
    FixtureConsumerTool,
    fixture_formats=[BlockchainFixture],
):
    """Evmone's implementation of the fixture consumer for blockchain tests."""

    default_binary = Path("evmone-blockchaintest")
    detect_binary_pattern = re.compile(r"^evmone-blockchaintest\b")

    def __init__(
        self,
        binary: Optional[Path] = None,
        trace: bool = False,
    ):
        """Initialize the EvmOneBlockchainFixtureConsumer class."""
        self.binary = binary if binary else self.default_binary
        super().__init__(trace=trace)

    def consume_fixture(
        self,
        fixture_format: FixtureFormat,
        fixture_path: Path,
        fixture_name: Optional[str] = None,
        debug_output_path: Optional[Path] = None,
    ) -> None:
        """
        Execute the appropriate fixture consumer for the fixture at
        `fixture_path`.
        """
        if fixture_format == BlockchainFixture:
            self.consume_test(
                fixture_path=fixture_path,
                fixture_name=fixture_name,
                debug_output_path=debug_output_path,
            )
        else:
            pytest.skip(self._skip_message(fixture_format))


class EvmoneExceptionMapper(ExceptionMapper):
    """
    Translate between EEST exceptions and error strings returned by Evmone.
    """

    mapping_substring: ClassVar[Dict[ExceptionBase, str]] = {
        TransactionException.SENDER_NOT_EOA: "sender not an eoa:",
        TransactionException.GAS_ALLOWANCE_EXCEEDED: "gas limit reached",
        TransactionException.PRIORITY_GREATER_THAN_MAX_FEE_PER_GAS: (
            "max priority fee per gas higher than max fee per gas"
        ),
        TransactionException.NONCE_IS_MAX: "nonce has max value:",
        TransactionException.TYPE_4_TX_CONTRACT_CREATION: "set code transaction must ",
        TransactionException.TYPE_4_INVALID_AUTHORITY_SIGNATURE: "invalid authorization signature",
        TransactionException.TYPE_4_INVALID_AUTHORITY_SIGNATURE_S_TOO_HIGH: (
            "authorization signature s value too high"
        ),
        TransactionException.TYPE_4_EMPTY_AUTHORIZATION_LIST: "empty authorization list",
        TransactionException.INTRINSIC_GAS_TOO_LOW: "intrinsic gas too low",
        TransactionException.INTRINSIC_GAS_BELOW_FLOOR_GAS_COST: "intrinsic gas too low",
        TransactionException.TYPE_3_TX_MAX_BLOB_GAS_ALLOWANCE_EXCEEDED: "blob gas limit exceeded",
        TransactionException.INITCODE_SIZE_EXCEEDED: "max initcode size exceeded",
        TransactionException.INSUFFICIENT_ACCOUNT_FUNDS: (
            "insufficient funds for gas * price + value"
        ),
        TransactionException.INSUFFICIENT_MAX_FEE_PER_GAS: (
            "max fee per gas less than block base fee"
        ),
        TransactionException.INSUFFICIENT_MAX_FEE_PER_BLOB_GAS: (
            "max blob fee per gas less than block base fee"
        ),
        TransactionException.TYPE_4_TX_PRE_FORK: "transaction type not supported",
        TransactionException.TYPE_3_TX_PRE_FORK: "transaction type not supported",
        TransactionException.TYPE_3_TX_INVALID_BLOB_VERSIONED_HASH: "invalid blob hash version",
        TransactionException.TYPE_3_TX_BLOB_COUNT_EXCEEDED: "blob gas limit exceeded",
        TransactionException.TYPE_3_TX_ZERO_BLOBS: "empty blob hashes list",
        TransactionException.TYPE_3_TX_CONTRACT_CREATION: (
            "blob transaction must not be a create transaction"
        ),
        TransactionException.NONCE_MISMATCH_TOO_LOW: "nonce too low",
        TransactionException.NONCE_MISMATCH_TOO_HIGH: "nonce too high",
        TransactionException.GAS_LIMIT_EXCEEDS_MAXIMUM: "max gas limit exceeded",
        # TODO EVMONE needs to differentiate when the section is missing in the
        # header or body
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
        EOFException.STACK_OVERFLOW: "err: stack_overflow",
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
        EOFException.AMBIGUOUS_CONTAINER_KIND: "err: ambiguous_container_kind",
        EOFException.STACK_HEIGHT_MISMATCH: "err: stack_height_mismatch",
        EOFException.TOO_MANY_CONTAINERS: "err: too_many_container_sections",
        EOFException.INVALID_CODE_SECTION_INDEX: "err: invalid_code_section_index",
        EOFException.CALLF_TO_NON_RETURNING: "err: callf_to_non_returning_function",
        EOFException.EOFCREATE_WITH_TRUNCATED_CONTAINER: "err: eofcreate_with_truncated_container",
    }
    mapping_regex: ClassVar[Dict[ExceptionBase, str]] = {}
