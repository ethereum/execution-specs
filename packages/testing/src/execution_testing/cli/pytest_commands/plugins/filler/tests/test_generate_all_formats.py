"""Test the --generate-all-formats functionality."""

from typing import Any

from execution_testing.cli.pytest_commands.plugins.shared.fixture_output import (  # noqa: E501
    FixtureOutput,
)


def test_fixture_output_with_generate_all_formats() -> None:
    """
    Test that FixtureOutput properly handles the should_generate_all_formats
    parameter.
    """
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


def test_fixture_output_from_config_includes_generate_all_formats() -> None:
    """
    Test that FixtureOutput.from_config includes the
    should_generate_all_formats option.
    """

    # Mock pytest config object
    class MockConfig:
        def getoption(self, option: str) -> Any:
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
    fixture_output = FixtureOutput.from_config(
        config  # type: ignore
    )

    assert fixture_output.should_generate_all_formats is True
    assert fixture_output.output_path.name == "test"


def test_tarball_output_does_not_auto_enable_generate_all_formats() -> None:
    """
    Test that tarball output (.tar.gz) alone does not enable
    should_generate_all_formats; the flag must be set explicitly.
    """

    class MockConfig:
        def getoption(self, option: str) -> Any:
            option_values = {
                "output": "/tmp/fixtures.tar.gz",
                "single_fixture_per_file": False,
                "clean": False,
                "generate_pre_alloc_groups": False,
                "use_pre_alloc_groups": False,
                "generate_all_formats": False,
            }
            return option_values.get(option, False)

    config = MockConfig()
    fixture_output = FixtureOutput.from_config(
        config  # type: ignore
    )

    assert fixture_output.should_generate_all_formats is False
    assert fixture_output.is_tarball is True


def test_regular_output_does_not_auto_enable_generate_all_formats() -> None:
    """
    Test that regular directory output doesn't enable
    should_generate_all_formats without the explicit flag.
    """

    class MockConfig:
        def getoption(self, option: str) -> Any:
            option_values = {
                "output": "/tmp/fixtures",
                "single_fixture_per_file": False,
                "clean": False,
                "generate_pre_alloc_groups": False,
                "use_pre_alloc_groups": False,
                "generate_all_formats": False,
            }
            return option_values.get(option, False)

    config = MockConfig()
    fixture_output = FixtureOutput.from_config(
        config  # type: ignore
    )

    assert fixture_output.should_generate_all_formats is False
    assert fixture_output.is_tarball is False


def test_explicit_generate_all_formats_with_tarball() -> None:
    """
    Test that explicitly setting should_generate_all_formats=True works with
    tarball output.
    """

    class MockConfig:
        def getoption(self, option: str) -> Any:
            option_values = {
                "output": "/tmp/fixtures.tar.gz",
                "single_fixture_per_file": False,
                "clean": False,
                "generate_pre_alloc_groups": False,
                "use_pre_alloc_groups": False,
                "generate_all_formats": True,
            }
            return option_values.get(option, False)

    config = MockConfig()
    fixture_output = FixtureOutput.from_config(
        config  # type: ignore
    )

    assert fixture_output.should_generate_all_formats is True
    assert fixture_output.is_tarball is True
