"""
Test the transition tool and subclasses.
"""

import os
import shutil
from pathlib import Path
from typing import Type

import pytest

from evm_transition_tool import (
    EvmOneTransitionTool,
    GethTransitionTool,
    TransitionTool,
    TransitionToolNotFoundInPath,
)


def test_default_tool():
    """
    Tests that the default t8n tool is set.
    """
    assert TransitionTool.default_tool is GethTransitionTool


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
            GethTransitionTool,
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

    def mock_which(self):
        return which_result

    class ReadResult:
        read_result: str

        def __init__(self, read_result):
            self.read_result = read_result

        def read(self):
            return self.read_result

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    def mock_popen(path):
        return ReadResult(read_result)

    # monkeypatch: the transition tools constructor raises an exception if the binary path does
    # not exist
    monkeypatch.setattr(shutil, "which", mock_which)
    monkeypatch.setattr(os, "popen", mock_popen)

    assert isinstance(TransitionTool.from_binary_path(binary_path=binary_path), expected_class)


def test_unknown_binary_path():
    """
    Test that `from_binary_path` raises `UnknownTransitionTool` for unknown
    binary paths.
    """
    with pytest.raises(TransitionToolNotFoundInPath):
        TransitionTool.from_binary_path(binary_path=Path("unknown_binary_path"))
