"""Fixture output configuration for generated test fixtures."""

import shutil
import subprocess
import tarfile
import warnings
from pathlib import Path

import pytest
from pydantic import BaseModel, Field


class FixtureOutput(BaseModel):
    """Represents the output destination for generated test fixtures."""

    output_path: Path = Field(
        description="Directory path to store the generated test fixtures"
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
        description="Clean (remove) output directory before filling.",
    )
    generate_pre_alloc_groups: bool = Field(
        default=False,
        description="Generate pre-allocation groups (phase 1).",
    )
    use_pre_alloc_groups: bool = Field(
        default=False,
        description="Use existing pre-allocation groups (phase 2).",
    )
    should_generate_all_formats: bool = Field(
        default=False,
        description="Generate all formats including BlockchainEngineXFixture.",
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
        # Local import: fixtures.collector imports from this module.
        from execution_testing.fixtures.blockchain import (
            BlockchainEngineXFixture,
        )

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
            # Phase 2: Only pre-allocation groups must exist, no other files
            # allowed
            if not self.pre_alloc_groups_folder_path.exists():
                return False
            # Check that only the pre-allocation group files exist
            existing_files = {
                f for f in self.directory.rglob("*") if f.is_file()
            }
            allowed_files = set(
                self.pre_alloc_groups_folder_path.rglob("*.json")
            )
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
                    + (
                        f"... and {len(dirs) - max_dirs} more"
                        if len(dirs) > max_dirs
                        else ""
                    )
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
                    + (
                        f"... and {len(files) - 3} more"
                        if len(files) > 3
                        else ""
                    )
                    + ")"
                    if files
                    else ""
                )
            )

        return " and ".join(summary_parts)

    def create_directories(self, is_master: bool) -> None:
        """
        Create output and metadata directories if needed.

        If clean flag is set, remove and recreate the directory. Otherwise,
        verify the directory is empty before proceeding.
        """
        if self.is_stdout:
            return

        # Only the master process should delete/create directories if using
        # pytest-xdist
        if not is_master:
            return

        if self.directory.exists() and self.clean:
            shutil.rmtree(self.directory)

        if (
            self.directory.exists()
            and not self.is_directory_usable_for_phase()
        ):
            summary = self.get_directory_summary()

            if self.generate_pre_alloc_groups:
                raise ValueError(
                    f"Output directory '{self.directory}' must be completely "
                    f"empty for pre-allocation group generation (phase 1). "
                    f"Contains: {summary}. Use --clean to remove all "
                    "existing files."
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
                    f"Contains: {summary}. Use --clean to remove all "
                    "existing files or specify a different output directory."
                )

        # Create directories
        self.directory.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

        # Create pre-allocation groups directory for phase 1
        if self.generate_pre_alloc_groups:
            self.pre_alloc_groups_folder_path.parent.mkdir(
                parents=True, exist_ok=True
            )

    @staticmethod
    def _pigz_available() -> bool:
        """Check if pigz (parallel gzip) is available on the system."""
        return shutil.which("pigz") is not None

    def create_tarball(self) -> None:
        """
        Create tarball of the output directory if configured to do so.

        Automatically uses pigz for parallel compression if available,
        otherwise falls back to standard single-threaded gzip.
        """
        if not self.is_tarball:
            return

        if self._pigz_available():
            self._create_tarball_with_pigz()
        else:
            self._create_tarball_standard()

    def _create_tarball_standard(self) -> None:
        """Create tarball using Python's tarfile module (single-threaded)."""
        with tarfile.open(self.output_path, "w:gz") as tar:
            for file in self.directory.rglob("*"):
                if file.suffix in {".json", ".ini"}:
                    arcname = Path("fixtures") / file.relative_to(
                        self.directory
                    )
                    tar.add(file, arcname=arcname)

    def _create_tarball_with_pigz(self) -> None:
        """
        Create tarball using Python tarfile + pigz for parallel compression.

        This approach uses Python's tarfile to create the uncompressed .tar
        (which correctly handles arcnames across all platforms), then uses
        pigz for parallel gzip compression with auto-detected core count.
        """
        # Create uncompressed tar first (output_path minus .gz suffix)
        temp_tar = self.output_path.with_suffix("")  # Remove .gz suffix

        try:
            # Use Python tarfile for cross-platform tar creation with arcnames
            with tarfile.open(temp_tar, "w") as tar:
                for file in self.directory.rglob("*"):
                    if file.suffix in {".json", ".ini"}:
                        arcname = Path("fixtures") / file.relative_to(
                            self.directory
                        )
                        tar.add(file, arcname=arcname)

            # Compress with pigz (parallel gzip, auto-detects available cores)
            subprocess.run(
                ["pigz", "-f", str(temp_tar)], check=True, capture_output=True
            )
        except (subprocess.CalledProcessError, OSError) as e:
            # Clean up temp file if it exists
            if temp_tar.exists():
                temp_tar.unlink()
            # Fall back to standard tarball creation with warning
            warnings.warn(
                f"pigz compression failed ({type(e).__name__}: {e}), "
                "falling back to standard gzip",
                stacklevel=2,
            )
            self._create_tarball_standard()

    @classmethod
    def from_config(cls, config: pytest.Config) -> "FixtureOutput":
        """Create a FixtureOutput instance from pytest configuration."""
        output_path = Path(config.getoption("output"))
        should_generate_all_formats = config.getoption("generate_all_formats")

        # Auto-enable --generate-all-formats for tarball output
        # Use same logic as is_tarball property
        if (
            output_path.suffix == ".gz"
            and output_path.with_suffix("").suffix == ".tar"
        ):
            should_generate_all_formats = True

        return cls(
            output_path=output_path,
            single_fixture_per_file=config.getoption(
                "single_fixture_per_file"
            ),
            clean=config.getoption("clean"),
            generate_pre_alloc_groups=config.getoption(
                "generate_pre_alloc_groups"
            ),
            use_pre_alloc_groups=config.getoption("use_pre_alloc_groups"),
            should_generate_all_formats=should_generate_all_formats,
        )


FORK_SUBDIR_PREFIX = "for_"
SUBFOLDER_LEVEL_SEPARATOR = "_at_"


def format_gas_limit_prefix(
    gas_value_millions: int, all_values_millions: list[int]
) -> str:
    """Return a stable, sortable gas-limit prefix for a fixture subfolder."""
    max_value = max(all_values_millions) if all_values_millions else 0
    width = max(4, len(str(max_value)))
    return f"{gas_value_millions:0{width}d}M"


def format_fork_subdir(
    fork_name: str,
    gas_limit_subdir: str | None = None,
) -> str:
    """
    Return the fork-based output subdirectory name.

    Without *gas_limit_subdir*: ``for_prague``
    With *gas_limit_subdir*:    ``for_prague_at_0002M``
    """
    base = f"{FORK_SUBDIR_PREFIX}{fork_name.lower()}"
    if gas_limit_subdir is not None:
        return f"{base}{SUBFOLDER_LEVEL_SEPARATOR}{gas_limit_subdir}"
    return base


def resolve_fixture_subfolder(
    markers: list[pytest.Mark],
) -> Path | None:
    """
    Build the output subdirectory from ``fixture_subfolder`` markers.

    Markers are sorted by *level* and their *prefix* values are joined with
    ``_at_`` to form a single directory name.  Returns ``None`` when no
    markers are present.
    """
    if not markers:
        return None
    ordered = sorted(markers, key=lambda m: m.kwargs.get("level", 0))
    prefixes = [m.kwargs["prefix"] for m in ordered]
    return Path(SUBFOLDER_LEVEL_SEPARATOR.join(prefixes))
