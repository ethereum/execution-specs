"""Unit tests for the FillingSession class."""

from pathlib import Path
from unittest.mock import patch

import pytest

from ethereum_test_base_types import Alloc
from ethereum_test_fixtures import (
    FixtureFillingPhase,
    PreAllocGroup,
    PreAllocGroups,
)
from ethereum_test_forks import Prague
from ethereum_test_types import Environment

from ..filler import FillingSession


class MockConfig:
    """Mock pytest config for testing."""

    def __init__(self, **options):
        """Initialize with option values."""
        self._options = options
        self.op_mode = "fill"  # Default operation mode

    def getoption(self, name, default=None):
        """Mock getoption method."""
        return self._options.get(name, default)


class MockFixtureOutput:
    """Mock fixture output for testing."""

    def __init__(self, pre_alloc_folder_exists=True):
        """Initialize with test conditions."""
        self._folder_exists = pre_alloc_folder_exists
        self.pre_alloc_groups_folder_path = Path("/tmp/test_pre_alloc")

    @classmethod
    def from_config(cls, config):
        """Mock factory method."""
        return cls()


class TestFillingSession:
    """Test cases for FillingSession class."""

    def test_init_normal_fill(self):
        """Test initialization for normal single-phase fill."""
        config = MockConfig()

        with patch("pytest_plugins.filler.filler.FixtureOutput", MockFixtureOutput):
            session = FillingSession.from_config(config)

        assert session.phase_manager.is_single_phase_fill
        assert session.pre_alloc_groups is None

    def test_init_pre_alloc_generation(self):
        """Test initialization for pre-alloc generation phase."""
        config = MockConfig(generate_pre_alloc_groups=True)

        with patch("pytest_plugins.filler.filler.FixtureOutput", MockFixtureOutput):
            session = FillingSession.from_config(config)

        assert session.phase_manager.is_pre_alloc_generation
        assert session.pre_alloc_groups is not None
        assert len(session.pre_alloc_groups.root) == 0

    def test_init_use_pre_alloc(self):
        """Test initialization for phase 2 (using pre-alloc groups)."""
        config = MockConfig(use_pre_alloc_groups=True)

        # Mock the file system operations
        test_group = PreAllocGroup(
            pre=Alloc().model_dump(mode="json"),
            environment=Environment().model_dump(mode="json"),
            network=Prague.name(),
        )
        mock_groups = PreAllocGroups(root={"test_hash": test_group})

        with patch("pytest_plugins.filler.filler.FixtureOutput", MockFixtureOutput):
            with patch.object(Path, "exists", return_value=True):
                with patch.object(PreAllocGroups, "from_folder", return_value=mock_groups):
                    session = FillingSession.from_config(config)

        assert session.phase_manager.is_fill_after_pre_alloc
        assert session.pre_alloc_groups is mock_groups

    def test_init_use_pre_alloc_missing_folder(self):
        """Test initialization fails when pre-alloc folder is missing."""
        config = MockConfig(use_pre_alloc_groups=True)

        with patch("pytest_plugins.filler.filler.FixtureOutput", MockFixtureOutput):
            with patch.object(Path, "exists", return_value=False):
                with pytest.raises(
                    FileNotFoundError, match="Pre-allocation groups folder not found"
                ):
                    FillingSession.from_config(config)

    def test_should_generate_format(self):
        """Test format generation decision."""
        config = MockConfig()

        with patch("pytest_plugins.filler.filler.FixtureOutput", MockFixtureOutput):
            session = FillingSession.from_config(config)

        # Mock fixture format
        class MockFormat:
            format_phases = {FixtureFillingPhase.FILL}

        assert session.should_generate_format(MockFormat())

    def test_should_generate_format_with_generate_all(self):
        """Test format generation with generate_all_formats flag."""
        config = MockConfig(generate_all_formats=True, use_pre_alloc_groups=True)

        mock_groups = PreAllocGroups(root={})

        with patch("pytest_plugins.filler.filler.FixtureOutput", MockFixtureOutput):
            with patch.object(Path, "exists", return_value=True):
                with patch.object(PreAllocGroups, "from_folder", return_value=mock_groups):
                    session = FillingSession.from_config(config)

        # Mock fixture format that normally wouldn't generate in phase 2
        class MockFormat:
            format_phases = {FixtureFillingPhase.FILL}

        # Should generate because generate_all=True
        assert session.should_generate_format(MockFormat())

    def test_get_pre_alloc_group(self):
        """Test getting a pre-alloc group by hash."""
        config = MockConfig(use_pre_alloc_groups=True)

        test_group = PreAllocGroup(
            pre=Alloc().model_dump(mode="json"),
            environment=Environment().model_dump(mode="json"),
            network=Prague.name(),
        )
        mock_groups = PreAllocGroups(root={"test_hash": test_group})

        with patch("pytest_plugins.filler.filler.FixtureOutput", MockFixtureOutput):
            with patch.object(Path, "exists", return_value=True):
                with patch.object(PreAllocGroups, "from_folder", return_value=mock_groups):
                    session = FillingSession.from_config(config)

        assert session.get_pre_alloc_group("test_hash") is test_group

    def test_get_pre_alloc_group_not_found(self):
        """Test getting a non-existent pre-alloc group."""
        config = MockConfig(use_pre_alloc_groups=True)

        mock_groups = PreAllocGroups(root={})

        with patch("pytest_plugins.filler.filler.FixtureOutput", MockFixtureOutput):
            with patch.object(Path, "exists", return_value=True):
                with patch.object(PreAllocGroups, "from_folder", return_value=mock_groups):
                    session = FillingSession.from_config(config)

        with pytest.raises(ValueError, match="Pre-allocation hash .* not found"):
            session.get_pre_alloc_group("missing_hash")

    def test_get_pre_alloc_group_not_initialized(self):
        """Test getting pre-alloc group when not initialized."""
        config = MockConfig()  # Normal fill, no pre-alloc groups

        with patch("pytest_plugins.filler.filler.FixtureOutput", MockFixtureOutput):
            session = FillingSession.from_config(config)

        with pytest.raises(ValueError, match="Pre-allocation groups not initialized"):
            session.get_pre_alloc_group("any_hash")

    def test_update_pre_alloc_group(self):
        """Test updating a pre-alloc group."""
        config = MockConfig(generate_pre_alloc_groups=True)

        with patch("pytest_plugins.filler.filler.FixtureOutput", MockFixtureOutput):
            session = FillingSession.from_config(config)

        test_group = PreAllocGroup(
            pre=Alloc().model_dump(mode="json"),
            environment=Environment().model_dump(mode="json"),
            network=Prague.name(),
        )
        session.update_pre_alloc_group("test_hash", test_group)

        assert "test_hash" in session.pre_alloc_groups
        assert session.pre_alloc_groups["test_hash"] is test_group

    def test_update_pre_alloc_group_wrong_phase(self):
        """Test updating pre-alloc group in wrong phase."""
        config = MockConfig()  # Normal fill

        with patch("pytest_plugins.filler.filler.FixtureOutput", MockFixtureOutput):
            session = FillingSession.from_config(config)

        test_group = PreAllocGroup(
            pre=Alloc().model_dump(mode="json"),
            environment=Environment().model_dump(mode="json"),
            network=Prague.name(),
        )
        with pytest.raises(
            ValueError, match="Can only update pre-alloc groups in generation phase"
        ):
            session.update_pre_alloc_group("test_hash", test_group)

    def test_save_pre_alloc_groups(self):
        """Test saving pre-alloc groups to disk."""
        config = MockConfig(generate_pre_alloc_groups=True)

        with patch("pytest_plugins.filler.filler.FixtureOutput", MockFixtureOutput):
            session = FillingSession.from_config(config)

        # Add a test group
        test_group = PreAllocGroup(
            pre=Alloc().model_dump(mode="json"),
            environment=Environment().model_dump(mode="json"),
            network=Prague.name(),
        )
        session.update_pre_alloc_group("test_hash", test_group)

        # Mock file operations
        with patch.object(Path, "mkdir") as mock_mkdir:
            with patch.object(PreAllocGroups, "to_folder") as mock_to_folder:
                session.save_pre_alloc_groups()

        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_to_folder.assert_called_once()

    def test_save_pre_alloc_groups_none(self):
        """Test saving when no pre-alloc groups exist."""
        config = MockConfig()  # Normal fill

        with patch("pytest_plugins.filler.filler.FixtureOutput", MockFixtureOutput):
            session = FillingSession.from_config(config)

        # Should not raise, just return
        session.save_pre_alloc_groups()

    def test_aggregate_pre_alloc_groups(self):
        """Test aggregating pre-alloc groups from workers (xdist)."""
        config = MockConfig(generate_pre_alloc_groups=True)

        with patch("pytest_plugins.filler.filler.FixtureOutput", MockFixtureOutput):
            session = FillingSession.from_config(config)

        # Worker groups to aggregate
        group1 = PreAllocGroup(
            pre=Alloc().model_dump(mode="json"),
            environment=Environment().model_dump(mode="json"),
            network=Prague.name(),
        )
        group2 = PreAllocGroup(
            pre=Alloc().model_dump(mode="json"),
            environment=Environment().model_dump(mode="json"),
            network=Prague.name(),
        )
        worker_groups = PreAllocGroups(root={"hash1": group1, "hash2": group2})

        session.aggregate_pre_alloc_groups(worker_groups)

        assert "hash1" in session.pre_alloc_groups
        assert "hash2" in session.pre_alloc_groups

    def test_aggregate_pre_alloc_groups_conflict(self):
        """Test aggregating conflicting pre-alloc groups."""
        config = MockConfig(generate_pre_alloc_groups=True)

        with patch("pytest_plugins.filler.filler.FixtureOutput", MockFixtureOutput):
            session = FillingSession.from_config(config)

        # Add initial group
        alloc1 = Alloc().model_dump(mode="json")
        group1 = PreAllocGroup(
            pre=alloc1,
            environment=Environment().model_dump(mode="json"),
            network=Prague.name(),
        )
        session.update_pre_alloc_group("hash1", group1)

        # Try to aggregate conflicting group with same hash but different pre
        alloc2_dict = Alloc().model_dump(mode="json")
        alloc2_dict["0x1234567890123456789012345678901234567890"] = None  # Make it different
        group2 = PreAllocGroup(
            pre=alloc2_dict,
            environment=Environment().model_dump(mode="json"),
            network=Prague.name(),
        )
        worker_groups = PreAllocGroups(root={"hash1": group2})

        with pytest.raises(ValueError, match="Conflicting pre-alloc groups"):
            session.aggregate_pre_alloc_groups(worker_groups)
