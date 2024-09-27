"""
Local pytest configuration for filler tests.
"""

import os
import sysconfig

import pytest


@pytest.fixture(autouse=True)
def monkeypatch_path_for_entry_points(monkeypatch):
    """
    Monkeypatch the PATH to add the "bin" directory where entrypoints are installed.

    This would typically be in the venv in which pytest is running these tests and fill,
    which, with uv, is `./.venv/bin`.

    This is required in order for fill to locate the ethereum-spec-evm-resolver
    "binary" (entrypoint) when being executed using pytester.
    """
    bin_dir = sysconfig.get_path("scripts")
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ['PATH']}")
