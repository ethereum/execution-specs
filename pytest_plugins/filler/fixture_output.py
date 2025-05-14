"""Fixture output configuration for generated test fixtures."""

import tarfile
from pathlib import Path

import pytest
from pydantic import BaseModel, Field


class FixtureOutput(BaseModel):
    """Represents the output destination for generated test fixtures."""

    output_path: Path = Field(description="Directory path to store the generated test fixtures")
    flat_output: bool = Field(
        default=False,
        description="Output each test case in the directory without the folder structure",
    )
    single_fixture_per_file: bool = Field(
        default=False,
        description=(
            "Don't group fixtures in JSON files by test function; "
            "write each fixture to its own file"
        ),
    )

    @property
    def directory(self) -> Path:
        """Return the actual directory path where fixtures will be written."""
        return self.strip_tarball_suffix(self.output_path)

    @property
    def metadata_dir(self) -> Path:
        """Return metadata directory to store fixture meta files."""
        if self.is_stdout:
            return self.directory
        return self.directory / ".meta"

    @property
    def is_tarball(self) -> bool:
        """Return True if the output should be packaged as a tarball."""
        path = self.output_path
        return path.suffix == ".gz" and path.with_suffix("").suffix == ".tar"

    @property
    def is_stdout(self) -> bool:
        """Return True if the fixture output is configured to be stdout."""
        return self.directory.name == "stdout"

    @staticmethod
    def strip_tarball_suffix(path: Path) -> Path:
        """Strip the '.tar.gz' suffix from the output path."""
        if str(path).endswith(".tar.gz"):
            return path.with_suffix("").with_suffix("")
        return path

    def create_directories(self) -> None:
        """Create output and metadata directories if needed."""
        if self.is_stdout:
            return

        self.directory.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

    def create_tarball(self) -> None:
        """Create tarball of the output directory if configured to do so."""
        if not self.is_tarball:
            return

        with tarfile.open(self.output_path, "w:gz") as tar:
            for file in self.directory.rglob("*"):
                if file.suffix in {".json", ".ini"}:
                    arcname = Path("fixtures") / file.relative_to(self.directory)
                    tar.add(file, arcname=arcname)

    @classmethod
    def from_options(
        cls, output_path: Path, flat_output: bool, single_fixture_per_file: bool
    ) -> "FixtureOutput":
        """Create a FixtureOutput instance from pytest options."""
        return cls(
            output_path=output_path,
            flat_output=flat_output,
            single_fixture_per_file=single_fixture_per_file,
        )

    @classmethod
    def from_config(cls, config: pytest.Config) -> "FixtureOutput":
        """Create a FixtureOutput instance from pytest configuration."""
        return cls(
            output_path=config.getoption("output"),
            flat_output=config.getoption("flat_output"),
            single_fixture_per_file=config.getoption("single_fixture_per_file"),
        )
