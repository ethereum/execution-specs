"""
`eest` is a CLI tool that helps with routine tasks.
Invoke using `uv run eest`.
"""

import sys

import click

from .commands import clean, info
from .make.cli import make


def ensure_utf8_output() -> None:
    """
    Reconfigure the standard streams to UTF-8 so output cannot crash.

    The `eest` commands print Unicode characters (box drawing, emoji)
    that a legacy console code page such as Windows `cp1252` cannot
    encode, otherwise raising `UnicodeEncodeError` mid-command. Streams
    that do not support reconfiguration (for example when output is
    captured in tests) are left untouched.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8")
        except (OSError, ValueError):
            pass


@click.group(
    context_settings={
        "help_option_names": ["-h", "--help"],
        "max_content_width": 120,
    }
)
def eest() -> None:
    """`eest` is a CLI tool that helps with routine tasks."""
    ensure_utf8_output()


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
eest.add_command(info)
