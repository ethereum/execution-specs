"""Tests for the `EthereumCLI` base class."""

from pathlib import Path

import pytest

from execution_testing.client_clis.ethereum_cli import (
    CLINotFoundInPathError,
    EthereumCLI,
)


class _MissingCLI(EthereumCLI):
    """A CLI whose binary is guaranteed not to be on `PATH`."""

    default_binary = Path("eels-nonexistent-binary-xyz")


def test_is_installed_accepts_path_binary() -> None:
    """`is_installed` handles a `Path` binary without raising."""
    # `shutil.which` must receive a `str`; a `Path` crashes on some
    # platforms (e.g. Windows under Python 3.11).
    assert _MissingCLI.is_installed() is False


def test_init_missing_path_binary_raises_cli_not_found() -> None:
    """Constructing a CLI with a missing `Path` binary raises cleanly."""
    with pytest.raises(CLINotFoundInPathError):
        _MissingCLI()
