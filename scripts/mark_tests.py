#!/usr/bin/env python3
"""
Add a ``@pytest.mark.<name>`` decorator to test functions listed in a
JSON file. Idempotent — re-running leaves already-marked tests alone.

INPUT FORMATS
-------------

The input JSON may be in any of these shapes. Parametrize brackets
(``[…]``) are stripped from node IDs since markers attach to the
function, not to individual parameter cases.

1. **Bare mapping** (the format emitted by ``--detect-gas-checks``)::

       {
         "tests/foo/test_bar.py::test_baz[case_id]": [ ... hits ... ],
         "tests/foo/test_bar.py::TestClass::test_method[other]": [ ... ]
       }

   Marker name must be supplied via ``--marker``.

2. **Bare list of node IDs**::

       [
         "tests/foo/test_bar.py::test_baz",
         "tests/foo/test_bar.py::TestClass::test_method"
       ]

   Marker name must be supplied via ``--marker``.

3. **Wrapped (self-describing)** — the JSON declares which marker it
   maps to, so producers can ship a single file without remembering to
   pass ``--marker``::

       {
         "marker": "gas_check",
         "tests": {
           "tests/foo/test_bar.py::test_baz[case]": [ ... ]
         }
       }

   or::

       {
         "marker": "slow",
         "nodeids": [
           "tests/foo/test_bar.py::test_baz",
           "tests/foo/test_bar.py::test_qux"
         ]
       }

   ``--marker`` on the command line overrides the value in the file.

USAGE
-----

::

    uv run python scripts/mark_tests.py REPORT.json --marker gas_check
    uv run python scripts/mark_tests.py --dry-run wrapped_report.json
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple

DEFAULT_MARKER = "gas_check"


# ---------------------------------------------------------------------------
# Input parsing
# ---------------------------------------------------------------------------


def _coerce_nodeids(raw: object) -> Iterable[str]:
    if isinstance(raw, dict):
        return raw.keys()
    if isinstance(raw, list):
        return [n for n in raw if isinstance(n, str)]
    raise ValueError(
        f"expected dict or list of node IDs, got {type(raw).__name__}"
    )


def load_input(
    payload: object, cli_marker: str | None
) -> Tuple[str, Dict[str, Set[str]]]:
    """
    Resolve the marker name and the ``{module: {qualname, ...}}`` map.

    Format detection:
      - ``dict`` with a ``"marker"`` key → wrapped form; nodeids come
        from ``"tests"`` or ``"nodeids"``.
      - any other ``dict`` → bare mapping (keys are nodeids).
      - ``list`` → bare list of nodeids.
    """
    marker_in_file: str | None = None
    if isinstance(payload, dict) and "marker" in payload:
        marker_in_file = payload["marker"]
        body = payload.get("tests")
        if body is None:
            body = payload.get("nodeids")
        if body is None:
            raise ValueError(
                "wrapped JSON must have a 'tests' or 'nodeids' field"
            )
        nodeids = list(_coerce_nodeids(body))
    else:
        nodeids = list(_coerce_nodeids(payload))

    marker = cli_marker or marker_in_file or DEFAULT_MARKER
    if not marker.isidentifier():
        raise ValueError(
            f"marker name {marker!r} is not a valid Python identifier"
        )

    targets: Dict[str, Set[str]] = defaultdict(set)
    for nodeid in nodeids:
        module, sep, rest = nodeid.partition("::")
        if not sep:
            continue
        bracket = rest.find("[")
        if bracket != -1:
            rest = rest[:bracket]
        targets[module].add(rest)

    return marker, targets


# ---------------------------------------------------------------------------
# AST navigation
# ---------------------------------------------------------------------------


def _is_marker(node: ast.AST, name: str) -> bool:
    """Match ``@pytest.mark.NAME`` and ``@pytest.mark.NAME(...)``."""
    if isinstance(node, ast.Call):
        node = node.func
    if not isinstance(node, ast.Attribute) or node.attr != name:
        return False
    mark = node.value
    if not isinstance(mark, ast.Attribute) or mark.attr != "mark":
        return False
    pytest_node = mark.value
    return isinstance(pytest_node, ast.Name) and pytest_node.id == "pytest"


def _has_marker(
    func: ast.FunctionDef | ast.AsyncFunctionDef, name: str
) -> bool:
    return any(_is_marker(d, name) for d in func.decorator_list)


def _find_function(
    body: List[ast.stmt], qualname: str
) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    """Resolve ``Class::Method::…`` (or just ``test_foo``) inside ``body``."""
    parts = qualname.split("::")
    current_body: List[ast.stmt] = body
    for i, part in enumerate(parts):
        last = i == len(parts) - 1
        for node in current_body:
            if (
                last
                and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name == part
            ):
                return node
            if (
                not last
                and isinstance(node, ast.ClassDef)
                and node.name == part
            ):
                current_body = node.body
                break
        else:
            return None
    return None


# ---------------------------------------------------------------------------
# Source modification
# ---------------------------------------------------------------------------


def _decorator_insert_line(
    func: ast.FunctionDef | ast.AsyncFunctionDef,
) -> int:
    """
    1-based line where a new decorator should be inserted.

    Above any existing decorators; above the ``def`` if none.
    """
    if func.decorator_list:
        return func.decorator_list[0].lineno
    return func.lineno


def _line_indent(line: str) -> str:
    return line[: len(line) - len(line.lstrip())]


def insert_markers(
    source: str, marker: str, targets: Set[str]
) -> Tuple[str, List[str], List[str]]:
    """
    Return ``(new_source, added_qualnames, missing_qualnames)``.

    Targets already carrying the marker are silently skipped.
    """
    tree = ast.parse(source)
    found: List[Tuple[str, ast.FunctionDef | ast.AsyncFunctionDef, bool]] = []
    missing: List[str] = []

    for qn in sorted(targets):
        func = _find_function(tree.body, qn)
        if func is None:
            missing.append(qn)
            continue
        found.append((qn, func, _has_marker(func, marker)))

    to_add = [(qn, func) for qn, func, present in found if not present]
    if not to_add:
        return source, [], missing

    lines = source.splitlines(keepends=True)
    # Insert in descending order so earlier insertions don't shift later
    # line numbers.
    to_add.sort(key=lambda pair: _decorator_insert_line(pair[1]), reverse=True)
    added: List[str] = []
    decorator_line = f"@pytest.mark.{marker}\n"
    for qn, func in to_add:
        idx = _decorator_insert_line(func) - 1  # 1-based -> 0-based
        if idx < 0 or idx >= len(lines):
            missing.append(qn)
            continue
        indent = _line_indent(lines[idx])
        lines.insert(idx, indent + decorator_line)
        added.append(qn)

    return "".join(lines), added, missing


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def main(argv: List[str] | None = None) -> int:
    """Parse command-line arguments and mark the listed test functions."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "report",
        type=Path,
        help="Path to JSON file listing node IDs (see module docstring "
        "for accepted shapes).",
    )
    parser.add_argument(
        "--marker",
        default=None,
        help=(
            "Pytest marker to apply. Overrides any 'marker' field in "
            f"the JSON. Defaults to {DEFAULT_MARKER!r} when neither is "
            "set."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would change without writing any file.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help=(
            "Repository root; node ID module paths are resolved against "
            "this directory (default: current directory)."
        ),
    )
    args = parser.parse_args(argv)

    try:
        payload = json.loads(args.report.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: failed to read {args.report}: {exc}", file=sys.stderr)
        return 2

    try:
        marker, targets_by_module = load_input(payload, args.marker)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(f"Marker: @pytest.mark.{marker}")

    total_added = 0
    total_already = 0
    total_missing = 0
    files_changed = 0
    files_skipped: List[Path] = []

    for module_rel, qualnames in sorted(targets_by_module.items()):
        module_path = args.root / module_rel
        if not module_path.is_file():
            files_skipped.append(module_path)
            total_missing += len(qualnames)
            continue
        try:
            original = module_path.read_text()
        except OSError as exc:
            print(f"  skip {module_rel}: {exc}", file=sys.stderr)
            continue

        try:
            new_source, added, missing = insert_markers(
                original, marker, qualnames
            )
        except SyntaxError as exc:
            print(
                f"  skip {module_rel}: syntax error at line "
                f"{exc.lineno}: {exc.msg}",
                file=sys.stderr,
            )
            continue

        already = len(qualnames) - len(added) - len(missing)
        total_added += len(added)
        total_already += already
        total_missing += len(missing)

        if added:
            files_changed += 1
            verb = "would mark" if args.dry_run else "marked"
            print(f"  {module_rel}: {verb} {len(added)}")
            for qn in added:
                print(f"    + {qn}")
            if not args.dry_run:
                module_path.write_text(new_source)
        elif missing:
            print(f"  {module_rel}: nothing to add")
        for qn in missing:
            print(f"    ? {qn}  (not found)")

    total_targets = sum(len(s) for s in targets_by_module.values())
    print()
    print(f"Targets in input  : {total_targets}")
    print(f"Markers added     : {total_added}")
    print(f"Already present   : {total_already}")
    print(f"Could not locate  : {total_missing}")
    print(f"Files changed     : {files_changed}")
    if files_skipped:
        print(f"Files skipped     : {len(files_skipped)} (not on disk)")
    if args.dry_run:
        print("(dry run — no files modified)")
    return 0 if total_missing == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
