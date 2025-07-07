"""Pytest plugin for configuring and verifying the solc compiler."""

import subprocess
from shutil import which

import pytest
from pytest_metadata.plugin import metadata_key  # type: ignore
from semver import Version

SOLC_EXPECTED_MIN_VERSION: Version = Version.parse("0.8.24")


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
            "Path to a solc executable (for Yul source compilation). Default: solc binary in PATH."
        ),
    )


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config):
    """Ensure that solc is available and get its version."""
    solc_bin = config.getoption("solc_bin")

    # Use provided solc binary or find it in PATH
    if solc_bin:
        if not which(solc_bin):
            pytest.exit(
                f"Specified solc binary not found: {solc_bin}",
                returncode=pytest.ExitCode.USAGE_ERROR,
            )
    else:
        solc_bin = which("solc")
        if not solc_bin:
            pytest.exit(
                "solc binary not found in PATH. Please install solc and ensure it's in your PATH.",
                returncode=pytest.ExitCode.USAGE_ERROR,
            )

    # Get solc version using subprocess
    try:
        result = subprocess.run(
            [solc_bin, "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        pytest.exit(
            f"Failed to get solc version. Command output: {e.stdout}",
            returncode=pytest.ExitCode.USAGE_ERROR,
        )
    except subprocess.TimeoutExpired:
        pytest.exit("Timeout while getting solc version.", returncode=pytest.ExitCode.USAGE_ERROR)
    except Exception as e:
        pytest.exit(
            f"Unexpected error while getting solc version: {e}",
            returncode=pytest.ExitCode.USAGE_ERROR,
        )

    # Parse version from output
    version_output = result.stdout
    version_line = None

    # Look for version in output (format: "Version: X.Y.Z+commit.hash")
    for line in version_output.split("\n"):
        if line.startswith("Version:"):
            version_line = line
            break

    if not version_line:
        pytest.exit(
            f"Could not parse solc version from output:\n{version_output}",
            returncode=pytest.ExitCode.USAGE_ERROR,
        )

    # Extract version number
    try:
        # --version format is typically something like "0.8.24+commit.e11b9ed9.Linux.g++"
        version_str = version_line.split()[1].split("+")[0]
        solc_version_semver = Version.parse(version_str)
    except (IndexError, ValueError) as e:
        pytest.exit(
            f"Failed to parse solc version from: {version_line}\nError: {e}",
            returncode=pytest.ExitCode.USAGE_ERROR,
        )

    # Store version in metadata
    if "Tools" not in config.stash[metadata_key]:
        config.stash[metadata_key]["Tools"] = {
            "solc": str(solc_version_semver),
        }
    else:
        config.stash[metadata_key]["Tools"]["solc"] = str(solc_version_semver)

    # Check minimum version requirement
    solc_version_semver = Version.parse(str(solc_version_semver).split()[0].split("-")[0])
    if solc_version_semver < SOLC_EXPECTED_MIN_VERSION:
        pytest.exit(
            f"Unsupported solc version: {solc_version_semver}. Minimum required version is "
            f"{SOLC_EXPECTED_MIN_VERSION}",
            returncode=pytest.ExitCode.USAGE_ERROR,
        )

    # Store for later use
    config.solc_version = solc_version_semver  # type: ignore
    config.option.solc_bin = solc_bin  # save for fixture

    if config.getoption("verbose") > 0:
        print(f"Using solc version {solc_version_semver} from {solc_bin}")


@pytest.fixture(autouse=True, scope="session")
def solc_bin(request: pytest.FixtureRequest):
    """Return configured solc binary path."""
    return request.config.getoption("solc_bin") or which("solc")


@pytest.hookimpl(trylast=True)
def pytest_report_header(config, start_path):
    """Add lines to pytest's console output header."""
    if config.option.collectonly:
        return
    solc_version = config.stash[metadata_key]["Tools"]["solc"]
    solc_path = config.option.solc_bin or which("solc")
    return [f"solc: {solc_version}", f"solc path: {solc_path}"]
