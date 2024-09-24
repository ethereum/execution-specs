"""
Pytest plugin for configuring and installing the solc compiler.
"""

from argparse import ArgumentTypeError
from shutil import which

import pytest
import solc_select.solc_select as solc_select  # type: ignore
from pytest_metadata.plugin import metadata_key  # type: ignore
from semver import Version

from ethereum_test_forks import Frontier
from ethereum_test_tools.code import Solc

DEFAULT_SOLC_VERSION = "0.8.24"


def pytest_addoption(parser: pytest.Parser):
    """
    Adds command-line options to pytest.
    """
    solc_group = parser.getgroup("solc", "Arguments defining the solc executable")
    solc_group.addoption(
        "--solc-bin",
        action="store",
        dest="solc_bin",
        type=str,
        default=None,
        help=(
            "Path to a solc executable (for Yul source compilation). "
            "No default; if unspecified `--solc-version` is used."
        ),
    )
    solc_group.addoption(
        "--solc-version",
        action="store",
        dest="solc_version",
        default=None,
        help=f"Version of the solc compiler to use. Default: {DEFAULT_SOLC_VERSION}.",
    )


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config):
    """
    Ensure that the specified solc version is:
    - available if --solc_bin has been specified,
    - installed via solc_select if --solc_version has been specified.
    """
    solc_bin = config.getoption("solc_bin")
    solc_version = config.getoption("solc_version")

    if solc_bin and solc_version:
        raise pytest.UsageError(
            "You cannot specify both --solc-bin and --solc-version. Please choose one."
        )

    if solc_bin:
        # will raise an error if the solc binary is not found.
        solc_version_semver = Solc(config.getoption("solc_bin")).version
    else:
        # if no solc binary is specified, use solc-select
        solc_version = solc_version or DEFAULT_SOLC_VERSION
        try:
            version, _ = solc_select.current_version()
        except ArgumentTypeError:
            version = None
        if version != solc_version:
            if config.getoption("verbose") > 0:
                print(f"Setting solc version {solc_version} via solc-select...")
            try:
                solc_select.switch_global_version(solc_version, always_install=True)
            except Exception as e:
                message = f"Failed to install solc version {solc_version}: {e}. "
                if isinstance(e, ArgumentTypeError):
                    message += "\nList available versions using `uv run solc-select install`."
                pytest.exit(message, returncode=pytest.ExitCode.USAGE_ERROR)
        solc_version_semver = Version.parse(solc_version)
        config.option.solc_bin = which("solc")  # save for fixture

    if "Tools" not in config.stash[metadata_key]:
        config.stash[metadata_key]["Tools"] = {
            "solc": str(solc_version_semver),
        }
    else:
        config.stash[metadata_key]["Tools"]["solc"] = str(solc_version_semver)

    if solc_version_semver < Frontier.solc_min_version():
        pytest.exit(
            f"Unsupported solc version: {solc_version}. Minimum required version is "
            f"{Frontier.solc_min_version()}",
            returncode=pytest.ExitCode.USAGE_ERROR,
        )
    config.solc_version = solc_version_semver  # type: ignore


@pytest.fixture(autouse=True, scope="session")
def solc_bin(request: pytest.FixtureRequest):
    """
    Returns the configured solc binary path.
    """
    return request.config.getoption("solc_bin")
