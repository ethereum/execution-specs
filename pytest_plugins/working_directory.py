"""
Pytest plugin to fix the working directory for all plugins after pytest has parsed the
configuration files in the necessary relative path to the hard-coded test files
for the commands that need them.
"""

from os import chdir

import pytest


def pytest_addoption(parser):  # noqa: D103
    wd_group = parser.getgroup(
        "working-directory",
        "Arguments related to fixing the work directory for all pytest plugins",
    )
    wd_group.addoption(
        "--working-directory",
        action="store",
        dest="working_directory",
        default=None,
        help=(
            "Specify the correct working directory for pytest plugins to parse the correct "
            "file paths."
        ),
    )


def fix_working_directory(config: pytest.Config) -> None:
    """Change the current working directory if specified as parameter."""
    working_directory = config.getoption("working_directory", default=None)
    if working_directory is not None:
        chdir(working_directory)


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config) -> None:
    """Change the current working directory if specified as parameter."""
    fix_working_directory(config)
