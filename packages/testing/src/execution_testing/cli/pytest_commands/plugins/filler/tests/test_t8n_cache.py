"""Unit tests for the t8n output cache functionality."""

import pytest

from execution_testing.fixtures import (
    get_all_fixture_format_names,
    strip_fixture_format_from_nodeid,
)

from ..filler import T8nOutputCache, _strip_xdist_group_suffix


class TestT8nOutputCache:
    """Test cases for the T8nOutputCache LRU cache."""

    def test_cache_basic_operations(self) -> None:
        """Test basic get/set operations."""
        cache = T8nOutputCache(maxsize=3)

        key = ("test.py::test[fork_Osaka]", "Osaka", 0)
        value = object()  # Mock TransitionToolOutput

        assert cache.get(key) is None
        cache.set(key, value)  # type: ignore[arg-type]
        assert cache.get(key) is value

    def test_cache_lru_eviction(self) -> None:
        """Test LRU eviction when cache exceeds maxsize."""
        cache = T8nOutputCache(maxsize=2)

        key1 = ("test1", "Osaka", 0)
        key2 = ("test2", "Osaka", 0)
        key3 = ("test3", "Osaka", 0)

        cache.set(key1, "value1")  # type: ignore[arg-type]
        cache.set(key2, "value2")  # type: ignore[arg-type]

        # Both should be present.
        assert cache.get(key1) == "value1"
        assert cache.get(key2) == "value2"

        # Adding key3 should evict key1 (oldest after key2 access).
        cache.set(key3, "value3")  # type: ignore[arg-type]
        assert cache.get(key1) is None  # Evicted
        assert cache.get(key2) == "value2"
        assert cache.get(key3) == "value3"

    def test_cache_lru_access_updates_order(self) -> None:
        """Test that get() updates LRU order."""
        cache = T8nOutputCache(maxsize=2)

        key1 = ("test1", "Osaka", 0)
        key2 = ("test2", "Osaka", 0)
        key3 = ("test3", "Osaka", 0)

        cache.set(key1, "value1")  # type: ignore[arg-type]
        cache.set(key2, "value2")  # type: ignore[arg-type]

        # Access key1 to make it recently used.
        cache.get(key1)

        # Adding key3 should evict key2 (now oldest).
        cache.set(key3, "value3")  # type: ignore[arg-type]
        assert cache.get(key1) == "value1"
        assert cache.get(key2) is None  # Evicted
        assert cache.get(key3) == "value3"

    def test_cache_hit_miss_tracking(self) -> None:
        """Test that hits and misses are tracked correctly."""
        cache = T8nOutputCache(maxsize=3)

        key = ("test", "Osaka", 0)

        # Miss.
        cache.get(key)
        assert cache.hits == 0
        assert cache.misses == 1

        # Set and hit.
        cache.set(key, "value")  # type: ignore[arg-type]
        cache.get(key)
        assert cache.hits == 1
        assert cache.misses == 1

        # Another hit.
        cache.get(key)
        assert cache.hits == 2
        assert cache.misses == 1

    def test_cache_stats(self) -> None:
        """Test stats() output format."""
        cache = T8nOutputCache(maxsize=3)

        key = ("test", "Osaka", 0)
        cache.set(key, "value")  # type: ignore[arg-type]
        cache.get(key)  # Hit
        cache.get(("other", "Osaka", 0))  # Miss

        stats = cache.stats()
        assert "hits=1" in stats
        assert "misses=1" in stats
        assert "rate=50.0%" in stats

    def test_cache_stats_empty(self) -> None:
        """Test stats() with no operations."""
        cache = T8nOutputCache(maxsize=3)
        stats = cache.stats()
        assert "hits=0" in stats
        assert "misses=0" in stats
        assert "rate=0.0%" in stats

    def test_cache_update_existing_key(self) -> None:
        """Test that setting an existing key updates value and LRU order."""
        cache = T8nOutputCache(maxsize=2)

        key1 = ("test1", "Osaka", 0)
        key2 = ("test2", "Osaka", 0)
        key3 = ("test3", "Osaka", 0)

        cache.set(key1, "old")  # type: ignore[arg-type]
        cache.set(key2, "value2")  # type: ignore[arg-type]

        # Update key1 (moves to end).
        cache.set(key1, "new")  # type: ignore[arg-type]
        assert cache.get(key1) == "new"

        # Adding key3 should evict key2 (now oldest).
        cache.set(key3, "value3")  # type: ignore[arg-type]
        assert cache.get(key1) == "new"
        assert cache.get(key2) is None


