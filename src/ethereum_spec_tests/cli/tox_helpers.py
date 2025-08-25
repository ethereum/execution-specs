"""
CLI commands used by tox.ini.

Contains wrappers to the external commands markdownlint-cli2 and pyspelling
(requires aspell) that fail silently if the command is not available. The
aim is to avoid disruption to external contributors.
"""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import click
from pyspelling import __main__ as pyspelling_main  # type: ignore
from rich.console import Console


def write_github_summary(title: str, tox_env: str, error_message: str, fix_commands: list[str]):
    """
    Write a summary to GitHub Actions when a check fails.

    Args:
        title: The title of the check that failed
        tox_env: The tox environment name (e.g., "spellcheck")
        error_message: Description of what went wrong
        fix_commands: List of commands to fix the issue locally

    """
    if not os.environ.get("GITHUB_ACTIONS"):
        return

    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_file:
        return

    with open(summary_file, "a") as f:
        f.write(f"## ❌ {title}\n\n")
        f.write(f"{error_message}\n\n")
        f.write("### To reproduce this check locally:\n")
        f.write("```bash\n")
        f.write(f"uvx --with=tox-uv tox -e {tox_env}\n")
        f.write("```\n\n")

        if fix_commands:
            f.write("### To verify and fix the issues:\n")
            f.write("```bash\n")
            for cmd in fix_commands:
                f.write(f"{cmd}\n")
            f.write("```\n")


@click.command(
    context_settings={
        "ignore_unknown_options": True,
        "allow_extra_args": True,
    }
)
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
def markdownlint(args):
    """
    Lint the markdown in ./README.md and ./docs/ using the external command
    markdownlint-cli2.

    Silently fail if markdownlint-cli2 is not installed.

    Allows argument forwarding to markdownlint-cli2.
    """
    markdownlint = shutil.which("markdownlint-cli2")
    if not markdownlint:
        # Note: There's an additional step in test.yaml to run markdownlint-cli2 in GitHub Actions
        click.echo("********* Install 'markdownlint-cli2' to enable markdown linting *********")
        sys.exit(0)

    if len(args) == 0:
        args = ["./docs/**/*.md", "./README.md"]

    command = ["node", markdownlint] + list(args)
    sys.exit(subprocess.run(command).returncode)


@click.command()
def pyspelling():
    """
    Spellcheck the markdown in ./README.md and ./docs/ using the pyspelling
    package.

    Silently fails if aspell is not installed (required by pyspelling).

    Command-line arguments are not forwarded to pyspelling.
    """
    if not shutil.which("aspell"):
        click.echo("aspell not installed, skipping spellcheck.")
        if os.environ.get("GITHUB_ACTIONS"):
            write_github_summary(
                title="Pyspelling Check Failed",
                tox_env="spellcheck",
                error_message=(
                    "aspell is not installed. This tool is required for spell checking "
                    " documentation."
                ),
                fix_commands=[
                    "# Install aspell on Ubuntu/Debian",
                    "sudo apt-get install aspell aspell-en",
                    "",
                    "# Install aspell on macOS",
                    "brew install aspell",
                ],
            )
            sys.exit(1)
        else:
            click.echo(
                "*********  Install 'aspell' and 'aspell-en' to enable spellcheck *********"
            )
            sys.exit(0)

    result = pyspelling_main.main()
    if result != 0:
        write_github_summary(
            title="Pyspelling Check Failed",
            tox_env="spellcheck",
            error_message="Pyspelling found spelling errors in the documentation.",
            fix_commands=[
                "# Check the pyspelling configuration",
                "cat .pyspelling.yml",
                "",
                "# Review and fix spelling errors manually",
                "# Pyspelling doesn't have an auto-fix option",
            ],
        )
    sys.exit(result)


@click.command()
def codespell():
    """
    Run codespell on the codebase and provide helpful error messages.

    Checks spelling in .github/, src/, tests/, and docs/ directories.
    """
    console = Console()

    # Define the paths to check
    paths_to_check = ["*.md", "*.ini", ".github/", "src/", "tests/", "docs/"]
    paths_str = " ".join(paths_to_check)

    # Run codespell
    result = subprocess.run(
        ["codespell"] + paths_to_check,
        capture_output=True,
        text=True,
    )

    # Print the output
    if result.stdout:
        console.print(result.stdout)
    if result.stderr:
        console.print(result.stderr, style="red")

    # If there were spelling errors, show a helpful message
    if result.returncode != 0:
        console.print("\n[bold red]❌ Spellcheck Failed[/bold red]")
        console.print(
            "[yellow]Please review the errors above. For single-suggestion fixes, you can "
            "automatically apply them with:[/yellow]"
        )
        console.print(f"[cyan]uv run codespell {paths_str} --write-changes[/cyan]\n")

        # Write to GitHub Actions summary
        write_github_summary(
            title="Spellcheck Failed",
            tox_env="spellcheck",
            error_message="Codespell found spelling errors in the code.",
            fix_commands=[
                "# Ensure codespell is installed (part of docs extras)",
                "uv sync --all-extras",
                "",
                "# Check for spelling errors",
                f"uv run codespell {paths_str}",
                "",
                "# Automatically fix single-suggestion errors",
                f"uv run codespell {paths_str} --write-changes",
            ],
        )

        sys.exit(1)

    sys.exit(0)
    sys.exit(pyspelling_main.main())


@click.command()
def validate_changelog():
    """
    Validate changelog formatting to ensure bullet points end with proper punctuation.

    Checks that all bullet points (including nested ones) end with either:
    - A period (.) for regular entries
    - A colon (:) for section headers that introduce lists
    """
    changelog_path = Path("docs/CHANGELOG.md")

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
        if re.match(r"^\s*-\s+", line) and re.search(r"[^\.:]$", line.rstrip()):
            invalid_lines.append((line_num, line.strip()))

    if invalid_lines:
        click.echo(f"❌ Found bullet points in {changelog_path} without proper punctuation:")
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
