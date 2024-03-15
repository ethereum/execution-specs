"""
Defines EVM tools for use in the Ethereum specification.
"""

import argparse
import subprocess
import sys
from typing import Optional, Sequence, Text, TextIO

from ethereum import __version__

from .b11r import B11R, b11r_arguments
from .daemon import Daemon, daemon_arguments
from .statetest import StateTest, state_test_arguments
from .t8n import T8N, t8n_arguments
from .utils import get_supported_forks

DESCRIPTION = """
This is the EVM tool for execution specs. The EVM tool
provides a few useful subcommands to facilitate testing
at the EVM layer.

Please refer to the following link for more information:
https://github.com/ethereum/go-ethereum/blob/master/cmd/evm/README.md

You can use this to run the following tools:
    1. t8n: A stateless state transition utility.
    2. b11r: The tool is used to assemble and seal full block rlps.


The following forks are supported:
""" + "\n".join(
    get_supported_forks()
)


def create_parser() -> argparse.ArgumentParser:
    """
    Create a command-line argument parser for the evm tool.
    """
    new_parser = argparse.ArgumentParser(
        description=DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    commit_hash = get_git_commit_hash()

    # Add -v option to parser to show the version of the tool
    new_parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {__version__} (Git commit: {commit_hash})",
        help="Show the version of the tool.",
    )

    # Add options to the t8n tool
    subparsers = new_parser.add_subparsers(dest="evm_tool")

    daemon_arguments(subparsers)
    t8n_arguments(subparsers)
    b11r_arguments(subparsers)
    state_test_arguments(subparsers)

    return new_parser


def get_git_commit_hash() -> str:
    """
    Run the 'git rev-parse HEAD' command to get the commit hash
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )

        # Extract and return the commit hash
        commit_hash = result.stdout.strip()
        return commit_hash
    # Handle errors (e.g., Git not found, not in a Git repository)
    except FileNotFoundError as e:
        return str(e)
    except subprocess.CalledProcessError as e:
        return "Error: " + str(e)


def main(
    args: Optional[Sequence[Text]] = None,
    out_file: Optional[TextIO] = None,
    in_file: Optional[TextIO] = None,
) -> int:
    """Run the tools based on the given options."""
    parser = create_parser()

    options, _ = parser.parse_known_args(args)

    if out_file is None:
        out_file = sys.stdout

    if in_file is None:
        in_file = sys.stdin

    if options.evm_tool == "t8n":
        t8n_tool = T8N(options, out_file, in_file)
        return t8n_tool.run()
    elif options.evm_tool == "b11r":
        b11r_tool = B11R(options, out_file, in_file)
        return b11r_tool.run()
    elif options.evm_tool == "daemon":
        daemon = Daemon(options)
        return daemon.run()
    elif options.evm_tool == "statetest":
        state_test = StateTest(options, out_file, in_file)
        return state_test.run()
    else:
        parser.print_help(file=out_file)
        return 0
