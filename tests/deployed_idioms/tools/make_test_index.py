#!/usr/bin/env python3
"""
Generate docs/TEST-INDEX.md: every corpus test function, the invariant class
(pattern) it tests, and the fork range it applies to.

A generator rather than a hand-written file, so the index cannot drift from the
tests. Fill counts are MEASURED here, under a single acquisition of the shared
mutation lock, so they are never copied from an older run.

Usage:  python3 tools/make_test_index.py            # measure + write
        python3 tools/make_test_index.py --no-fill   # skip measurement
"""

import argparse
import fcntl
import json
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent))
from _layout import (  # noqa: E402
    CORPUS, INSTRUMENTS, archetypes as _archetypes, fill_bin, lock_path, spec_root,
)

ROOT = CORPUS
EELS = spec_root()
FILL = fill_bin()

# Explicit, auditable: archetype directory -> invariant class number.
CLASS_OF = {
    "frozen_budget": 1, "subfloor_budget": 2, "hardcoded_cost_equality": 3,
    "retained_epilogue": 4, "forwarding_prediction": 5, "depth_forwarding": 6,
    "stipend_fallback": 7, "refund_cap": 8, "refund_not_spendable": 9,
    "gas_monotonicity": 10, "halt_vs_revert": 11, "oog_as_signal": 12,
    "block_vs_sender_accounting": 13, "state_gas_clamp": 14,
    "calldata_floor_refund": 15, "reservoir_allocation": 16,
    "intrinsic_cost": 17, "dynamic_cost_prediction": 18,
    "gasleft_sufficiency": 20, "returndata_fidelity": 21,
    "code_presence_identity": 22, "counterfactual_address": 23,
    "transient_storage_lifetime": 24, "eoa_caller_identity": 25,
}
SUMMARY = re.compile(r"(?P<f>\d+) failed, (?P<p1>\d+) passed|(?P<p2>\d+) passed in")


def class_titles():
    """Pull '**N. Title.**' headings out of the class catalogue."""
    txt = (CORPUS / "docs" / "INVARIANT-CLASSES.md").read_text()
    out = {}
    for n, title in re.findall(r"(?m)^\*\*(\d+)\.\s+(.+?)\*\*", txt):
        out[int(n)] = title.rstrip(".").strip()
    return out


def first_doc_line(src, fn):
    """The first sentence of a test function's docstring."""
    m = re.search(r"(?ms)^def " + re.escape(fn) + r"\(.*?\)\s*->\s*None:\s*\n\s*\"\"\"(.*?)\"\"\"", src)
    if not m:
        return ""
    body = " ".join(l.strip() for l in m.group(1).strip().splitlines())
    return re.split(r"(?<=[.])\s", body)[0].strip()


def fork_range(src, fn):
    """valid_from / valid_until decorators attached to this function."""
    blk = src.split(f"def {fn}(")[0]
    chunk = blk.rsplit("\n\n", 1)[-1] if "\n\n" in blk else blk
    f = re.findall(r'valid_from\("(\w+)"\)', chunk)
    u = re.findall(r'valid_until\("(\w+)"\)', chunk)
    if not f and not u:
        m = re.search(r'pytestmark\s*=\s*pytest\.mark\.valid_from\("(\w+)"\)', src)
        if m:
            f = [m.group(1)]
    lo = f[-1] if f else "?"
    hi = u[-1] if u else "Amsterdam"
    return f"{lo} → {hi}"


