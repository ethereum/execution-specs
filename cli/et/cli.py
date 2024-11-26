"""
`et` is the dev CLI for EEST. It provides commands to help developers write tests.
Invoke using `uv run et`.
"""

import click

from cli.et.make.cli import make


@click.group()
def et():
    """
    `et` 👽 is the dev CLI for EEST. It provides commands to help developers write tests.
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
et.add_command(make)
