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

from execution_testing.client_clis.file_utils import (
    dump_files_to_directory,
)
from execution_testing.client_clis.fixture_consumer_tool import (
    FixtureConsumerTool,
)
from execution_testing.exceptions import (
    ExceptionBase,
    ExceptionMapper,
    TransactionException,
)
from execution_testing.exceptions.exceptions.block import BlockException
from execution_testing.fixtures.base import FixtureFormat
from execution_testing.fixtures.blockchain import BlockchainFixture
from execution_testing.fixtures.state import StateFixture
from execution_testing.forks import Fork

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

    # evmone uses space-separated fork names for some forks
    fork_name_map: ClassVar[Dict[str, str]] = {
        "TangerineWhistle": "Tangerine Whistle",
        "SpuriousDragon": "Spurious Dragon",
    }

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
        fmt_name = fixture_format.format_name
        return f"Fixture format {fmt_name} not supported by {self.binary}"

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
                cmd_str = " ".join(command)
                raise Exception(
                    f"Unexpected exit code:\n{cmd_str}\n\n Error:\n"
                    f"{result.stderr}"
                )

            try:
                output_data = json.load(tempfile_json)
            except json.JSONDecodeError as e:
                raise Exception(
                    "Failed to parse JSON output from "
                    f"evmone-state/blockchaintest: {e}"
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
        call the command every time and select a single result from there.
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
        TransactionException.TYPE_4_TX_CONTRACT_CREATION: (
            "set code transaction must "
        ),
        TransactionException.TYPE_4_INVALID_AUTHORITY_SIGNATURE: (
            "invalid authorization signature"
        ),
        TransactionException.TYPE_4_INVALID_AUTHORITY_SIGNATURE_S_TOO_HIGH: (
            "authorization signature s value too high"
        ),
        TransactionException.TYPE_4_EMPTY_AUTHORIZATION_LIST: (
            "empty authorization list"
        ),
        TransactionException.INTRINSIC_GAS_TOO_LOW: "intrinsic gas too low",
        TransactionException.INTRINSIC_GAS_BELOW_FLOOR_GAS_COST: (
            "intrinsic gas too low"
        ),
        TransactionException.TYPE_3_TX_MAX_BLOB_GAS_ALLOWANCE_EXCEEDED: (
            "blob gas limit exceeded"
        ),
        TransactionException.INITCODE_SIZE_EXCEEDED: (
            "max initcode size exceeded"
        ),
        TransactionException.INSUFFICIENT_ACCOUNT_FUNDS: (
            "insufficient funds for gas * price + value"
        ),
        TransactionException.INSUFFICIENT_MAX_FEE_PER_GAS: (
            "max fee per gas less than block base fee"
        ),
        TransactionException.INSUFFICIENT_MAX_FEE_PER_BLOB_GAS: (
            "max blob fee per gas less than block base fee"
        ),
        TransactionException.TYPE_4_TX_PRE_FORK: (
            "transaction type not supported"
        ),
        TransactionException.TYPE_3_TX_PRE_FORK: (
            "transaction type not supported"
        ),
        TransactionException.TYPE_2_TX_PRE_FORK: (
            "transaction type not supported"
        ),
        TransactionException.TYPE_1_TX_PRE_FORK: (
            "transaction type not supported"
        ),
        TransactionException.TYPE_3_TX_INVALID_BLOB_VERSIONED_HASH: (
            "invalid blob hash version"
        ),
        TransactionException.TYPE_3_TX_BLOB_COUNT_EXCEEDED: (
            "blob gas limit exceeded"
        ),
        TransactionException.TYPE_3_TX_ZERO_BLOBS: "empty blob hashes list",
        TransactionException.TYPE_3_TX_CONTRACT_CREATION: (
            "blob transaction must not be a create transaction"
        ),
        TransactionException.NONCE_MISMATCH_TOO_LOW: "nonce too low",
        TransactionException.NONCE_MISMATCH_TOO_HIGH: "nonce too high",
        TransactionException.GAS_LIMIT_EXCEEDS_MAXIMUM: (
            "max gas limit exceeded"
        ),
        BlockException.INVALID_DEPOSIT_EVENT_LAYOUT: (
            "invalid deposit event layout"
        ),
        # TODO EVMONE needs to differentiate when the system contract is
        # missing or failing
        BlockException.SYSTEM_CONTRACT_EMPTY: (
            "system contract empty or failed"
        ),
        BlockException.SYSTEM_CONTRACT_CALL_FAILED: (
            "system contract empty or failed"
        ),
    }
    mapping_regex: ClassVar[Dict[ExceptionBase, str]] = {}
