"""Pytest plugin for configuring and installing the solc compiler."""

import platform
import subprocess
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
    """Add command-line options to pytest."""
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
            # solc-select current does not support ARM linux
            if platform.system().lower() == "linux" and platform.machine().lower() == "aarch64":
                error_message = (
                    f"Version {version} does not match solc_version {solc_version} "
                    "and since solc-select currently does not support ARM linux you must "
                    "manually do the following: "
                    "Build solc from source, and manually move the binary to "
                    ".venv/.solc-select/artifacts/solc-x.y.z/solc-x.y.z, then run "
                    "'uv run solc-select use <x.y.z>'"
                )
                pytest.exit(error_message, returncode=pytest.ExitCode.USAGE_ERROR)

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

    # test whether solc_version matches actual one
    # using subprocess because that's how yul is compiled in
    # ./src/ethereum_test_specs/static_state/common/compile_yul.py
    expected_solc_version_string: str = str(solc_version_semver)
    actual_solc_version = subprocess.run(
        ["solc", "--version"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=True,
    )
    actual_solc_version_string = actual_solc_version.stdout
    # use only look at first 10 chars to pass e.g.
    # actual: 0.8.25+commit.b61c2a91.Linux.g++ should pass with expected: "0.8.25+commit.b61c2a91
    if (
        expected_solc_version_string[:10] not in actual_solc_version_string
    ) or expected_solc_version_string == "":
        error_message = f"Expected solc version {solc_version_semver} but detected a\
 different solc version:\n{actual_solc_version_string}\nCritical error, aborting.."
        pytest.exit(error_message, returncode=pytest.ExitCode.USAGE_ERROR)


@pytest.fixture(autouse=True, scope="session")
def solc_bin(request: pytest.FixtureRequest):
    """Return configured solc binary path."""
    return request.config.getoption("solc_bin")


@pytest.hookimpl(trylast=True)
def pytest_report_header(config, start_path):
    """Add lines to pytest's console output header."""
    if config.option.collectonly:
        return
    solc_version = config.stash[metadata_key]["Tools"]["solc"]
    return [(f"solc: {solc_version}")]
