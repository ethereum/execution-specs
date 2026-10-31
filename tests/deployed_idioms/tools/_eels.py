"""
Locate the execution-spec checkout that fills these tests.

Every tool here needs two paths: the spec repo root and its `fill` binary. They
used to be derived from this file's own location (`ROOT.parent/engine/eels`),
and one tool hardcoded an absolute path from the author's machine — so the
corpus ran only in the tree it was written in and failed immediately from a
clean checkout. Resolution order:

  1. $EELS_ROOT                         -- set this; it is the portable answer
  2. a few conventional sibling layouts -- convenience for this workspace
  3. a clear error naming $EELS_ROOT    -- never a confusing FileNotFoundError

`fill` is looked for in the repo's `.venv/bin` and then on PATH, so a system
or activated-venv install works too.
"""

import os
import shutil
from pathlib import Path

_PATTERNS = Path(__file__).resolve().parents[1]

_CANDIDATES = [
    _PATTERNS.parent / "engine" / "eels",
    _PATTERNS.parent.parent / "engine" / "eels",
    _PATTERNS.parent / "execution-spec-tests",
    _PATTERNS.parent / "execution-specs",
    _PATTERNS.parent / "eels",
]


def _looks_like_eels(p: Path) -> bool:
    return (p / "src" / "ethereum" / "forks").is_dir() or (p / "tests").is_dir()


def eels_root() -> Path:
    env = os.environ.get("EELS_ROOT")
    if env:
        p = Path(env).expanduser().resolve()
        if not _looks_like_eels(p):
            raise SystemExit(
                f"EELS_ROOT={p} does not look like an execution-spec checkout "
                "(no src/ethereum/forks/ and no tests/)."
            )
        return p
    for c in _CANDIDATES:
        if c.is_dir() and _looks_like_eels(c):
            return c.resolve()
    raise SystemExit(
        "Cannot find the execution-spec checkout. Set EELS_ROOT, e.g.\n"
        "  EELS_ROOT=/path/to/execution-spec-tests python3 tools/verify_corpus.py\n"
        f"Tried: {', '.join(str(c) for c in _CANDIDATES)}"
    )


def fill_bin(root: Path | None = None) -> Path:
    root = root or eels_root()
    venv = root / ".venv" / "bin" / "fill"
    if venv.exists():
        return venv
    on_path = shutil.which("fill")
    if on_path:
        return Path(on_path)
    raise SystemExit(
        f"No `fill` binary: looked in {venv} and on PATH. Install the spec "
        "repo's dev environment, or activate its venv."
    )


def forks_dir(root: Path | None = None) -> Path:
    return (root or eels_root()) / "src" / "ethereum" / "forks"
