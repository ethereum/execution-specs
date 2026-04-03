#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""
Create a release tarball from a merged fixture directory.

Archive all ``.json`` and ``.ini`` files under a ``fixtures/`` prefix,
matching the structure produced by
``execution_testing.cli.pytest_commands.plugins.shared.fixture_output``.

Use ``pigz`` for parallel compression when available, otherwise fall
back to Python's built-in gzip.
"""

import shutil
import subprocess
import sys
import tarfile
import warnings
from pathlib import Path


def create_tarball_with_pigz(source_dir: Path, output_path: Path) -> None:
    """Create tarball using Python tarfile + pigz for parallel compression."""
    temp_tar = output_path.with_suffix("")  # strip .gz

    with tarfile.open(temp_tar, "w") as tar:
        for file in sorted(source_dir.rglob("*")):
            if file.is_file() and file.suffix in {".json", ".ini"}:
                arcname = Path("fixtures") / file.relative_to(source_dir)
                tar.add(file, arcname=str(arcname))

    subprocess.run(
        ["pigz", "-f", str(temp_tar)],
        check=True,
        capture_output=True,
    )


def create_tarball_standard(source_dir: Path, output_path: Path) -> None:
    """Create tarball using Python's tarfile module (single-threaded)."""
    with tarfile.open(output_path, "w:gz") as tar:
        for file in sorted(source_dir.rglob("*")):
            if file.is_file() and file.suffix in {".json", ".ini"}:
                arcname = Path("fixtures") / file.relative_to(source_dir)
                tar.add(file, arcname=str(arcname))


def main() -> None:
    """Entry point."""
    if len(sys.argv) != 3:
        print(
            "Usage: create_release_tarball.py <source_dir> <output.tar.gz>",
            file=sys.stderr,
        )
        sys.exit(1)

    source_dir = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    if not source_dir.is_dir():
        print(f"Error: '{source_dir}' is not a directory.", file=sys.stderr)
        sys.exit(1)

    if shutil.which("pigz"):
        try:
            create_tarball_with_pigz(source_dir, output_path)
        except (subprocess.CalledProcessError, OSError) as e:
            warnings.warn(
                f"pigz failed ({type(e).__name__}: {e}), falling back to gzip",
                stacklevel=2,
            )
            create_tarball_standard(source_dir, output_path)
    else:
        create_tarball_standard(source_dir, output_path)

    print(f"Created {output_path}")


if __name__ == "__main__":
    main()
