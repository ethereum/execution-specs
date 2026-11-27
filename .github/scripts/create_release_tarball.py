#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""
Create a release tarball from a merged fixture directory.

Archive all `.json` and `.ini` files under a `fixtures/` prefix,
matching the structure produced by
`execution_testing.cli.pytest_commands.plugins.shared.fixture_output`.

Use `pigz` for parallel compression when available, otherwise fall
back to Python's built-in gzip.
"""

import shutil
import subprocess
import sys
import tarfile
import warnings
from pathlib import Path


def add_fixture_files(tar: tarfile.TarFile, source_dir: Path) -> None:
    """Add the fixture files under `source_dir` to `tar`, sorted."""
    for file in sorted(source_dir.rglob("*")):
        if file.is_file() and file.suffix in {".json", ".ini"}:
            arcname = Path("fixtures") / file.relative_to(source_dir)
            tar.add(file, arcname=str(arcname))


def create_tarball_with_pigz(source_dir: Path, output_path: Path) -> None:
    """
    Create tarball by streaming Python tarfile into pigz, which compresses
    in parallel while files are still being added.
    """
    with output_path.open("wb") as out:
        pigz = subprocess.Popen(
            ["pigz", "-c"], stdin=subprocess.PIPE, stdout=out
        )
        assert pigz.stdin is not None
        try:
            with tarfile.open(fileobj=pigz.stdin, mode="w|") as tar:
                add_fixture_files(tar, source_dir)
        finally:
            pigz.stdin.close()
            returncode = pigz.wait()
    if returncode != 0:
        raise subprocess.CalledProcessError(returncode, "pigz")


def create_tarball_standard(source_dir: Path, output_path: Path) -> None:
    """Create tarball using Python's tarfile module (single-threaded)."""
    with tarfile.open(output_path, "w:gz") as tar:
        add_fixture_files(tar, source_dir)


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
