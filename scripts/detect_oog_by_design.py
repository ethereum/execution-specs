#!/usr/bin/env -S uv run --script
# /// script
# dependencies = []
# ///
r"""
Detect EEST tests that are out-of-gas by design.

Scans EIP-3155 traces emitted by EELS (the default t8n in this repo)
under a `--evm-dump-dir` and reports every transaction step whose
`error` field is exactly "OutOfGasError" -- the Python exception class
name written by EELS at
src/ethereum_spec_tools/evm_tools/t8n/evm_trace/eip3155.py:69-70.

The OOG class is uniformly named `OutOfGasError` across every fork
(src/ethereum/forks/*/vm/exceptions.py:51) and distinct from all
other halt classes, so exact equality on that string gives zero
false positives.

Filtering for "by design" is delegated to `fill`: if a test was
filled successfully and its trace contains `OutOfGasError`, the
post-state matched the author's declaration, so the OOG is by
definition expected. Caveat (by-design under EELS semantics): in
the rare case where an author only asserts generic post-state
(e.g. balance unchanged) and an EELS OOG happens to satisfy it
incidentally, this script will flag the test anyway. Within EELS
semantics this is the strongest signal obtainable without a
separate ground-truth source.

The default JSON output is consumable by `scripts/mark_tests.py`:
it is the wrapped self-describing form

    {"marker": "<name>", "nodeids": ["tests/foo/test_bar.py::test_baz", ...]}

so the two scripts chain directly:

    uv run scripts/detect_oog_by_design.py tests/ported_static \
        --evm-dump-dir ~/.tmp/oog-traces --output oog_report.json
    uv run scripts/mark_tests.py oog_report.json

Trace dump dirs are keyed by the *sanitized* test name
(`ported_static__stRevertTest__revert_prefound_oog__test_...`), which
is lossy: the module's `test_` prefix is stripped
(fixtures/collector.py:114-120) and class names are not encoded. Each
sanitized name is therefore reconstructed into a pytest node ID and
**verified against the source AST** (the `test_` prefix is re-added and
the function is located, including any enclosing class) before being
emitted. Names that cannot be verified are reported as unresolved
rather than guessed -- and `mark_tests.py` independently re-checks every
node ID against the filesystem, so a wrong ID can never silently
mis-mark a test.

This script is stdlib-only on purpose: it does NOT import
`execution_testing`, so it is unaffected by the latent substring-match
bug in that package's `_is_out_of_gas_error` helper, which tests for the
substring "out of gas" and so never matches the EELS class name
"OutOfGasError".
"""

import argparse
import ast
import json
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import IO, Iterator

OOG_ERROR_NAME = "OutOfGasError"
TRACE_FILE_RE = re.compile(r"trace-(\d+)-0x[0-9a-fA-F]+\.jsonl")
DEFAULT_MARKER = "out_of_gas"


@dataclass(frozen=True)
class OogEvent:
    """Single out-of-gas event recorded from a trace step line."""

    test_id: str
    config: str
    block: int
    tx_index: int
    depth: int
    op_name: str
    pc: int
    trace_file: str


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Detect EEST tests that are out-of-gas by design "
            "(top-level or sub-call) by scanning EELS EIP-3155 traces. "
            "Emit mark_tests.py-compatible node IDs."
        ),
    )
    parser.add_argument(
        "test_path",
        nargs="?",
        default="tests/ported_static",
        help=(
            "Test path forwarded to fill and used to scope the trace "
            "scan. Default: tests/ported_static."
        ),
    )
    parser.add_argument(
        "--evm-dump-dir",
        default=str(Path.home() / ".tmp" / "oog-traces"),
        help=(
            "Directory containing per-test trace subdirectories. "
            "Default: ~/.tmp/oog-traces."
        ),
    )
    parser.add_argument(
        "--run-fill",
        action="store_true",
        help=(
            "Run `fill` with --traces before scanning. Without this "
            "flag the script only scans an existing --evm-dump-dir."
        ),
    )
    parser.add_argument(
        "--workers",
        default="auto",
        help="Value passed to fill's -n flag. Default: auto.",
    )
    parser.add_argument(
        "--fork",
        default=None,
        help=(
            "Optional fork override forwarded to fill. When unset, "
            "fill iterates every valid fork per test."
        ),
    )
    parser.add_argument(
        "--marker",
        default=DEFAULT_MARKER,
        help=(
            "Marker name embedded in the JSON output for mark_tests.py. "
            f"Default: {DEFAULT_MARKER!r}."
        ),
    )
    parser.add_argument(
        "--repo-root",
        default=str(Path.cwd()),
        help=(
            "Repository root used to verify node IDs against the source "
            "(node ID module paths are relative to this). Default: cwd."
        ),
    )
    parser.add_argument(
        "--output",
        default="-",
        help=(
            "Output destination. `-` (default) prints a text report to "
            "stdout. A path ending in `.json` writes the mark_tests.py "
            "wrapped form {marker, nodeids}; any other path writes the "
            "text report to that file."
        ),
    )
    parser.add_argument(
        "--events-json",
        default=None,
        help=(
            "Optional path to also write the detailed per-event records "
            "(test_id, config, block, tx, depth, op, pc, trace_file)."
        ),
    )
    parser.add_argument(
        "--top-level-only",
        action="store_true",
        help="Report only events at depth == 1.",
    )
    return parser.parse_args()


