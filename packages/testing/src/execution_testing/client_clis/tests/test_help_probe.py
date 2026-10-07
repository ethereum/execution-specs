"""Test the `--help` probe run when a transition tool is instantiated."""

import sys
from pathlib import Path
from typing import Type

import pytest

from execution_testing.client_clis import (
    BesuTransitionTool,
    GethTransitionTool,
    NimbusTransitionTool,
    TransitionTool,
)

pytestmark = pytest.mark.skipif(
    sys.platform == "win32", reason="the fake binaries are shell scripts"
)

TOOLS = [GethTransitionTool, BesuTransitionTool, NimbusTransitionTool]


def fake_binary(tmp_path: Path, script: str) -> Path:
    """Write an executable shell script standing in for a client binary."""
    binary = tmp_path / "fake-evm"
    binary.write_text(f"#!/bin/sh\n{script}\n")
    binary.chmod(0o755)
    return binary


@pytest.mark.parametrize("tool", TOOLS)
def test_a_failing_help_probe_raises(
    tmp_path: Path, tool: Type[TransitionTool]
) -> None:
    """
    A `--help` probe that exits with an error must not be read as "no
    fork is supported": the stderr of the tool is reported instead.
    """
    binary = fake_binary(tmp_path, "echo 'cannot start' >&2\nexit 3")
    with pytest.raises(Exception, match="non-zero status") as excinfo:
        tool(binary=binary)
    assert "cannot start" in str(excinfo.value)


@pytest.mark.parametrize("tool", TOOLS)
def test_a_successful_help_probe_is_kept(
    tmp_path: Path, tool: Type[TransitionTool]
) -> None:
    """The output of a successful `--help` probe is the help string."""
    binary = fake_binary(tmp_path, "echo 'forks: Prague'")
    assert tool(binary=binary).help_string == "forks: Prague\n"  # type: ignore[attr-defined]
