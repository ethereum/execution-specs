"""CLI entry point: load -> analyze -> render -> format -> write."""

from __future__ import annotations

import argparse
import ast
import logging
import os
import re
import subprocess
import sys
from pathlib import Path

from .analyzer import analyze, load_filler
from .render import render_test

logger = logging.getLogger(__name__)


def post_format(source: str) -> str:
    """Format generated Python source with ruff."""
    # ruff format
    try:
        result = subprocess.run(
            ["ruff", "format", "--stdin-filename", "test.py", "-"],
            input=source,
            capture_output=True,
            text=True,
            env={**os.environ, "RUST_MIN_STACK": "8388608"},
        )
        if result.returncode == 0:
            source = result.stdout
    except FileNotFoundError:
        pass  # ruff not installed

    # ruff check --fix (accept output even with remaining unfixable issues)
    try:
        result = subprocess.run(
            [
                "ruff",
                "check",
                "--fix",
                "--stdin-filename",
                "test.py",
                "-",
            ],
            input=source,
            capture_output=True,
            text=True,
            env={**os.environ, "RUST_MIN_STACK": "8388608"},
        )
        if result.stdout:
            source = result.stdout
    except FileNotFoundError:
        pass

    # Add # noqa for generated code issues that can't be auto-fixed.
    # Track docstring boundaries to avoid adding noqa inside docstrings.
    lines = source.split("\n")
    fixed_lines: list[str] = []
    in_docstring = False
    for line in lines:
        stripped = line.rstrip()
        if '"""' in stripped:
            count = stripped.count('"""')
            if count == 1:
                in_docstring = not in_docstring
            # count == 2 means open+close on same line, no state change
        if in_docstring:
            fixed_lines.append(line)
            continue
        noqa_parts: list[str] = []
        if len(stripped) > 79:
            noqa_parts.append("E501")
        # F841: deploy_contract assigns to variables used in expect dicts
        if "= pre.deploy_contract(" in stripped:
            noqa_parts.append("F841")
        if noqa_parts and "# noqa" not in stripped:
            codes = ", ".join(noqa_parts)
            fixed_lines.append(f"{stripped}  # noqa: {codes}")
        else:
            fixed_lines.append(line)
    source = "\n".join(fixed_lines)

    return source


def _filler_name_to_filename(stem: str) -> str:
    """Convert filler stem to output filename."""
    name = re.sub(r"Filler$", "", stem)
    # camel_to_snake
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", s)
    result = s.lower()
    result = result.replace("+", "_plus_")
    result = result.replace("-", "_minus_")
    result = re.sub(r"[^a-z0-9_]", "_", result)
    result = re.sub(r"_+", "_", result)
    return "test_" + result.strip("_") + ".py"


def discover_fillers(fillers_dir: Path) -> list[Path]:
    """Walk a directory for *Filler.yml and *Filler.json files."""
    found: list[Path] = []
    for root, _dirs, files in os.walk(fillers_dir):
        for f in sorted(files):
            if f.endswith("Filler.yml") or f.endswith("Filler.json"):
                found.append(Path(root) / f)
    return found


def process_single_filler(
    filler_path: Path,
    fillers_base: Path,
    output_dir: Path,
    dry_run: bool = False,
) -> str:
    """
    Process one filler file.

    Return "ok", "fail", or "warn".
    """
    try:
        # Relative path for the generated test's ported_from marker
        try:
            rel_path = filler_path.relative_to(fillers_base.parent)
        except ValueError:
            rel_path = filler_path

        # Load
        test_name, model = load_filler(filler_path)

        # Analyze
        ir = analyze(test_name, model, rel_path)

        # Render
        source = render_test(ir)

        # Verify syntax
        try:
            ast.parse(source)
        except SyntaxError as e:
            logger.error(
                "Syntax error in generated code for %s: %s",
                filler_path,
                e,
            )
            return "fail"

        # Format
        source = post_format(source)

        if dry_run:
            print(f"[DRY-RUN] {filler_path} -> {ir.test_name}")
            return "ok"

        # Write
        category = rel_path.parts[-2] if len(rel_path.parts) >= 2 else ""
        out_subdir = output_dir / category
        out_subdir.mkdir(parents=True, exist_ok=True)

        # Write __init__.py if needed
        init_file = out_subdir / "__init__.py"
        if not init_file.exists():
            init_file.write_text(
                f'"""Ported static tests: {category}."""  # noqa: N999\n'
            )

        out_file = out_subdir / _filler_name_to_filename(filler_path.stem)
        out_file.write_text(source)
        logger.info("OK: %s -> %s", filler_path.name, out_file)
        return "ok"

    except Exception as e:
        logger.error("FAIL: %s: %s", filler_path, e)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Traceback:", exc_info=True)
        return "fail"


def main() -> None:
    """Run the filler-to-python pipeline."""
    parser = argparse.ArgumentParser(
        description="Convert static filler YAML/JSON to Python test files."
    )
    parser.add_argument(
        "--fillers",
        type=Path,
        required=True,
        help="Directory containing *Filler.yml/*.json files.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Output directory for generated .py test files.",
    )
    parser.add_argument(
        "--single",
        type=Path,
        default=None,
        help="Process a single filler file instead of the whole directory.",
    )
    parser.add_argument(
        "--filter",
        type=Path,
        default=None,
        help="Only convert fillers listed in this file (one path per line).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and analyze but don't write files.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging.",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    if args.single:
        filler_paths = [args.single]
    else:
        if not args.fillers.is_dir():
            logger.error("--fillers must be a directory: %s", args.fillers)
            sys.exit(1)
        filler_paths = discover_fillers(args.fillers)

    # Apply filter
    if args.filter:
        allowed = set()
        for line in args.filter.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                allowed.add(line)
        filler_paths = [
            p for p in filler_paths if str(p) in allowed or p.name in allowed
        ]

    if not filler_paths:
        logger.warning("No filler files found.")
        sys.exit(0)

    logger.info("Processing %d filler(s)...", len(filler_paths))

    counts = {"ok": 0, "fail": 0, "warn": 0}
    for filler_path in filler_paths:
        status = process_single_filler(
            filler_path,
            args.fillers,
            args.output,
            dry_run=args.dry_run,
        )
        counts[status] += 1

    # Summary
    total = sum(counts.values())
    print(
        f"\nDone: {counts['ok']}/{total} OK, "
        f"{counts['fail']} failed, {counts['warn']} warnings"
    )
    if counts["fail"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
