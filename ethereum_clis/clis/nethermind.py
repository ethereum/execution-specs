"""Interfaces for Nethermind CLIs."""

import json
import re
import subprocess
import textwrap
from functools import cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pytest

from ethereum_test_exceptions import ExceptionMapper
from ethereum_test_fixtures import BlockchainFixture, EOFFixture, FixtureFormat, StateFixture

from ..ethereum_cli import EthereumCLI
from ..file_utils import dump_files_to_directory
from ..fixture_consumer_tool import FixtureConsumerTool


class Nethtest(EthereumCLI):
    """Nethermind `nethtest` binary base class."""

    default_binary = Path("nethtest")
    detect_binary_pattern = re.compile(r"^\d+\.\d+\.\d+-[a-zA-Z0-9]+(\+[a-f0-9]{40})?$")
    version_flag: str = "--version"
    cached_version: Optional[str] = None

    def __init__(
        self,
        binary: Path,
        trace: bool = False,
        exception_mapper: ExceptionMapper | None = None,
    ):
        """Initialize the Nethtest class."""
        self.binary = binary
        self.trace = trace
        # TODO: Implement NethermindExceptionMapper
        self.exception_mapper = exception_mapper if exception_mapper else None

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
        command: Tuple[str, ...],
        result: subprocess.CompletedProcess,
        debug_output_path: Path,
    ):
        consume_direct_call = " ".join(command)
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

    @cache  # noqa
    def help(self, subcommand: str | None = None) -> str:
        """Return the help string, optionally for a subcommand."""
        help_command = [str(self.binary)]
        if subcommand:
            help_command.append(subcommand)
        help_command.append("--help")
        return self._run_command(help_command).stdout

    @cache  # noqa
    def has_eof_support(self) -> bool:
        """
        Return True if the `nethtest` binary supports the `--eofTest` flag.

        Currently, nethtest EOF support is only available in nethermind's feature/evm/eof
        branch https://github.com/NethermindEth/nethermind/tree/feature/evm/eof
        """
        return "--eofTest" in self.help()


