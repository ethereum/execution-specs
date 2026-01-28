"""Test cases for the execution_testing.fixtures.collector module."""

import json
from pathlib import Path

import pytest

from ..collector import FixtureCollector, TestInfo
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


class TestPreSerialization:
    """Tests for the pre-serialization optimization in FixtureCollector."""

    def test_add_fixture_populates_pre_serialized(
        self, output_dir: Path, filler_path: Path, module_path: Path
    ) -> None:
        """
        add_fixture() stores a pre-serialized JSON string for each fixture.
        """
        collector = FixtureCollector(
            output_dir=output_dir,
            fill_static_tests=False,
            single_fixture_per_file=False,
            filler_path=filler_path,
            generate_index=False,
        )
        fixture = _make_fixture(1)
        info = _make_info("tx_test", module_path)
        collector.add_fixture(info, fixture)

        fixture_id = info.get_id()
        assert fixture_id in collector._pre_serialized
        # The pre-serialized string must be valid JSON matching the fixture
        parsed = json.loads(collector._pre_serialized[fixture_id])
        assert parsed == fixture.json_dict_with_info()

    def test_dump_fixtures_clears_pre_serialized(
        self, output_dir: Path, filler_path: Path, module_path: Path
    ) -> None:
        """dump_fixtures() clears _pre_serialized alongside all_fixtures."""
        collector = FixtureCollector(
            output_dir=output_dir,
            fill_static_tests=False,
            single_fixture_per_file=False,
            filler_path=filler_path,
            generate_index=False,
        )
        fixture = _make_fixture(1)
        info = _make_info("tx_test", module_path)
        collector.add_fixture(info, fixture)

        assert len(collector._pre_serialized) == 1
        collector.dump_fixtures()
        assert len(collector._pre_serialized) == 0
        assert len(collector.all_fixtures) == 0


class TestWriteFixtureFile:
    """Tests for _write_fixture_file output format correctness."""

    def test_single_fixture_matches_json_dumps(
        self, output_dir: Path, filler_path: Path, module_path: Path
    ) -> None:
        """Output for a single fixture must match json.dumps(..., indent=4)."""
        collector = FixtureCollector(
            output_dir=output_dir,
            fill_static_tests=False,
            single_fixture_per_file=False,
            filler_path=filler_path,
            generate_index=False,
        )
        fixture = _make_fixture(1)
        info = _make_info("tx_test", module_path)
        collector.add_fixture(info, fixture)
        collector.dump_fixtures()

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
            fill_static_tests=False,
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

        json_files = list(output_dir.rglob("*.json"))
        assert len(json_files) == 1
        written = json_files[0].read_text()

        expected_dict = {
            info.get_id(): fixture.json_dict_with_info()
            for info, fixture in fixtures_and_infos
        }
        expected = json.dumps(dict(sorted(expected_dict.items())), indent=4)
        assert written == expected

    def test_flush_then_append_matches_json_dumps(
        self, output_dir: Path, filler_path: Path, module_path: Path
    ) -> None:
        """
        When flush_interval triggers a mid-run dump, subsequent fixtures
        appended to the same file must produce output matching json.dumps.
        """
        collector = FixtureCollector(
            output_dir=output_dir,
            fill_static_tests=False,
            single_fixture_per_file=False,
            filler_path=filler_path,
            flush_interval=2,
            generate_index=False,
        )
        all_pairs = []
        # Add 3 fixtures — the 2nd add triggers a flush, then a 3rd is added
        for i in range(3):
            fixture = _make_fixture(i)
            info = _make_info(f"tx_test_{i}", module_path)
            collector.add_fixture(info, fixture)
            all_pairs.append((info, fixture))

        # Final dump for remaining fixtures
        collector.dump_fixtures()

        json_files = list(output_dir.rglob("*.json"))
        assert len(json_files) == 1
        written = json_files[0].read_text()

        expected_dict = {
            info.get_id(): fixture.json_dict_with_info()
            for info, fixture in all_pairs
        }
        expected = json.dumps(dict(sorted(expected_dict.items())), indent=4)
        assert written == expected

    def test_output_is_valid_json(
        self, output_dir: Path, filler_path: Path, module_path: Path
    ) -> None:
        """The written file must be parseable as valid JSON."""
        collector = FixtureCollector(
            output_dir=output_dir,
            fill_static_tests=False,
            single_fixture_per_file=False,
            filler_path=filler_path,
            generate_index=False,
        )
        for i in range(3):
            fixture = _make_fixture(i)
            info = _make_info(f"tx_test_{i}", module_path)
            collector.add_fixture(info, fixture)

        collector.dump_fixtures()

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
            fill_static_tests=False,
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

        json_files = list(output_dir.rglob("*.json"))
        assert len(json_files) == 1
        content = json_files[0].read_text()
        parsed = json.loads(content)
        keys = list(parsed.keys())
        assert keys == sorted(keys)


class TestExtractEntriesFromFile:
    """Tests for _extract_entries_from_file to avoid re-serialization."""

    def test_extract_preserves_json_format(
        self, output_dir: Path, filler_path: Path, module_path: Path
    ) -> None:
        """Extracted entries produce identical output when re-written."""
        collector = FixtureCollector(
            output_dir=output_dir,
            fill_static_tests=False,
            single_fixture_per_file=False,
            filler_path=filler_path,
            generate_index=False,
        )
        # Write initial fixtures
        for i in range(3):
            fixture = _make_fixture(i)
            info = _make_info(f"tx_test_{i}", module_path)
            collector.add_fixture(info, fixture)
        collector.dump_fixtures()

        json_files = list(output_dir.rglob("*.json"))

        # Extract and verify the entries match what json.dumps would produce
        extracted = collector._extract_entries_from_file(json_files[0])
        assert len(extracted) == 3

        for _, value_str in extracted.items():
            # Each extracted value should be valid JSON
            parsed = json.loads(value_str)
            # And should match json.dumps with indent=4
            expected = json.dumps(parsed, indent=4)
            assert value_str == expected

    def test_extract_then_write_is_identical(
        self, output_dir: Path, filler_path: Path, module_path: Path
    ) -> None:
        """
        Simulates xdist: worker A writes, worker B reads and adds more.
        Final output should match json.dumps of all fixtures.
        """
        collector1 = FixtureCollector(
            output_dir=output_dir,
            fill_static_tests=False,
            single_fixture_per_file=False,
            filler_path=filler_path,
            generate_index=False,
        )
        # Worker A writes fixtures 0-2
        pairs_a = []
        for i in range(3):
            fixture = _make_fixture(i)
            info = _make_info(f"tx_test_{i}", module_path)
            collector1.add_fixture(info, fixture)
            pairs_a.append((info, fixture))
        collector1.dump_fixtures()

        # Worker B writes fixtures 3-5 to the same file
        collector2 = FixtureCollector(
            output_dir=output_dir,
            fill_static_tests=False,
            single_fixture_per_file=False,
            filler_path=filler_path,
            generate_index=False,
        )
        pairs_b = []
        for i in range(3, 6):
            fixture = _make_fixture(i)
            info = _make_info(f"tx_test_{i}", module_path)
            collector2.add_fixture(info, fixture)
            pairs_b.append((info, fixture))
        collector2.dump_fixtures()

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
