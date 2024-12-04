"""
`eest` is a CLI tool that helps with routine tasks.
Invoke using `uv run eest`.
"""

import click

from cli.eest.commands import clean
from cli.eest.make.cli import make


@click.group(context_settings=dict(help_option_names=["-h", "--help"], max_content_width=120))
def eest():
    """
    `eest` is a CLI tool that helps with routine tasks.
    """
    pass


"""
################################
||                            ||
||    Command Registration    ||
||                            ||
################################

Register nested commands here. For more information, see Click documentation:
https://click.palletsprojects.com/en/8.0.x/commands/#nested-handling-and-contexts
"""
eest.add_command(make)
eest.add_command(clean)
