"""Unit tests for the t8n output cache functionality."""

import hashlib
from typing import Any

import pytest

from execution_testing.fixtures import (
    BlockchainEngineFixture,
    BlockchainFixture,
    FixtureFormat,
    LabeledFixtureFormat,
    StateFixture,
    strip_fixture_format_from_node,
)

from ...shared.helpers import labeled_format_parameter_set
from ..filler import _strip_xdist_group_suffix


class MockItem:
    """Mock pytest.Item for testing collection sorting behavior."""

    nodeid: str
    name: str
    _markers: list[pytest.Mark]

    def __init__(
        self,
        nodeid: str,
        fixture_format: LabeledFixtureFormat | FixtureFormat | None,
        name: str | None = None,
    ) -> None:
        """Initialize name from nodeid if not provided."""
        self.nodeid = nodeid
        if not name:
            parts = nodeid.split("::")
            name = parts[-1] if "::" in nodeid else nodeid
        self.name = name
        self._markers = []
        if fixture_format is not None:
            param = labeled_format_parameter_set(fixture_format)
            for mark in param.marks:
                self._markers.append(mark)  # type: ignore[arg-type]

    def get_closest_marker(self, name: str) -> pytest.Mark | None:
        """Return marker by name if present."""
        for marker in self._markers:
            if marker.name == name:
                return marker
        return None

    def add_marker(self, marker: Any) -> None:
        """Add a marker to the item."""
        self._markers.append(marker)


class TestStripFixtureFormatFromNodeid:
    """Test cases for strip_fixture_format_from_node function."""

    def test_strip_blockchain_test(self) -> None:
        """Test stripping blockchain_test format."""
        item = MockItem(
            "tests/test.py::test_foo[fork_Osaka-blockchain_test]",
            BlockchainFixture,
        )
        expected = "tests/test.py::test_foo[fork_Osaka-]"
        assert strip_fixture_format_from_node(item) == expected

    def test_strip_blockchain_test_engine(self) -> None:
        """Test stripping blockchain_test_engine format."""
        item = MockItem(
            "tests/test.py::test_foo[fork_Osaka-blockchain_test_engine]",
            BlockchainEngineFixture,
        )
        expected = "tests/test.py::test_foo[fork_Osaka-]"
        assert strip_fixture_format_from_node(item) == expected

    def test_strip_state_test(self) -> None:
        """Test stripping state_test format."""
        item = MockItem(
            "tests/test.py::test_foo[fork_Osaka-state_test]",
            StateFixture,
        )
        expected = "tests/test.py::test_foo[fork_Osaka-]"
        assert strip_fixture_format_from_node(item) == expected

    def test_strip_format_in_middle(self) -> None:
        """Test stripping format when it's in the middle of params."""
        item = MockItem(
            "tests/test.py::test_foo[fork_Osaka-blockchain_test-param1]",
            BlockchainFixture,
        )
        expected = "tests/test.py::test_foo[fork_Osaka--param1]"
        assert strip_fixture_format_from_node(item) == expected

    def test_no_format_unchanged(self) -> None:
        """Test that nodeids without fixture format are unchanged."""
        item = MockItem(
            "tests/test.py::test_foo[fork_Osaka-some_param]",
            None,
        )
        assert strip_fixture_format_from_node(item) == item.nodeid

    def test_no_params_unchanged(self) -> None:
        """Test that nodeids without parameters are unchanged."""
        item = MockItem(
            "tests/test.py::test_foo",
            None,
        )
        assert strip_fixture_format_from_node(item) == item.nodeid

    def test_empty_params_unchanged(self) -> None:
        """Test that nodeids with empty params are unchanged."""
        item = MockItem(
            "tests/test.py::test_foo[]",
            None,
        )
        assert strip_fixture_format_from_node(item) == item.nodeid

    def test_format_at_start(self) -> None:
        """Test stripping format at start of params."""
        item = MockItem(
            "tests/test.py::test_foo[blockchain_test-fork_Osaka]",
            BlockchainFixture,
        )
        expected = "tests/test.py::test_foo[-fork_Osaka]"
        assert strip_fixture_format_from_node(item) == expected

    def test_only_format(self) -> None:
        """Test stripping format at start of params."""
        item = MockItem(
            "tests/test.py::test_foo[blockchain_test]",
            BlockchainFixture,
        )
        expected = "tests/test.py::test_foo[]"
        assert strip_fixture_format_from_node(item) == expected

    def test_related_formats_same_base(self) -> None:
        """Test that related formats produce the same base nodeid."""
        base_nodeid = "tests/test.py::test_foo[fork_Osaka--param1]"

        node_bt = MockItem(
            "tests/test.py::test_foo[fork_Osaka-blockchain_test-param1]",
            BlockchainFixture,
        )
        node_bte = MockItem(
            "tests/test.py::test_foo[fork_Osaka-blockchain_test_engine-param1]",
            BlockchainEngineFixture,
        )

        # Both should strip to the same base.
        assert strip_fixture_format_from_node(node_bt) == base_nodeid
        assert strip_fixture_format_from_node(node_bte) == base_nodeid

    def test_longer_format_matched_first(self) -> None:
        """Test that longer format names are matched before shorter ones."""
        # blockchain_test_engine should match before blockchain_test.
        node = MockItem(
            "tests/test.py::test[fork_Osaka-blockchain_test_engine]",
            BlockchainEngineFixture,
        )
        expected = "tests/test.py::test[fork_Osaka-]"
        result = strip_fixture_format_from_node(node)
        assert result == expected
        # Verify it didn't partially match blockchain_test.
        assert "blockchain_test" not in result


