"""Tests for the bounded per-worker cache of parsed fixture files."""

from pathlib import Path
from typing import List

import pytest

from execution_testing.cli.pytest_commands.plugins.consume.simulators import (
    base,
)

FixtureFileCache = base.FixtureFileCache


class _ParsedFile:
    """Stand-in for the parsed fixtures of one file."""

    def __init__(self, text: str) -> None:
        self.text = text


class _FixturesStub:
    """Replacement for `Fixtures` that records every parse."""

    parsed: List[str] = []

    @classmethod
    def model_validate_json(cls, text: str) -> _ParsedFile:
        cls.parsed.append(text)
        return _ParsedFile(text)


@pytest.fixture
def parsed(monkeypatch: pytest.MonkeyPatch) -> List[str]:
    """Route fixture parsing through the stub and expose the parse log."""
    _FixturesStub.parsed = []
    monkeypatch.setattr(base, "Fixtures", _FixturesStub)
    return _FixturesStub.parsed


def _write(tmp_path: Path, name: str, size: int) -> Path:
    """Create a fixture file of exactly `size` bytes."""
    path = tmp_path / name
    path.write_text("x" * size)
    return path


def test_repeated_access_loads_once(tmp_path: Path, parsed: List[str]) -> None:
    """A cached file is parsed once and the same object is returned."""
    cache = FixtureFileCache(max_bytes=100)
    path = _write(tmp_path, "a.json", 10)

    first = cache[path]
    second = cache[path]

    assert first is second
    assert parsed == ["x" * 10]
    assert len(cache) == 1
    assert cache.cached_bytes == 10


def test_evicts_least_recently_used_file(
    tmp_path: Path, parsed: List[str]
) -> None:
    """Exceeding the bound drops the file that was used longest ago."""
    cache = FixtureFileCache(max_bytes=25)
    a = _write(tmp_path, "a.json", 10)
    b = _write(tmp_path, "b.json", 10)
    c = _write(tmp_path, "c.json", 10)

    cache[a]
    cache[b]
    cache[a]  # `a` is now more recently used than `b`.
    cache[c]

    assert a in cache
    assert b not in cache
    assert c in cache
    assert cache.cached_bytes == 20
    assert len(parsed) == 3

    cache[b]  # Reloads `b` and evicts `a`, the least recently used file.

    assert a not in cache
    assert len(parsed) == 4


def test_keeps_single_file_over_the_bound(
    tmp_path: Path, parsed: List[str]
) -> None:
    """A file larger than the bound is still cached until the next load."""
    cache = FixtureFileCache(max_bytes=5)
    big = _write(tmp_path, "big.json", 50)
    small = _write(tmp_path, "small.json", 1)

    cache[big]
    assert big in cache
    assert cache[big] is cache[big]
    assert len(parsed) == 1

    cache[small]
    assert big not in cache
    assert small in cache
    assert cache.cached_bytes == 1


def test_missing_file_is_rejected(tmp_path: Path) -> None:
    """Looking up a path that is not a file fails loudly."""
    cache = FixtureFileCache()
    with pytest.raises(AssertionError, match="Expected a file path"):
        cache[tmp_path / "missing.json"]
