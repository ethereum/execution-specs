#!/usr/bin/env python3
"""
Phase-5 mutation harness (PLAN.md phase 5, SCHEMA.md §4.2).

Perturbs one execution rule in the pinned EELS tree, re-fills every archetype,
and reports which archetypes detect which mutation. A test that survives every
mutation of the rule it claims to depend on protects nothing and is rejected.

Everything is auto-discovered, so parallel contributors never edit a shared
file:
  * archetypes  = every `tests/<name>/` directory containing a `test_*.py`
                  (`tests/tools/` is excluded: its failures are measurements)
  * mutations   = every `tools/mutations/*.json` file, merged

A mutation entry:
    {
      "retention-256": {
        "file":    "amsterdam/vm/gas.py",      # relative to src/ethereum/forks/
        "find":    "return ExecutionGas(gas - (gas // Uint(64)))",
        "replace": "return ExecutionGas(gas - (gas // Uint(256)))",
        "why":     "63/64 retention -> 255/256",
        "fork":    "Amsterdam"                 # optional, default Amsterdam
      }
    }

`find` must occur in the target file or the cell reads TARGET-MISSING -- a
mutation that silently fails to apply would read as "survives", which is the
single most dangerous failure mode here.

Safety properties, each one earned the hard way:
  * a pristine copy of every touched file, restored after EVERY run and
    md5-verified at exit;
  * a run with no parseable pytest summary is retried then reported
    UNTRUSTWORTHY, never read as a pass -- `fill` prints no FAILED lines both
    when all tests pass and when the run dies before executing;
  * the summary regex handles the all-failed form ("9 failed in 0.8s"), which
    carries no "passed" count;
  * unique --output directory and `-p no:cacheprovider` per run, since shared
    output dirs and .pytest_cache contend across concurrent agents and yield
    spurious exit=4.

Usage:  python3 tools/mutate.py              # full matrix
        python3 tools/mutate.py --list       # discovered mutations/archetypes
        python3 tools/mutate.py -k retention # only matching mutations
        python3 tools/mutate.py --archetype gas_monotonicity
        python3 tools/mutate.py --md         # emit a markdown table
"""

import argparse
import fcntl
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
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

SUMMARY = re.compile(
    r"(?P<f1>\d+) failed, (?P<p1>\d+) passed"
    r"|(?P<f3>\d+) failed, \d+ deselected"
    r"|(?P<f2>\d+) failed in"
    r"|(?P<p2>\d+) passed in"
)




def discover_archetypes() -> dict[str, Path]:
    """Every tests/<name>/ holding a test_*.py, except the tools instruments."""
    out = {}
    return _archetypes(_WAVE)


def discover_mutations() -> dict[str, dict]:
    """Merge every tools/mutations/*.json. Later files must not collide."""
    merged: dict[str, dict] = {}
    for f in sorted(mutations_dir().glob("*.json")):
        for name, spec in json.loads(f.read_text()).items():
            if name in merged:
                raise SystemExit(f"duplicate mutation {name!r} in {f.name}")
            spec["_source"] = f.name
            merged[name] = spec
    return merged


def fill(test_dir: Path, outdir: Path, fork: str) -> tuple[str, int, int]:
    """
    Return (verdict, failed, passed).

    verdict is one of:
      pass           every collected test passed
      FAIL           at least one test failed -- the mutation was detected
      n/a            nothing was collected, so this pair is not comparable.
                     Happens whenever a fork-specific mutation meets a
                     fork-restricted archetype (e.g. an Osaka mutation against
                     an EIP8037-only archetype). `fill` prints "no tests ran",
                     which carries no counts; reporting that as
                     "untrustworthy" made every cross-fork mutation look like a
                     broken run.
      untrustworthy  no summary could be parsed after retries -- treat as no
                     result, never as a pass.
    """
    for _ in range(3):
        p = subprocess.run(
            [str(FILL), str(test_dir), "--from", fork, "--until", fork,
             "--output", str(outdir), "-q", "--tb=no", "-p", "no:cacheprovider"],
            capture_output=True, text=True, cwd=EELS,
        )
        text = p.stdout + p.stderr
        if "no tests ran" in text:
            return "n/a", 0, 0
        m = SUMMARY.search(text)
        if m:
            g = m.groupdict()
            if g["f1"]:
                return "FAIL", int(g["f1"]), int(g["p1"])
            if g["f3"]:
                return "FAIL", int(g["f3"]), 0
            if g["f2"]:
                return "FAIL", int(g["f2"]), 0
            return "pass", 0, int(g["p2"])
    return "untrustworthy", -1, -1


_WAVE = "all"
SENTINEL = "# MUTATION"


