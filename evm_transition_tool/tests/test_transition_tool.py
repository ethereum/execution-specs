"""
Test the transition tool and subclasses.
"""

import shutil
import subprocess
from pathlib import Path
from typing import Type

import pytest

from evm_transition_tool import (
    EvmOneTransitionTool,
    ExecutionSpecsTransitionTool,
    GethTransitionTool,
    NimbusTransitionTool,
    TransitionTool,
    TransitionToolNotFoundInPath,
)


def test_default_tool():
    """
    Tests that the default t8n tool is set.
    """
    assert TransitionTool.default_tool is ExecutionSpecsTransitionTool


@pytest.mark.parametrize(
    "binary_path,which_result,read_result,expected_class",
    [
        (
            Path("evm"),
            "evm",
            "evm version 1.12.1-unstable-c7b099b2-20230627",
            GethTransitionTool,
        ),
        (
            Path("evmone-t8n"),
            "evmone-t8n",
            "evmone-t8n 0.11.0-dev+commit.93997506",
            EvmOneTransitionTool,
        ),
        (
            None,
            "evm",
            "evm version 1.12.1-unstable-c7b099b2-20230627",
            ExecutionSpecsTransitionTool,
        ),
        (
            Path("t8n"),
            "t8n",
            "Nimbus-t8n 0.1.2\n\x1b[0m",
            NimbusTransitionTool,
        ),
    ],
)
def test_from_binary(
    monkeypatch,
    binary_path: Path | None,
    which_result: str,
    read_result: str,
    expected_class: Type[TransitionTool],
):
    """
    Test that `from_binary` instantiates the correct subclass.
    """

    class MockCompletedProcess:
        def __init__(self, stdout):
            self.stdout = stdout
            self.stderr = None
            self.returncode = 0

    def mock_which(self):
        return which_result

    def mock_run(args, **kwargs):
        return MockCompletedProcess(read_result.encode())

    monkeypatch.setattr(shutil, "which", mock_which)
    monkeypatch.setattr(subprocess, "run", mock_run)

    assert isinstance(TransitionTool.from_binary_path(binary_path=binary_path), expected_class)


def test_unknown_binary_path():
    """
    Test that `from_binary_path` raises `UnknownTransitionTool` for unknown
    binary paths.
    """
    with pytest.raises(TransitionToolNotFoundInPath):
        TransitionTool.from_binary_path(binary_path=Path("unknown_binary_path"))
