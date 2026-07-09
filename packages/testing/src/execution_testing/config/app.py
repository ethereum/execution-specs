"""
A module for managing application configurations.

Classes:
- AppConfig: Holds configurations for the application framework.
"""

from pathlib import Path

from pydantic import BaseModel

from execution_testing.cli.pytest_commands.plugins.consume import (
    releases,
)


class AppConfig(BaseModel):
    """A class for accessing documentation-related configurations."""

    @property
    def version(self) -> str:
        """Get the version of the latest mainnet `tests` release."""
        spec = f"{releases.TESTS_FEATURE_NAME}@latest"
        try:
            release = releases.find_release(
                spec, releases.get_release_information()
            )
        except releases.NoSuchReleaseError:
            return "unknown"
        return release.tag_name.split("@v")[-1]

    DEFAULT_LOGS_DIR: Path = (
        Path(__file__).resolve().parent.parent.parent / "logs"
    )
    """The default directory where log files are stored."""

    ROOT_DIR: Path = Path(__file__).resolve().parents[2]
    """The root directory of the project."""
