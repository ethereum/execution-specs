"""
Conftest for ported static tests.

Temporarily skip ported static tests that fail on Amsterdam and its
descendant forks due to EIP-8037's two-dimensional gas model. The gas
limits in these ported static test cases have not yet been updated to
account for state gas.

TODO: Update gas limits in the 3452 failing ported static test cases and
remove this skip list.
"""

from pathlib import Path

import pytest
from execution_testing.fixtures import BaseFixture, LabeledFixtureFormat
from execution_testing.forks import Amsterdam

_SKIP_LIST_PATH = Path(__file__).parent / "amsterdam_skip_list.txt"
_AMSTERDAM_SKIP_CASES: frozenset[str] = frozenset(
    line.strip()
    for line in _SKIP_LIST_PATH.read_text().splitlines()
    if line.strip() and not line.lstrip().startswith("#")
)


def _fixture_format_tokens() -> tuple[str, ...]:
    """
    Return the fixture format suffixes pytest appends inside parametrize ids.
    """
    names = set(BaseFixture.formats) | set(
        LabeledFixtureFormat.registered_labels
    )
    return tuple(f"-{name}" for name in sorted(names, key=len, reverse=True))


def _normalize_nodeid(nodeid: str, tokens: tuple[str, ...]) -> str:
    """Strip pytest fixture-format suffixes to match the skip list format."""
    for token in tokens:
        nodeid = nodeid.replace(token, "")
    return nodeid


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Skip ported static test cases listed in amsterdam_skip_list.txt."""
    skip_marker = pytest.mark.skip(
        reason="Ported static test gas limits not yet updated for EIP-8037"
    )
    tokens = _fixture_format_tokens()
    for item in items:
        if "ported_static" not in item.nodeid:
            continue
        callspec = getattr(item, "callspec", None)
        fork = callspec.params.get("fork") if callspec else None
        if fork is None or not fork >= Amsterdam:
            continue
        # The skip list is written against fork_Amsterdam, but the
        # EIP-8037 breakage applies equally to its descendant forks.
        # Rewriting the item's fork token to Amsterdam's lets one list
        # cover them all.
        normalized = _normalize_nodeid(item.nodeid, tokens).replace(
            f"fork_{fork.name()}", "fork_Amsterdam"
        )
        for skip_case in _AMSTERDAM_SKIP_CASES:
            if skip_case in normalized:
                item.add_marker(skip_marker)
                break
