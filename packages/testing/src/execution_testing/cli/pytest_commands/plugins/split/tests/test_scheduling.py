"""Unit tests for the scheduling module's public API."""

from __future__ import annotations

from collections import OrderedDict
from typing import NamedTuple

import pytest

from execution_testing.cli.pytest_commands.plugins.split.scheduling import (
    assign_runners,
    build_group_durations,
    lpt_schedule,
    sort_items_within_groups,
)


class Item(NamedTuple):
    """Minimal pytest item stub used in place of ``pytest.Item``."""

    nodeid: str


class TestAssignRunners:
    """Tests for :func:`assign_runners` (end-to-end split)."""

    def test_shared_key_stays_on_one_runner(self) -> None:
        """Items sharing a key land together."""
        a1 = Item("t.py::f[fork_A-p_X-state_test]")
        a2 = Item("t.py::f[fork_A-p_X-blockchain_test]")
        b = Item("t.py::f[fork_A-p_Y-state_test]")
        keyed = [("group_A", a1), ("group_A", a2), ("group_B", b)]
        durations = {a1.nodeid: 1.0, a2.nodeid: 1.0, b.nodeid: 1.0}

        groups = assign_runners(2, keyed, durations)
        for g in groups:
            if a1 in g.selected:
                assert a2 in g.selected
                break

    def test_heaviest_group_first(self) -> None:
        """Heavy group anchors one runner, light groups fill the other."""
        heavy = [Item(f"t.py::heavy[{i}]") for i in range(3)]
        light = [Item(f"t.py::light[{i}]") for i in range(3)]
        keyed = [("heavy", h) for h in heavy] + [
            ("light", item) for item in light
        ]
        durations = {item.nodeid: 100.0 for item in heavy}
        durations.update({item.nodeid: 1.0 for item in light})

        groups = assign_runners(2, keyed, durations)
        sorted_totals = sorted(g.duration for g in groups)
        assert sorted_totals[0] == pytest.approx(3.0)
        assert sorted_totals[1] == pytest.approx(300.0)

    def test_per_item_keys_singleton_groups(self) -> None:
        """Items with distinct keys each become their own group."""
        a = Item("t.py::test_a")
        b = Item("t.py::test_b")
        keyed = [(a.nodeid, a), (b.nodeid, b)]
        durations = {a.nodeid: 10.0, b.nodeid: 5.0}
        groups = assign_runners(2, keyed, durations)
        assert len(groups[0].selected) == 1
        assert len(groups[1].selected) == 1

    def test_unknown_duration_fallback(self) -> None:
        """Unknown items get the average of known durations."""
        known = Item("t.py::known")
        unknown = Item("t.py::unknown")
        keyed = [("known", known), ("unknown", unknown)]
        durations = {known.nodeid: 10.0}

        groups = assign_runners(2, keyed, durations)
        for g in groups:
            if known in g.selected:
                assert g.duration == pytest.approx(10.0)
            if unknown in g.selected:
                assert g.duration == pytest.approx(10.0)

    def test_intra_group_order_preserved(self) -> None:
        """Items within one group keep their original order."""
        items = [
            Item("t.py::f[engine_x]"),
            Item("t.py::f[blockchain]"),
            Item("t.py::f[state]"),
        ]
        keyed = [("shared", item) for item in items]
        durations = {i.nodeid: 1.0 for i in items}
        groups = assign_runners(1, keyed, durations)
        assert groups[0].selected == list(items)

    def test_deselected_partitions_items(self) -> None:
        """Selected + deselected equals the full input for every runner."""
        items = [Item(f"t.py::f[{i}]") for i in range(3)]
        keyed = [(f"key_{i}", item) for i, item in enumerate(items)]
        durations = {i.nodeid: 1.0 for i in items}

        groups = assign_runners(2, keyed, durations)
        all_ids = {i.nodeid for i in items}
        for g in groups:
            combined = {i.nodeid for i in g.selected} | {
                i.nodeid for i in g.deselected
            }
            assert combined == all_ids

    def test_empty_runners(self) -> None:
        """More splits than groups yields empty runners without error."""
        only = Item("t.py::f")
        keyed = [("solo", only)]
        durations = {only.nodeid: 1.0}
        groups = assign_runners(5, keyed, durations)

        assert len(groups) == 5
        non_empty = [g for g in groups if g.selected]
        empty = [g for g in groups if not g.selected]
        assert len(non_empty) == 1
        assert all(len(g.deselected) == 1 for g in empty)

    def test_single_runner(self) -> None:
        """``splits=1`` returns every item on one runner."""
        items = [Item("t.py::f"), Item("t.py::g")]
        keyed = [("k1", items[0]), ("k2", items[1])]
        durations = {i.nodeid: 1.0 for i in items}
        groups = assign_runners(1, keyed, durations)
        assert len(groups) == 1
        assert groups[0].selected == list(items)
        assert groups[0].deselected == []

    def test_durations_with_xdist_suffix_match(self) -> None:
        """Durations that still carry ``@xdist_group`` suffixes match."""
        heavy = Item("t.py::heavy")
        light = Item("t.py::light")
        # Pre-normalized: plugin always normalizes before calling the
        # algorithm, so this test mirrors that contract.
        durations = {heavy.nodeid: 100.0, light.nodeid: 1.0}
        keyed = [("h", heavy), ("l", light)]
        groups = assign_runners(2, keyed, durations)
        sorted_totals = sorted(g.duration for g in groups)
        assert sorted_totals[0] == pytest.approx(1.0)
        assert sorted_totals[1] == pytest.approx(100.0)

    def test_max_group_duration_tracked(self) -> None:
        """Each runner reports the duration of its heaviest group."""
        heavy_a = Item("t.py::heavy[a]")
        heavy_b = Item("t.py::heavy[b]")
        light = Item("t.py::light")
        keyed = [
            ("heavy", heavy_a),
            ("heavy", heavy_b),
            ("light", light),
        ]
        durations = {
            heavy_a.nodeid: 100.0,
            heavy_b.nodeid: 50.0,
            light.nodeid: 1.0,
        }
        groups = assign_runners(2, keyed, durations)
        for g in groups:
            if heavy_a in g.selected:
                assert g.max_group_duration == pytest.approx(150.0)
            else:
                assert g.max_group_duration == pytest.approx(1.0)