class NethtestFixtureConsumer(
    Nethtest,
    FixtureConsumerTool,
    fixture_formats=[StateFixture, BlockchainFixture, EOFFixture],
):
    """Nethermind implementation of the fixture consumer."""

    def _build_command_with_options(
        self,
        fixture_format: FixtureFormat,
        fixture_path: Path,
        fixture_name: Optional[str] = None,
        debug_output_path: Optional[Path] = None,
    ) -> Tuple[str, ...]:
        assert fixture_name, "Fixture name must be provided for nethtest."
        command = [str(self.binary)]
        if fixture_format is BlockchainFixture:
            command += ["--blockTest", "--filter", f"{re.escape(fixture_name)}"]
        elif fixture_format is StateFixture:
            # TODO: consider using `--filter` here to readily access traces from the output
            pass  # no additional options needed
        elif fixture_format is EOFFixture:
            command += ["--eofTest"]
        else:
            raise Exception(
                f"Fixture format {fixture_format.format_name} not supported by {self.binary}"
            )
        command += ["--input", str(fixture_path)]
        if debug_output_path:
            command += ["--trace"]
        return tuple(command)

    @cache  # noqa
    def consume_state_test_file(
        self,
        fixture_path: Path,
        command: Tuple[str],
        debug_output_path: Optional[Path] = None,
    ) -> Tuple[List[Dict[str, Any]], str]:
        """
        Consume an entire state test file.

        The `evm statetest` will always execute all the tests contained in a file without the
        possibility of selecting a single test, so this function is cached in order to only call
        the command once and `consume_state_test` can simply select the result that
        was requested.
        """
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if debug_output_path:
            self._consume_debug_dump(command, result, debug_output_path)

        if result.returncode != 0:
            raise Exception(
                f"Unexpected exit code:\n{' '.join(command)}\n\n Error:\n{result.stderr}"
            )

        try:
            result_json = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            raise Exception(
                f"Failed to parse JSON output on stdout from nethtest:\n{result.stdout}"
            ) from e

        if not isinstance(result_json, list):
            raise Exception(f"Unexpected result from evm statetest: {result_json}")
        return result_json, result.stderr

    def consume_state_test(
        self,
        command: Tuple[str, ...],
        fixture_path: Path,
        fixture_name: Optional[str] = None,
        debug_output_path: Optional[Path] = None,
    ):
        """
        Consume a single state test.

        Uses the cached result from `consume_state_test_file` in order to not call the command
        every time an select a single result from there.
        """
        file_results, stderr = self.consume_state_test_file(
            fixture_path=fixture_path,
            command=command,
            debug_output_path=debug_output_path,
        )

        if fixture_name:
            # TODO: this check is too fragile; extend for ethereum/tests?
            nethtest_suffix = "_d0g0v0_"
            assert all(
                test_result["name"].endswith(nethtest_suffix) for test_result in file_results
            ), (
                "consume direct with nethtest doesn't support the multi-data statetest format "
                "used in ethereum/tests (yet)"
            )
            test_result = [
                test_result
                for test_result in file_results
                if test_result["name"].removesuffix(nethtest_suffix)
                == f"{fixture_name.split('/')[-1]}"
                # TODO: the following was required for nethermind's feature/evm/eof branch
                # nethtest version: 1.32.0-unstable+025871675bd2e0839f93d2b70416ebae9dbae012
                # == f"{fixture_name.split('.py::')[-1]}"
            ]
            assert len(test_result) < 2, f"Multiple test results for {fixture_name}"
            assert len(test_result) == 1, f"Test result for {fixture_name} missing"
            assert test_result[0]["pass"], (
                f"State test '{fixture_name}' failed, available stderr:\n {stderr}"
            )
        else:
            if any(not test_result["pass"] for test_result in file_results):
                exception_text = "State test failed: \n" + "\n".join(
                    f"{test_result['name']}: " + test_result["error"]
                    for test_result in file_results
                    if not test_result["pass"]
                )
                raise Exception(exception_text)

    def consume_blockchain_test(
        self,
        command: Tuple[str, ...],
        fixture_path: Path,
        fixture_name: Optional[str] = None,
        debug_output_path: Optional[Path] = None,
    ):
        """Execute the the fixture at `fixture_path` via `nethtest`."""
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if debug_output_path:
            self._consume_debug_dump(command, result, debug_output_path)

        if result.returncode != 0:
            raise Exception(
                f"nethtest exited with non-zero exit code ({result.returncode}).\n"
                f"stdout:\n{result.stdout}\n"
                f"stderr:\n{result.stderr}\n"
                f"{' '.join(command)}"
            )

    @cache  # noqa
    def consume_eof_test_file(
        self,
        fixture_path: Path,
        command: Tuple[str],
        debug_output_path: Optional[Path] = None,
    ) -> Tuple[Dict[Any, Any], str, str]:
        """Consume an entire EOF fixture file."""
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        pattern = re.compile(r"^(test_.+?)\s+(PASS|FAIL)$", re.MULTILINE)
        test_results = {
            match.group(1): match.group(2) == "PASS"  # Convert "PASS" to True and "FAIL" to False
            for match in pattern.finditer(result.stdout)
        }

        if debug_output_path:
            self._consume_debug_dump(command, result, debug_output_path)

        if result.returncode != 0:
            raise Exception(
                f"Unexpected exit code:\n{' '.join(command)}\n\n Error:\n{result.stderr}"
            )

        return test_results, result.stdout, result.stderr

    def consume_eof_test(self, command, fixture_path, fixture_name, debug_output_path):
        """Execute the the EOF fixture at `fixture_path` via `nethtest`."""
        if not self.has_eof_support():
            pytest.skip("This version of nethtest does not support the `--eofTest` flag.")
        file_results, stdout, stderr = self.consume_eof_test_file(
            fixture_path=fixture_path,
            command=command,
            debug_output_path=debug_output_path,
        )
        modified_fixture_name = fixture_name.split("::")[-1].replace("\\x", "/x")
        assert modified_fixture_name in file_results, (
            f"Test result for {fixture_name} missing, available stdout:\n{stdout}.\n"
            f"Parsed test results: {file_results}"
        )
        if stderr:
            available_stderr = f"Available stderr:\n{stderr}"
        else:
            available_stderr = "(No output available.)"
        assert file_results[modified_fixture_name], (
            f"EOF test '{fixture_name}' failed. {available_stderr}"
        )

    def consume_fixture(
        self,
        fixture_format: FixtureFormat,
        fixture_path: Path,
        fixture_name: Optional[str] = None,
        debug_output_path: Optional[Path] = None,
    ):
        """Execute the appropriate geth fixture consumer for the fixture at `fixture_path`."""
        command = self._build_command_with_options(
            fixture_format, fixture_path, fixture_name, debug_output_path
        )
        if fixture_format == BlockchainFixture:
            self.consume_blockchain_test(
                command=command,
                fixture_path=fixture_path,
                fixture_name=fixture_name,
                debug_output_path=debug_output_path,
            )
        elif fixture_format == StateFixture:
            self.consume_state_test(
                command=command,
                fixture_path=fixture_path,
                fixture_name=fixture_name,
                debug_output_path=debug_output_path,
            )
        elif fixture_format == EOFFixture:
            self.consume_eof_test(
                command=command,
                fixture_path=fixture_path,
                fixture_name=fixture_name,
                debug_output_path=debug_output_path,
            )
        else:
            raise Exception(
                f"Fixture format {fixture_format.format_name} not supported by {self.binary}"
            )
