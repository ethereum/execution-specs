"""
Pytest plugin to help working with the `ethereum-spec-evm-resolver`.

This plugin sets the `EELS_RESOLUTIONS_FILE` environment variable to the path
of the `eels_resolutions.json` file in the pytest root directory. If the
environment variable is already set, the plugin will not override it.
"""

import os
import shutil
from pathlib import Path

import pytest
from pytest_metadata.plugin import metadata_key  # type: ignore


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config) -> None:
    """
    Set the EELS_RESOLUTIONS_FILE environment variable.

    Args:
        config (pytest.Config): The pytest configuration object.

    """
    evm_bin = config.getoption("evm_bin", default=None)
    if evm_bin and "resolver" not in str(evm_bin):
        # evm_bin is not set for the framework tests: always set the env var.
        return

    env_var_name = "EELS_RESOLUTIONS_FILE"
    eels_resolutions_file = os.getenv(env_var_name)

    if os.getenv("EELS_RESOLUTIONS"):
        # If the user sets this variable, assume they know what they're doing.
        return

    if eels_resolutions_file:
        file_path = Path(eels_resolutions_file)
        if not file_path.is_absolute():
            raise ValueError(f"The path provided in {env_var_name} must be an absolute path.")
        if not file_path.exists():
            raise FileNotFoundError(
                f"The file {file_path} does not exist. "
                f"Ensure the {env_var_name} points to an existing file."
            )
    else:
        root_dir = config.rootpath
        default_file_path = root_dir / "eels_resolutions.json"
        os.environ[env_var_name] = str(default_file_path)
        eels_resolutions_file = str(default_file_path)

    if "Tools" in config.stash[metadata_key]:
        # don't overwrite existing tools metadata added by other plugins
        config.stash[metadata_key]["Tools"]["EELS Resolutions"] = str(eels_resolutions_file)
    else:
        config.stash[metadata_key]["Tools"] = {"EELS Resolutions": str(eels_resolutions_file)}

    config._eels_resolutions_file = eels_resolutions_file  # type: ignore


def pytest_report_header(config: pytest.Config, startdir: Path) -> str:
    """
    Report the EELS_RESOLUTIONS_FILE path to the pytest report header.

    Args:
        config (pytest.Config): The pytest configuration object.
        startdir (Path): The starting directory for the test run.

    Returns:
        str: A string to add to the pytest report header.

    """
    eels_resolutions_file = getattr(config, "_eels_resolutions_file", None)
    if eels_resolutions_file:
        return f"EELS resolutions file: {eels_resolutions_file}"
    return ""


@pytest.fixture(scope="session", autouse=True)
def output_metadata_dir_with_teardown(request):
    """
    Session-scoped fixture that attempts to retrieve the filler's
    "output_metadata_dir" fixture value and copies the EELS resolutions
    file there, if `_eels_resolutions_file` is set on the config object.
    """
    yield
    try:
        output_metadata_dir = request.getfixturevalue("output_metadata_dir")
        if output_metadata_dir.name == "stdout":
            return
    except pytest.FixtureLookupError:
        output_metadata_dir = None

    eels_resolutions_file = getattr(request.config, "_eels_resolutions_file", None)
    if output_metadata_dir and eels_resolutions_file:
        shutil.copy(
            Path(eels_resolutions_file),
            Path(output_metadata_dir) / Path(eels_resolutions_file).name,
        )
