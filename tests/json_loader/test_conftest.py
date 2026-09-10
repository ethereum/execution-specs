"""Tests for the session teardown hook in this directory's conftest."""

from types import SimpleNamespace
from typing import cast

from execution_testing.evm_tools.t8n import ForkCache
from pytest import Session, Stash

from .conftest import pytest_sessionfinish
from .stash_keys import fork_cache_key


class RecordingForkCache:
    """Fork cache stand-in that records whether it was closed."""

    def __init__(self) -> None:
        self.closed = False

    def __exit__(self, *args: object, **kwargs: object) -> None:
        """Record the close."""
        self.closed = True


def test_session_finish_closes_the_stored_fork_cache() -> None:
    """Close the cache the session start hook stored, and drop the key."""
    cache = RecordingForkCache()
    stash = Stash()
    stash[fork_cache_key] = cast(ForkCache, cache)

    pytest_sessionfinish(cast(Session, SimpleNamespace(stash=stash)), 0)

    assert cache.closed
    assert fork_cache_key not in stash


def test_session_finish_tolerates_a_missing_fork_cache() -> None:
    """Return quietly when the session start hook stored no cache."""
    stash = Stash()

    pytest_sessionfinish(cast(Session, SimpleNamespace(stash=stash)), 0)

    assert fork_cache_key not in stash
