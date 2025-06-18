"""Fixture output configuration for generated test fixtures."""

import shutil
import tarfile
from pathlib import Path

import pytest
from pydantic import BaseModel, Field

from ethereum_test_fixtures.blockchain import BlockchainEngineXFixture


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
    clean: bool = Field(
        default=False,
        description="Clean (remove) the output directory before filling fixtures.",
    )
    generate_pre_alloc_groups: bool = Field(
        default=False,
        description="Generate pre-allocation groups (phase 1).",
    )
    use_pre_alloc_groups: bool = Field(
        default=False,
        description="Use existing pre-allocation groups (phase 2).",
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

    @property
    def pre_alloc_groups_folder_path(self) -> Path:
        """Return the path for pre-allocation groups folder."""
        engine_x_dir = BlockchainEngineXFixture.output_base_dir_name()
        return self.directory / engine_x_dir / "pre_alloc"

    @staticmethod
    def strip_tarball_suffix(path: Path) -> Path:
        """Strip the '.tar.gz' suffix from the output path."""
        if str(path).endswith(".tar.gz"):
            return path.with_suffix("").with_suffix("")
        return path

    def is_directory_empty(self) -> bool:
        """Check if the output directory is empty."""
        if not self.directory.exists():
            return True

        return not any(self.directory.iterdir())

    def is_directory_usable_for_phase(self) -> bool:
        """Check if the output directory is usable for the current phase."""
        if not self.directory.exists():
            return True

        if self.generate_pre_alloc_groups:
            # Phase 1: Directory must be completely empty
            return self.is_directory_empty()
        elif self.use_pre_alloc_groups:
            # Phase 2: Only pre-allocation groups must exist, no other files allowed
            if not self.pre_alloc_groups_folder_path.exists():
                return False
            # Check that only the pre-allocation group files exist
            existing_files = {f for f in self.directory.rglob("*") if f.is_file()}
            allowed_files = set(self.pre_alloc_groups_folder_path.rglob("*.json"))
            return existing_files == allowed_files
        else:
            # Normal filling: Directory must be empty
            return self.is_directory_empty()

    def get_directory_summary(self) -> str:
        """Return a summary of directory contents for error reporting."""
        if not self.directory.exists():
            return "directory does not exist"

        items = list(self.directory.iterdir())
        if not items:
            return "empty directory"

        dirs = [d.name for d in items if d.is_dir()]
        files = [f.name for f in items if f.is_file()]

        max_dirs = 4
        summary_parts = []
        if dirs:
            summary_parts.append(
                f"{len(dirs)} directories"
                + (
                    f" ({', '.join(dirs[:max_dirs])}"
                    + (f"... and {len(dirs) - max_dirs} more" if len(dirs) > max_dirs else "")
                    + ")"
                    if dirs
                    else ""
                )
            )
        if files:
            summary_parts.append(
                f"{len(files)} files"
                + (
                    f" ({', '.join(files[:3])}"
                    + (f"... and {len(files) - 3} more" if len(files) > 3 else "")
                    + ")"
                    if files
                    else ""
                )
            )

        return " and ".join(summary_parts)

    def create_directories(self, is_master: bool) -> None:
        """
        Create output and metadata directories if needed.

        If clean flag is set, remove and recreate the directory.
        Otherwise, verify the directory is empty before proceeding.
        """
        if self.is_stdout:
            return

        # Only the master process should delete/create directories if using pytest-xdist
        if not is_master:
            return

        if self.directory.exists() and self.clean:
            shutil.rmtree(self.directory)

        if self.directory.exists() and not self.is_directory_usable_for_phase():
            summary = self.get_directory_summary()

            if self.generate_pre_alloc_groups:
                raise ValueError(
                    f"Output directory '{self.directory}' must be completely empty for "
                    f"pre-allocation group generation (phase 1). Contains: {summary}. "
                    "Use --clean to remove all existing files."
                )
            elif self.use_pre_alloc_groups:
                if not self.pre_alloc_groups_folder_path.exists():
                    raise ValueError(
                        "Pre-allocation groups folder not found at "
                        f"'{self.pre_alloc_groups_folder_path}'. "
                        "Run phase 1 with --generate-pre-alloc-groups first."
                    )
            else:
                raise ValueError(
                    f"Output directory '{self.directory}' is not empty. "
                    f"Contains: {summary}. Use --clean to remove all existing files "
                    "or specify a different output directory."
                )

        # Create directories
        self.directory.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

        # Create pre-allocation groups directory for phase 1
        if self.generate_pre_alloc_groups:
            self.pre_alloc_groups_folder_path.parent.mkdir(parents=True, exist_ok=True)

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
    def from_config(cls, config: pytest.Config) -> "FixtureOutput":
        """Create a FixtureOutput instance from pytest configuration."""
        return cls(
            output_path=config.getoption("output"),
            flat_output=config.getoption("flat_output"),
            single_fixture_per_file=config.getoption("single_fixture_per_file"),
            clean=config.getoption("clean"),
            generate_pre_alloc_groups=config.getoption("generate_pre_alloc_groups"),
            use_pre_alloc_groups=config.getoption("use_pre_alloc_groups"),
        )
