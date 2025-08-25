"""Test the --generate-all-formats functionality."""

from pytest_plugins.filler.fixture_output import FixtureOutput


def test_fixture_output_with_generate_all_formats():
    """Test that FixtureOutput properly handles the should_generate_all_formats parameter."""
    # Test with should_generate_all_formats=True
    fixture_output = FixtureOutput(
        output_path="/tmp/test",
        should_generate_all_formats=True,
    )
    assert fixture_output.should_generate_all_formats is True

    # Test with should_generate_all_formats=False (default)
    fixture_output = FixtureOutput(
        output_path="/tmp/test",
    )
    assert fixture_output.should_generate_all_formats is False


def test_fixture_output_from_config_includes_generate_all_formats():
    """Test that FixtureOutput.from_config includes the should_generate_all_formats option."""

    # Mock pytest config object
    class MockConfig:
        def getoption(self, option):
            option_values = {
                "output": "/tmp/test",
                "single_fixture_per_file": False,
                "clean": False,
                "generate_pre_alloc_groups": False,
                "use_pre_alloc_groups": False,
                "generate_all_formats": True,  # Test the new option
            }
            return option_values.get(option, False)

    config = MockConfig()
    fixture_output = FixtureOutput.from_config(config)

    assert fixture_output.should_generate_all_formats is True
    assert fixture_output.output_path.name == "test"


def test_tarball_output_auto_enables_generate_all_formats():
    """Test that tarball output (.tar.gz) automatically enables should_generate_all_formats."""

    # Mock pytest config object with tarball output
    class MockConfig:
        def getoption(self, option):
            option_values = {
                "output": "/tmp/fixtures.tar.gz",  # Tarball output
                "single_fixture_per_file": False,
                "clean": False,
                "generate_pre_alloc_groups": False,
                "use_pre_alloc_groups": False,
                "generate_all_formats": False,  # Explicitly False
            }
            return option_values.get(option, False)

    config = MockConfig()
    fixture_output = FixtureOutput.from_config(config)

    # Should auto-enable should_generate_all_formats due to tarball output
    assert fixture_output.should_generate_all_formats is True
    assert fixture_output.is_tarball is True


def test_regular_output_does_not_auto_enable_generate_all_formats():
    """Test that regular directory output doesn't auto-enable should_generate_all_formats."""

    # Mock pytest config object with regular output
    class MockConfig:
        def getoption(self, option):
            option_values = {
                "output": "/tmp/fixtures",  # Regular directory output
                "single_fixture_per_file": False,
                "clean": False,
                "generate_pre_alloc_groups": False,
                "use_pre_alloc_groups": False,
                "generate_all_formats": False,  # Explicitly False
            }
            return option_values.get(option, False)

    config = MockConfig()
    fixture_output = FixtureOutput.from_config(config)

    # Should remain False for regular directory output
    assert fixture_output.should_generate_all_formats is False
    assert fixture_output.is_tarball is False


def test_explicit_generate_all_formats_overrides_tarball_auto_enable():
    """Test that explicitly setting should_generate_all_formats=True works with tarball output."""

    # Mock pytest config object with tarball output and explicit flag
    class MockConfig:
        def getoption(self, option):
            option_values = {
                "output": "/tmp/fixtures.tar.gz",  # Tarball output
                "single_fixture_per_file": False,
                "clean": False,
                "generate_pre_alloc_groups": False,
                "use_pre_alloc_groups": False,
                "generate_all_formats": True,  # Explicitly True
            }
            return option_values.get(option, False)

    config = MockConfig()
    fixture_output = FixtureOutput.from_config(config)

    # Should be True (both explicitly set and auto-enabled)
    assert fixture_output.should_generate_all_formats is True
    assert fixture_output.is_tarball is True