class TestCacheKeyConsistency:
    """Test that cache keys are consistent across fixture formats."""

    @pytest.mark.parametrize(
        "labeled_fixture_format,format_name",
        [
            (BlockchainFixture, "blockchain_test"),
            (BlockchainEngineFixture, "blockchain_test_engine"),
            (StateFixture, "state_test"),
            (
                LabeledFixtureFormat(
                    BlockchainFixture, "blockchain_test_from_state_test", ""
                ),
                "blockchain_test_from_state_test",
            ),
            (
                LabeledFixtureFormat(
                    BlockchainEngineFixture,
                    "blockchain_test_engine_from_state_test",
                    "",
                ),
                "blockchain_test_engine_from_state_test",
            ),
        ],
    )
    def test_format_stripping_produces_consistent_key(
        self, labeled_fixture_format: LabeledFixtureFormat, format_name: str
    ) -> None:
        """Test that all format variants produce the same base key."""
        base = "tests/test.py::test_case[fork_Osaka--param1]"
        nodeid = f"tests/test.py::test_case[fork_Osaka-{format_name}-param1]"
        node = MockItem(nodeid, labeled_fixture_format)

        result = strip_fixture_format_from_node(node)
        assert result == base, f"Format {format_name} did not strip correctly"


class TestStripXdistGroupSuffix:
    """Test cases for _strip_xdist_group_suffix function."""

    def test_strips_t8n_cache_suffix(self) -> None:
        """Test that t8n-cache-* suffixes are stripped."""
        nodeid = "test.py::test[params]@t8n-cache-12345678"
        expected = "test.py::test[params]"
        assert _strip_xdist_group_suffix(nodeid) == expected

    def test_preserves_other_group_suffixes(self) -> None:
        """Test that non-cache group suffixes (e.g., bigmem) are preserved."""
        nodeid = "test.py::test[params]@bigmem"
        assert _strip_xdist_group_suffix(nodeid) == nodeid

    def test_preserves_custom_group_suffixes(self) -> None:
        """Test that custom xdist_group markers are preserved."""
        nodeid = "test.py::test[params]@custom_group"
        assert _strip_xdist_group_suffix(nodeid) == nodeid

    def test_no_suffix_unchanged(self) -> None:
        """Test that nodeids without @ are unchanged."""
        nodeid = "test.py::test[params]"
        assert _strip_xdist_group_suffix(nodeid) == nodeid

    def test_at_in_params_preserved(self) -> None:
        """Test that @ in params (not suffix) is preserved."""
        # This tests the rsplit behavior - only the last @ is considered.
        nodeid = "test.py::test[email@example.com]@t8n-cache-abc"
        expected = "test.py::test[email@example.com]"
        assert _strip_xdist_group_suffix(nodeid) == expected


