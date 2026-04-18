"""Unit tests for :func:`group_key`."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, cast

from _pytest.nodes import Item

from execution_testing.cli.pytest_commands.plugins.split.grouping import (
    group_key,
)


@dataclass
class _CallSpec:
    """Minimal stub mirroring ``pytest.Function.callspec``."""

    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class _Item:
    """Minimal stub mirroring the item fields ``group_key`` reads."""

    nodeid: str
    callspec: _CallSpec | None = None


def _as_item(nodeid: str, callspec: _CallSpec | None = None) -> Item:
    """Cast the stub to ``Item`` for type-checker friendliness."""
    return cast(Item, _Item(nodeid=nodeid, callspec=callspec))


class TestGroupKeyAuthoritative:
    """``parametrized_fork`` from the callspec is the primary source."""

    def test_callspec_fork_is_used(self) -> None:
        """Key uses the callspec's fork, not whatever's in the nodeid."""
        item = _as_item(
            "t.py::test_f[fork_Osaka-state_test]",
            _CallSpec(params={"parametrized_fork": "Osaka"}),
        )
        assert group_key(item) == "t.py::test_f|fork=Osaka"

    def test_callspec_wins_over_ambiguous_nodeid(self) -> None:
        """A param value starting with ``fork_`` cannot hijack the key."""
        # Nodeid's first ``fork_*`` token is the bogus param value, but
        # the real fork in the callspec is Osaka -- authoritative path
        # must ignore the nodeid scan entirely.
        item = _as_item(
            "t.py::test_f[fork_candidate-fork_Osaka-state_test]",
            _CallSpec(params={"parametrized_fork": "Osaka"}),
        )
        assert group_key(item) == "t.py::test_f|fork=Osaka"

    def test_fork_object_is_stringified(self) -> None:
        """Non-string fork values are rendered via ``str(fork)``."""

        class _Fork:
            def __str__(self) -> str:
                return "Prague"

        item = _as_item(
            "t.py::test_f[fork_Prague]",
            _CallSpec(params={"parametrized_fork": _Fork()}),
        )
        assert group_key(item) == "t.py::test_f|fork=Prague"


class TestGroupKeyFallback:
    """Without callspec or ``parametrized_fork``, fall back to nodeid."""

    def test_no_callspec_uses_nodeid_scan(self) -> None:
        """Items with no callspec scan the nodeid for ``fork_*``."""
        item = _as_item("t.py::test_f[fork_A-state_test]")
        assert group_key(item) == "t.py::test_f|fork=A"

    def test_unparametrized_item_is_singleton(self) -> None:
        """No ``[`` in nodeid yields the bare nodeid as its own group."""
        item = _as_item("t.py::test_f")
        assert group_key(item) == "t.py::test_f"

    def test_parametrized_without_fork_groups_by_function(self) -> None:
        """Parametrized items with no fork token share one group."""
        a = _as_item("t.py::test_f[x=1]")
        b = _as_item("t.py::test_f[x=2]")
        assert group_key(a) == group_key(b) == "t.py::test_f"

    def test_callspec_without_fork_param_falls_back(self) -> None:
        """Callspec present but no ``parametrized_fork`` uses the scan."""
        item = _as_item(
            "t.py::test_f[fork_A-state_test]",
            _CallSpec(params={"other": "value"}),
        )
        assert group_key(item) == "t.py::test_f|fork=A"

    def test_xdist_suffix_stripped_before_parsing(self) -> None:
        """The ``@t8n-cache-*`` suffix is removed before key building."""
        item = _as_item("t.py::test_f[fork_A]@t8n-cache-abc123")
        assert group_key(item) == "t.py::test_f|fork=A"
