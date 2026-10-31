#!/usr/bin/env python3
"""
Run `fill` while holding the same exclusive lock `tools/mutate.py` takes.

Measurement and verification runs must be serialised against the mutation
harness, not just against each other: a `fill` that lands inside another
agent's mutation window reads mutated gas numbers and looks like a clean
measurement. That happened once during this work (an archetype that
passes on a pristine tree reported +2,900 execution gas), which is why
this wrapper exists.

Usage: locked_fill.py <fill args...>
"""

import fcntl
import subprocess
import sys
import time
from pathlib import Path

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent))
from _layout import (  # noqa: E402
    CORPUS, INSTRUMENTS, archetypes as _archetypes, fill_bin, forks_dir,
    lock_path, mutations_dir, spec_root,
)

ROOT = CORPUS
EELS = spec_root()
FILL = fill_bin()
FORKS = forks_dir()

if dirty:
    raise SystemExit(f"REFUSING: EELS forks tree is dirty:\n{dirty}")

p = subprocess.run([str(FILL), *sys.argv[1:]], cwd=EELS)
fcntl.flock(lock_fd, fcntl.LOCK_UN)
sys.exit(p.returncode)
