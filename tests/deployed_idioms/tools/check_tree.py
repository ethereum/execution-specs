#!/usr/bin/env python3
"""
Decide whether a dirty EELS fork tree is someone's LIVE mutation or a stale
leftover — before touching it.

Why this is a tool and not a habit: an agent found `src/ethereum/forks/` dirty
three separate times, and every time it was another contributor's **in-flight**
mutation. Reflexively running `git checkout --` would have silently corrupted a
neighbour's measurement mid-run. The opposite error is just as bad: a genuine
leftover from a run killed before its `finally` (the `timeout <n> python3
<lock-holding script>` corruption mode) poisons every later measurement, and a
corpus fill against it looks like an ordinary pass.

Exit codes:  0 clean · 10 live mutation, WAIT · 20 stale leftover, restore it

Usage:  python3 tools/check_tree.py
"""

import glob
import json
import subprocess
import sys
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


def main() -> int:
    diff = subprocess.run(["git", "diff", "src/ethereum/forks/"],
                          capture_output=True, text=True, cwd=EELS).stdout
    if not diff.strip():
        print("tree CLEAN — src/ethereum/forks/ matches git HEAD")
        return 0

    files = subprocess.run(["git", "diff", "--name-only", "src/ethereum/forks/"],
                           capture_output=True, text=True, cwd=EELS).stdout.split()
    added = {l[1:].strip() for l in diff.splitlines()
             if l.startswith("+") and not l.startswith("+++") and l[1:].strip()}

    matches = []
    # EVERY wave's mutations, not just wave 1. Globbing only the top-level
    # directory made this return "stale, restore it" while an expansion-wave
    # mutation was genuinely in flight — the dangerous direction.
    files = sorted(glob.glob(str(mutations_dir() / "*.json")))
    for f in files:
        for name, spec in json.load(open(f)).items():
            if name.startswith("_"):
                continue
            for line in str(spec.get("replace", "")).splitlines():
                if line.strip() and line.strip() in added:
                    matches.append((name, Path(f).name))
                    break

    live = subprocess.run(["pgrep", "-f", "tools/mutate.py"],
                          capture_output=True, text=True).stdout.split()

    print(f"tree DIRTY: {len(files)} file(s)")
    for p in files:
        print(f"  {p}")
    print(f"mutate.py processes alive: {len(live)}")
    if matches:
        print(f"diff matches registered mutation(s): "
              f"{', '.join(n + ' [' + s + ']' for n, s in matches)}")

    if matches and live:
        print("\nVERDICT: LIVE mutation run. Do NOT restore — you would corrupt a "
              "measurement in progress. Wait for the lock.")
        return 10
    if matches and not live:
        print("\nVERDICT: a registered mutation is applied but NO mutate.py is alive. "
              "That is the signature of a run killed before its `finally` — most "
              "likely `timeout` sending SIGTERM. Restore:\n"
              "  git -C engine/eels checkout -- src/ethereum/forks/")
        return 20
    print("\nVERDICT: the diff matches NO registered mutation. Either a hand edit or "
          "an intentional change. Inspect before restoring; do not assume.")
    return 20


if __name__ == "__main__":
    sys.exit(main())
