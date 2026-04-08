"""Unit tests for the grouped least-duration splitting algorithm."""

from __future__ import annotations

from typing import NamedTuple

import pytest

from execution_testing.pytest_plugins.split.grouped_least_duration import (
    grouped_least_duration,
    grouping_key,
    normalize_durations,
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
        """Strip format and xdist suffix, keep fork and params."""
        nid = (
            "tests/istanbul/test_chainid.py::test_chainid"
            "[fork_Prague-typed_transaction_2-blockchain_test]"
            "@t8n-cache-abc123"
        )
        assert grouping_key(nid) == (
            "tests/istanbul/test_chainid.py::test_chainid"
            "[fork_Prague-typed_transaction_2]"
        )

    def test_no_xdist_group_suffix(self) -> None:
        """Strip format, keep fork and params without xdist suffix."""
        nid = (
            "tests/istanbul/test_chainid.py::test_chainid"
            "[fork_Prague-typed_transaction_2-state_test]"
        )
        assert grouping_key(nid) == (
            "tests/istanbul/test_chainid.py::test_chainid"
            "[fork_Prague-typed_transaction_2]"
        )

    def test_singleton_no_bracket(self) -> None:
        """Unparametrized nodeid returns the full nodeid as key."""
        nid = "tests/utils/test_helpers.py::test_something"
        assert grouping_key(nid) == nid

    def test_different_formats_same_key(self) -> None:
        """All fixture formats for the same test case share a key."""
        base = "tests/test.py::test_fn"
        nids = [
            f"{base}[fork_Cancun-param_X-state_test]@t8n-cache-aa",
            f"{base}[fork_Cancun-param_X-blockchain_test]@t8n-cache-bb",
            f"{base}[fork_Cancun-param_X-blockchain_test_engine_x]",
        ]
        keys = {grouping_key(n) for n in nids}
        assert keys == {f"{base}[fork_Cancun-param_X]"}

    def test_different_params_different_keys(self) -> None:
        """Different test case params produce different keys."""
        base = "tests/test.py::test_fn"
        k1 = grouping_key(f"{base}[fork_A-param_X-state_test]")
        k2 = grouping_key(f"{base}[fork_A-param_Y-state_test]")
        assert k1 != k2
        assert k1 == f"{base}[fork_A-param_X]"
        assert k2 == f"{base}[fork_A-param_Y]"

    def test_format_in_middle_of_params(self) -> None:
        """Format token is stripped regardless of position."""
        nid = (
            "t.py::test_fn[fork_BPO1-target_blobs-blockchain_test-base_fee_7]"
        )
        assert grouping_key(nid) == (
            "t.py::test_fn[fork_BPO1-target_blobs-base_fee_7]"
        )


# ---------------------------------------------------------------------------
# grouped_least_duration
# ---------------------------------------------------------------------------


class TestGroupedLeastDuration:
    """Test the splitting algorithm."""

    def test_format_variants_same_runner(self) -> None:
        """Format variants of the same test case land together."""
        items = [
            Item("t.py::f[fork_A-p_X-state_test]"),
            Item("t.py::f[fork_A-p_X-blockchain_test]"),
            Item("t.py::f[fork_A-p_Y-state_test]"),
        ]
        durations = {i.nodeid: 1.0 for i in items}
        groups = grouped_least_duration(2, items, durations)

        # p_X format variants must be on the same runner
        x_items = [items[0], items[1]]
        for g in groups:
            if x_items[0] in g.selected:
                assert x_items[1] in g.selected
                break

    def test_heaviest_group_first(self) -> None:
        """Heavy group anchors one runner; light groups fill the other."""
        heavy = [
            Item("t.py::heavy[fork_A-p_X-state_test]"),
            Item("t.py::heavy[fork_A-p_X-blockchain_test]"),
            Item("t.py::heavy[fork_A-p_X-blockchain_test_engine_x]"),
        ]
        light = [
            Item("t.py::light[fork_B-p_Y-state_test]"),
            Item("t.py::light[fork_B-p_Y-blockchain_test]"),
            Item("t.py::light[fork_B-p_Y-blockchain_test_engine_x]"),
        ]
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
        known = Item("t.py::known[fork_A-state_test]")
        unknown = Item("t.py::unknown[fork_B-state_test]")
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
            Item("t.py::f[fork_A-p-blockchain_test_engine_x]"),
            Item("t.py::f[fork_A-p-blockchain_test]"),
            Item("t.py::f[fork_A-p-state_test]"),
        ]
        durations = {i.nodeid: 1.0 for i in items}
        groups = grouped_least_duration(1, items, durations)
        assert groups[0].selected == list(items)

    def test_deselected_correctness(self) -> None:
        """Selected + deselected == all items for every runner."""
        items = [
            Item("t.py::f[fork_A-p1-state_test]"),
            Item("t.py::f[fork_A-p2-state_test]"),
            Item("t.py::g[fork_A-p1-state_test]"),
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
        items = [Item("t.py::f[fork_A-state_test]")]
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
            Item("t.py::f[fork_A-state_test]"),
            Item("t.py::g[fork_B-state_test]"),
        ]
        durations = {i.nodeid: 1.0 for i in items}
        groups = grouped_least_duration(1, items, durations)

        assert len(groups) == 1
        assert groups[0].selected == list(items)
        assert groups[0].deselected == []

    def test_durations_with_xdist_suffix_match(self) -> None:
        """Durations with ``@xdist_group`` suffixes match bare nodeids."""
        heavy = Item("t.py::heavy[fork_A-state_test]")
        light = Item("t.py::light[fork_B-state_test]")
        raw_durations = {
            "t.py::heavy[fork_A-state_test]@t8n-cache-aaa": 100.0,
            "t.py::light[fork_B-state_test]@t8n-cache-bbb": 1.0,
        }
        durations = normalize_durations(raw_durations)
        groups = grouped_least_duration(2, [heavy, light], durations)
        durations_sorted = sorted(g.duration for g in groups)
        assert durations_sorted[0] == pytest.approx(1.0)
        assert durations_sorted[1] == pytest.approx(100.0)

    def test_max_group_duration_field(self) -> None:
        """``SplitGroup.max_group_duration`` returns the heaviest group."""
        items = [
            Item("t.py::heavy[fork_A-state_test]"),
            Item("t.py::heavy[fork_A-blockchain_test]"),
            Item("t.py::light[fork_B-state_test]"),
        ]
        durations = {
            items[0].nodeid: 100.0,
            items[1].nodeid: 50.0,
            items[2].nodeid: 1.0,
        }
        groups = grouped_least_duration(2, items, durations)
        # heavy group = 150, light group = 1
        for g in groups:
            if items[0] in g.selected:
                assert g.max_group_duration == pytest.approx(150.0)
            else:
                assert g.max_group_duration == pytest.approx(1.0)
