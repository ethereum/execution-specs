"""
Test the forks plugin.
"""

import configparser
import json
import os
import textwrap
from datetime import datetime
from pathlib import Path

import pytest

from pytest_plugins.test_filler.test_filler import default_output_directory


# flake8: noqa
def get_all_files_in_directory(base_dir):  # noqa: D103
    base_path = Path(base_dir)
    return [f.relative_to(os.getcwd()) for f in base_path.rglob("*") if f.is_file()]


def count_keys_in_fixture(file_path):  # noqa: D103
    with open(file_path, "r") as f:
        data = json.load(f)
        if not isinstance(data, dict):  # Ensure the loaded data is a dictionary
            raise ValueError(
                f"Expected a dictionary in {file_path}, but got {type(data).__name__}."
            )
        return len(data)


test_module_paris = textwrap.dedent(
    """\
    import pytest

    from ethereum_test_tools import Account, Environment, TestAddress, Transaction

    @pytest.mark.valid_from("Paris")
    @pytest.mark.valid_until("Shanghai")
    def test_paris_one(state_test):
        state_test(env=Environment(),
                    pre={TestAddress: Account(balance=1_000_000)}, post={}, tx=Transaction())

    @pytest.mark.valid_from("Paris")
    @pytest.mark.valid_until("Shanghai")
    def test_paris_two(state_test):
        state_test(env=Environment(),
                    pre={TestAddress: Account(balance=1_000_000)}, post={}, tx=Transaction())
    """
)
test_count_paris = 4

test_module_shanghai = textwrap.dedent(
    """\
    import pytest

    from ethereum_test_tools import Account, Environment, TestAddress, Transaction

    @pytest.mark.valid_from("Paris")
    @pytest.mark.valid_until("Shanghai")
    def test_shanghai_one(state_test):
        state_test(env=Environment(),
                    pre={TestAddress: Account(balance=1_000_000)}, post={}, tx=Transaction())

    @pytest.mark.parametrize("x", [1, 2, 3])
    @pytest.mark.valid_from("Paris")
    @pytest.mark.valid_until("Shanghai")
    def test_shanghai_two(state_test, x):
        state_test(env=Environment(),
                    pre={TestAddress: Account(balance=1_000_000)}, post={}, tx=Transaction())
    """
)

test_count_shanghai = 8
total_test_count = test_count_paris + test_count_shanghai


