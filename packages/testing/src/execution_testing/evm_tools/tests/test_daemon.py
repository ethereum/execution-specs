"""Test platform handling in the t8n daemon."""

import argparse

import pytest

from execution_testing.evm_tools import daemon
from execution_testing.evm_tools.daemon import Daemon


def test_daemon_run_rejects_windows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`Daemon.run` fails clearly on Windows, which has no Unix sockets."""
    monkeypatch.setattr(daemon.sys, "platform", "win32")
    instance = Daemon(argparse.Namespace(uds="daemon.sock", timeout=0))
    with pytest.raises(RuntimeError, match="Unix domain sockets"):
        instance.run()
