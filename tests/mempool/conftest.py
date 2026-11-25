"""Pytest fixtures shared by the mempool tests."""

import pytest


@pytest.fixture
def mempool_ruleset() -> str:
    """Return the admission rule set the mempool tests assume."""
    return "public-mempool-v1"
