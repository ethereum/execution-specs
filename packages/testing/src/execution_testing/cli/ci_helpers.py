"""
CLI helper commands for CI static checks.

Contains wrappers to markdownlint-cli2 and changelog validation that fail
silently if external tools are not available, to avoid disruption to
external contributors.
"""

import re
import shutil
import subprocess
import sys
from pathlib import Path

import click
import semver


def find_project_root() -> Path:
    """Locate the root directory of this project."""
    # Search upwards from file location
    script_dir = Path(__file__).resolve().parent
    for parent in [script_dir, *script_dir.parents]:
        if (parent / "pyproject.toml").exists() and (parent / ".git").exists():
            return parent

    raise FileNotFoundError(
        "Unable to locate project root! "
        "Looking for a directory with both pyproject.toml and .git."
    )


@click.command(
    context_settings={
        "ignore_unknown_options": True,
        "allow_extra_args": True,
    }
)
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
def markdownlint(args: tuple[str, ...]) -> None:
    """
    Lint the markdown in ./README.md and ./docs/ using the external command
    markdownlint-cli2.

    Silently fail if markdownlint-cli2 is not installed.

    Allows argument forwarding to markdownlint-cli2.
    """
    expected_version = "0.20.0"
    markdownlint = shutil.which("markdownlint-cli2")
    if not markdownlint:
        # Note: There's an additional step in test.yaml to run markdownlint-
        # cli2 in GitHub Actions
        click.echo(
            "********* Install 'markdownlint-cli2' to enable markdown linting"
            " *********\n"
            "```\n"
            f"sudo npm install -g markdownlint-cli2@{expected_version}\n"
            "```"
        )
        sys.exit(0)

    result = subprocess.run(
        [markdownlint, "--version"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        version_match = re.search(r"v?(\d+\.\d+\.\d+)", result.stdout)
        installed_version = version_match.group(1) if version_match else None
        if installed_version:
            installed = semver.Version.parse(installed_version)
            expected = semver.Version.parse(expected_version)
            minor_mismatch = (installed.major, installed.minor) != (
                expected.major,
                expected.minor,
            )
        else:
            minor_mismatch = False
        if minor_mismatch:
            lines = [
                f"WARNING: markdownlint-cli2 {installed_version} "
                f"installed, CI uses {expected_version}",
                "",
                "Lint results may differ from CI.",
                f"  npm install -g markdownlint-cli2@{expected_version}",
            ]
            width = max(len(line) for line in lines) + 4
            border = "*" * width
            box = "\n".join(f"* {line:<{width - 4}} *" for line in lines)
            click.echo(f"\n{border}\n{box}\n{border}\n")

    args_list: list[str] = (
        list(args) if len(args) > 0 else ["./docs/**/*.md", "./*.md"]
    )

    command = ["node", markdownlint] + args_list
    sys.exit(subprocess.run(command).returncode)


@click.command()
def validate_changelog() -> None:
    """
    Validate changelog formatting to ensure bullet points end with proper
    punctuation.

    Check that all bullet points (including nested ones) end with either:
    - A period (.) for regular entries
    - A colon (:) for section headers that introduce lists
    """
    project_root = find_project_root()
    changelog_path = Path(project_root / "docs/CHANGELOG.md")

    if not changelog_path.exists():
        click.echo(f"❌ Changelog file not found: {changelog_path}")
        sys.exit(1)

    try:
        with open(changelog_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        click.echo(f"❌ Error reading changelog: {e}.")
        sys.exit(1)

    # Find bullet points that don't end with period or colon
    invalid_lines = []
    for line_num, line in enumerate(content.splitlines(), 1):
        if re.match(r"^\s*-\s+", line) and re.search(
            r"[^\.:]$", line.rstrip()
        ):
            invalid_lines.append((line_num, line.strip()))

    if invalid_lines:
        click.echo(
            f"❌ Found bullet points in {changelog_path} without proper "
            "punctuation:"
        )
        click.echo()
        for line_num, line in invalid_lines:
            click.echo(f"Line {line_num}: {line}")
        click.echo()
        click.echo("💡 All bullet points should end with:")
        click.echo("  - A period (.) for regular entries.")
        click.echo("  - A colon (:) for paragraphs that introduce lists.")
        sys.exit(1)
    else:
        click.echo("✅ All bullet points have proper punctuation!")
        sys.exit(0)
