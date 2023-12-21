"""
Go-ethereum Transition tool interface.
"""

import shutil
import subprocess
import textwrap
from pathlib import Path
from re import compile
from typing import Optional

from ethereum_test_forks import Fork

from .transition_tool import FixtureFormats, TransitionTool, dump_files_to_directory


class GethTransitionTool(TransitionTool):
    """
    Go-ethereum `evm` Transition tool interface wrapper class.
    """

    default_binary = Path("evm")
    detect_binary_pattern = compile(r"^evm version\b")
    t8n_subcommand: Optional[str] = "t8n"
    statetest_subcommand: Optional[str] = "statetest"
    blocktest_subcommand: Optional[str] = "blocktest"

    binary: Path
    cached_version: Optional[str] = None
    trace: bool

    def __init__(
        self,
        *,
        binary: Optional[Path] = None,
        trace: bool = False,
    ):
        super().__init__(binary=binary, trace=trace)
        args = [str(self.binary), str(self.t8n_subcommand), "--help"]
        try:
            result = subprocess.run(args, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            raise Exception("evm process unexpectedly returned a non-zero status code: " f"{e}.")
        except Exception as e:
            raise Exception(f"Unexpected exception calling evm tool: {e}.")
        self.help_string = result.stdout

    def is_fork_supported(self, fork: Fork) -> bool:
        """
        Returns True if the fork is supported by the tool.

        If the fork is a transition fork, we want to check the fork it transitions to.
        """
        return fork.transition_tool_name() in self.help_string

    def verify_fixture(
        self, fixture_format: FixtureFormats, fixture_path: Path, debug_output_path: Optional[Path]
    ):
        """
        Executes `evm [state|block]test` to verify the fixture at `fixture_path`.
        """
        command: list[str] = [str(self.binary)]

        if debug_output_path:
            command += ["--debug", "--json", "--verbosity", "100"]

        if FixtureFormats.is_state_test(fixture_format):
            assert self.statetest_subcommand, "statetest subcommand not set"
            command.append(self.statetest_subcommand)
        elif FixtureFormats.is_blockchain_test(fixture_format):
            assert self.blocktest_subcommand, "blocktest subcommand not set"
            command.append(self.blocktest_subcommand)
        else:
            raise Exception(f"Invalid test fixture format: {fixture_format}")

        command.append(str(fixture_path))

        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        if debug_output_path:
            debug_fixture_path = debug_output_path / "fixtures.json"
            shutil.copyfile(fixture_path, debug_fixture_path)
            # Use the local copy of the fixture in the debug directory
            verify_fixtures_call = " ".join(command[:-1]) + f" {debug_fixture_path}"
            verify_fixtures_script = textwrap.dedent(
                f"""\
                #!/bin/bash
                {verify_fixtures_call}
                """
            )
            dump_files_to_directory(
                str(debug_output_path),
                {
                    "verify_fixtures_args.py": command,
                    "verify_fixtures_returncode.txt": result.returncode,
                    "verify_fixtures_stdout.txt": result.stdout.decode(),
                    "verify_fixtures_stderr.txt": result.stderr.decode(),
                    "verify_fixtures.sh+x": verify_fixtures_script,
                },
            )

        if result.returncode != 0:
            raise Exception(
                f"Failed to verify fixture via: '{' '.join(command)}'. "
                f"Error: '{result.stderr.decode()}'"
            )