@pytest.mark.parametrize(
    "args, expected_fixture_files, expected_fixture_counts",
    [
        pytest.param(
            [],
            [
                Path("fixtures/blockchain_tests/paris/module_paris/paris_one.json"),
                Path("fixtures/blockchain_tests_hive/paris/module_paris/paris_one.json"),
                Path("fixtures/state_tests/paris/module_paris/paris_one.json"),
                Path("fixtures/blockchain_tests/paris/module_paris/paris_two.json"),
                Path("fixtures/blockchain_tests_hive/paris/module_paris/paris_two.json"),
                Path("fixtures/state_tests/paris/module_paris/paris_two.json"),
                Path("fixtures/blockchain_tests/shanghai/module_shanghai/shanghai_one.json"),
                Path("fixtures/blockchain_tests_hive/shanghai/module_shanghai/shanghai_one.json"),
                Path("fixtures/state_tests/shanghai/module_shanghai/shanghai_one.json"),
                Path("fixtures/blockchain_tests/shanghai/module_shanghai/shanghai_two.json"),
                Path("fixtures/blockchain_tests_hive/shanghai/module_shanghai/shanghai_two.json"),
                Path("fixtures/state_tests/shanghai/module_shanghai/shanghai_two.json"),
            ],
            [2, 2, 2, 2, 2, 2, 2, 2, 2, 6, 6, 6],
            id="default-args",
        ),
        pytest.param(
            ["--build-name", "test_build"],
            [
                Path("fixtures/blockchain_tests/paris/module_paris/paris_one.json"),
                Path("fixtures/blockchain_tests_hive/paris/module_paris/paris_one.json"),
                Path("fixtures/state_tests/paris/module_paris/paris_one.json"),
                Path("fixtures/blockchain_tests/paris/module_paris/paris_two.json"),
                Path("fixtures/blockchain_tests_hive/paris/module_paris/paris_two.json"),
                Path("fixtures/state_tests/paris/module_paris/paris_two.json"),
                Path("fixtures/blockchain_tests/shanghai/module_shanghai/shanghai_one.json"),
                Path("fixtures/blockchain_tests_hive/shanghai/module_shanghai/shanghai_one.json"),
                Path("fixtures/state_tests/shanghai/module_shanghai/shanghai_one.json"),
                Path("fixtures/blockchain_tests/shanghai/module_shanghai/shanghai_two.json"),
                Path("fixtures/blockchain_tests_hive/shanghai/module_shanghai/shanghai_two.json"),
                Path("fixtures/state_tests/shanghai/module_shanghai/shanghai_two.json"),
            ],
            [2, 2, 2, 2, 2, 2, 2, 2, 2, 6, 6, 6],
            id="build-name-in-fixtures-ini-file",
        ),
        pytest.param(
            ["--flat-output"],
            [
                Path("fixtures/blockchain_tests/paris_one.json"),
                Path("fixtures/blockchain_tests_hive/paris_one.json"),
                Path("fixtures/state_tests/paris_one.json"),
                Path("fixtures/blockchain_tests/paris_two.json"),
                Path("fixtures/blockchain_tests_hive/paris_two.json"),
                Path("fixtures/state_tests/paris_two.json"),
                Path("fixtures/blockchain_tests/shanghai_one.json"),
                Path("fixtures/blockchain_tests_hive/shanghai_one.json"),
                Path("fixtures/state_tests/shanghai_one.json"),
                Path("fixtures/blockchain_tests/shanghai_two.json"),
                Path("fixtures/blockchain_tests_hive/shanghai_two.json"),
                Path("fixtures/state_tests/shanghai_two.json"),
            ],
            [2, 2, 2, 2, 2, 2, 2, 2, 2, 6, 6, 6],
            id="flat-output",
        ),
        pytest.param(
            ["--flat-output", "--output", "other_fixtures"],
            [
                Path("other_fixtures/blockchain_tests/paris_one.json"),
                Path("other_fixtures/blockchain_tests_hive/paris_one.json"),
                Path("other_fixtures/state_tests/paris_one.json"),
                Path("other_fixtures/blockchain_tests/paris_two.json"),
                Path("other_fixtures/blockchain_tests_hive/paris_two.json"),
                Path("other_fixtures/state_tests/paris_two.json"),
                Path("other_fixtures/blockchain_tests/shanghai_one.json"),
                Path("other_fixtures/blockchain_tests_hive/shanghai_one.json"),
                Path("other_fixtures/state_tests/shanghai_one.json"),
                Path("other_fixtures/blockchain_tests/shanghai_two.json"),
                Path("other_fixtures/blockchain_tests_hive/shanghai_two.json"),
                Path("other_fixtures/state_tests/shanghai_two.json"),
            ],
            [2, 2, 2, 2, 2, 2, 2, 2, 2, 6, 6, 6],
            id="flat-output_custom-output-dir",
        ),
        pytest.param(
            ["--single-fixture-per-file"],
            [
                Path(
                    "fixtures/blockchain_tests/paris/module_paris/paris_one__fork_Paris_blockchain_test.json"
                ),
                Path(
                    "fixtures/state_tests/paris/module_paris/paris_one__fork_Paris_state_test.json"
                ),
                Path(
                    "fixtures/blockchain_tests_hive/paris/module_paris/paris_one__fork_Paris_blockchain_test_hive.json"
                ),
                Path(
                    "fixtures/blockchain_tests/paris/module_paris/paris_one__fork_Shanghai_blockchain_test.json"
                ),
                Path(
                    "fixtures/state_tests/paris/module_paris/paris_one__fork_Shanghai_state_test.json"
                ),
                Path(
                    "fixtures/blockchain_tests_hive/paris/module_paris/paris_one__fork_Shanghai_blockchain_test_hive.json"
                ),
                Path(
                    "fixtures/blockchain_tests/paris/module_paris/paris_two__fork_Paris_blockchain_test.json"
                ),
                Path(
                    "fixtures/state_tests/paris/module_paris/paris_two__fork_Paris_state_test.json"
                ),
                Path(
                    "fixtures/blockchain_tests_hive/paris/module_paris/paris_two__fork_Paris_blockchain_test_hive.json"
                ),
                Path(
                    "fixtures/blockchain_tests/paris/module_paris/paris_two__fork_Shanghai_blockchain_test.json"
                ),
                Path(
                    "fixtures/state_tests/paris/module_paris/paris_two__fork_Shanghai_state_test.json"
                ),
                Path(
                    "fixtures/blockchain_tests_hive/paris/module_paris/paris_two__fork_Shanghai_blockchain_test_hive.json"
                ),
                Path(
                    "fixtures/blockchain_tests/shanghai/module_shanghai/shanghai_one__fork_Paris_blockchain_test.json"
                ),
                Path(
                    "fixtures/state_tests/shanghai/module_shanghai/shanghai_one__fork_Paris_state_test.json"
                ),
                Path(
                    "fixtures/blockchain_tests_hive/shanghai/module_shanghai/shanghai_one__fork_Paris_blockchain_test_hive.json"
                ),
                Path(
                    "fixtures/blockchain_tests/shanghai/module_shanghai/shanghai_one__fork_Shanghai_blockchain_test.json"
                ),
                Path(
                    "fixtures/state_tests/shanghai/module_shanghai/shanghai_one__fork_Shanghai_state_test.json"
                ),
                Path(
                    "fixtures/blockchain_tests_hive/shanghai/module_shanghai/shanghai_one__fork_Shanghai_blockchain_test_hive.json"
                ),
                Path(
                    "fixtures/blockchain_tests/shanghai/module_shanghai/shanghai_two__fork_Paris_blockchain_test_x_1.json"
                ),
                Path(
                    "fixtures/state_tests/shanghai/module_shanghai/shanghai_two__fork_Paris_state_test_x_1.json"
                ),
                Path(
                    "fixtures/blockchain_tests_hive/shanghai/module_shanghai/shanghai_two__fork_Paris_blockchain_test_hive_x_1.json"
                ),
                Path(
                    "fixtures/blockchain_tests/shanghai/module_shanghai/shanghai_two__fork_Paris_blockchain_test_x_2.json"
                ),
                Path(
                    "fixtures/state_tests/shanghai/module_shanghai/shanghai_two__fork_Paris_state_test_x_2.json"
                ),
                Path(
                    "fixtures/blockchain_tests_hive/shanghai/module_shanghai/shanghai_two__fork_Paris_blockchain_test_hive_x_2.json"
                ),
                Path(
                    "fixtures/blockchain_tests/shanghai/module_shanghai/shanghai_two__fork_Paris_blockchain_test_x_3.json"
                ),
                Path(
                    "fixtures/state_tests/shanghai/module_shanghai/shanghai_two__fork_Paris_state_test_x_3.json"
                ),
                Path(
                    "fixtures/blockchain_tests_hive/shanghai/module_shanghai/shanghai_two__fork_Paris_blockchain_test_hive_x_3.json"
                ),
                Path(
                    "fixtures/blockchain_tests/shanghai/module_shanghai/shanghai_two__fork_Shanghai_blockchain_test_x_1.json"
                ),
                Path(
                    "fixtures/state_tests/shanghai/module_shanghai/shanghai_two__fork_Shanghai_state_test_x_1.json"
                ),
                Path(
                    "fixtures/blockchain_tests_hive/shanghai/module_shanghai/shanghai_two__fork_Shanghai_blockchain_test_hive_x_1.json"
                ),
                Path(
                    "fixtures/blockchain_tests/shanghai/module_shanghai/shanghai_two__fork_Shanghai_blockchain_test_x_2.json"
                ),
                Path(
                    "fixtures/state_tests/shanghai/module_shanghai/shanghai_two__fork_Shanghai_state_test_x_2.json"
                ),
                Path(
                    "fixtures/blockchain_tests_hive/shanghai/module_shanghai/shanghai_two__fork_Shanghai_blockchain_test_hive_x_2.json"
                ),
                Path(
                    "fixtures/blockchain_tests/shanghai/module_shanghai/shanghai_two__fork_Shanghai_blockchain_test_x_3.json"
                ),
                Path(
                    "fixtures/state_tests/shanghai/module_shanghai/shanghai_two__fork_Shanghai_state_test_x_3.json"
                ),
                Path(
                    "fixtures/blockchain_tests_hive/shanghai/module_shanghai/shanghai_two__fork_Shanghai_blockchain_test_hive_x_3.json"
                ),
            ],
            [1] * 36,
            id="single-fixture-per-file",
        ),
        pytest.param(
            ["--single-fixture-per-file", "--output", "other_fixtures"],
            [
                Path(
                    "other_fixtures/blockchain_tests/paris/module_paris/paris_one__fork_Paris_blockchain_test.json"
                ),
                Path(
                    "other_fixtures/state_tests/paris/module_paris/paris_one__fork_Paris_state_test.json"
                ),
                Path(
                    "other_fixtures/blockchain_tests_hive/paris/module_paris/paris_one__fork_Paris_blockchain_test_hive.json"
                ),
                Path(
                    "other_fixtures/blockchain_tests/paris/module_paris/paris_one__fork_Shanghai_blockchain_test.json"
                ),
                Path(
                    "other_fixtures/state_tests/paris/module_paris/paris_one__fork_Shanghai_state_test.json"
                ),
                Path(
                    "other_fixtures/blockchain_tests_hive/paris/module_paris/paris_one__fork_Shanghai_blockchain_test_hive.json"
                ),
                Path(
                    "other_fixtures/blockchain_tests/paris/module_paris/paris_two__fork_Paris_blockchain_test.json"
                ),
                Path(
                    "other_fixtures/state_tests/paris/module_paris/paris_two__fork_Paris_state_test.json"
                ),
                Path(
                    "other_fixtures/blockchain_tests_hive/paris/module_paris/paris_two__fork_Paris_blockchain_test_hive.json"
                ),
                Path(
                    "other_fixtures/blockchain_tests/paris/module_paris/paris_two__fork_Shanghai_blockchain_test.json"
                ),
                Path(
                    "other_fixtures/state_tests/paris/module_paris/paris_two__fork_Shanghai_state_test.json"
                ),
                Path(
                    "other_fixtures/blockchain_tests_hive/paris/module_paris/paris_two__fork_Shanghai_blockchain_test_hive.json"
                ),
                Path(
                    "other_fixtures/blockchain_tests/shanghai/module_shanghai/shanghai_one__fork_Paris_blockchain_test.json"
                ),
                Path(
                    "other_fixtures/state_tests/shanghai/module_shanghai/shanghai_one__fork_Paris_state_test.json"
                ),
                Path(
                    "other_fixtures/blockchain_tests_hive/shanghai/module_shanghai/shanghai_one__fork_Paris_blockchain_test_hive.json"
                ),
                Path(
                    "other_fixtures/blockchain_tests/shanghai/module_shanghai/shanghai_one__fork_Shanghai_blockchain_test.json"
                ),
                Path(
                    "other_fixtures/state_tests/shanghai/module_shanghai/shanghai_one__fork_Shanghai_state_test.json"
                ),
                Path(
                    "other_fixtures/blockchain_tests_hive/shanghai/module_shanghai/shanghai_one__fork_Shanghai_blockchain_test_hive.json"
                ),
                Path(
                    "other_fixtures/blockchain_tests/shanghai/module_shanghai/shanghai_two__fork_Paris_blockchain_test_x_1.json"
                ),
                Path(
                    "other_fixtures/state_tests/shanghai/module_shanghai/shanghai_two__fork_Paris_state_test_x_1.json"
                ),
                Path(
                    "other_fixtures/blockchain_tests_hive/shanghai/module_shanghai/shanghai_two__fork_Paris_blockchain_test_hive_x_1.json"
                ),
                Path(
                    "other_fixtures/blockchain_tests/shanghai/module_shanghai/shanghai_two__fork_Paris_blockchain_test_x_2.json"
                ),
                Path(
                    "other_fixtures/state_tests/shanghai/module_shanghai/shanghai_two__fork_Paris_state_test_x_2.json"
                ),
                Path(
                    "other_fixtures/blockchain_tests_hive/shanghai/module_shanghai/shanghai_two__fork_Paris_blockchain_test_hive_x_2.json"
                ),
                Path(
                    "other_fixtures/blockchain_tests/shanghai/module_shanghai/shanghai_two__fork_Paris_blockchain_test_x_3.json"
                ),
                Path(
                    "other_fixtures/state_tests/shanghai/module_shanghai/shanghai_two__fork_Paris_state_test_x_3.json"
                ),
                Path(
                    "other_fixtures/blockchain_tests_hive/shanghai/module_shanghai/shanghai_two__fork_Paris_blockchain_test_hive_x_3.json"
                ),
                Path(
                    "other_fixtures/blockchain_tests/shanghai/module_shanghai/shanghai_two__fork_Shanghai_blockchain_test_x_1.json"
                ),
                Path(
                    "other_fixtures/state_tests/shanghai/module_shanghai/shanghai_two__fork_Shanghai_state_test_x_1.json"
                ),
                Path(
                    "other_fixtures/blockchain_tests_hive/shanghai/module_shanghai/shanghai_two__fork_Shanghai_blockchain_test_hive_x_1.json"
                ),
                Path(
                    "other_fixtures/blockchain_tests/shanghai/module_shanghai/shanghai_two__fork_Shanghai_blockchain_test_x_2.json"
                ),
                Path(
                    "other_fixtures/state_tests/shanghai/module_shanghai/shanghai_two__fork_Shanghai_state_test_x_2.json"
                ),
                Path(
                    "other_fixtures/blockchain_tests_hive/shanghai/module_shanghai/shanghai_two__fork_Shanghai_blockchain_test_hive_x_2.json"
                ),
                Path(
                    "other_fixtures/blockchain_tests/shanghai/module_shanghai/shanghai_two__fork_Shanghai_blockchain_test_x_3.json"
                ),
                Path(
                    "other_fixtures/state_tests/shanghai/module_shanghai/shanghai_two__fork_Shanghai_state_test_x_3.json"
                ),
                Path(
                    "other_fixtures/blockchain_tests_hive/shanghai/module_shanghai/shanghai_two__fork_Shanghai_blockchain_test_hive_x_3.json"
                ),
            ],
            [1] * 36,
            id="single-fixture-per-file_custom_output_dir",
        ),
        pytest.param(
            ["--flat-output", "--single-fixture-per-file"],
            [
                Path("fixtures/blockchain_tests/paris_one__fork_Paris_blockchain_test.json"),
                Path("fixtures/state_tests/paris_one__fork_Paris_state_test.json"),
                Path(
                    "fixtures/blockchain_tests_hive/paris_one__fork_Paris_blockchain_test_hive.json"
                ),
                Path("fixtures/blockchain_tests/paris_one__fork_Shanghai_blockchain_test.json"),
                Path("fixtures/state_tests/paris_one__fork_Shanghai_state_test.json"),
                Path(
                    "fixtures/blockchain_tests_hive/paris_one__fork_Shanghai_blockchain_test_hive.json"
                ),
                Path("fixtures/blockchain_tests/paris_two__fork_Paris_blockchain_test.json"),
                Path("fixtures/state_tests/paris_two__fork_Paris_state_test.json"),
                Path(
                    "fixtures/blockchain_tests_hive/paris_two__fork_Paris_blockchain_test_hive.json"
                ),
                Path("fixtures/blockchain_tests/paris_two__fork_Shanghai_blockchain_test.json"),
                Path("fixtures/state_tests/paris_two__fork_Shanghai_state_test.json"),
                Path(
                    "fixtures/blockchain_tests_hive/paris_two__fork_Shanghai_blockchain_test_hive.json"
                ),
                Path("fixtures/blockchain_tests/shanghai_one__fork_Paris_blockchain_test.json"),
                Path("fixtures/state_tests/shanghai_one__fork_Paris_state_test.json"),
                Path(
                    "fixtures/blockchain_tests_hive/shanghai_one__fork_Paris_blockchain_test_hive.json"
                ),
                Path("fixtures/blockchain_tests/shanghai_one__fork_Shanghai_blockchain_test.json"),
                Path("fixtures/state_tests/shanghai_one__fork_Shanghai_state_test.json"),
                Path(
                    "fixtures/blockchain_tests_hive/shanghai_one__fork_Shanghai_blockchain_test_hive.json"
                ),
                Path(
                    "fixtures/blockchain_tests/shanghai_two__fork_Paris_blockchain_test_x_1.json"
                ),
                Path("fixtures/state_tests/shanghai_two__fork_Paris_state_test_x_1.json"),
                Path(
                    "fixtures/blockchain_tests_hive/shanghai_two__fork_Paris_blockchain_test_hive_x_1.json"
                ),
                Path(
                    "fixtures/blockchain_tests/shanghai_two__fork_Paris_blockchain_test_x_2.json"
                ),
                Path("fixtures/state_tests/shanghai_two__fork_Paris_state_test_x_2.json"),
                Path(
                    "fixtures/blockchain_tests_hive/shanghai_two__fork_Paris_blockchain_test_hive_x_2.json"
                ),
                Path(
                    "fixtures/blockchain_tests/shanghai_two__fork_Paris_blockchain_test_x_3.json"
                ),
                Path("fixtures/state_tests/shanghai_two__fork_Paris_state_test_x_3.json"),
                Path(
                    "fixtures/blockchain_tests_hive/shanghai_two__fork_Paris_blockchain_test_hive_x_3.json"
                ),
                Path(
                    "fixtures/blockchain_tests/shanghai_two__fork_Shanghai_blockchain_test_x_1.json"
                ),
                Path("fixtures/state_tests/shanghai_two__fork_Shanghai_state_test_x_1.json"),
                Path(
                    "fixtures/blockchain_tests_hive/shanghai_two__fork_Shanghai_blockchain_test_hive_x_1.json"
                ),
                Path(
                    "fixtures/blockchain_tests/shanghai_two__fork_Shanghai_blockchain_test_x_2.json"
                ),
                Path("fixtures/state_tests/shanghai_two__fork_Shanghai_state_test_x_2.json"),
                Path(
                    "fixtures/blockchain_tests_hive/shanghai_two__fork_Shanghai_blockchain_test_hive_x_2.json"
                ),
                Path(
                    "fixtures/blockchain_tests/shanghai_two__fork_Shanghai_blockchain_test_x_3.json"
                ),
                Path("fixtures/state_tests/shanghai_two__fork_Shanghai_state_test_x_3.json"),
                Path(
                    "fixtures/blockchain_tests_hive/shanghai_two__fork_Shanghai_blockchain_test_hive_x_3.json"
                ),
            ],
            [1] * 36,
            id="flat-single-per-file_flat-output",
        ),
    ],
)
def test_fixture_output_based_on_command_line_args(
    testdir, args, expected_fixture_files, expected_fixture_counts
):
    """
    Test:
    - fixture files are created at the expected paths.
    - no other files are present in the output directory.
    - each fixture file contains the expected number of fixtures.

    The modules above generate the following test cases:
        tests/paris/test_module_paris.py::test_paris_one[fork_Paris] PASSED
        tests/paris/test_module_paris.py::test_paris_one[fork_Shanghai] PASSED
        tests/paris/test_module_paris.py::test_paris_two[fork_Paris] PASSED
        tests/paris/test_module_paris.py::test_paris_two[fork_Shanghai] PASSED
        tests/shanghai/test_module_shanghai.py::test_shanghai_one[fork_Paris] PASSED
        tests/shanghai/test_module_shanghai.py::test_shanghai_one[fork_Shanghai] PASSED
        tests/shanghai/test_module_shanghai.py::test_shanghai_two[fork_Paris-x=1] PASSED
        tests/shanghai/test_module_shanghai.py::test_shanghai_two[fork_Paris-x=2] PASSED
        tests/shanghai/test_module_shanghai.py::test_shanghai_two[fork_Paris-x=3] PASSED
        tests/shanghai/test_module_shanghai.py::test_shanghai_two[fork_Shanghai-x=1] PASSED
        tests/shanghai/test_module_shanghai.py::test_shanghai_two[fork_Shanghai-x=2] PASSED
        tests/shanghai/test_module_shanghai.py::test_shanghai_two[fork_Shanghai-x=3] PASSED
    """
    tests_dir = testdir.mkdir("tests")

    paris_tests_dir = tests_dir.mkdir("paris")
    test_module = paris_tests_dir.join("test_module_paris.py")
    test_module.write(test_module_paris)

    shanghai_tests_dir = tests_dir.mkdir("shanghai")
    test_module = shanghai_tests_dir.join("test_module_shanghai.py")
    test_module.write(test_module_shanghai)

    testdir.copy_example(name="pytest.ini")
    args.append("-v")
    args.append("--no-html")
    result = testdir.runpytest(*args)
    result.assert_outcomes(
        passed=total_test_count * 3,
        failed=0,
        skipped=0,
        errors=0,
    )
    if "--output" in args:
        output_dir = Path(args[args.index("--output") + 1]).absolute()
    else:
        output_dir = Path(default_output_directory()).absolute()
    assert output_dir.exists()

    all_files = get_all_files_in_directory(output_dir)

    ini_file = None
    expected_fixtures_ini_filename = "fixtures.ini"
    for file in all_files:
        if file.name == expected_fixtures_ini_filename:
            ini_file = file
            all_files.remove(file)
            break

    for fixture_file, fixture_count in zip(expected_fixture_files, expected_fixture_counts):
        assert fixture_file.exists()
        assert fixture_count == count_keys_in_fixture(fixture_file)

    assert set(all_files) == set(
        expected_fixture_files
    ), f"Unexpected files in directory: {set(all_files) - set(expected_fixture_files)}"

    assert ini_file is not None, f"No {expected_fixtures_ini_filename} file was written"
    config = configparser.ConfigParser()
    config.read(ini_file)

    properties = {key: value for key, value in config.items("fixtures")}
    assert "timestamp" in properties
    timestamp = datetime.fromisoformat(properties["timestamp"])
    assert timestamp.year == datetime.now().year
    if "--build-name" in args:
        assert "build" in properties
        build_name = args[args.index("--build-name") + 1]
        assert properties["build"] == build_name