class TestBuildGroupDurations:
    """Tests for :func:`build_group_durations`."""

    def test_groups_preserve_collection_order(self) -> None:
        """Items sharing a key keep their original order."""
        a, b, c = Item("t.py::a"), Item("t.py::b"), Item("t.py::a")
        keyed = [("k1", a), ("k2", b), ("k1", c)]
        groups, _ = build_group_durations(keyed, {})
        assert list(groups.keys()) == ["k1", "k2"]
        assert groups["k1"] == [a, c]
        assert groups["k2"] == [b]

    def test_unknown_items_use_known_mean(self) -> None:
        """Per-group total blends known durations with the known mean."""
        known = Item("t.py::known")
        unknown = Item("t.py::unknown")
        keyed = [("k", known), ("k", unknown)]
        _, group_durations = build_group_durations(keyed, {known.nodeid: 4.0})
        assert group_durations["k"] == pytest.approx(8.0)

    def test_no_known_durations_fallback_one(self) -> None:
        """With zero known durations every item weighs ``1.0``."""
        a, b = Item("t.py::a"), Item("t.py::b")
        _, group_durations = build_group_durations([("g", a), ("g", b)], {})
        assert group_durations["g"] == pytest.approx(2.0)


class TestLPTSchedule:
    """Tests for :func:`lpt_schedule`."""

    def test_heaviest_anchors_least_loaded(self) -> None:
        """Heaviest group lands on runner 0; remaining fills runner 1."""
        keys, totals, max_group = lpt_schedule(
            {"heavy": 100.0, "mid": 20.0, "light": 5.0}, 2
        )
        assert sorted(totals) == [25.0, 100.0]
        heavy_runner = max(range(2), key=lambda i: totals[i])
        assert keys[heavy_runner] == ["heavy"]
        assert max_group[heavy_runner] == pytest.approx(100.0)

    def test_empty_runners_when_splits_exceed_groups(self) -> None:
        """Extra runners get no keys and zero totals."""
        keys, totals, max_group = lpt_schedule({"only": 7.0}, 3)
        assert sum(len(k) for k in keys) == 1
        assert sum(totals) == pytest.approx(7.0)
        assert max(max_group) == pytest.approx(7.0)