def run_fill(
    test_path: str,
    dump_dir: Path,
    workers: str,
    fork: str | None,
) -> None:
    """Invoke `uv run fill ...` with tracing enabled."""
    cmd = [
        "uv",
        "run",
        "fill",
        test_path,
        "--traces",
        "--evm-dump-dir",
        str(dump_dir),
        "-n",
        workers,
    ]
    if fork is not None:
        cmd += ["--fork", fork]
    print(f"+ {' '.join(cmd)}", file=sys.stderr)
    subprocess.run(cmd, check=True)


def parse_relative_path(
    path: Path,
    dump_root: Path,
) -> tuple[str, str, int, int] | None:
    """
    Decode a trace-file path under DUMP into its identifiers.

    Return (test_id, config, block_idx, tx_idx) or None if the path
    does not match the expected layout. The test_id is the sanitized
    function-level name (fixtures/collector.py:146-171).
    """
    try:
        rel = path.relative_to(dump_root)
    except ValueError:
        return None
    parts = rel.parts
    if len(parts) < 4:
        return None
    config, block_str, filename = parts[-3], parts[-2], parts[-1]
    test_id = "/".join(parts[:-3])
    m = TRACE_FILE_RE.match(filename)
    if m is None:
        return None
    try:
        block_idx = int(block_str)
    except ValueError:
        return None
    return test_id, config, block_idx, int(m.group(1))


