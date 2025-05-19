"""
A module for managing application configurations.

Classes:
- AppConfig: Holds configurations for the application framework.
"""

from pathlib import Path

from pydantic import BaseModel

import pytest_plugins.consume.releases as releases


class AppConfig(BaseModel):
    """A class for accessing documentation-related configurations."""

    @property
    def version(self) -> str:
        """Get the current version from releases."""
        spec = "stable@latest"
        release_url = releases.get_release_url(spec)
        return release_url.split("/v")[-1].split("/")[0]

    DEFAULT_LOGS_DIR: Path = Path(__file__).resolve().parent.parent.parent / "logs"
    """The default directory where log files are stored."""

    DEFAULT_EVM_LOGS_DIR: Path = DEFAULT_LOGS_DIR / "evm"
    """The default directory where EVM log files are stored."""

    ROOT_DIR: Path = Path(__file__).resolve().parents[2]
    """The root directory of the project."""
