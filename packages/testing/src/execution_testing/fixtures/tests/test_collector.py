"""Test cases for the execution_testing.fixtures.collector module."""

import json
from pathlib import Path

import pytest

from ..base import BaseFixture
from ..collector import FixtureCollector, TestInfo, merge_partial_fixture_files
from ..file import Fixtures
from ..transaction import FixtureResult, TransactionFixture


def _make_fixture(nonce: int = 0) -> TransactionFixture:
    """Create a minimal TransactionFixture for testing."""
    fixture = TransactionFixture(
        transaction=f"0x{nonce:04x}",
        result={"Paris": FixtureResult(intrinsic_gas=nonce)},
    )
    fixture.fill_info(
        "t8n-test",
        f"test description {nonce}",
        fixture_source_url="http://example.com",
        ref_spec=None,
        _info_metadata={},
    )
    return fixture


def _make_info(test_id: str, module_path: Path) -> TestInfo:
    """Create a TestInfo for testing."""
    return TestInfo(
        name=f"test_func[fork_Paris-{test_id}]",
        id=f"{module_path}::test_func[fork_Paris-{test_id}]",
        original_name="test_func",
        module_path=module_path,
    )


@pytest.fixture
def output_dir(tmp_path: Path) -> Path:
    """Create output directory for test fixtures."""
    out = tmp_path / "output"
    out.mkdir()
    return out


@pytest.fixture
def filler_path(tmp_path: Path) -> Path:
    """Create a filler path (tests directory root)."""
    p = tmp_path / "tests"
    p.mkdir()
    return p


@pytest.fixture
def module_path(filler_path: Path) -> Path:
    """Create a dummy test module path."""
    mod = filler_path / "cancun" / "test_example.py"
    mod.parent.mkdir(parents=True, exist_ok=True)
    mod.touch()
    return mod