def scan_trace_file(
    path: Path,
    ids: tuple[str, str, int, int],
) -> Iterator[OogEvent]:
    """
    Yield deduplicated OOG events from a single trace .jsonl file.

    Stream the file line by line. Skip lines lacking `depth` -- the
    trailing FinalTrace summary has no depth (see eip3155.py:54-70)
    and would otherwise double-count top-level OOG. Deduplicate
    within a file by (depth, pc, op_name) to suppress the tracer's
    occasional double-stamping of the same event.
    """
    test_id, config, block, tx_idx = ids
    seen: set[tuple[int, int, str]] = set()
    with path.open("r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "depth" not in obj:
                continue
            if obj.get("error") != OOG_ERROR_NAME:
                continue
            key = (
                int(obj["depth"]),
                int(obj.get("pc", -1)),
                str(obj.get("opName", "")),
            )
            if key in seen:
                continue
            seen.add(key)
            yield OogEvent(
                test_id=test_id,
                config=config,
                block=block,
                tx_index=tx_idx,
                depth=key[0],
                op_name=key[2],
                pc=key[1],
                trace_file=str(path),
            )


def scan(dump_root: Path, top_level_only: bool) -> list[OogEvent]:
    """Walk DUMP_ROOT for trace files and collect all OOG events."""
    events: list[OogEvent] = []
    for path in sorted(dump_root.rglob("trace-*.jsonl")):
        ids = parse_relative_path(path, dump_root)
        if ids is None:
            continue
        for ev in scan_trace_file(path, ids):
            if top_level_only and ev.depth != 1:
                continue
            events.append(ev)
    return events


# ---------------------------------------------------------------------------
# Node-ID resolution
# ---------------------------------------------------------------------------


def _find_function_qualnames(module_path: Path, funcname: str) -> list[str]:
    """
    Return the qualnames of every function named ``funcname`` in a module.

    A top-level ``def funcname`` yields ``"funcname"``; a method inside
    ``class Foo`` yields ``"Foo::funcname"`` (the ``::`` separator that
    mark_tests.py's `_find_function` expects). More than one result means
    the sanitized name is ambiguous (same function name in two classes);
    all are returned so the caller can over-mark rather than guess.
    """
    try:
        tree = ast.parse(module_path.read_text())
    except (OSError, SyntaxError):
        return []
    out: list[str] = []

    def walk(body: list[ast.stmt], prefix: list[str]) -> None:
        for node in body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name == funcname:
                    out.append("::".join(prefix + [node.name]))
            elif isinstance(node, ast.ClassDef):
                walk(node.body, prefix + [node.name])

    walk(tree.body, [])
    return out


def resolve_node_ids(
    test_id: str,
    repo_root: Path,
) -> tuple[list[str], str | None]:
    """
    Reconstruct verified pytest node IDs from a sanitized test_id.

    The sanitized name is ``<reldir>__<stem>__<funcname>`` where reldir
    parts are joined by ``__``, ``stem`` is the module file stem with its
    ``test_`` prefix stripped, and ``funcname`` is the (unstripped) test
    function. The module file is located by re-adding the ``test_``
    prefix (with fallbacks) and confirming it exists; the function is then
    located in its AST. Return ``(node_ids, error)`` -- ``node_ids`` is
    empty and ``error`` set when nothing verifies.
    """
    tokens = test_id.split("__")
    if len(tokens) < 2:
        return [], f"{test_id}: too few path components"
    funcname = tokens[-1]
    stem = tokens[-2]
    reldir_parts = tokens[:-2]
    candidates = (f"test_{stem}.py", f"{stem}.py", f"{stem}Filler.py")
    for fname in candidates:
        module_rel = Path("tests", *reldir_parts, fname)
        abs_path = repo_root / module_rel
        if not abs_path.is_file():
            continue
        qualnames = _find_function_qualnames(abs_path, funcname)
        if qualnames:
            return (
                [f"{module_rel.as_posix()}::{qn}" for qn in qualnames],
                None,
            )
        return [], (
            f"{test_id}: found {module_rel.as_posix()} but no function "
            f"{funcname!r}"
        )
    return [], f"{test_id}: no module file for stem {stem!r}"


def resolve_all(
    events: list[OogEvent],
    repo_root: Path,
) -> tuple[list[str], list[str]]:
    """
    Map distinct OOG test_ids to sorted unique node IDs.

    Return (node_ids, warnings). Warnings list test_ids that could not
    be resolved to a verified node ID.
    """
    node_ids: set[str] = set()
    warnings: list[str] = []
    for test_id in sorted({ev.test_id for ev in events}):
        resolved, err = resolve_node_ids(test_id, repo_root)
        if err:
            warnings.append(err)
        node_ids.update(resolved)
    return sorted(node_ids), warnings


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def emit_text(
    events: list[OogEvent],
    node_ids: list[str],
    warnings: list[str],
    marker: str,
    stream: IO[str],
) -> None:
    """Write a grouped text report to ``stream``."""
    by_test: dict[str, list[OogEvent]] = defaultdict(list)
    for ev in events:
        by_test[ev.test_id].append(ev)
    for test_id in sorted(by_test):
        print(test_id, file=stream)
        for ev in by_test[test_id]:
            print(
                f"  {ev.config}  block={ev.block}  tx={ev.tx_index}  "
                f"depth={ev.depth}  op={ev.op_name}  pc={ev.pc}",
                file=stream,
            )
    total = len(by_test)
    sub_call = sum(
        1 for evs in by_test.values() if any(e.depth > 1 for e in evs)
    )
    top_only = total - sub_call
    print("", file=stream)
    print(f"Marker:                    @pytest.mark.{marker}", file=stream)
    print(f"Total OOG-by-design tests: {total}", file=stream)
    print(f"  Top-level OOG only:      {top_only}", file=stream)
    print(f"  Any sub-call OOG:        {sub_call}", file=stream)
    print(f"Resolved node IDs:         {len(node_ids)}", file=stream)
    if warnings:
        print(f"Unresolved test IDs:       {len(warnings)}", file=stream)
        for w in warnings:
            print(f"  ? {w}", file=stream)


def emit_mark_tests_json(
    node_ids: list[str],
    marker: str,
    stream: IO[str],
) -> None:
    """Write the mark_tests.py wrapped form {marker, nodeids}."""
    json.dump({"marker": marker, "nodeids": node_ids}, stream, indent=2)
    stream.write("\n")


def emit_events_json(events: list[OogEvent], path: Path) -> None:
    """Write the detailed per-event records to ``path``."""
    with path.open("w") as f:
        json.dump([asdict(e) for e in events], f, indent=2)
        f.write("\n")


def main() -> int:
    """Entry point."""
    args = parse_args()
    dump_dir = Path(args.evm_dump_dir).expanduser()
    repo_root = Path(args.repo_root).expanduser()
    if args.run_fill:
        dump_dir.mkdir(parents=True, exist_ok=True)
        run_fill(args.test_path, dump_dir, args.workers, args.fork)
    if not dump_dir.exists():
        print(
            f"error: --evm-dump-dir {dump_dir} does not exist "
            "(use --run-fill to generate traces)",
            file=sys.stderr,
        )
        return 2
    events = scan(dump_dir, args.top_level_only)
    node_ids, warnings = resolve_all(events, repo_root)

    if args.events_json:
        emit_events_json(events, Path(args.events_json).expanduser())

    if args.output == "-":
        emit_text(events, node_ids, warnings, args.marker, sys.stdout)
    else:
        out = Path(args.output).expanduser()
        with out.open("w") as f:
            if out.suffix == ".json":
                emit_mark_tests_json(node_ids, args.marker, f)
            else:
                emit_text(events, node_ids, warnings, args.marker, f)
        # Always surface unresolved IDs on stderr so they are never lost
        # when the primary output is the machine-readable JSON.
        for w in warnings:
            print(f"warning: unresolved {w}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
