"""Unit tests for the grouped least-duration splitting algorithm."""

from __future__ import annotations

from typing import NamedTuple

import pytest

from execution_testing.pytest_plugins.split.grouped_least_duration import (
    grouped_least_duration,
    grouping_key,
)


class Item(NamedTuple):
    """Minimal pytest item stub (matches pytest-split's test pattern)."""

    nodeid: str


# ---------------------------------------------------------------------------
# grouping_key
# ---------------------------------------------------------------------------


class TestGroupingKey:
    """Test the grouping key extraction."""

    def test_standard_nodeid(self) -> None:
        """Extract fork from a full nodeid with xdist group suffix."""
        nid = (
            "tests/istanbul/test_chainid.py::test_chainid"
            "[fork_Prague-typed_transaction_2-blockchain_test]"
            "@t8n-cache-abc123"
        )
        assert grouping_key(nid) == (
            "tests/istanbul/test_chainid.py::test_chainid[fork_Prague]"
        )

    def test_no_xdist_group_suffix(self) -> None:
        """Extract fork when no @xdist_group suffix is present."""
        nid = (
            "tests/istanbul/test_chainid.py::test_chainid"
            "[fork_Prague-typed_transaction_2-state_test]"
        )
        assert grouping_key(nid) == (
            "tests/istanbul/test_chainid.py::test_chainid[fork_Prague]"
        )

    def test_singleton_no_bracket(self) -> None:
        """Unparametrized nodeid returns the full nodeid as key."""
        nid = "tests/utils/test_helpers.py::test_something"
        assert grouping_key(nid) == nid

    def test_different_formats_same_key(self) -> None:
        """All fixture formats for the same function+fork share a key."""
        base = "tests/test.py::test_fn"
        nids = [
            f"{base}[fork_Cancun-state_test]@t8n-cache-aa",
            f"{base}[fork_Cancun-blockchain_test]@t8n-cache-bb",
            f"{base}[fork_Cancun-blockchain_test_engine_x]@t8n-cache-cc",
        ]
        keys = {grouping_key(n) for n in nids}
        assert keys == {f"{base}[fork_Cancun]"}


# ---------------------------------------------------------------------------
# grouped_least_duration
# ---------------------------------------------------------------------------


class TestGroupedLeastDuration:
    """Test the splitting algorithm."""

    def test_basic_grouping_same_runner(self) -> None:
        """Items with the same (function, fork) always land together."""
        items = [
            Item("t.py::f[fork_A-state_test]"),
            Item("t.py::f[fork_A-blockchain_test]"),
            Item("t.py::f[fork_B-state_test]"),
        ]
        durations = {i.nodeid: 1.0 for i in items}
        groups = grouped_least_duration(2, items, durations)

        # fork_A items must be on the same runner
        a_items = [items[0], items[1]]
        for g in groups:
            if a_items[0] in g.selected:
                assert a_items[1] in g.selected
                break

    def test_heaviest_group_first(self) -> None:
        """Heavy group anchors one runner; light groups fill the other."""
        heavy = [Item(f"t.py::heavy[fork_A-fmt_{i}]") for i in range(3)]
        light = [Item(f"t.py::light[fork_B-fmt_{i}]") for i in range(3)]
        durations = {}
        for item in heavy:
            durations[item.nodeid] = 100.0
        for item in light:
            durations[item.nodeid] = 1.0

        groups = grouped_least_duration(2, heavy + light, durations)
        durations_sorted = sorted(g.duration for g in groups)
        assert durations_sorted[0] == pytest.approx(3.0)
        assert durations_sorted[1] == pytest.approx(300.0)

    def test_singleton_no_bracket(self) -> None:
        """Unparametrized tests are each their own group."""
        items = [
            Item("t.py::test_a"),
            Item("t.py::test_b"),
        ]
        durations = {"t.py::test_a": 10.0, "t.py::test_b": 5.0}
        groups = grouped_least_duration(2, items, durations)
        assert len(groups[0].selected) == 1
        assert len(groups[1].selected) == 1

    def test_unknown_duration_fallback(self) -> None:
        """Unknown items get the average of known durations."""
        known = Item("t.py::known[fork_A-fmt]")
        unknown = Item("t.py::unknown[fork_B-fmt]")
        durations = {known.nodeid: 10.0}

        groups = grouped_least_duration(2, [known, unknown], durations)
        for g in groups:
            if known in g.selected:
                assert g.duration == pytest.approx(10.0)
            if unknown in g.selected:
                assert g.duration == pytest.approx(10.0)

    def test_intra_group_order_preserved(self) -> None:
        """Items within a group appear in original collection order."""
        items = [
            Item("t.py::f[fork_A-c]"),
            Item("t.py::f[fork_A-b]"),
            Item("t.py::f[fork_A-a]"),
        ]
        durations = {i.nodeid: 1.0 for i in items}
        groups = grouped_least_duration(1, items, durations)
        assert groups[0].selected == list(items)

    def test_deselected_correctness(self) -> None:
        """Selected + deselected == all items for every runner."""
        items = [
            Item("t.py::f[fork_A-fmt]"),
            Item("t.py::f[fork_B-fmt]"),
            Item("t.py::g[fork_A-fmt]"),
        ]
        durations = {i.nodeid: 1.0 for i in items}
        groups = grouped_least_duration(2, items, durations)

        all_ids = {i.nodeid for i in items}
        for g in groups:
            combined = {i.nodeid for i in g.selected} | {
                i.nodeid for i in g.deselected
            }
            assert combined == all_ids

    def test_empty_runners(self) -> None:
        """More splits than groups: some runners are empty, no crash."""
        items = [Item("t.py::f[fork_A-fmt]")]
        durations = {items[0].nodeid: 1.0}
        groups = grouped_least_duration(5, items, durations)

        assert len(groups) == 5
        non_empty = [g for g in groups if g.selected]
        assert len(non_empty) == 1
        empty = [g for g in groups if not g.selected]
        assert all(len(g.deselected) == 1 for g in empty)

    def test_single_runner(self) -> None:
        """Return all items as selected when splits=1."""
        items = [
            Item("t.py::f[fork_A-fmt]"),
            Item("t.py::g[fork_B-fmt]"),
        ]
        durations = {i.nodeid: 1.0 for i in items}
        groups = grouped_least_duration(1, items, durations)

        assert len(groups) == 1
        assert groups[0].selected == list(items)
        assert groups[0].deselected == []