class TestCacheExecutionOrder:
    """Test that execution order maximizes cache hits."""

    def test_blockchain_test_sorts_before_blockchain_test_engine(self) -> None:
        """Test blockchain_test < blockchain_test_engine alphabetically."""
        # Alphabetical order determines which format runs first.
        assert "blockchain_test" < "blockchain_test_engine"

    def test_related_formats_group_together_when_sorted(self) -> None:
        """Test that sorting by base nodeid groups related formats together."""
        nodes = [
            MockItem(
                "tests/test.py::test_foo[fork_Osaka-blockchain_test]",
                BlockchainFixture,
            ),
            MockItem(
                "tests/test.py::test_bar[fork_Osaka-blockchain_test]",
                BlockchainFixture,
            ),
            MockItem(
                "tests/test.py::test_foo[fork_Osaka-blockchain_test_engine]",
                BlockchainEngineFixture,
            ),
            MockItem(
                "tests/test.py::test_bar[fork_Osaka-blockchain_test_engine]",
                BlockchainEngineFixture,
            ),
        ]

        # Sort by base nodeid (as the collection hook does).
        sorted_nodes = sorted(nodes, key=strip_fixture_format_from_node)

        # Related formats should be adjacent after sorting.
        test_bar_indices = [
            i for i, n in enumerate(sorted_nodes) if "test_bar" in n.nodeid
        ]
        test_foo_indices = [
            i for i, n in enumerate(sorted_nodes) if "test_foo" in n.nodeid
        ]

        # Check adjacency: indices should be consecutive.
        assert test_bar_indices == [0, 1] or test_bar_indices == [2, 3]
        assert test_foo_indices == [0, 1] or test_foo_indices == [2, 3]

    def test_related_formats_grouped_when_sorted(self) -> None:
        """Test sorting groups related formats together (same base nodeid)."""
        nodes = [
            MockItem(
                "tests/test.py::test_foo[fork_Osaka-blockchain_test]",
                BlockchainFixture,
            ),
            MockItem(
                "tests/test.py::test_bar[fork_Osaka-blockchain_test]",
                BlockchainFixture,
            ),
            MockItem(
                "tests/test.py::test_foo[fork_Osaka-blockchain_test_engine]",
                BlockchainEngineFixture,
            ),
        ]

        # Sort by base nodeid.
        sorted_nodes = sorted(nodes, key=strip_fixture_format_from_node)

        # test_bar items should be adjacent, test_foo items should be adjacent.
        foo_indices = [
            i for i, n in enumerate(sorted_nodes) if "test_foo" in n.nodeid
        ]
        bar_indices = [
            i for i, n in enumerate(sorted_nodes) if "test_bar" in n.nodeid
        ]

        # Check foo items are adjacent (difference is 1).
        assert max(foo_indices) - min(foo_indices) == len(foo_indices) - 1
        # Check bar items are adjacent (just one item here).
        assert len(bar_indices) == 1

    def test_sorting_groups_multiple_tests_by_base_nodeid(self) -> None:
        """Test sorting groups items by base nodeid."""
        nodes = [
            # Deliberately interleaved: test_a and test_b formats mixed.
            MockItem(
                "tests/test.py::test_b[fork_Osaka-blockchain_test_engine]",
                BlockchainEngineFixture,
            ),
            MockItem(
                "tests/test.py::test_a[fork_Osaka-blockchain_test]",
                BlockchainFixture,
            ),
            MockItem(
                "tests/test.py::test_b[fork_Osaka-blockchain_test]",
                BlockchainFixture,
            ),
            MockItem(
                "tests/test.py::test_a[fork_Osaka-blockchain_test_engine]",
                BlockchainEngineFixture,
            ),
        ]

        # Sort by base nodeid.
        sorted_nodes = sorted(nodes, key=strip_fixture_format_from_node)

        # After sorting, test_a formats should be adjacent, test_b adjacent.
        test_a_indices = [
            i for i, n in enumerate(sorted_nodes) if "test_a" in n.nodeid
        ]
        test_b_indices = [
            i for i, n in enumerate(sorted_nodes) if "test_b" in n.nodeid
        ]

        # Check test_a items are adjacent.
        assert max(test_a_indices) - min(test_a_indices) == 1
        # Check test_b items are adjacent.
        assert max(test_b_indices) - min(test_b_indices) == 1


