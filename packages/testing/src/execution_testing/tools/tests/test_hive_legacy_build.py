"""Tests for the deprecated hive build arguments script, legacy_build.sh."""

import os
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

SCRIPT = (
    Path(__file__).resolve().parents[4] / "docker" / "hive" / "legacy_build.sh"
)
COMMIT = "c" * 40


@pytest.fixture
def root(tmp_path: Path) -> Path:
    """Lay out an image filesystem with stub git and uv that log calls."""
    (tmp_path / "repo" / "packages" / "testing").mkdir(parents=True)
    fixtures = tmp_path / "fixtures"
    (fixtures / ".meta").mkdir(parents=True)
    (fixtures / "blockchain_tests").mkdir()
    (tmp_path / "staged").mkdir()
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    # git clone creates the tree; rev-parse prints the commit.
    (bin_dir / "git").write_text(
        f"#!{sys.executable}\n"
        "import os, sys\n"
        "args = sys.argv[1:]\n"
        "line = 'git ' + ' '.join(args) + '\\n'\n"
        "open(os.environ['STUB_LOG'], 'a').write(line)\n"
        "if args[0] == 'clone':\n"
        "    os.makedirs(os.path.join(args[-1], 'packages', 'testing'))\n"
        "if 'rev-parse' in args:\n"
        f"    print('{COMMIT}')\n"
    )
    (bin_dir / "uv").write_text(
        f"#!{sys.executable}\n"
        "import os, sys\n"
        "open(os.environ['STUB_LOG'], 'a').write("
        "'uv ' + ' '.join(sys.argv[1:]) + ' downloads='"
        " + os.environ.get('UV_PYTHON_DOWNLOADS', '') + '\\n')\n"
    )
    for stub in bin_dir.iterdir():
        stub.chmod(0o755)
    return tmp_path


def run(root: Path, **build_args: str) -> subprocess.CompletedProcess:
    """Run the script with the given build arguments in the environment."""
    env = {
        **os.environ,
        "PATH": f"{root / 'bin'}:{os.environ['PATH']}",
        "STUB_LOG": str(root / "calls"),
        "EELS_LEGACY_STATE": str(root / "state"),
        "EELS_LEGACY_STAGED": str(root / "staged"),
        "EELS_LEGACY_REPO": str(root / "repo"),
        "EELS_LEGACY_FIXTURES_DIR": str(root / "fixtures"),
        **build_args,
    }
    return subprocess.run(
        ["sh", str(SCRIPT)], env=env, capture_output=True, text=True
    )


def calls(root: Path) -> list[str]:
    """Return the logged git and uv calls."""
    log = root / "calls"
    return log.read_text().splitlines() if log.exists() else []


def state(root: Path) -> dict[str, str]:
    """Return the recorded state files and their contents."""
    directory = root / "state"
    if not directory.exists():
        return {}
    return {f.name: f.read_text().strip() for f in directory.iterdir()}


@pytest.mark.parametrize(
    "build_args",
    [
        {},
        {"tag": "latest", "fixtures": "tests@v20.0.2", "branch": "x"},
    ],
    ids=["no-arguments", "tag-wins"],
)
def test_published_image_is_left_alone(
    root: Path, build_args: dict[str, str]
) -> None:
    """Without legacy arguments, or with a tag, nothing changes."""
    result = run(root, **build_args)
    assert result.returncode == 0, result.stderr
    assert calls(root) == []
    assert not (root / "state").exists()
    assert not (root / "staged").exists(), "the staging directory is removed"
    assert "deprecated" not in result.stderr


def test_fixtures_release_is_cached(root: Path) -> None:
    """A release name or URL is cached at build time, as Dockerfile.git did."""
    url = "https://example.org/fixtures.tar.gz?a=b&c=d"
    result = run(root, fixtures=url)
    assert result.returncode == 0, result.stderr
    assert "deprecated" in result.stderr
    assert calls(root) == [
        f"uv run --no-sync consume cache --input {url} downloads="
    ]
    assert state(root) == {"fixtures": url}


def test_staged_tarball_replaces_the_image_fixtures(root: Path) -> None:
    """`fixtures=/fixtures` extracts .meta and the image's format only."""
    source = root / "source" / "fixtures"
    for directory in (".meta", "blockchain_tests", "state_tests"):
        (source / directory).mkdir(parents=True)
        (source / directory / "a.json").write_text("{}")
    with tarfile.open(root / "staged" / "fixtures.tar.gz", "w:gz") as tar:
        tar.add(source, arcname="fixtures")
    result = run(root, fixtures="/fixtures")
    assert result.returncode == 0, result.stderr
    assert sorted(p.name for p in (root / "fixtures").iterdir()) == [
        ".meta",
        "blockchain_tests",
    ]
    assert state(root) == {"fixtures": "/fixtures"}
    assert calls(root) == []


def test_image_fixtures_without_a_staged_tarball(root: Path) -> None:
    """`fixtures=/fixtures` alone names the image's own fixtures."""
    result = run(root, fixtures="/fixtures")
    assert result.returncode == 0, result.stderr
    assert state(root) == {}
    assert (root / "fixtures" / "blockchain_tests").exists()


def test_branch_replaces_the_framework(root: Path) -> None:
    """A branch is cloned and synced as Dockerfile.git did, downloads on."""
    result = run(root, branch="devnets/bogota/1")
    assert result.returncode == 0, result.stderr
    log = calls(root)
    assert log[0].startswith("git clone --depth 1 ")
    assert log[1].endswith("fetch --depth 1 origin devnets/bogota/1")
    assert log[3] == "uv sync downloads=automatic"
    assert state(root) == {"branch": "devnets/bogota/1", "commit": COMMIT}
    assert (root / "repo" / "packages" / "testing").exists()


def test_execute_images_ignore_fixtures(root: Path) -> None:
    """Execute simulators had no fixtures argument; it is reported, unused."""
    result = run(
        root, fixtures="tests@v20.0.2", EEST_SIMULATOR="execute-blobs"
    )
    assert result.returncode == 0, result.stderr
    assert "ignoring fixtures" in result.stderr
    assert calls(root) == []
    assert state(root) == {}
