"""
A small pytest plugin that shows the a concise help string that only contains
the options defined by the plugins defined in execution-spec-tests.
"""

import argparse
from pathlib import Path

import pytest


def pytest_addoption(parser):
    """
    Adds command-line options to pytest for specific help commands.
    """
    help_group = parser.getgroup("help_options", "Help options for different commands")
    help_group.addoption(
        "--fill-help",
        action="store_true",
        dest="show_fill_help",
        default=False,
        help="Show help options only for the fill command and exit.",
    )
    help_group.addoption(
        "--consume-help",
        action="store_true",
        dest="show_consume_help",
        default=False,
        help="Show help options specific to the consume command and exit.",
    )


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    """
    Handle specific help flags by displaying the corresponding help message.
    """
    if config.getoption("show_fill_help"):
        show_specific_help(
            config,
            "pytest.ini",
            [
                "evm",
                "solc",
                "fork range",
                "filler location",
                "defining debug",
                "pre-allocation behavior",
            ],
        )
    elif config.getoption("show_consume_help"):
        show_specific_help(config, "pytest-consume.ini", ["consuming"])


def show_specific_help(config, expected_ini, substrings):
    """
    Print help options filtered by specific substrings from the given configuration.
    """
    pytest_ini = Path(config.inifile)
    if pytest_ini.name != expected_ini:
        raise ValueError(f"Unexpected {expected_ini} file option generating help.")

    test_parser = argparse.ArgumentParser()
    for group in config._parser.optparser._action_groups:
        if any(substring in group.title for substring in substrings):
            new_group = test_parser.add_argument_group(group.title, group.description)
            for action in group._group_actions:
                kwargs = {
                    "default": action.default,
                    "help": action.help,
                    "required": action.required,
                }
                if isinstance(action, argparse._StoreTrueAction):
                    kwargs["action"] = "store_true"
                else:
                    kwargs["type"] = action.type
                if action.nargs:
                    kwargs["nargs"] = action.nargs
                new_group.add_argument(*action.option_strings, **kwargs)

    print(test_parser.format_help())
    pytest.exit("After displaying help.", returncode=pytest.ExitCode.OK)
