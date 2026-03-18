"""
Test the filler plugin.
"""

import configparser
import json
import os
import textwrap
from datetime import datetime
from pathlib import Path

import pytest

from execution_testing.test_types import Environment
from execution_testing.client_clis import (
    ExecutionSpecsTransitionTool,
    TransitionTool,
)
from ..filler import default_output_directory


# flake8: noqa
def get_all_files_in_directory(base_dir: str) -> list[Path]:  # noqa: D103
    base_path = Path(base_dir)
    return [
        f.relative_to(os.getcwd()) for f in base_path.rglob("*") if f.is_file()
    ]


def count_keys_in_fixture(file_path: Path) -> int:  # noqa: D103
    with open(file_path, "r") as f:
        data = json.load(f)
        if not isinstance(
            data, dict
        ):  # Ensure the loaded data is a dictionary
            raise ValueError(
                f"Expected a dictionary in {file_path}, but got {type(data).__name__}."
            )
        return len(data)


test_module_paris = textwrap.dedent(
    """\
    import pytest

    from execution_testing import  Account, Environment, TestAddress, Transaction

    @pytest.mark.valid_from("Paris")
    @pytest.mark.valid_until("Shanghai")
    def test_paris_one(state_test) -> None:
        state_test(env=Environment(),
                    pre={TestAddress: Account(balance=1_000_000)}, post={}, tx=Transaction())

    @pytest.mark.valid_from("Paris")
    @pytest.mark.valid_until("Shanghai")
    def test_paris_two(state_test) -> None:
        state_test(env=Environment(),
                    pre={TestAddress: Account(balance=1_000_000)}, post={}, tx=Transaction())
    """
)
test_count_paris = 4