class TestPartialFixtureFiles:
    """Tests for partial fixture file writing and merging."""

    def test_single_fixture_matches_json_dumps(
        self, output_dir: Path, filler_path: Path, module_path: Path
    ) -> None:
        """Output for a single fixture must match json.dumps(..., indent=4)."""
        collector = FixtureCollector(
            output_dir=output_dir,
            single_fixture_per_file=False,
            filler_path=filler_path,
            generate_index=False,
        )
        fixture = _make_fixture(1)
        info = _make_info("tx_test", module_path)
        collector.add_fixture(info, fixture)
        collector.dump_fixtures()
        merge_partial_fixture_files(output_dir)

        # Find the written file
        json_files = list(output_dir.rglob("*.json"))
        assert len(json_files) == 1
        written = json_files[0].read_text()

        # Build expected output using the original json.dumps approach
        fixture_id = info.get_id()
        expected_dict = {fixture_id: fixture.json_dict_with_info()}
        expected = json.dumps(dict(sorted(expected_dict.items())), indent=4)
        assert written == expected

    def test_multiple_fixtures_match_json_dumps(
        self, output_dir: Path, filler_path: Path, module_path: Path
    ) -> None:
        """
        Output for multiple fixtures must match json.dumps(..., indent=4).
        """
        collector = FixtureCollector(
            output_dir=output_dir,
            single_fixture_per_file=False,
            filler_path=filler_path,
            generate_index=False,
        )
        fixtures_and_infos = []
        for i in range(5):
            fixture = _make_fixture(i)
            info = _make_info(f"tx_test_{i}", module_path)
            collector.add_fixture(info, fixture)
            fixtures_and_infos.append((info, fixture))

        collector.dump_fixtures()
        merge_partial_fixture_files(output_dir)

        json_files = list(output_dir.rglob("*.json"))
        assert len(json_files) == 1
        written = json_files[0].read_text()

        expected_dict = {
            info.get_id(): fixture.json_dict_with_info()
            for info, fixture in fixtures_and_infos
        }
        expected = json.dumps(dict(sorted(expected_dict.items())), indent=4)
        assert written == expected

    def test_multiple_workers_merge_correctly(
        self, output_dir: Path, filler_path: Path, module_path: Path
    ) -> None:
        """
        Simulates xdist: worker A and B write partial files, merge at end.
        Final output should match json.dumps of all fixtures.
        """
        collector1 = FixtureCollector(
            output_dir=output_dir,
            single_fixture_per_file=False,
            filler_path=filler_path,
            generate_index=False,
            worker_id="gw0",
        )
        # Worker A writes fixtures 0-2
        pairs_a = []
        for i in range(3):
            fixture = _make_fixture(i)
            info = _make_info(f"tx_test_{i}", module_path)
            collector1.add_fixture(info, fixture)
            pairs_a.append((info, fixture))
        collector1.close_streaming_files()

        # Worker B writes fixtures 3-5 (separate partial file)
        collector2 = FixtureCollector(
            output_dir=output_dir,
            single_fixture_per_file=False,
            filler_path=filler_path,
            generate_index=False,
            worker_id="gw1",
        )
        pairs_b = []
        for i in range(3, 6):
            fixture = _make_fixture(i)
            info = _make_info(f"tx_test_{i}", module_path)
            collector2.add_fixture(info, fixture)
            pairs_b.append((info, fixture))
        collector2.close_streaming_files()

        # Merge at session end
        merge_partial_fixture_files(output_dir)

        # Verify final output matches json.dumps of all 6 fixtures
        json_files = list(output_dir.rglob("*.json"))
        assert len(json_files) == 1
        written = json_files[0].read_text()

        expected_dict = {
            info.get_id(): fixture.json_dict_with_info()
            for info, fixture in pairs_a + pairs_b
        }
        expected = json.dumps(dict(sorted(expected_dict.items())), indent=4)
        assert written == expected

    def test_output_is_valid_json(
        self, output_dir: Path, filler_path: Path, module_path: Path
    ) -> None:
        """The written file must be parseable as valid JSON."""
        collector = FixtureCollector(
            output_dir=output_dir,
            single_fixture_per_file=False,
            filler_path=filler_path,
            generate_index=False,
        )
        for i in range(3):
            fixture = _make_fixture(i)
            info = _make_info(f"tx_test_{i}", module_path)
            collector.add_fixture(info, fixture)

        collector.dump_fixtures()
        merge_partial_fixture_files(output_dir)

        json_files = list(output_dir.rglob("*.json"))
        assert len(json_files) == 1
        parsed = json.loads(json_files[0].read_text())
        assert isinstance(parsed, dict)
        assert len(parsed) == 3

    def test_fixtures_sorted_by_key(
        self, output_dir: Path, filler_path: Path, module_path: Path
    ) -> None:
        """Fixture entries in the output file must be sorted by key."""
        collector = FixtureCollector(
            output_dir=output_dir,
            single_fixture_per_file=False,
            filler_path=filler_path,
            generate_index=False,
        )
        # Add in reverse order
        for i in reversed(range(3)):
            fixture = _make_fixture(i)
            info = _make_info(f"tx_test_{i}", module_path)
            collector.add_fixture(info, fixture)

        collector.dump_fixtures()
        merge_partial_fixture_files(output_dir)

        json_files = list(output_dir.rglob("*.json"))
        assert len(json_files) == 1
        content = json_files[0].read_text()
        parsed = json.loads(content)
        keys = list(parsed.keys())
        assert keys == sorted(keys)

    def test_partial_files_cleaned_up_after_merge(
        self, output_dir: Path, filler_path: Path, module_path: Path
    ) -> None:
        """Partial JSONL files are deleted after merging."""
        collector = FixtureCollector(
            output_dir=output_dir,
            single_fixture_per_file=False,
            filler_path=filler_path,
            generate_index=False,
        )
        fixture = _make_fixture(1)
        info = _make_info("tx_test", module_path)
        collector.add_fixture(info, fixture)
        collector.dump_fixtures()

        # Verify partial file exists before merge
        partial_files = list(output_dir.rglob("*.partial.*.jsonl"))
        assert len(partial_files) == 1

        merge_partial_fixture_files(output_dir)

        # Verify partial file is deleted after merge
        partial_files = list(output_dir.rglob("*.partial.*.jsonl"))
        assert len(partial_files) == 0