def measure(dirs):
    """Fill each archetype once, holding the shared lock for the whole sweep."""
    lock = open(lock_path(), "w")
    waited = 0
    while True:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except BlockingIOError:
            if not waited:
                print("waiting for the mutation lock so counts are not measured "
                      "against a mutated tree...", flush=True)
            time.sleep(5); waited += 5
            if waited > 2400:
                raise SystemExit("gave up waiting for the lock")
    try:
        dirty = subprocess.run(["git", "diff", "--stat", "src/ethereum/forks/"],
                               capture_output=True, text=True, cwd=EELS).stdout.strip()
        if dirty:
            raise SystemExit(f"REFUSING: fork tree differs from HEAD:\n{dirty}")
        counts = {}
        for d in dirs:
            out = tempfile.mkdtemp(prefix="idx-")
            p = subprocess.run(
                [str(FILL), str(_archetypes()[d]), "--until", "Amsterdam",
                 "--output", out, "-q", "--tb=no", "-p", "no:cacheprovider"],
                capture_output=True, text=True, cwd=EELS)
            m = SUMMARY.search(p.stdout + p.stderr)
            if not m:
                counts[d] = None
                print(f"  {d}: UNTRUSTWORTHY (no summary parsed)")
            elif m.group("f"):
                counts[d] = -int(m.group("f"))
                print(f"  {d}: {m.group('f')} FAILED")
            else:
                counts[d] = int(m.group("p2"))
        return counts
    finally:
        fcntl.flock(lock, fcntl.LOCK_UN); lock.close()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-fill", action="store_true")
    a = ap.parse_args()

    dirs = sorted(_archetypes().keys(),
                  key=lambda d: CLASS_OF.get(d.split("/")[-1], 99))
    titles = class_titles()
    counts = {} if a.no_fill else measure(dirs)

    total_fn = 0
    lines = []
    for d in dirs:
        cls = CLASS_OF.get(d)
        title = titles.get(cls, "?")
        n = counts.get(d)
        fills = "not measured" if n is None and a.no_fill else (
            f"{n:,} filled" if isinstance(n, int) and n >= 0 else "**FAILING**")
        lines.append(f"\n### #{cls} — {title}\n")
        lines.append(f"`{d}/` · {fills} · [README](../{d}/README.md)\n")
        lines.append("| test function | asserts | forks |")
        lines.append("|---|---|---|")
        for f in sorted(_archetypes()[d].glob("test_*.py")):
            src = f.read_text()
            for fn in re.findall(r"(?m)^def (test_\w+)", src):
                total_fn += 1
                lines.append(f"| `{fn}` | {first_doc_line(src, fn) or '—'} | {fork_range(src, fn)} |")

    measured = sum(v for v in counts.values() if isinstance(v, int) and v >= 0)
    hdr = [
        "# Test index — every corpus test and the pattern it tests",
        "",
        "Generated by `python3 tools/make_test_index.py`. Do not hand-edit: the fill",
        "counts are measured under the shared mutation lock at generation time, and the",
        "`asserts` column is each test's own docstring.",
        "",
        "```text",
        f"invariant classes with an archetype   {len(dirs)}",
        f"test functions                        {total_fn}",
        f"filled fixtures                       {measured:,}" if counts else
        f"filled fixtures                       not measured (--no-fill)",
        "```",
        "",
        "**Why the two numbers differ so much.** A test function is filled once per",
        "parametrisation, per applicable fork, per fixture format (`state_test`,",
        "`blockchain_test_from_state_test`, `blockchain_test_engine_from_state_test`), so",
        f"{total_fn} functions expand to {measured:,} executable fixtures. The function count is",
        "what was written; the fixture count is what a client runs.",
        "",
        "Deliberately absent: **#19** collapses into #1, **#26** is covered by 5,103 lines",
        "in `tests/cancun/eip6780_selfdestruct/`, **#27** is a recorded candidate. See",
        "`docs/INVARIANT-CLASSES.md`. Measurement instruments live in `tests/tools/` and are",
        "not corpus tests — their *failures are the measurement*.",
    ]
    (ROOT / "docs" / "TEST-INDEX.md").write_text("\n".join(hdr + lines) + "\n")
    print(f"\nwrote docs/TEST-INDEX.md — {len(dirs)} classes, {total_fn} test functions, "
          f"{measured:,} filled")
    return 0


if __name__ == "__main__":
    sys.exit(main())
