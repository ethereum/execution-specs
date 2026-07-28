"""
A module for managing application configurations.

Classes:
- AppConfig: Holds configurations for the application framework.
"""

from importlib.metadata import version as package_version
from pathlib import Path

from pydantic import BaseModel


class AppConfig(BaseModel):
    """A class for accessing documentation-related configurations."""

    @property
    def version(self) -> str:
        """Get the locally installed EEST package version."""
        return package_version("ethereum-execution-testing")

    DEFAULT_LOGS_DIR: Path = (
        Path(__file__).resolve().parent.parent.parent / "logs"
    )
    """The default directory where log files are stored."""

    ROOT_DIR: Path = Path(__file__).resolve().parents[2]
    """The root directory of the project."""