class TestLegacyCompatibility:
    """
    Tests verifying the new partial file approach produces byte-identical
    output to the legacy Fixtures.collect_into_file() method.
    """

    def test_single_fixture_matches_legacy(
        self, output_dir: Path, filler_path: Path, module_path: Path
    ) -> None:
        """Single fixture output matches legacy collect_into_file()."""
        fixture: BaseFixture = _make_fixture(1)
        info = _make_info("tx_test", module_path)
        fixture_id = info.get_id()

        # Legacy approach: use Fixtures.collect_into_file()
        legacy_dir = output_dir / "legacy"
        legacy_dir.mkdir()
        legacy_file = legacy_dir / "test.json"
        legacy_fixtures = Fixtures(root={fixture_id: fixture})
        legacy_fixtures.collect_into_file(legacy_file)
        legacy_output = legacy_file.read_text()

        # New approach: use partial files + merge
        new_dir = output_dir / "new"
        new_dir.mkdir()
        collector = FixtureCollector(
            output_dir=new_dir,
            single_fixture_per_file=False,
            filler_path=filler_path,
            generate_index=False,
        )
        collector.add_fixture(info, fixture)
        collector.dump_fixtures()
        merge_partial_fixture_files(new_dir)
        new_files = list(new_dir.rglob("*.json"))
        assert len(new_files) == 1
        new_output = new_files[0].read_text()

        assert new_output == legacy_output

    def test_multiple_fixtures_match_legacy(
        self, output_dir: Path, filler_path: Path, module_path: Path
    ) -> None:
        """Multiple fixtures output matches legacy collect_into_file()."""
        fixtures_dict: dict[str, BaseFixture] = {}
        infos = []
        for i in range(5):
            fixture = _make_fixture(i)
            info = _make_info(f"tx_test_{i}", module_path)
            fixtures_dict[info.get_id()] = fixture
            infos.append(info)

        # Legacy approach
        legacy_dir = output_dir / "legacy"
        legacy_dir.mkdir()
        legacy_file = legacy_dir / "test.json"
        legacy_fixtures = Fixtures(root=fixtures_dict)
        legacy_fixtures.collect_into_file(legacy_file)
        legacy_output = legacy_file.read_text()

        # New approach
        new_dir = output_dir / "new"
        new_dir.mkdir()
        collector = FixtureCollector(
            output_dir=new_dir,
            single_fixture_per_file=False,
            filler_path=filler_path,
            generate_index=False,
        )
        for i, info in enumerate(infos):
            collector.add_fixture(info, list(fixtures_dict.values())[i])
        collector.dump_fixtures()
        merge_partial_fixture_files(new_dir)
        new_files = list(new_dir.rglob("*.json"))
        assert len(new_files) == 1
        new_output = new_files[0].read_text()

        assert new_output == legacy_output

    def test_multiple_workers_match_legacy(
        self, output_dir: Path, filler_path: Path, module_path: Path
    ) -> None:
        """
        Multiple workers writing to same logical file matches legacy output.
        """
        fixtures_dict: dict[str, BaseFixture] = {}
        infos = []
        for i in range(6):
            fixture = _make_fixture(i)
            info = _make_info(f"tx_test_{i}", module_path)
            fixtures_dict[info.get_id()] = fixture
            infos.append(info)

        # Legacy approach: all fixtures in one call
        legacy_dir = output_dir / "legacy"
        legacy_dir.mkdir()
        legacy_file = legacy_dir / "test.json"
        legacy_fixtures = Fixtures(root=fixtures_dict)
        legacy_fixtures.collect_into_file(legacy_file)
        legacy_output = legacy_file.read_text()

        # New approach: simulate 3 workers, each with 2 fixtures
        new_dir = output_dir / "new"
        new_dir.mkdir()
        fixture_values = list(fixtures_dict.values())
        for worker_idx in range(3):
            collector = FixtureCollector(
                output_dir=new_dir,
                single_fixture_per_file=False,
                filler_path=filler_path,
                generate_index=False,
                worker_id=f"gw{worker_idx}",
            )
            start = worker_idx * 2
            for i in range(start, start + 2):
                collector.add_fixture(infos[i], fixture_values[i])
            collector.close_streaming_files()

        merge_partial_fixture_files(new_dir)
        new_files = list(new_dir.rglob("*.json"))
        assert len(new_files) == 1
        new_output = new_files[0].read_text()

        assert new_output == legacy_output

    def test_special_characters_in_keys_match_legacy(
        self, output_dir: Path, filler_path: Path, module_path: Path
    ) -> None:
        """Fixture IDs with special characters produce identical output."""
        # Create fixtures with complex IDs (typical pytest node IDs)
        fixtures_dict: dict[str, BaseFixture] = {}
        infos = []
        complex_ids = [
            "param[fork_Paris-state_test]",
            "param[fork_Shanghai-blockchain_test]",
            'param[value="quoted"]',
            "param[path/with/slashes]",
        ]
        for i, test_id in enumerate(complex_ids):
            fixture = _make_fixture(i)
            info = _make_info(test_id, module_path)
            fixtures_dict[info.get_id()] = fixture
            infos.append(info)

        # Legacy approach
        legacy_dir = output_dir / "legacy"
        legacy_dir.mkdir()
        legacy_file = legacy_dir / "test.json"
        legacy_fixtures = Fixtures(root=fixtures_dict)
        legacy_fixtures.collect_into_file(legacy_file)
        legacy_output = legacy_file.read_text()

        # New approach
        new_dir = output_dir / "new"
        new_dir.mkdir()
        collector = FixtureCollector(
            output_dir=new_dir,
            single_fixture_per_file=False,
            filler_path=filler_path,
            generate_index=False,
        )
        for i, info in enumerate(infos):
            collector.add_fixture(info, list(fixtures_dict.values())[i])
        collector.dump_fixtures()
        merge_partial_fixture_files(new_dir)
        new_files = list(new_dir.rglob("*.json"))
        assert len(new_files) == 1
        new_output = new_files[0].read_text()

        assert new_output == legacy_output


