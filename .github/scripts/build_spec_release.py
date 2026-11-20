"""
Build the `ethereum-execution` release archives up to a given fork.

Usage: `uv run python .github/scripts/build_spec_release.py --until
<fork> --out-dir <dir>`, or `just build-spec-release <fork>`.

The default branch holds every fork the specs know about, including
the forks still under development. A PyPI release only ships the forks
up to and including `--until`, in fork order.

The script exports the committed tree at `HEAD` into a temporary
directory, deletes the later fork packages there, removes them from
the packages list in `pyproject.toml`, and builds the sdist and wheel
from that copy. The checkout itself is never modified. Both archives
are then checked: the later forks must be absent and every kept fork
present.
"""

import argparse
import re
import shutil
import subprocess
import tarfile
import tempfile
import zipfile
from pathlib import Path

from ethereum_spec_tools.forks import Hardfork

REPO_ROOT = Path(__file__).resolve().parents[2]


def split_forks(
    until: str, all_forks: list[str]
) -> tuple[list[str], list[str]]:
    """
    Split fork short names, in fork order, at `until`.

    Return the forks up to and including `until`, then the later ones.
    """
    if until not in all_forks:
        known = ", ".join(all_forks)
        raise SystemExit(f"Unknown fork {until!r}. Known forks: {known}")
    index = all_forks.index(until) + 1
    return all_forks[:index], all_forks[index:]


def remove_packages(pyproject: str, forks: list[str]) -> str:
    """
    Remove the packages of `forks` from the setuptools packages list.

    Fail if a fork has no entry, since the list would then be out of
    step with the source tree.
    """
    for fork in forks:
        pattern = re.compile(
            rf'^\s*"ethereum\.forks\.{fork}(\.[\w.]+)?",\n', re.MULTILINE
        )
        pyproject, count = pattern.subn("", pyproject)
        if count == 0:
            raise SystemExit(f"No `ethereum.forks.{fork}` packages listed")
    return pyproject


def archive_fork_dirs(names: list[str]) -> set[str]:
    """Return the fork package names found in a list of archive paths."""
    found = set()
    for name in names:
        match = re.search(r"(?:^|/)ethereum/forks/(\w+)/__init__\.py$", name)
        if match:
            found.add(match.group(1))
    return found


def check_archive(path: Path, kept: list[str], dropped: list[str]) -> None:
    """Check that an archive ships exactly the kept forks."""
    if path.suffix == ".whl":
        with zipfile.ZipFile(path) as wheel:
            names = wheel.namelist()
    else:
        with tarfile.open(path) as sdist:
            names = sdist.getnames()
    found = archive_fork_dirs(names)
    leaked = found & set(dropped)
    missing = set(kept) - found
    if leaked or missing:
        raise SystemExit(
            f"{path.name}: unexpected forks {sorted(leaked)}, "
            f"missing forks {sorted(missing)}"
        )
    print(f"{path.name}: {len(found)} forks, none after the release fork")


def main() -> None:
    """Build and check the release archives."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--until",
        required=True,
        help="Last fork to ship, by short name, for example `amsterdam`.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        required=True,
        help="Directory for the sdist and wheel; emptied first.",
    )
    args = parser.parse_args()

    all_forks = [fork.short_name for fork in Hardfork.discover()]
    kept, dropped = split_forks(args.until, all_forks)
    print(f"Shipping {kept[0]} to {kept[-1]} ({len(kept)} forks)")
    print(f"Leaving out: {', '.join(dropped) if dropped else 'nothing'}")

    out_dir = args.out_dir.resolve()
    shutil.rmtree(out_dir, ignore_errors=True)
    out_dir.mkdir(parents=True)

    with tempfile.TemporaryDirectory() as tmp:
        tree = Path(tmp) / "tree"
        tree.mkdir()
        # Export the committed tree only: a release is built from a
        # tag, never from uncommitted changes.
        archive = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "archive", "HEAD"],
            check=True,
            capture_output=True,
        ).stdout
        subprocess.run(
            ["tar", "-x", "-C", str(tree)], input=archive, check=True
        )

        for fork in dropped:
            shutil.rmtree(tree / "src" / "ethereum" / "forks" / fork)
        pyproject = tree / "pyproject.toml"
        pyproject.write_text(remove_packages(pyproject.read_text(), dropped))

        subprocess.run(
            ["uv", "build", "--sdist", "--wheel", "--out-dir", str(out_dir)],
            cwd=tree,
            check=True,
        )

    archives = sorted(out_dir.glob("ethereum_execution-*"))
    if len(archives) != 2:
        raise SystemExit(f"Expected an sdist and a wheel, got {archives}")
    for path in archives:
        check_archive(path, kept, dropped)


if __name__ == "__main__":
    main()
