"""
The `make` CLI streamlines the process of scaffolding tasks, such as generating new test files,
enabling developers to concentrate on the core aspects of specification testing.


The module calls the appropriate function for the subcommand. If an invalid subcommand
is chosen, it throws an error and shows a list of valid subcommands. If no subcommand
is present, it shows a list of valid subcommands to choose from.
"""

import click

from .commands import test


@click.group()
def make():
    """
    Generate project files from the CLI.
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
make.add_command(test)
