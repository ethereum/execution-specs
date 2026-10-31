#!/usr/bin/env python3
"""
Fill the corpus and report the result, safely.

Two gates:

  --only-fork <F>   THE ACCEPTANCE GATE. Every fixture a client would run on
                    fork F must pass today. The signal this corpus gives is a
                    test going green -> red after a future change, which is
                    impossible if it is already red. A test that fails here is
                    rejected: re-scope it with `valid_until` so it runs only
                    where its invariant holds, or re-pin it to what the fork
                    actually does.
  (default)         The whole fork range, for completeness.

Why this wrapper rather than calling `fill` directly: `tools/mutate.py`
perturbs the shared spec tree for the duration of a run, so filling while a
mutation is in flight measures the corpus against a MUTATED engine and the
result looks like an ordinary pass. This takes the same lock and additionally
refuses to run against a tree that differs from git HEAD. Either guard alone
is insufficient -- the lock misses a tree left dirty by a killed run, the git
check misses a run that is legitimately mid-mutation.

Usage:
    python3 tools/verify_corpus.py --only-fork Amsterdam
    python3 tools/verify_corpus.py --wave expansion
"""

import argparse
import fcntl
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _layout import (  # noqa: E402
    INSTRUMENTS, WAVES, fill_bin, lock_path, spec_root, wave_dirs,
)

SUMMARY = re.compile(
    r"(?P<f1>\d+) failed, (?P<p1>\d+) passed"
    r"|(?P<f3>\d+) failed, \d+ deselected"
    r"|(?P<f2>\d+) failed in"
    r"|(?P<p2>\d+) passed in"
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fork", default="Amsterdam", help="--until fork")
    ap.add_argument("--only-fork", default=None,
                    help="fill ONLY this fork (--from X --until X): the gate")
    ap.add_argument("--wave", default="all", choices=("all",) + WAVES)
    args = ap.parse_args()

    root = spec_root()
    lock = open(lock_path(), "w")
    waited = 0
    while True:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except BlockingIOError:
            if not waited:
                print("a mutate.py run holds the lock; waiting so the corpus is "
                      "not measured against a mutated tree...", flush=True)
            time.sleep(5)
            waited += 5
            if waited > 2400:
                raise SystemExit("gave up waiting for the mutation lock")
    try:
        dirty = subprocess.run(["git", "diff", "--stat", "src/ethereum/forks/"],
                               capture_output=True, text=True, cwd=root).stdout.strip()
        if dirty:
            raise SystemExit(
                "REFUSING TO RUN: the fork tree differs from git HEAD:\n" + dirty +
                "\nA mutation run was probably killed mid-edit. Restore with\n"
                "  git checkout -- src/ethereum/forks/\nand re-run."
            )
        total_f = total_p = 0
        for wd in wave_dirs(args.wave):
            out = tempfile.mkdtemp(prefix="corpus-")
            scope = (["--from", args.only_fork, "--until", args.only_fork]
                     if args.only_fork else ["--until", args.fork])
            p = subprocess.run(
                [str(fill_bin()), str(wd), "--ignore", str(wd / INSTRUMENTS)]
                + scope + ["--output", out, "-q", "--tb=no", "-p", "no:cacheprovider"],
                capture_output=True, text=True, cwd=root)
            text = p.stdout + p.stderr
            m = SUMMARY.search(text)
            if not m:
                print(f"{wd.name}: UNTRUSTWORTHY, no pytest summary parsed. Raw tail:")
                print("\n".join(text.strip().splitlines()[-10:]))
                return 2
            g = m.groupdict()
            f = int(g["f1"] or g["f2"] or g["f3"] or 0)
            pa = int(g["p1"] or g["p2"] or 0)
            total_f += f
            total_p += pa
            label = (f"--from {args.only_fork} --until {args.only_fork}"
                     if args.only_fork else f"--until {args.fork}")
            print(f"  {wd.name:<10} ({label}): {m.group(0)}")
            for line in text.splitlines():
                if line.startswith("FAILED"):
                    print("     " + line[7:])
        print(f"  {'TOTAL':<10} {total_p} passed, {total_f} failed")
        return 1 if total_f else 0
    finally:
        fcntl.flock(lock, fcntl.LOCK_UN)
        lock.close()


if __name__ == "__main__":
    sys.exit(main())
