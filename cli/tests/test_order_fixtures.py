"""
Tests for the order_fixtures module and click CLI.
"""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from click.testing import CliRunner
from order_fixtures import order_fixtures, process_directory


def create_temp_json_file(directory, name, content):  # noqa: D103
    file_path = directory / name
    with file_path.open("w") as f:
        json.dump(content, f)
    return file_path


@pytest.fixture
def input_output_dirs():
    """
    Create temporary input and output directories
    """
    with TemporaryDirectory() as input_dir, TemporaryDirectory() as output_dir:
        yield Path(input_dir), Path(output_dir)


def test_order_fixture(input_output_dirs):
    """
    Test sorting a single JSON fixture.
    """
    input_dir, output_dir = input_output_dirs
    create_temp_json_file(input_dir, "test.json", {"z": 0, "a": [3, 2, 1]})
    expected_output = {"a": [1, 2, 3], "z": 0}

    process_directory(input_dir, output_dir)

    output_file = output_dir / "test.json"
    assert output_file.exists()

    with output_file.open("r") as f:
        output_content = json.load(f)

    assert output_content == expected_output


def test_cli_invocation(input_output_dirs):
    """
    Test the CLI interface.
    """
    runner = CliRunner()
    input_dir, output_dir = input_output_dirs
    create_temp_json_file(input_dir, "test.json", {"c": 2, "b": [4, 3, 5]})

    result = runner.invoke(
        order_fixtures, ["--input", str(input_dir), "--output", str(output_dir)]
    )

    assert result.exit_code == 0
    assert (output_dir / "test.json").exists()


def test_input_is_file_instead_of_directory():
    """
    Test the CLI interface when the input path is a file, not a directory.
    """
    runner = CliRunner()
    with TemporaryDirectory() as temp_dir:
        temp_file = Path(temp_dir) / "temp_file.txt"
        temp_file.touch()

        result = runner.invoke(order_fixtures, ["--input", str(temp_file), "--output", temp_dir])

        assert result.exit_code != 0
        assert "Error: Invalid value for '--input'" in result.output


def test_input_directory_does_not_exist():
    """
    Test the CLI interface when the input directory does not exist.
    """
    runner = CliRunner()
    with TemporaryDirectory() as temp_dir:
        non_existent_dir = Path(temp_dir) / "nonexistent"

        result = runner.invoke(
            order_fixtures, ["--input", str(non_existent_dir), "--output", temp_dir]
        )

        assert result.exit_code != 0
        assert "Error: Invalid value for '--input'" in result.output