def assert_pristine(texts: dict) -> None:
    """
    Refuse to run against an already-mutated tree.

    This is the catastrophic case the lock exists to prevent: if a second
    process reads a first process's mutation as its own "pristine" baseline,
    it restores that mutation at exit and the pinned reference
    implementation is left permanently corrupted. Belt and braces.
    """
    for f, t in texts.items():
        if SENTINEL in t:
            raise SystemExit(
                f"REFUSING TO RUN: {f} already contains a mutation marker. "
                "Another mutate.py may be running, or a previous run died "
                "mid-mutation. Restore the file from git before continuing."
            )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("-k", default=None, help="only mutations matching this substring")
    ap.add_argument("--archetype", default=None, help="only this archetype")
    ap.add_argument("--md", action="store_true", help="emit a markdown table")
    ap.add_argument("--wave", default="all",
                    help="all | wave1 | expansion (default: all)")
    args = ap.parse_args()

    global _WAVE
    _WAVE = args.wave
    archetypes = discover_archetypes()
    mutations = discover_mutations()
    if args.archetype:
        archetypes = {k: v for k, v in archetypes.items() if args.archetype in k}
    if args.k:
        mutations = {k: v for k, v in mutations.items() if args.k in k}

    if args.list:
        print(f"archetypes ({len(archetypes)}):")
        for n in archetypes:
            print(f"  {n}")
        print(f"\nmutations ({len(mutations)}):")
        for n, s in mutations.items():
            print(f"  {n:<24} [{s['_source']}] {s.get('why','')}")
        return 0
    if not archetypes or not mutations:
        raise SystemExit("nothing discovered -- check tests/ and tools/mutations/")

    # The harness edits files shared with every other contributor, so only
    # one instance may hold them at a time. Without this, concurrent runs
    # interleave their edits and one restores the other's mutation as
    # "pristine".
    lock_file = lock_path()
    lock_fd = open(lock_file, "w")
    waited = 0.0
    while True:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except BlockingIOError:
            if waited == 0.0:
                print("another mutate.py holds the lock; waiting...", flush=True)
            time.sleep(5)
            waited += 5
            if waited > 1800:
                raise SystemExit("gave up waiting for the mutation lock")

    pristine: dict[Path, str] = {}
    for spec in mutations.values():
        f = FORKS / spec["file"]
        if f not in pristine:
            pristine[f] = f.read_text()
    assert_pristine(pristine)
    md5s = {f: hashlib.md5(t.encode()).hexdigest() for f, t in pristine.items()}
    tmp = Path(tempfile.mkdtemp(prefix="mut-"))

    rows: dict[str, dict[str, str]] = {}
    try:
        rows["(baseline)"] = {}
        for an, ad in archetypes.items():
            v, _f, ps = fill(ad, tmp / f"base-{an}", "Amsterdam")
            rows["(baseline)"][an] = f"pass({ps})" if v == "pass" else v.upper()

        for mn, spec in mutations.items():
            tgt = FORKS / spec["file"]
            src = pristine[tgt]
            if spec["find"] not in src:
                rows[mn] = {an: "TARGET-MISSING" for an in archetypes}
                continue
            tgt.write_text(src.replace(spec["find"], spec["replace"]))
            rows[mn] = {}
            for an, ad in archetypes.items():
                v, f_, _p = fill(ad, tmp / f"{mn}-{an}", spec.get("fork", "Amsterdam"))
                rows[mn][an] = {"pass": "survives",
                                "FAIL": f"DETECTED({f_})",
                                "n/a": "n/a"}.get(v, "UNTRUSTWORTHY")
            tgt.write_text(src)
    finally:
        for f, t in pristine.items():
            f.write_text(t)
        shutil.rmtree(tmp, ignore_errors=True)
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        lock_fd.close()

    for f, want in md5s.items():
        got = hashlib.md5(f.read_text().encode()).hexdigest()
        assert got == want, f"FATAL: {f} not restored"

    names = list(archetypes)
    if args.md:
        print("| mutation | " + " | ".join(names) + " |")
        print("|" + "---|" * (len(names) + 1))
        for mn, c in rows.items():
            print(f"| `{mn}` | " + " | ".join(c.get(n, "?") for n in names) + " |")
    else:
        w = max(len(n) for n in rows) + 1
        cw = max(max((len(n) for n in names), default=8), 16) + 2
        print(f"{'mutation':<{w}}" + "".join(f"{n:<{cw}}" for n in names))
        print("-" * (w + cw * len(names)))
        for mn, c in rows.items():
            print(f"{mn:<{w}}" + "".join(f"{c.get(n,'?'):<{cw}}" for n in names))

    undetected = [m for m, c in rows.items()
                  if m != "(baseline)"
                  and all("DETECTED" not in v for v in c.values())
                  and any(v == "survives" for v in c.values())]
    if undetected:
        print("\nUNDETECTED by every archetype (coverage gaps, or intentionally "
              "within tolerance -- document which):")
        for m in undetected:
            print(f"  {m}: {mutations[m].get('why','')}")
    print("\nall touched reference files restored and md5-verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
