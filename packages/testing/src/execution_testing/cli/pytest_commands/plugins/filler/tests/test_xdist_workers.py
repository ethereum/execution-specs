"""Tests for the xdist worker count that `fill -n auto` uses."""

import sys
from types import SimpleNamespace
from typing import cast

import pytest

from .. import filler
from ..filler import auto_worker_count

GIB = 1024**3


@pytest.mark.parametrize(
    "cores,total_memory,implementation,expected",
    [
        pytest.param(16, 32 * GIB, "cpython", 16, id="cpython-16-cores"),
        pytest.param(32, 32 * GIB, "cpython", 17, id="cpython-32-threads"),
        pytest.param(16, 32 * GIB, "pypy", 8, id="pypy-16-cores"),
        pytest.param(4, int(15.6 * GIB), "pypy", 3, id="pypy-4-vcpus"),
        pytest.param(8, GIB, "cpython", 1, id="at-least-one-worker"),
        pytest.param(8, None, "cpython", 8, id="memory-unknown"),
        pytest.param(4, 64 * GIB, "graalpy", 4, id="other-implementation"),
    ],
)
def test_auto_worker_count(
    cores: int, total_memory: int | None, implementation: str, expected: int
) -> None:
    """Use one worker per core, capped by the memory budget."""
    assert auto_worker_count(cores, total_memory, implementation) == expected


def _config(numprocesses: str) -> pytest.Config:
    """Build the part of a config that the hook reads."""
    option = SimpleNamespace(numprocesses=numprocesses)
    return cast(pytest.Config, SimpleNamespace(option=option))


def test_numeric_override_is_left_to_xdist(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Return None so pytest-xdist applies a numeric override itself."""
    monkeypatch.setenv("PYTEST_XDIST_AUTO_NUM_WORKERS", "3")
    assert filler.pytest_xdist_auto_num_workers(_config("auto")) is None


def test_hook_combines_cores_and_memory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Count physical cores for `auto` and logical ones for `logical`."""
    monkeypatch.delenv("PYTEST_XDIST_AUTO_NUM_WORKERS", raising=False)
    monkeypatch.setattr(
        filler, "_core_count", lambda logical: 64 if logical else 8
    )
    monkeypatch.setattr(filler, "_total_memory", lambda: 32 * GIB)
    name = sys.implementation.name
    assert filler.pytest_xdist_auto_num_workers(
        _config("auto")
    ) == auto_worker_count(8, 32 * GIB, name)
    assert filler.pytest_xdist_auto_num_workers(
        _config("logical")
    ) == auto_worker_count(64, 32 * GIB, name)