class TestSortItemsWithinGroups:
    """Tests for :func:`sort_items_within_groups`."""

    def test_items_sorted_slowest_first(self) -> None:
        """Each group's items come out in duration-DESC order."""
        fast = Item("t.py::f[fast]")
        mid = Item("t.py::f[mid]")
        slow = Item("t.py::f[slow]")
        groups = OrderedDict([("g", [fast, mid, slow])])
        durations = {fast.nodeid: 1.0, mid.nodeid: 5.0, slow.nodeid: 10.0}
        out = sort_items_within_groups(groups, durations)
        assert out["g"] == [slow, mid, fast]

    def test_group_order_preserved(self) -> None:
        """Sort mutates within groups only; group key order is kept."""
        a, b = Item("t.py::a"), Item("t.py::b")
        groups = OrderedDict([("k1", [a]), ("k2", [b])])
        out = sort_items_within_groups(groups, {})
        assert list(out.keys()) == ["k1", "k2"]

    def test_stable_on_ties(self) -> None:
        """Items with identical durations keep their input order."""
        x = Item("t.py::f[x]")
        y = Item("t.py::f[y]")
        z = Item("t.py::f[z]")
        groups = OrderedDict([("g", [x, y, z])])
        out = sort_items_within_groups(
            groups, {x.nodeid: 1.0, y.nodeid: 1.0, z.nodeid: 1.0}
        )
        assert out["g"] == [x, y, z]

    def test_unknown_items_use_known_mean(self) -> None:
        """Unknown items are weighted at the known-items mean."""
        known_slow = Item("t.py::known_slow")
        unknown = Item("t.py::unknown")
        known_fast = Item("t.py::known_fast")
        groups = OrderedDict([("g", [known_fast, unknown, known_slow])])
        out = sort_items_within_groups(
            groups,
            {known_slow.nodeid: 100.0, known_fast.nodeid: 1.0},
        )
        # Mean is ~50.5, so unknown > known_fast but < known_slow.
        assert out["g"] == [known_slow, unknown, known_fast]


class TestAssignRunnersIntraGroupSort:
    """End-to-end: :func:`assign_runners` + ``sort_intra_group``."""

    def test_default_sorts_slowest_first_within_group(self) -> None:
        """With ``sort_intra_group`` (default) slow items lead each group."""
        fast = Item("t.py::f[fast]")
        slow = Item("t.py::f[slow]")
        keyed = [("g", fast), ("g", slow)]
        durations = {fast.nodeid: 1.0, slow.nodeid: 100.0}
        groups = assign_runners(1, keyed, durations)
        assert groups[0].selected == [slow, fast]

    def test_disabled_preserves_collection_order(self) -> None:
        """``sort_intra_group=False`` keeps the original input order."""
        fast = Item("t.py::f[fast]")
        slow = Item("t.py::f[slow]")
        keyed = [("g", fast), ("g", slow)]
        durations = {fast.nodeid: 1.0, slow.nodeid: 100.0}
        groups = assign_runners(1, keyed, durations, sort_intra_group=False)
        assert groups[0].selected == [fast, slow]

    def test_sort_does_not_cross_group_boundaries(self) -> None:
        """Groups stay contiguous; sort only applies within each group."""
        a_fast = Item("t.py::a[fast]")
        a_slow = Item("t.py::a[slow]")
        b_fast = Item("t.py::b[fast]")
        b_slow = Item("t.py::b[slow]")
        keyed = [
            ("a", a_fast),
            ("a", a_slow),
            ("b", b_fast),
            ("b", b_slow),
        ]
        durations = {
            a_fast.nodeid: 1.0,
            a_slow.nodeid: 10.0,
            b_fast.nodeid: 2.0,
            b_slow.nodeid: 20.0,
        }
        groups = assign_runners(1, keyed, durations)
        # Heaviest group first (b total 22 > a total 11), each
        # internally slowest-first, and no interleaving.
        assert groups[0].selected == [b_slow, b_fast, a_slow, a_fast]