class TestCollectionSortingBehavior:
    """Test collection sorting behavior ensures cache hits."""

    def _sort_items_by_base_nodeid(self, items: list[MockItem]) -> None:
        """Sort items by base nodeid (cache-friendly order)."""
        items.sort(key=lambda item: strip_fixture_format_from_node(item))

    def _add_xdist_markers(self, items: list[MockItem]) -> None:
        """Add xdist_group markers based on base nodeid hash."""
        for item in items:
            base_nodeid = strip_fixture_format_from_node(item)
            h = hashlib.md5(
                base_nodeid.encode(), usedforsecurity=False
            ).hexdigest()[:8]
            item.add_marker(pytest.mark.xdist_group(name=f"t8n-cache-{h}"))

    def _simulate_collection_without_xdist(
        self, items: list[MockItem]
    ) -> None:
        """Simulate collection behavior WITHOUT xdist (sorts items)."""
        self._sort_items_by_base_nodeid(items)

    def _simulate_collection_with_xdist(self, items: list[MockItem]) -> None:
        """Simulate collection behavior WITH xdist (adds markers AND sorts)."""
        self._add_xdist_markers(items)
        self._sort_items_by_base_nodeid(items)

    def test_items_sorted_without_xdist(self) -> None:
        """Test that items are sorted when xdist is NOT enabled."""
        items = [
            MockItem(
                "tests/test.py::test_b[fork_Osaka-blockchain_test]",
                BlockchainFixture,
            ),
            MockItem(
                "tests/test.py::test_a[fork_Osaka-blockchain_test]",
                BlockchainFixture,
            ),
        ]

        self._simulate_collection_without_xdist(items)

        # After sorting by base nodeid, test_a should come before test_b.
        assert "test_a" in items[0].nodeid
        assert "test_b" in items[1].nodeid

    def test_items_sorted_with_xdist(self) -> None:
        """Test items are sorted with xdist for cache locality."""
        items = [
            MockItem(
                "tests/test.py::test_b[fork_Osaka-blockchain_test]",
                BlockchainFixture,
            ),
            MockItem(
                "tests/test.py::test_a[fork_Osaka-blockchain_test]",
                BlockchainFixture,
            ),
        ]

        self._simulate_collection_with_xdist(items)

        # After sorting by base nodeid, test_a should come before test_b.
        assert "test_a" in items[0].nodeid
        assert "test_b" in items[1].nodeid

    def test_xdist_groups_have_consistent_hash(self) -> None:
        """Test xdist_group markers use consistent hashes."""
        items = [
            MockItem(
                "tests/test.py::test_foo[fork_Osaka-blockchain_test]",
                BlockchainFixture,
            ),
            MockItem(
                "tests/test.py::test_foo[fork_Osaka-blockchain_test_engine]",
                BlockchainEngineFixture,
            ),
        ]

        self._simulate_collection_with_xdist(items)

        marker0 = items[0].get_closest_marker("xdist_group")
        marker1 = items[1].get_closest_marker("xdist_group")

        assert marker0 is not None, "First item needs xdist_group marker."
        assert marker1 is not None, "Second item needs xdist_group marker."

        group0 = marker0.kwargs.get("name", "")
        group1 = marker1.kwargs.get("name", "")

        assert group0 == group1, (
            f"Related formats should have the same xdist_group. "
            f"Got: {group0} vs {group1}"
        )
        assert group0.startswith("t8n-cache-")

    def test_xdist_sorting_groups_related_formats(self) -> None:
        """Test xdist collection groups related formats together."""
        items = [
            MockItem(
                "tests/test.py::test_b[fork_Osaka-blockchain_test]",
                BlockchainFixture,
            ),
            MockItem(
                "tests/test.py::test_a[fork_Osaka-blockchain_test]",
                BlockchainFixture,
            ),
            MockItem(
                "tests/test.py::test_b[fork_Osaka-blockchain_test_engine]",
                BlockchainEngineFixture,
            ),
            MockItem(
                "tests/test.py::test_a[fork_Osaka-blockchain_test_engine]",
                BlockchainEngineFixture,
            ),
        ]

        self._simulate_collection_with_xdist(items)

        # Items should be sorted so related formats are adjacent.
        nodeids = [i.nodeid for i in items]
        # test_a variants should be together, test_b variants together.
        test_a_indices = [i for i, n in enumerate(nodeids) if "test_a" in n]
        test_b_indices = [i for i, n in enumerate(nodeids) if "test_b" in n]

        # Check adjacency (difference between indices should be 1).
        assert max(test_a_indices) - min(test_a_indices) == 1
        assert max(test_b_indices) - min(test_b_indices) == 1
