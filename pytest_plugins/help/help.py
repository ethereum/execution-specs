"""
A small pytest plugin that shows the a concise help string that only contains
the options defined by the plugins defined in execution-spec-tests.
"""

import argparse
from pathlib import Path

import pytest


def pytest_addoption(parser):
    """
    Adds command-line options to pytest.
    """
    help_group = parser.getgroup("test_help", "Arguments related to running execution-spec-tests")
    help_group.addoption(
        "--test-help",
        action="store_true",
        dest="show_test_help",
        default=False,
        help=(
            "Only show help options specific to a specific execution-spec-tests command and "
            "exit."
        ),
    )


def pytest_configure(config):
    """
    Print execution-spec-tests help if specified on the command-line.
    """
    if config.getoption("show_test_help"):
        show_test_help(config)
        pytest.exit("After displaying help.", returncode=pytest.ExitCode.OK)


def show_test_help(config):
    """
    Print the help for argparse groups that contain substrings indicating
    that group is specific to execution-spec-tests command-line
    arguments.
    """
    pytest_ini = Path(config.inifile)
    if pytest_ini.name == "pytest.ini":
        test_group_substrings = [
            "execution-spec-tests",
            "evm",
            "solc",
            "fork range",
            "filler location",
            "defining debug",
            "pre-allocation behavior",
        ]
    elif pytest_ini.name in [
        "pytest-consume.ini",
    ]:
        test_group_substrings = [
            "execution-spec-tests",
            "consuming",
            "defining debug",
        ]
    else:
        raise ValueError("Unexpected pytest.ini file option generating test help.")

    test_parser = argparse.ArgumentParser()
    for group in config._parser.optparser._action_groups:
        if any(group for substring in test_group_substrings if substring in group.title):
            new_group = test_parser.add_argument_group(group.title, group.description)
            for action in group._group_actions:
                # Copy the option to the new group.
                # Works for 'store', 'store_true', and 'store_false'.
                kwargs = {
                    "default": action.default,
                    "help": action.help,
                    "required": action.required,
                }
                if isinstance(action, argparse._StoreTrueAction):
                    kwargs["action"] = "store_true"
                else:
                    kwargs["type"] = action.type
                if action.nargs is not None and action.nargs != 0:
                    kwargs["nargs"] = action.nargs
                new_group.add_argument(*action.option_strings, **kwargs)
    print(test_parser.format_help())