class TestStripFixtureFormatFromNodeid:
    """Test cases for strip_fixture_format_from_nodeid function."""

    def test_strip_blockchain_test(self) -> None:
        """Test stripping blockchain_test format."""
        nodeid = "tests/test.py::test_foo[fork_Osaka-blockchain_test]"
        expected = "tests/test.py::test_foo[fork_Osaka]"
        assert strip_fixture_format_from_nodeid(nodeid) == expected

    def test_strip_blockchain_test_engine(self) -> None:
        """Test stripping blockchain_test_engine format."""
        nodeid = "tests/test.py::test_foo[fork_Osaka-blockchain_test_engine]"
        expected = "tests/test.py::test_foo[fork_Osaka]"
        assert strip_fixture_format_from_nodeid(nodeid) == expected

    def test_strip_state_test(self) -> None:
        """Test stripping state_test format."""
        nodeid = "tests/test.py::test_foo[fork_Osaka-state_test]"
        expected = "tests/test.py::test_foo[fork_Osaka]"
        assert strip_fixture_format_from_nodeid(nodeid) == expected

    def test_strip_format_in_middle(self) -> None:
        """Test stripping format when it's in the middle of params."""
        nodeid = "tests/test.py::test_foo[fork_Osaka-blockchain_test-param1]"
        expected = "tests/test.py::test_foo[fork_Osaka-param1]"
        assert strip_fixture_format_from_nodeid(nodeid) == expected

    def test_no_format_unchanged(self) -> None:
        """Test that nodeids without fixture format are unchanged."""
        nodeid = "tests/test.py::test_foo[fork_Osaka-some_param]"
        assert strip_fixture_format_from_nodeid(nodeid) == nodeid

    def test_no_params_unchanged(self) -> None:
        """Test that nodeids without parameters are unchanged."""
        nodeid = "tests/test.py::test_foo"
        assert strip_fixture_format_from_nodeid(nodeid) == nodeid

    def test_empty_params_unchanged(self) -> None:
        """Test that nodeids with empty params are unchanged."""
        nodeid = "tests/test.py::test_foo[]"
        assert strip_fixture_format_from_nodeid(nodeid) == nodeid

    def test_format_at_start(self) -> None:
        """Test stripping format at start of params."""
        nodeid = "tests/test.py::test_foo[blockchain_test-fork_Osaka]"
        expected = "tests/test.py::test_foo[fork_Osaka]"
        assert strip_fixture_format_from_nodeid(nodeid) == expected

    def test_related_formats_same_base(self) -> None:
        """Test that related formats produce the same base nodeid."""
        base_nodeid = "tests/test.py::test_foo[fork_Osaka-param1]"

        nodeid_bt = "tests/test.py::test_foo[fork_Osaka-blockchain_test-param1]"
        nodeid_bte = (
            "tests/test.py::test_foo[fork_Osaka-blockchain_test_engine-param1]"
        )

        # Both should strip to the same base.
        assert strip_fixture_format_from_nodeid(nodeid_bt) == base_nodeid
        assert strip_fixture_format_from_nodeid(nodeid_bte) == base_nodeid

    def test_longer_format_matched_first(self) -> None:
        """Test that longer format names are matched before shorter ones."""
        # blockchain_test_engine should match before blockchain_test.
        nodeid = "tests/test.py::test[fork_Osaka-blockchain_test_engine]"
        expected = "tests/test.py::test[fork_Osaka]"
        result = strip_fixture_format_from_nodeid(nodeid)
        assert result == expected
        # Verify it didn't partially match blockchain_test.
        assert "blockchain_test" not in result


class TestGetAllFixtureFormatNames:
    """Test cases for get_all_fixture_format_names function."""

    def test_returns_tuple(self) -> None:
        """Test that function returns a tuple (hashable for lru_cache)."""
        result = get_all_fixture_format_names()
        assert isinstance(result, tuple)

    def test_contains_known_formats(self) -> None:
        """Test that common fixture formats are included."""
        formats = get_all_fixture_format_names()
        assert "blockchain_test" in formats
        assert "state_test" in formats

    def test_sorted_by_length_descending(self) -> None:
        """Test that formats are sorted by length (longest first)."""
        formats = get_all_fixture_format_names()
        lengths = [len(f) for f in formats]
        assert lengths == sorted(lengths, reverse=True)

    def test_blockchain_test_engine_before_blockchain_test(self) -> None:
        """Test that longer names come before their prefixes."""
        formats = get_all_fixture_format_names()
        # blockchain_test_engine is longer and should come first.
        if "blockchain_test_engine" in formats and "blockchain_test" in formats:
            idx_engine = formats.index("blockchain_test_engine")
            idx_bt = formats.index("blockchain_test")
            assert idx_engine < idx_bt


class TestCacheKeyConsistency:
    """Test that cache keys are consistent across fixture formats."""

    @pytest.mark.parametrize(
        "format_name",
        [
            "blockchain_test",
            "blockchain_test_engine",
            "state_test",
            "blockchain_test_from_state_test",
            "blockchain_test_engine_from_state_test",
        ],
    )
    def test_format_stripping_produces_consistent_key(
        self, format_name: str
    ) -> None:
        """Test that all format variants produce the same base key."""
        base = "tests/test.py::test_case[fork_Osaka-param1]"
        nodeid = f"tests/test.py::test_case[fork_Osaka-{format_name}-param1]"

        result = strip_fixture_format_from_nodeid(nodeid)
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
