"""
CLI commands used by tox.ini.

Contains wrappers to the external commands markdownlint-cli2 and pyspelling
(requires aspell) that fail silently if the command is not available. The
aim is to avoid disruption to external contributors.
"""

import os
import shutil
import subprocess
import sys

import click
from pyspelling import __main__ as pyspelling_main  # type: ignore


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
            sys.exit(1)
        else:
            click.echo(
                "*********  Install 'aspell' and 'aspell-en' to enable spellcheck *********"
            )
            sys.exit(0)

    sys.exit(pyspelling_main.main())