class TestStreamingWrites:
    """
    Tests for the streaming write/merge path.

    Fixtures for the stateful benchmarks reach several gigabytes each. The
    write and merge must therefore never hold a whole fixture in memory, and
    must still produce output byte-identical to `json.dumps`.
    """

    def _make_big_fixture(self, nonce: int, payload_kb: int) -> BaseFixture:
        """A fixture whose JSON is large enough to dwarf any copy budget."""
        fixture = TransactionFixture(
            transaction="0x" + "ab" * (payload_kb * 512),
            result={"Paris": FixtureResult(intrinsic_gas=nonce)},
        )
        fixture.fill_info(
            "t8n-test",
            f"big fixture {nonce}",
            fixture_source_url="http://example.com",
            ref_spec=None,
            _info_metadata={},
        )
        return fixture

    def test_merge_does_not_materialise_the_fixture(
        self, output_dir: Path, filler_path: Path, module_path: Path
    ) -> None:
        """
        Merging must allocate far less than the fixture it merges.

        The previous implementation embedded each fixture as an escaped string
        inside a JSONL envelope, then on merge read that line back, parsed it
        and re-indented it with `.replace()` -- several full-size copies, so
        peak allocation exceeded the document size. This pins the streaming
        behaviour deterministically rather than by timing.
        """
        import tracemalloc

        collector = FixtureCollector(
            output_dir=output_dir,
            single_fixture_per_file=False,
            filler_path=filler_path,
            generate_index=False,
        )
        fixture = self._make_big_fixture(0, payload_kb=4096)
        collector.add_fixture(_make_info("big", module_path), fixture)
        collector.close_streaming_files()

        document_size = sum(
            p.stat().st_size for p in output_dir.rglob("*.fixture.json")
        )
        assert document_size > 4_000_000, (
            "fixture not large enough to be a test"
        )

        tracemalloc.start()
        merge_partial_fixture_files(output_dir)
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Generous: a streaming merge needs a copy chunk plus the index, so
        # well under the document. The old code peaked above document_size.
        assert peak < document_size // 2, (
            f"merge peaked at {peak} bytes for a {document_size}-byte "
            "fixture -- it is not streaming"
        )

    def test_large_fixture_output_matches_json_dumps(
        self, output_dir: Path, filler_path: Path, module_path: Path
    ) -> None:
        """A multi-megabyte fixture must still round-trip byte-identically."""
        collector = FixtureCollector(
            output_dir=output_dir,
            single_fixture_per_file=False,
            filler_path=filler_path,
            generate_index=False,
        )
        fixture = self._make_big_fixture(1, payload_kb=512)
        info = _make_info("big", module_path)
        collector.add_fixture(info, fixture)
        collector.close_streaming_files()
        merge_partial_fixture_files(output_dir)

        written = next(
            p for p in output_dir.rglob("*.json") if ".partial." not in p.name
        ).read_text()
        expected = json.dumps(
            {info.get_id(): fixture.json_dict_with_info()}, indent=4
        )
        assert written == expected

    def test_existing_target_is_folded_in(
        self, output_dir: Path, filler_path: Path, module_path: Path
    ) -> None:
        """
        A second session must accumulate into the existing target file.

        The existing document is folded in by byte range rather than parsed,
        so this also covers `_iter_document_entries` against real output.
        """
        first = _make_fixture(0)
        first_info = _make_info("first", module_path)
        collector = FixtureCollector(
            output_dir=output_dir,
            single_fixture_per_file=False,
            filler_path=filler_path,
            generate_index=False,
        )
        collector.add_fixture(first_info, first)
        collector.close_streaming_files()
        merge_partial_fixture_files(output_dir)

        second = _make_fixture(1)
        second_info = _make_info("second", module_path)
        collector2 = FixtureCollector(
            output_dir=output_dir,
            single_fixture_per_file=False,
            filler_path=filler_path,
            generate_index=False,
        )
        collector2.add_fixture(second_info, second)
        collector2.close_streaming_files()
        merge_partial_fixture_files(output_dir)

        target = next(
            p for p in output_dir.rglob("*.json") if ".partial." not in p.name
        )
        written = target.read_text()
        expected = json.dumps(
            dict(
                sorted(
                    {
                        first_info.get_id(): first.json_dict_with_info(),
                        second_info.get_id(): second.json_dict_with_info(),
                    }.items()
                )
            ),
            indent=4,
        )
        assert written == expected
        assert json.loads(written), "must remain valid JSON"

    def test_part_and_seed_files_are_cleaned_up(
        self, output_dir: Path, filler_path: Path, module_path: Path
    ) -> None:
        """No part, index or seed file may survive a merge."""
        collector = FixtureCollector(
            output_dir=output_dir,
            single_fixture_per_file=False,
            filler_path=filler_path,
            generate_index=False,
        )
        for i in range(3):
            collector.add_fixture(
                _make_info(f"t{i}", module_path), _make_fixture(i)
            )
        collector.close_streaming_files()
        merge_partial_fixture_files(output_dir)

        assert not list(output_dir.rglob("*.fixture.json"))
        assert not list(output_dir.rglob("*.partial.*.jsonl"))
        assert not list(output_dir.rglob("*.seed.json"))
