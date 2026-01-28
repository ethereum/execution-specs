#!/usr/bin/env python3
"""
Fast checks runner with fix hints.

Run static checks with actionable fix hints on failure.
Users run checks via tox; this script provides the implementation with
helpful error messages and GitHub Actions integration.

Usage:
    python scripts/fast_checks.py <check>

Available checks:
    spellcheck, lint, format, typecheck, spec-lint, lockcheck,
    actionlint, markdownlint, changelog
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


@dataclass
class Check:
    """Configuration for a single check."""

    name: str
    fix_hint: str
    verify_cmd: str
    run: Callable[[], int]  # Function that runs the check, returns exit code


def write_github_summary(check: Check, check_key: str, output: str) -> None:
    """Write failure summary to GITHUB_STEP_SUMMARY if in CI."""
    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_file:
        return

    # Truncate output if too long
    max_output = 2000
    if len(output) > max_output:
        output = output[:max_output] + "\n... (truncated)"

    with open(summary_file, "a") as f:
        f.write(f"## ❌ {check.name} failed\n\n")
        f.write("```\n")
        f.write(output)
        f.write("\n```\n\n")
        f.write("### How to fix\n\n")
        f.write("```bash\n")
        f.write(check.fix_hint)
        f.write("\n```\n\n")
        f.write("### How to verify\n\n")
        f.write("Run the tool directly:\n\n")
        f.write("```bash\n")
        f.write(check.verify_cmd)
        f.write("\n```\n\n")
        f.write("Or via tox:\n\n")
        f.write("```bash\n")
        f.write(f"tox -e {check_key}\n")
        f.write("```\n")


def strip_markdown_code_blocks(text: str) -> str:
    """Remove markdown code block markers for terminal output."""
    # Remove ```bash and ``` markers
    return re.sub(r"```\w*\n?", "", text)


def print_fix_hint(check: Check) -> None:
    """Print fix hint to stderr."""
    sep = "=" * 60
    hint = strip_markdown_code_blocks(check.fix_hint).strip()
    print(f"\n{sep}", file=sys.stderr)
    print(f"{check.name} failed:", file=sys.stderr)
    print(sep, file=sys.stderr)
    print(hint, file=sys.stderr)
    print(f"\nVerify fix:\n{check.verify_cmd}", file=sys.stderr)
    print(sep, file=sys.stderr)


def run_command(cmd: list[str]) -> tuple[int, str]:
    """Run command, return exit code and combined output."""
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)

    return result.returncode, result.stdout + result.stderr


def find_project_root() -> Path:
    """Locate the root directory of this project."""
    script_dir = Path(__file__).resolve().parent
    for parent in [script_dir, *script_dir.parents]:
        if (parent / "pyproject.toml").exists() and (parent / ".git").exists():
            return parent

    raise FileNotFoundError(
        "Unable to locate project root! "
        "Looking for a directory with both pyproject.toml and .git."
    )


# Check implementations


def run_codespell() -> int:
    """Run codespell spelling check."""
    code, _ = run_command(["codespell"])
    return code


def run_ruff_check() -> int:
    """Run ruff linting check."""
    code, _ = run_command(["ruff", "check"])
    return code


def run_ruff_format() -> int:
    """Run ruff format check."""
    code, _ = run_command(["ruff", "format", "--check"])
    return code


def run_mypy() -> int:
    """Run mypy type check."""
    code, _ = run_command(["mypy"])
    return code


def run_spec_lint() -> int:
    """Run ethereum-spec-lint check."""
    code, _ = run_command(["ethereum-spec-lint"])
    return code


def run_lockcheck() -> int:
    """Run uv lock --check."""
    code, _ = run_command(["uv", "lock", "--check"])
    return code


def run_actionlint() -> int:
    """Run actionlint on GitHub workflows."""
    code, _ = run_command(
        [
            "actionlint",
            "-pyflakes",
            "pyflakes",
            "-shellcheck",
            "shellcheck -S warning",
        ]
    )
    return code


def run_markdownlint() -> int:
    """Run markdownlint-cli2 on markdown files."""
    if not shutil.which("markdownlint-cli2"):
        print(
            "markdownlint-cli2 not found.\n"
            "This Node.js tool must be installed separately:\n"
            "https://github.com/DavidAnson/markdownlint-cli2#install",
            file=sys.stderr,
        )
        return 1
    code, _ = run_command(["markdownlint-cli2", "./docs/**/*.md", "./*.md"])
    return code


def run_changelog() -> int:
    """Validate changelog formatting (bullet points end with . or :)."""
    project_root = find_project_root()
    changelog_path = project_root / "docs" / "CHANGELOG.md"

    if not changelog_path.exists():
        print(
            f"❌ Changelog file not found: {changelog_path}", file=sys.stderr
        )
        return 1

    try:
        content = changelog_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"❌ Error reading changelog: {e}", file=sys.stderr)
        return 1

    # Find bullet points that don't end with period or colon
    invalid_lines = []
    for line_num, line in enumerate(content.splitlines(), 1):
        if re.match(r"^\s*-\s+", line) and re.search(
            r"[^\.:]$", line.rstrip()
        ):
            invalid_lines.append((line_num, line.strip()))

    if invalid_lines:
        print(
            f"❌ Bullet points in {changelog_path} lack proper punctuation:\n"
        )
        for line_num, line in invalid_lines:
            print(f"Line {line_num}: {line}")
        print("\n💡 All bullet points should end with:")
        print("  - A period (.) for regular entries.")
        print("  - A colon (:) for paragraphs that introduce lists.")
        return 1
    else:
        print("✅ All bullet points have proper punctuation!")
        return 0


# Check registry
CHECKS: dict[str, Check] = {
    "spellcheck": Check(
        name="Spellcheck (via codespell)",
        fix_hint=(
            "If false positive, add to whitelist:\n"
            "```bash\n"
            "uv run whitelist <word>\n"
            "```\n\n"
            "To auto-fix interactively:\n"
            "```bash\n"
            "uv run codespell -i 3\n"
            "```"
        ),
        verify_cmd="uv run codespell",
        run=run_codespell,
    ),
    "lint": Check(
        name="Python lint check (via ruff)",
        fix_hint=(
            "To (potentially) auto-fix:\n```bash\nuv run ruff check --fix\n```"
        ),
        verify_cmd="uv run ruff check",
        run=run_ruff_check,
    ),
    "format": Check(
        name="Python format check (via ruff)",
        fix_hint=("To auto-fix:\n```bash\nuv run ruff format\n```"),
        verify_cmd="uv run ruff format --check",
        run=run_ruff_format,
    ),
    "typecheck": Check(
        name="Python typecheck (via mypy)",
        fix_hint="No autofix. Fix the type errors above manually.",
        verify_cmd="uv run mypy",
        run=run_mypy,
    ),
    "spec-lint": Check(
        name="Ethereum spec lint check",
        fix_hint="No autofix. Fix the spec issues above.",
        verify_cmd="uv run ethereum-spec-lint",
        run=run_spec_lint,
    ),
    "lockcheck": Check(
        name="Lock file check (via uv)",
        fix_hint=(
            "To sync the lock file:\n"
            "```bash\n"
            "uv lock\n"
            "```\n\n"
            "Then commit the updated uv.lock."
        ),
        verify_cmd="uv lock --check",
        run=run_lockcheck,
    ),
    "actionlint": Check(
        name="GitHub Actions workflow check (via actionlint)",
        fix_hint="No autofix. Fix the workflow issues above.",
        verify_cmd="uv run actionlint",
        run=run_actionlint,
    ),
    "markdownlint": Check(
        name="Markdown lint check (via markdownlint-cli2)",
        fix_hint=(
            "Ensure markdownlint-cli2 is installed, then fix the issues above."
        ),
        verify_cmd="markdownlint-cli2 './docs/**/*.md' './*.md'",
        run=run_markdownlint,
    ),
    "changelog": Check(
        name="Changelog validation",
        fix_hint="Ensure bullet points end with `.` or `:`.",
        verify_cmd="python scripts/fast_checks.py changelog",
        run=run_changelog,
    ),
}


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run static checks with fix hints on failure.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example: python scripts/fast_checks.py lint",
    )
    parser.add_argument(
        "check",
        choices=list(CHECKS.keys()),
        help="The check to run",
    )

    args = parser.parse_args()
    check = CHECKS[args.check]

    exit_code = check.run()

    if exit_code != 0:
        print_fix_hint(check)
        # Only show aggregate hint when not running under tox
        if "TOX_ENV_NAME" not in os.environ:
            print(
                "\nRun all fast checks: tox -e fast-checks\n", file=sys.stderr
            )
        # For changelog, we already built the output message
        if args.check != "changelog":
            write_github_summary(check, args.check, "See check output above")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
