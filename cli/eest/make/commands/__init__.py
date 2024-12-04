"""
This subpackage holds subcommands for the make command. New subcommands must be created as
modules and exported from this package, then registered under the make command in
`cli.py`.
"""

from .test import test

__all__ = ["test"]
