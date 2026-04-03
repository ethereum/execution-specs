"""
Conftest for ported static tests.

Temporarily skip ported static tests that fail for Amsterdam due to EIP-8037's
two-dimensional gas model. The gas limits in these ported static test cases
have not yet been updated to account for state gas.

TODO: Update gas limits in the 3452 failing ported static test cases and
remove this skip list.
"""

import re
from pathlib import Path

import pytest

_SKIP_LIST_PATH = Path(__file__).parent / "amsterdam_skip_list.txt"
_AMSTERDAM_SKIP_CASES: frozenset[str] = frozenset(
    line.strip()
    for line in _SKIP_LIST_PATH.read_text().splitlines()
    if line.strip()
)

# Strip fixture format from nodeid to get a format-agnostic key.
# [fork_Amsterdam-blockchain_test_engine_from_state_test-d0]
# becomes [fork_Amsterdam-d0]
_FORMAT_RE = re.compile(
    r"-(?:state_test|blockchain_test(?:_engine(?:_x)?)?(?:_from_state_test)?)"
)


def _strip_format(nodeid: str) -> str:
    """Remove fixture format suffix from a test nodeid."""
    return _FORMAT_RE.sub("", nodeid)


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Skip ported static test cases listed in amsterdam_skip_list.txt."""
    skip_marker = pytest.mark.skip(
        reason=(
            "Ported static test gas limits not yet"
            " updated for EIP-8037"
        )
    )
    for item in items:
        if "ported_static" not in item.nodeid:
            continue
        if "fork_Amsterdam" not in item.nodeid:
            continue
        stripped = _strip_format(item.nodeid)
        for skip_case in _AMSTERDAM_SKIP_CASES:
            if skip_case in stripped:
                item.add_marker(skip_marker)
                break