test_module_shanghai = textwrap.dedent(
    """\
    import pytest

    from execution_testing import  Account, Environment, TestAddress, Transaction

    @pytest.mark.valid_from("Paris")
    @pytest.mark.valid_until("Shanghai")
    def test_shanghai_one(state_test) -> None:
        state_test(env=Environment(),
                    pre={TestAddress: Account(balance=1_000_000)}, post={}, tx=Transaction())

    @pytest.mark.parametrize("x", [1, 2, 3])
    @pytest.mark.valid_from("Paris")
    @pytest.mark.valid_until("Shanghai")
    def test_shanghai_two(state_test, x) -> None:
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
                Path(
                    "fixtures/blockchain_tests/for_paris/paris/module_paris/paris_one.json"
                ),
                Path(
                    "fixtures/blockchain_tests/for_shanghai/paris/module_paris/paris_one.json"
                ),
                Path(
                    "fixtures/blockchain_tests_engine/for_paris/paris/module_paris/paris_one.json"
                ),
                Path(
                    "fixtures/blockchain_tests_engine/for_shanghai/paris/module_paris/paris_one.json"
                ),
                Path(
                    "fixtures/state_tests/for_paris/paris/module_paris/paris_one.json"
                ),
                Path(
                    "fixtures/state_tests/for_shanghai/paris/module_paris/paris_one.json"
                ),
                Path(
                    "fixtures/blockchain_tests/for_paris/paris/module_paris/paris_two.json"
                ),
                Path(
                    "fixtures/blockchain_tests/for_shanghai/paris/module_paris/paris_two.json"
                ),
                Path(
                    "fixtures/blockchain_tests_engine/for_paris/paris/module_paris/paris_two.json"
                ),
                Path(
                    "fixtures/blockchain_tests_engine/for_shanghai/paris/module_paris/paris_two.json"
                ),
                Path(
                    "fixtures/state_tests/for_paris/paris/module_paris/paris_two.json"
                ),
                Path(
                    "fixtures/state_tests/for_shanghai/paris/module_paris/paris_two.json"
                ),
                Path(
                    "fixtures/blockchain_tests/for_paris/shanghai/module_shanghai/shanghai_one.json"
                ),
                Path(
                    "fixtures/blockchain_tests/for_shanghai/shanghai/module_shanghai/shanghai_one.json"
                ),
                Path(
                    "fixtures/blockchain_tests_engine/for_paris/shanghai/module_shanghai/shanghai_one.json"
                ),
                Path(
                    "fixtures/blockchain_tests_engine/for_shanghai/shanghai/module_shanghai/shanghai_one.json"
                ),
                Path(
                    "fixtures/state_tests/for_paris/shanghai/module_shanghai/shanghai_one.json"
                ),
                Path(
                    "fixtures/state_tests/for_shanghai/shanghai/module_shanghai/shanghai_one.json"
                ),
                Path(
                    "fixtures/blockchain_tests/for_paris/shanghai/module_shanghai/shanghai_two.json"
                ),
                Path(
                    "fixtures/blockchain_tests/for_shanghai/shanghai/module_shanghai/shanghai_two.json"
                ),
                Path(
                    "fixtures/blockchain_tests_engine/for_paris/shanghai/module_shanghai/shanghai_two.json"
                ),
                Path(
                    "fixtures/blockchain_tests_engine/for_shanghai/shanghai/module_shanghai/shanghai_two.json"
                ),
                Path(
                    "fixtures/state_tests/for_paris/shanghai/module_shanghai/shanghai_two.json"
                ),
                Path(
                    "fixtures/state_tests/for_shanghai/shanghai/module_shanghai/shanghai_two.json"
                ),
            ],
            [
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                3,
                3,
                3,
                3,
                3,
                3,
            ],
            id="default-args",
        ),
        pytest.param(
            ["--skip-index"],
            [
                Path(
                    "fixtures/blockchain_tests/for_paris/paris/module_paris/paris_one.json"
                ),
                Path(
                    "fixtures/blockchain_tests/for_shanghai/paris/module_paris/paris_one.json"
                ),
                Path(
                    "fixtures/blockchain_tests_engine/for_paris/paris/module_paris/paris_one.json"
                ),
                Path(
                    "fixtures/blockchain_tests_engine/for_shanghai/paris/module_paris/paris_one.json"
                ),
                Path(
                    "fixtures/state_tests/for_paris/paris/module_paris/paris_one.json"
                ),
                Path(
                    "fixtures/state_tests/for_shanghai/paris/module_paris/paris_one.json"
                ),
                Path(
                    "fixtures/blockchain_tests/for_paris/paris/module_paris/paris_two.json"
                ),
                Path(
                    "fixtures/blockchain_tests/for_shanghai/paris/module_paris/paris_two.json"
                ),
                Path(
                    "fixtures/blockchain_tests_engine/for_paris/paris/module_paris/paris_two.json"
                ),
                Path(
                    "fixtures/blockchain_tests_engine/for_shanghai/paris/module_paris/paris_two.json"
                ),
                Path(
                    "fixtures/state_tests/for_paris/paris/module_paris/paris_two.json"
                ),
                Path(
                    "fixtures/state_tests/for_shanghai/paris/module_paris/paris_two.json"
                ),
                Path(
                    "fixtures/blockchain_tests/for_paris/shanghai/module_shanghai/shanghai_one.json"
                ),
                Path(
                    "fixtures/blockchain_tests/for_shanghai/shanghai/module_shanghai/shanghai_one.json"
                ),
                Path(
                    "fixtures/blockchain_tests_engine/for_paris/shanghai/module_shanghai/shanghai_one.json"
                ),
                Path(
                    "fixtures/blockchain_tests_engine/for_shanghai/shanghai/module_shanghai/shanghai_one.json"
                ),
                Path(
                    "fixtures/state_tests/for_paris/shanghai/module_shanghai/shanghai_one.json"
                ),
                Path(
                    "fixtures/state_tests/for_shanghai/shanghai/module_shanghai/shanghai_one.json"
                ),
                Path(
                    "fixtures/blockchain_tests/for_paris/shanghai/module_shanghai/shanghai_two.json"
                ),
                Path(
                    "fixtures/blockchain_tests/for_shanghai/shanghai/module_shanghai/shanghai_two.json"
                ),
                Path(
                    "fixtures/blockchain_tests_engine/for_paris/shanghai/module_shanghai/shanghai_two.json"
                ),
                Path(
                    "fixtures/blockchain_tests_engine/for_shanghai/shanghai/module_shanghai/shanghai_two.json"
                ),
                Path(
                    "fixtures/state_tests/for_paris/shanghai/module_shanghai/shanghai_two.json"
                ),
                Path(
                    "fixtures/state_tests/for_shanghai/shanghai/module_shanghai/shanghai_two.json"
                ),
            ],
            [
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                3,
                3,
                3,
                3,
                3,
                3,
            ],
            id="skip-index",
        ),
        pytest.param(
            ["--build-name", "test_build"],
            [
                Path(
                    "fixtures/blockchain_tests/for_paris/paris/module_paris/paris_one.json"
                ),
                Path(
                    "fixtures/blockchain_tests/for_shanghai/paris/module_paris/paris_one.json"
                ),
                Path(
                    "fixtures/blockchain_tests_engine/for_paris/paris/module_paris/paris_one.json"
                ),
                Path(
                    "fixtures/blockchain_tests_engine/for_shanghai/paris/module_paris/paris_one.json"
                ),
                Path(
                    "fixtures/state_tests/for_paris/paris/module_paris/paris_one.json"
                ),
                Path(
                    "fixtures/state_tests/for_shanghai/paris/module_paris/paris_one.json"
                ),
                Path(
                    "fixtures/blockchain_tests/for_paris/paris/module_paris/paris_two.json"
                ),
                Path(
                    "fixtures/blockchain_tests/for_shanghai/paris/module_paris/paris_two.json"
                ),
                Path(
                    "fixtures/blockchain_tests_engine/for_paris/paris/module_paris/paris_two.json"
                ),
                Path(
                    "fixtures/blockchain_tests_engine/for_shanghai/paris/module_paris/paris_two.json"
                ),
                Path(
                    "fixtures/state_tests/for_paris/paris/module_paris/paris_two.json"
                ),
                Path(
                    "fixtures/state_tests/for_shanghai/paris/module_paris/paris_two.json"
                ),
                Path(
                    "fixtures/blockchain_tests/for_paris/shanghai/module_shanghai/shanghai_one.json"
                ),
                Path(
                    "fixtures/blockchain_tests/for_shanghai/shanghai/module_shanghai/shanghai_one.json"
                ),
                Path(
                    "fixtures/blockchain_tests_engine/for_paris/shanghai/module_shanghai/shanghai_one.json"
                ),
                Path(
                    "fixtures/blockchain_tests_engine/for_shanghai/shanghai/module_shanghai/shanghai_one.json"
                ),
                Path(
                    "fixtures/state_tests/for_paris/shanghai/module_shanghai/shanghai_one.json"
                ),
                Path(
                    "fixtures/state_tests/for_shanghai/shanghai/module_shanghai/shanghai_one.json"
                ),
                Path(
                    "fixtures/blockchain_tests/for_paris/shanghai/module_shanghai/shanghai_two.json"
                ),
                Path(
                    "fixtures/blockchain_tests/for_shanghai/shanghai/module_shanghai/shanghai_two.json"
                ),
                Path(
                    "fixtures/blockchain_tests_engine/for_paris/shanghai/module_shanghai/shanghai_two.json"
                ),
                Path(
                    "fixtures/blockchain_tests_engine/for_shanghai/shanghai/module_shanghai/shanghai_two.json"
                ),
                Path(
                    "fixtures/state_tests/for_paris/shanghai/module_shanghai/shanghai_two.json"
                ),
                Path(
                    "fixtures/state_tests/for_shanghai/shanghai/module_shanghai/shanghai_two.json"
                ),
            ],
            [
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                3,
                3,
                3,
                3,
                3,
                3,
            ],
            id="build-name-in-fixtures-ini-file",
        ),
        pytest.param(
            ["--single-fixture-per-file"],
            [
                Path(
                    "fixtures/blockchain_tests/for_paris/paris/module_paris/paris_one__fork_Paris_blockchain_test_from_state_test.json"
                ),
                Path(
                    "fixtures/state_tests/for_paris/paris/module_paris/paris_one__fork_Paris_state_test.json"
                ),
                Path(
                    "fixtures/blockchain_tests_engine/for_paris/paris/module_paris/paris_one__fork_Paris_blockchain_test_engine_from_state_test.json"
                ),
                Path(
                    "fixtures/blockchain_tests/for_shanghai/paris/module_paris/paris_one__fork_Shanghai_blockchain_test_from_state_test.json"
                ),
                Path(
                    "fixtures/state_tests/for_shanghai/paris/module_paris/paris_one__fork_Shanghai_state_test.json"
                ),
                Path(
                    "fixtures/blockchain_tests_engine/for_shanghai/paris/module_paris/paris_one__fork_Shanghai_blockchain_test_engine_from_state_test.json"
                ),
                Path(
                    "fixtures/blockchain_tests/for_paris/paris/module_paris/paris_two__fork_Paris_blockchain_test_from_state_test.json"
                ),
                Path(
                    "fixtures/state_tests/for_paris/paris/module_paris/paris_two__fork_Paris_state_test.json"
                ),
                Path(
                    "fixtures/blockchain_tests_engine/for_paris/paris/module_paris/paris_two__fork_Paris_blockchain_test_engine_from_state_test.json"
                ),
                Path(
                    "fixtures/blockchain_tests/for_shanghai/paris/module_paris/paris_two__fork_Shanghai_blockchain_test_from_state_test.json"
                ),
                Path(
                    "fixtures/state_tests/for_shanghai/paris/module_paris/paris_two__fork_Shanghai_state_test.json"
                ),
                Path(
                    "fixtures/blockchain_tests_engine/for_shanghai/paris/module_paris/paris_two__fork_Shanghai_blockchain_test_engine_from_state_test.json"
                ),
                Path(
                    "fixtures/blockchain_tests/for_paris/shanghai/module_shanghai/shanghai_one__fork_Paris_blockchain_test_from_state_test.json"
                ),
                Path(
                    "fixtures/state_tests/for_paris/shanghai/module_shanghai/shanghai_one__fork_Paris_state_test.json"
                ),
                Path(
                    "fixtures/blockchain_tests_engine/for_paris/shanghai/module_shanghai/shanghai_one__fork_Paris_blockchain_test_engine_from_state_test.json"
                ),
                Path(
                    "fixtures/blockchain_tests/for_shanghai/shanghai/module_shanghai/shanghai_one__fork_Shanghai_blockchain_test_from_state_test.json"
                ),
                Path(
                    "fixtures/state_tests/for_shanghai/shanghai/module_shanghai/shanghai_one__fork_Shanghai_state_test.json"
                ),
                Path(
                    "fixtures/blockchain_tests_engine/for_shanghai/shanghai/module_shanghai/shanghai_one__fork_Shanghai_blockchain_test_engine_from_state_test.json"
                ),
                Path(
                    "fixtures/blockchain_tests/for_paris/shanghai/module_shanghai/shanghai_two__fork_Paris_blockchain_test_from_state_test_x_1.json"
                ),
                Path(
                    "fixtures/state_tests/for_paris/shanghai/module_shanghai/shanghai_two__fork_Paris_state_test_x_1.json"
                ),
                Path(
                    "fixtures/blockchain_tests_engine/for_paris/shanghai/module_shanghai/shanghai_two__fork_Paris_blockchain_test_engine_from_state_test_x_1.json"
                ),
                Path(
                    "fixtures/blockchain_tests/for_paris/shanghai/module_shanghai/shanghai_two__fork_Paris_blockchain_test_from_state_test_x_2.json"
                ),
                Path(
                    "fixtures/state_tests/for_paris/shanghai/module_shanghai/shanghai_two__fork_Paris_state_test_x_2.json"
                ),
                Path(
                    "fixtures/blockchain_tests_engine/for_paris/shanghai/module_shanghai/shanghai_two__fork_Paris_blockchain_test_engine_from_state_test_x_2.json"
                ),
                Path(
                    "fixtures/blockchain_tests/for_paris/shanghai/module_shanghai/shanghai_two__fork_Paris_blockchain_test_from_state_test_x_3.json"
                ),
                Path(
                    "fixtures/state_tests/for_paris/shanghai/module_shanghai/shanghai_two__fork_Paris_state_test_x_3.json"
                ),
                Path(
                    "fixtures/blockchain_tests_engine/for_paris/shanghai/module_shanghai/shanghai_two__fork_Paris_blockchain_test_engine_from_state_test_x_3.json"
                ),
                Path(
                    "fixtures/blockchain_tests/for_shanghai/shanghai/module_shanghai/shanghai_two__fork_Shanghai_blockchain_test_from_state_test_x_1.json"
                ),
                Path(
                    "fixtures/state_tests/for_shanghai/shanghai/module_shanghai/shanghai_two__fork_Shanghai_state_test_x_1.json"
                ),
                Path(
                    "fixtures/blockchain_tests_engine/for_shanghai/shanghai/module_shanghai/shanghai_two__fork_Shanghai_blockchain_test_engine_from_state_test_x_1.json"
                ),
                Path(
                    "fixtures/blockchain_tests/for_shanghai/shanghai/module_shanghai/shanghai_two__fork_Shanghai_blockchain_test_from_state_test_x_2.json"
                ),
                Path(
                    "fixtures/state_tests/for_shanghai/shanghai/module_shanghai/shanghai_two__fork_Shanghai_state_test_x_2.json"
                ),
                Path(
                    "fixtures/blockchain_tests_engine/for_shanghai/shanghai/module_shanghai/shanghai_two__fork_Shanghai_blockchain_test_engine_from_state_test_x_2.json"
                ),
                Path(
                    "fixtures/blockchain_tests/for_shanghai/shanghai/module_shanghai/shanghai_two__fork_Shanghai_blockchain_test_from_state_test_x_3.json"
                ),
                Path(
                    "fixtures/state_tests/for_shanghai/shanghai/module_shanghai/shanghai_two__fork_Shanghai_state_test_x_3.json"
                ),
                Path(
                    "fixtures/blockchain_tests_engine/for_shanghai/shanghai/module_shanghai/shanghai_two__fork_Shanghai_blockchain_test_engine_from_state_test_x_3.json"
                ),
            ],
            [1] * 36,
            id="single-fixture-per-file",
        ),
        pytest.param(
            ["--single-fixture-per-file", "--output", "other_fixtures"],
            [
                Path(
                    "other_fixtures/blockchain_tests/for_paris/paris/module_paris/paris_one__fork_Paris_blockchain_test_from_state_test.json"
                ),
                Path(
                    "other_fixtures/state_tests/for_paris/paris/module_paris/paris_one__fork_Paris_state_test.json"
                ),
                Path(
                    "other_fixtures/blockchain_tests_engine/for_paris/paris/module_paris/paris_one__fork_Paris_blockchain_test_engine_from_state_test.json"
                ),
                Path(
                    "other_fixtures/blockchain_tests/for_shanghai/paris/module_paris/paris_one__fork_Shanghai_blockchain_test_from_state_test.json"
                ),
                Path(
                    "other_fixtures/state_tests/for_shanghai/paris/module_paris/paris_one__fork_Shanghai_state_test.json"
                ),
                Path(
                    "other_fixtures/blockchain_tests_engine/for_shanghai/paris/module_paris/paris_one__fork_Shanghai_blockchain_test_engine_from_state_test.json"
                ),
                Path(
                    "other_fixtures/blockchain_tests/for_paris/paris/module_paris/paris_two__fork_Paris_blockchain_test_from_state_test.json"
                ),
                Path(
                    "other_fixtures/state_tests/for_paris/paris/module_paris/paris_two__fork_Paris_state_test.json"
                ),
                Path(
                    "other_fixtures/blockchain_tests_engine/for_paris/paris/module_paris/paris_two__fork_Paris_blockchain_test_engine_from_state_test.json"
                ),
                Path(
                    "other_fixtures/blockchain_tests/for_shanghai/paris/module_paris/paris_two__fork_Shanghai_blockchain_test_from_state_test.json"
                ),
                Path(
                    "other_fixtures/state_tests/for_shanghai/paris/module_paris/paris_two__fork_Shanghai_state_test.json"
                ),
                Path(
                    "other_fixtures/blockchain_tests_engine/for_shanghai/paris/module_paris/paris_two__fork_Shanghai_blockchain_test_engine_from_state_test.json"
                ),
                Path(
                    "other_fixtures/blockchain_tests/for_paris/shanghai/module_shanghai/shanghai_one__fork_Paris_blockchain_test_from_state_test.json"
                ),
                Path(
                    "other_fixtures/state_tests/for_paris/shanghai/module_shanghai/shanghai_one__fork_Paris_state_test.json"
                ),
                Path(
                    "other_fixtures/blockchain_tests_engine/for_paris/shanghai/module_shanghai/shanghai_one__fork_Paris_blockchain_test_engine_from_state_test.json"
                ),
                Path(
                    "other_fixtures/blockchain_tests/for_shanghai/shanghai/module_shanghai/shanghai_one__fork_Shanghai_blockchain_test_from_state_test.json"
                ),
                Path(
                    "other_fixtures/state_tests/for_shanghai/shanghai/module_shanghai/shanghai_one__fork_Shanghai_state_test.json"
                ),
                Path(
                    "other_fixtures/blockchain_tests_engine/for_shanghai/shanghai/module_shanghai/shanghai_one__fork_Shanghai_blockchain_test_engine_from_state_test.json"
                ),
                Path(
                    "other_fixtures/blockchain_tests/for_paris/shanghai/module_shanghai/shanghai_two__fork_Paris_blockchain_test_from_state_test_x_1.json"
                ),
                Path(
                    "other_fixtures/state_tests/for_paris/shanghai/module_shanghai/shanghai_two__fork_Paris_state_test_x_1.json"
                ),
                Path(
                    "other_fixtures/blockchain_tests_engine/for_paris/shanghai/module_shanghai/shanghai_two__fork_Paris_blockchain_test_engine_from_state_test_x_1.json"
                ),
                Path(
                    "other_fixtures/blockchain_tests/for_paris/shanghai/module_shanghai/shanghai_two__fork_Paris_blockchain_test_from_state_test_x_2.json"
                ),
                Path(
                    "other_fixtures/state_tests/for_paris/shanghai/module_shanghai/shanghai_two__fork_Paris_state_test_x_2.json"
                ),
                Path(
                    "other_fixtures/blockchain_tests_engine/for_paris/shanghai/module_shanghai/shanghai_two__fork_Paris_blockchain_test_engine_from_state_test_x_2.json"
                ),
                Path(
                    "other_fixtures/blockchain_tests/for_paris/shanghai/module_shanghai/shanghai_two__fork_Paris_blockchain_test_from_state_test_x_3.json"
                ),
                Path(
                    "other_fixtures/state_tests/for_paris/shanghai/module_shanghai/shanghai_two__fork_Paris_state_test_x_3.json"
                ),
                Path(
                    "other_fixtures/blockchain_tests_engine/for_paris/shanghai/module_shanghai/shanghai_two__fork_Paris_blockchain_test_engine_from_state_test_x_3.json"
                ),
                Path(
                    "other_fixtures/blockchain_tests/for_shanghai/shanghai/module_shanghai/shanghai_two__fork_Shanghai_blockchain_test_from_state_test_x_1.json"
                ),
                Path(
                    "other_fixtures/state_tests/for_shanghai/shanghai/module_shanghai/shanghai_two__fork_Shanghai_state_test_x_1.json"
                ),
                Path(
                    "other_fixtures/blockchain_tests_engine/for_shanghai/shanghai/module_shanghai/shanghai_two__fork_Shanghai_blockchain_test_engine_from_state_test_x_1.json"
                ),
                Path(
                    "other_fixtures/blockchain_tests/for_shanghai/shanghai/module_shanghai/shanghai_two__fork_Shanghai_blockchain_test_from_state_test_x_2.json"
                ),
                Path(
                    "other_fixtures/state_tests/for_shanghai/shanghai/module_shanghai/shanghai_two__fork_Shanghai_state_test_x_2.json"
                ),
                Path(
                    "other_fixtures/blockchain_tests_engine/for_shanghai/shanghai/module_shanghai/shanghai_two__fork_Shanghai_blockchain_test_engine_from_state_test_x_2.json"
                ),
                Path(
                    "other_fixtures/blockchain_tests/for_shanghai/shanghai/module_shanghai/shanghai_two__fork_Shanghai_blockchain_test_from_state_test_x_3.json"
                ),
                Path(
                    "other_fixtures/state_tests/for_shanghai/shanghai/module_shanghai/shanghai_two__fork_Shanghai_state_test_x_3.json"
                ),
                Path(
                    "other_fixtures/blockchain_tests_engine/for_shanghai/shanghai/module_shanghai/shanghai_two__fork_Shanghai_blockchain_test_engine_from_state_test_x_3.json"
                ),
            ],
            [1] * 36,
            id="single-fixture-per-file_custom_output_dir",
        ),
    ],
)
def test_fixture_output_based_on_command_line_args(
    testdir: pytest.Testdir,
    args: list[str],
    expected_fixture_files: list[Path],
    expected_fixture_counts: list[int],
) -> None:
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

    testdir.copy_example(
        name="src/execution_testing/cli/pytest_commands/pytest_ini_files/pytest-fill.ini"
    )
    args.append("-c")
    args.append("pytest-fill.ini")
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

    all_files = get_all_files_in_directory(str(output_dir))
    meta_dir = os.path.join(output_dir, ".meta")
    assert os.path.exists(meta_dir), f"The directory {meta_dir} does not exist"

    expected_ini_file = "fixtures.ini"
    expected_index_file = "index.json"
    expected_resolver_file = None
    resolver_file = None
    if TransitionTool.default_tool == ExecutionSpecsTransitionTool:
        expected_resolver_file = "eels_resolutions.json"

    ini_file = None
    index_file = None
    for file in all_files:
        if file.name == expected_ini_file:
            ini_file = file
        elif file.name == expected_index_file:
            index_file = file
        elif expected_resolver_file and file.name == expected_resolver_file:
            resolver_file = file
            assert resolver_file.exists(), f"{resolver_file} does not exist"

    expected_additional_files = {expected_ini_file, expected_index_file}
    if resolver_file:
        expected_additional_files.add(str(expected_resolver_file))
    all_fixtures = [
        file
        for file in all_files
        if file.name not in expected_additional_files
    ]
    for fixture_file, fixture_count in zip(
        expected_fixture_files, expected_fixture_counts
    ):
        assert fixture_file.exists(), f"{fixture_file} does not exist"
        assert fixture_count == count_keys_in_fixture(fixture_file), (
            f"Fixture count mismatch for {fixture_file}"
        )

    assert set(all_fixtures) == set(expected_fixture_files), (
        f"Unexpected files in directory: {set(all_fixtures) - set(expected_fixture_files)}"
    )

    assert ini_file is not None, (
        f"No {expected_ini_file} file was found in {meta_dir}"
    )
    config = configparser.ConfigParser()
    ini_file_text = ini_file.read_text()
    # ini_file_text = ini_file_text.replace(default_t8n.server_url, "t8n_server_path")
    config.read_string(ini_file_text)

    if "--skip-index" not in args:
        assert index_file is not None, (
            f"No {expected_index_file} file was found in {meta_dir}"
        )

    properties = {key: value for key, value in config.items("fixtures")}
    assert "timestamp" in properties
    timestamp = datetime.fromisoformat(properties["timestamp"])
    assert timestamp.year == datetime.now().year
    if "--build-name" in args:
        assert "build" in properties
        build_name = args[args.index("--build-name") + 1]
        assert properties["build"] == build_name


test_module_execution_witness = textwrap.dedent(
    """\
    import pytest

    from execution_testing import  Account, Environment, Op, Transaction

    @pytest.mark.valid_at("Amsterdam")
    def test_execution_witness(state_test, pre) -> None:
        contract = pre.deploy_contract(code=Op.SSTORE(0, 1) + Op.STOP)
        state_test(env=Environment(),
                    pre=pre, post={contract: Account(storage={0: 1})},
                    tx=Transaction(to=contract, gas_limit=100_000, sender=pre.fund_eoa()))
    """
)

test_module_execution_witness_soundness = textwrap.dedent(
    """\
    import pytest

    from execution_testing import (
        Account,
        Alloc,
        Block,
        BlockchainTestFiller,
        ExecutionWitnessHeadersExpectation,
        Op,
        Transaction,
    )
    from execution_testing.test_types.execution_witness.modifiers import (
        remove_header_at,
    )

    @pytest.mark.valid_at("Amsterdam")
    def test_execution_witness_soundness(
        pre: Alloc,
        blockchain_test: BlockchainTestFiller,
    ) -> None:
        offset = 2
        contract = pre.deploy_contract(
            code=Op.BLOCKHASH(Op.SUB(Op.NUMBER, offset)) + Op.POP + Op.STOP
        )
        sender = pre.fund_eoa()
        tx = Transaction(sender=sender, to=contract, gas_limit=500_000)

        blocks = [Block(txs=[]) for _ in range(offset)]
        blocks.append(
            Block(
                txs=[tx],
                expected_execution_witness_headers=(
                    ExecutionWitnessHeadersExpectation(
                        expected_count=offset,
                    ).modify(remove_header_at(-1))
                ),
                expected_stateless_validation_success=False,
            )
        )

        blockchain_test(
            pre=pre,
            blocks=blocks,
            post={sender: Account(nonce=1)},
        )
    """
)

test_module_execution_witness_expected_true = textwrap.dedent(
    """\
    import pytest

    from execution_testing import (
        Account,
        Alloc,
        Block,
        BlockchainTestFiller,
        ExecutionWitnessHeadersExpectation,
        Op,
        Transaction,
    )

    @pytest.mark.valid_at("Amsterdam")
    def test_execution_witness_expected_true(
        pre: Alloc,
        blockchain_test: BlockchainTestFiller,
    ) -> None:
        offset = 2
        contract = pre.deploy_contract(
            code=Op.BLOCKHASH(Op.SUB(Op.NUMBER, offset)) + Op.POP + Op.STOP
        )
        sender = pre.fund_eoa()
        tx = Transaction(sender=sender, to=contract, gas_limit=500_000)

        blocks = [Block(txs=[]) for _ in range(offset)]
        blocks.append(
            Block(
                txs=[tx],
                expected_execution_witness_headers=(
                    ExecutionWitnessHeadersExpectation(
                        expected_count=offset,
                    )
                ),
                expected_stateless_validation_success=True,
            )
        )

        blockchain_test(
            pre=pre,
            blocks=blocks,
            post={sender: Account(nonce=1)},
        )
    """
)

test_module_execution_witness_missing_expected = textwrap.dedent(
    """\
    import pytest

    from execution_testing import (
        Account,
        Alloc,
        Block,
        BlockchainTestFiller,
        ExecutionWitnessHeadersExpectation,
        Op,
        Transaction,
    )
    from execution_testing.test_types.execution_witness.modifiers import (
        remove_header_at,
    )

    @pytest.mark.valid_at("Amsterdam")
    def test_execution_witness_missing_expected(
        pre: Alloc,
        blockchain_test: BlockchainTestFiller,
    ) -> None:
        offset = 2
        contract = pre.deploy_contract(
            code=Op.BLOCKHASH(Op.SUB(Op.NUMBER, offset)) + Op.POP + Op.STOP
        )
        sender = pre.fund_eoa()
        tx = Transaction(sender=sender, to=contract, gas_limit=500_000)

        blocks = [Block(txs=[]) for _ in range(offset)]
        blocks.append(
            Block(
                txs=[tx],
                expected_execution_witness_headers=(
                    ExecutionWitnessHeadersExpectation(
                        expected_count=offset,
                    ).modify(remove_header_at(-1))
                ),
            )
        )

        blockchain_test(
            pre=pre,
            blocks=blocks,
            post={sender: Account(nonce=1)},
        )
    """
)


def test_execution_witness_in_blockchain_fixture(
    testdir: pytest.Testdir,
) -> None:
    """
    Fill a minimal Amsterdam state_test that calls a pre-deployed contract,
    then verify the resulting blockchain fixture contains execution witness
    and stateless validation fields.
    """
    tests_dir = testdir.mkdir("tests")
    amsterdam_tests_dir = tests_dir.mkdir("amsterdam")
    test_module = amsterdam_tests_dir.join("test_module_execution_witness.py")
    test_module.write(test_module_execution_witness)

    testdir.copy_example(
        name="src/execution_testing/cli/pytest_commands/pytest_ini_files/pytest-fill.ini"
    )
    args = ["-c", "pytest-fill.ini", "-v", "--until=Amsterdam", "--no-html"]
    result = testdir.runpytest(*args)
    result.assert_outcomes(
        passed=3,
        failed=0,
        skipped=0,
        errors=0,
    )

    output_dir = Path(default_output_directory()).absolute()
    assert output_dir.exists()

    fixture_path = Path(
        "fixtures/blockchain_tests/for_amsterdam/amsterdam/"
        "module_execution_witness/execution_witness.json"
    )
    assert fixture_path.exists(), f"{fixture_path} does not exist"

    with open(fixture_path, "r") as f:
        fixture_data = json.load(f)

    assert len(fixture_data) == 1, "Expected exactly one fixture"
    fixture = next(iter(fixture_data.values()))
    block = fixture["blocks"][0]

    # executionWitness exists with non-empty state, codes, and headers
    assert "executionWitness" in block
    witness = block["executionWitness"]
    assert len(witness["state"]) > 0, "executionWitness.state is empty"
    assert len(witness["codes"]) > 0, "executionWitness.codes is empty"
    assert len(witness["headers"]) > 0, "executionWitness.headers is empty"

    # statelessInputBytes and statelessOutputBytes are non-empty hex strings
    assert "statelessInputBytes" in block
    sib = block["statelessInputBytes"]
    assert isinstance(sib, str) and sib.startswith("0x") and len(sib) > 2

    assert "statelessOutputBytes" in block
    sob = block["statelessOutputBytes"]
    assert isinstance(sob, str) and sob.startswith("0x") and len(sob) > 2

    from ethereum.forks.amsterdam.stateless_host import (
        deserialize_stateless_output,
    )
    from ethereum_types.bytes import Bytes as EthereumBytes

    stateless_output = deserialize_stateless_output(
        EthereumBytes(bytes.fromhex(sob[2:]))
    )
    assert stateless_output.successful_validation is True


def test_execution_witness_expected_true_reuses_canonical_stateless_result(
    testdir: pytest.Testdir,
) -> None:
    """Explicit True expectation should preserve the canonical success path."""
    tests_dir = testdir.mkdir("tests")
    amsterdam_tests_dir = tests_dir.mkdir("amsterdam")
    test_module = amsterdam_tests_dir.join(
        "test_module_execution_witness_expected_true.py"
    )
    test_module.write(test_module_execution_witness_expected_true)

    testdir.copy_example(
        name="src/execution_testing/cli/pytest_commands/pytest_ini_files/pytest-fill.ini"
    )
    args = ["-c", "pytest-fill.ini", "-v", "--until=Amsterdam", "--no-html"]
    result = testdir.runpytest(*args)
    assert result.ret == 0

    fixture_path = Path(
        "fixtures/blockchain_tests/for_amsterdam/amsterdam/"
        "module_execution_witness_expected_true/"
        "execution_witness_expected_true.json"
    )
    assert fixture_path.exists(), f"{fixture_path} does not exist"

    with open(fixture_path, "r") as f:
        fixture_data = json.load(f)

    fixture = next(iter(fixture_data.values()))
    block = fixture["blocks"][-1]

    from ethereum.forks.amsterdam.stateless_host import (
        deserialize_stateless_output,
    )
    from ethereum_types.bytes import Bytes as EthereumBytes

    stateless_output = deserialize_stateless_output(
        EthereumBytes(bytes.fromhex(block["statelessOutputBytes"][2:]))
    )

    assert stateless_output.successful_validation is True


def test_execution_witness_soundness_rewrites_stateless_fixture_bytes(
    testdir: pytest.Testdir,
) -> None:
    """Mutated witness fixtures should carry mutated stateless bytes."""
    tests_dir = testdir.mkdir("tests")
    amsterdam_tests_dir = tests_dir.mkdir("amsterdam")
    test_module = amsterdam_tests_dir.join(
        "test_module_execution_witness_soundness.py"
    )
    test_module.write(test_module_execution_witness_soundness)

    testdir.copy_example(
        name="src/execution_testing/cli/pytest_commands/pytest_ini_files/pytest-fill.ini"
    )
    args = ["-c", "pytest-fill.ini", "-v", "--until=Amsterdam", "--no-html"]
    result = testdir.runpytest(*args)
    assert result.ret == 0

    fixture_path = Path(
        "fixtures/blockchain_tests/for_amsterdam/amsterdam/"
        "module_execution_witness_soundness/"
        "execution_witness_soundness.json"
    )
    assert fixture_path.exists(), f"{fixture_path} does not exist"

    with open(fixture_path, "r") as f:
        fixture_data = json.load(f)

    fixture = next(iter(fixture_data.values()))
    block = fixture["blocks"][-1]

    assert len(block["executionWitness"]["headers"]) == 1

    from ethereum.forks.amsterdam.stateless_guest import (
        deserialize_stateless_input,
    )
    from ethereum.forks.amsterdam.stateless_host import (
        deserialize_stateless_output,
    )
    from ethereum_types.bytes import Bytes as EthereumBytes

    stateless_input = deserialize_stateless_input(
        EthereumBytes(bytes.fromhex(block["statelessInputBytes"][2:]))
    )
    stateless_output = deserialize_stateless_output(
        EthereumBytes(bytes.fromhex(block["statelessOutputBytes"][2:]))
    )

    assert stateless_output.successful_validation is False
    assert len(stateless_input.witness.headers) == 1
    assert [
        "0x" + bytes(header).hex() for header in stateless_input.witness.headers
    ] == block["executionWitness"]["headers"]


def test_execution_witness_modifier_requires_explicit_guest_expectation(
    testdir: pytest.Testdir,
) -> None:
    """Mutated witness tests should declare the expected guest result."""
    tests_dir = testdir.mkdir("tests")
    amsterdam_tests_dir = tests_dir.mkdir("amsterdam")
    test_module = amsterdam_tests_dir.join(
        "test_module_execution_witness_missing_expected.py"
    )
    test_module.write(test_module_execution_witness_missing_expected)

    testdir.copy_example(
        name="src/execution_testing/cli/pytest_commands/pytest_ini_files/pytest-fill.ini"
    )
    args = ["-c", "pytest-fill.ini", "-v", "--until=Amsterdam", "--no-html"]
    result = testdir.runpytest(*args)
    assert result.ret != 0
    result.stdout.fnmatch_lines(
        [
            "*Mutated execution witness tests must set "
            "expected_stateless_validation_success explicitly*"
        ]
    )


test_module_environment_variables = textwrap.dedent(
    """\
    import pytest

    from execution_testing import  Account, Environment, Transaction

    @pytest.mark.parametrize("block_gas_limit", [Environment().gas_limit])
    @pytest.mark.valid_at("Cancun")
    def test_max_gas_limit(state_test, pre, block_gas_limit) -> None:
        env = Environment()
        assert block_gas_limit == {expected_gas_limit}
        tx = Transaction(gas_limit=block_gas_limit, sender=pre.fund_eoa())
        state_test(env=env, pre=pre, post={{}}, tx=tx)
    """
)


@pytest.mark.parametrize(
    "args, expected_fixture_files, expected_fixture_counts, expected_gas_limit",
    [
        pytest.param(
            [],
            [
                Path(
                    "fixtures/state_tests/for_cancun/cancun/module_environment_variables/max_gas_limit.json"
                ),
            ],
            [1],
            Environment().gas_limit,
            id="default-args",
        ),
        pytest.param(
            ["--block-gas-limit", str(Environment().gas_limit * 2)],
            [
                Path(
                    "fixtures/state_tests/for_cancun/cancun/module_environment_variables/max_gas_limit.json"
                ),
            ],
            [1],
            Environment().gas_limit * 2,
            id="higher-gas-limit",
        ),
    ],
)
@pytest.mark.usefixtures("restore_environment_defaults")
def test_fill_variables(
    testdir: pytest.Testdir,
    args: list[str],
    expected_fixture_files: list[Path],
    expected_fixture_counts: list[int],
    expected_gas_limit: int,
) -> None:
    """
    Test filling tests that depend on variables such as the max block gas limit.
    """
    tests_dir = testdir.mkdir("tests")

    cancun_tests_dir = tests_dir.mkdir("cancun")
    test_module = cancun_tests_dir.join("test_module_environment_variables.py")
    test_module.write(
        test_module_environment_variables.format(
            expected_gas_limit=expected_gas_limit
        )
    )

    testdir.copy_example(
        name="src/execution_testing/cli/pytest_commands/pytest_ini_files/pytest-fill.ini"
    )
    args.append("-c")
    args.append("pytest-fill.ini")
    args.append("-v")
    args.append("-m")
    args.append("state_test")
    args.append("--no-html")
    result = testdir.runpytest(*args)
    result.assert_outcomes(
        passed=1,
        failed=0,
        skipped=0,
        errors=0,
    )
    if "--output" in args:
        output_dir = Path(args[args.index("--output") + 1]).absolute()
    else:
        output_dir = Path(default_output_directory()).absolute()
    assert output_dir.exists()

    all_files = get_all_files_in_directory(str(output_dir))
    meta_dir = os.path.join(output_dir, ".meta")
    assert os.path.exists(meta_dir), f"The directory {meta_dir} does not exist"

    expected_ini_file = "fixtures.ini"
    expected_index_file = "index.json"
    expected_resolver_file = None
    resolver_file = None
    if TransitionTool.default_tool == ExecutionSpecsTransitionTool:
        expected_resolver_file = "eels_resolutions.json"

    ini_file = None
    index_file = None
    for file in all_files:
        if file.name == expected_ini_file:
            ini_file = file
        elif file.name == expected_index_file:
            index_file = file
        elif expected_resolver_file and file.name == expected_resolver_file:
            resolver_file = file
            assert resolver_file.exists(), f"{resolver_file} does not exist"

    expected_additional_files = {expected_ini_file, expected_index_file}
    if resolver_file:
        expected_additional_files.add(str(expected_resolver_file))
    all_fixtures = [
        file
        for file in all_files
        if file.name not in expected_additional_files
    ]
    for fixture_file, fixture_count in zip(
        expected_fixture_files, expected_fixture_counts
    ):
        assert fixture_file.exists(), f"{fixture_file} does not exist"
        assert fixture_count == count_keys_in_fixture(fixture_file), (
            f"Fixture count mismatch for {fixture_file}"
        )

    assert set(all_fixtures) == set(expected_fixture_files), (
        f"Unexpected files in directory: {set(all_fixtures) - set(expected_fixture_files)}"
    )

    assert ini_file is not None, (
        f"No {expected_ini_file} file was found in {meta_dir}"
    )
    config = configparser.ConfigParser()
    ini_file_text = ini_file.read_text()
    # ini_file_text = ini_file_text.replace(default_t8n.server_url, "t8n_server_path")
    config.read_string(ini_file_text)

    if "--skip-index" not in args:
        assert index_file is not None, (
            f"No {expected_index_file} file was found in {meta_dir}"
        )

    properties = {key: value for key, value in config.items("fixtures")}
    assert "timestamp" in properties
    timestamp = datetime.fromisoformat(properties["timestamp"])
    assert timestamp.year == datetime.now().year
    if "--build-name" in args:
        assert "build" in properties
        build_name = args[args.index("--build-name") + 1]
        assert properties["build"] == build_name
