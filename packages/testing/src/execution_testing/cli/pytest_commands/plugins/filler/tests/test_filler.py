"""
Test the filler plugin.
"""

import configparser
import json
import os
import textwrap
from collections.abc import Generator
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from typing import Any

import pytest

from execution_testing.client_clis import (
    ExecutionSpecsTransitionTool,
    TransitionTool,
)
from execution_testing.fixtures import (
    BlockchainEngineFixture,
    BlockchainFixture,
)
from execution_testing.fixtures.file import Fixtures
from execution_testing.test_types import Environment

from ..filler import default_output_directory

# Path to the real benchmark conftest.py that we copy into testdirs.
BENCHMARK_CONFTEST_PATH = (
    Path(__file__).resolve().parents[9] / "tests" / "benchmark" / "conftest.py"
)


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
                    pre={TestAddress: Account(balance=1_000_000)}, post={}, tx=Transaction(gas_limit=0x5208))

    @pytest.mark.valid_from("Paris")
    @pytest.mark.valid_until("Shanghai")
    def test_paris_two(state_test) -> None:
        state_test(env=Environment(),
                    pre={TestAddress: Account(balance=1_000_000)}, post={}, tx=Transaction(gas_limit=0x5208))
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
                    pre={TestAddress: Account(balance=1_000_000)}, post={}, tx=Transaction(gas_limit=0x5208))

    @pytest.mark.parametrize("x", [1, 2, 3])
    @pytest.mark.valid_from("Paris")
    @pytest.mark.valid_until("Shanghai")
    def test_shanghai_two(state_test, x) -> None:
        state_test(env=Environment(),
                    pre={TestAddress: Account(balance=1_000_000)}, post={}, tx=Transaction(gas_limit=0x5208))
    """
)

test_count_shanghai = 8
total_test_count = test_count_paris + test_count_shanghai


@pytest.fixture()
def tests_dir(testdir: pytest.Testdir) -> Any:
    """Create the top-level tests/ directory."""
    return testdir.mkdir("tests")


@pytest.fixture()
def paris_tests_dir(tests_dir: Any) -> Any:
    """Populate tests/paris/ with test_module_paris."""
    paris_dir = tests_dir.mkdir("paris")
    paris_dir.join("test_module_paris.py").write(test_module_paris)
    return paris_dir


@pytest.fixture()
def benchmark_dir(tests_dir: Any) -> Any:
    """Create tests/benchmark/ with conftest and test module."""
    bm_dir = tests_dir.mkdir("benchmark")
    bm_dir.join("conftest.py").write(BENCHMARK_CONFTEST_PATH.read_text())
    bm_dir.join("test_module_benchmark.py").write(test_module_benchmark)
    return bm_dir


@pytest.fixture()
def all_benchmark_dirs(benchmark_dir: Any) -> Any:
    """Extend benchmark/ with compute/ and stateful/ subdirectories."""
    for subdir in ("compute", "stateful"):
        d = benchmark_dir.mkdir(subdir)
        d.join(f"test_module_{subdir}.py").write(test_module_benchmark)
    return benchmark_dir


@pytest.fixture()
def fill_base_args(testdir: pytest.Testdir) -> list[str]:
    """Copy fill ini and return base pytest args."""
    testdir.copy_example(
        name=(
            "src/execution_testing/cli/pytest_commands"
            "/pytest_ini_files/pytest-fill.ini"
        )
    )
    return ["-c", "pytest-fill.ini", "--no-html"]


@pytest.fixture()
def execute_base_args(testdir: pytest.Testdir) -> list[str]:
    """Copy execute ini and return base pytest args."""
    testdir.copy_example(
        name=(
            "src/execution_testing/cli/pytest_commands"
            "/pytest_ini_files/pytest-execute.ini"
        )
    )
    return [
        "-c",
        "pytest-execute.ini",
        "--collect-only",
        "-q",
        "--chain-id",
        "1",
    ]


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
                    tx=Transaction(to=contract, sender=pre.fund_eoa()))
    """
)

test_module_execution_witness_skip_stateless = textwrap.dedent(
    """\
    import pytest

    from execution_testing import (
        Account,
        Alloc,
        Block,
        BlockchainTestFiller,
        Op,
        Transaction,
    )

    @pytest.mark.valid_at("Amsterdam")
    @pytest.mark.skip_stateless_validation
    def test_skip_stateless_validation(
        pre: Alloc,
        blockchain_test: BlockchainTestFiller,
    ) -> None:
        contract = pre.deploy_contract(code=Op.SSTORE(0, 1) + Op.STOP)
        sender = pre.fund_eoa()
        tx = Transaction(to=contract, sender=sender)

        blockchain_test(
            pre=pre,
            post={
                contract: Account(storage={0: 1}),
                sender: Account(nonce=1),
            },
            blocks=[Block(txs=[tx])],
        )
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


test_module_execution_witness_rlp_modifier = textwrap.dedent(
    """\
    import pytest

    from execution_testing import (
        Account,
        Alloc,
        Block,
        BlockchainTestFiller,
        Header,
        Op,
        Transaction,
    )

    @pytest.mark.valid_at("Amsterdam")
    def test_execution_witness_rlp_modifier(
        pre: Alloc,
        blockchain_test: BlockchainTestFiller,
    ) -> None:
        contract = pre.deploy_contract(code=Op.SSTORE(0, 1) + Op.STOP)
        sender = pre.fund_eoa()
        tx = Transaction(to=contract, sender=sender)

        blockchain_test(
            pre=pre,
            post={
                contract: Account(storage={0: 1}),
                sender: Account(nonce=1),
            },
            blocks=[
                Block(
                    txs=[tx],
                    rlp_modifier=Header(extra_data=b"mutated"),
                )
            ],
        )
    """
)


test_module_execution_witness_rlp_modifier_stateless_intent = textwrap.dedent(
    """\
    import pytest

    from execution_testing import (
        Alloc,
        Block,
        BlockchainTestFiller,
        Header,
    )

    @pytest.mark.valid_at("Amsterdam")
    def test_execution_witness_rlp_modifier_stateless_intent(
        pre: Alloc,
        blockchain_test: BlockchainTestFiller,
    ) -> None:
        blockchain_test(
            pre=pre,
            post={},
            blocks=[
                Block(
                    rlp_modifier=Header(extra_data=b"mutated"),
                    expected_stateless_validation_success=True,
                )
            ],
        )
    """
)


def test_execution_witness_in_blockchain_fixture(
    testdir: pytest.Testdir,
) -> None:
    """
    Fill a minimal Amsterdam state_test that calls a pre-deployed contract,
    then verify the resulting blockchain and engine fixtures contain
    execution witness data.
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

    fixture_data = Fixtures.model_validate_json(fixture_path.read_text())

    assert len(fixture_data) == 1, "Expected exactly one fixture"
    fixture = next(iter(fixture_data.values()))
    assert isinstance(fixture, BlockchainFixture)
    block = fixture.blocks[0]

    # executionWitness exists with non-empty state, codes, and headers
    witness = block.execution_witness
    assert witness is not None
    assert len(witness.state) > 0, "executionWitness.state is empty"
    assert len(witness.codes) > 0, "executionWitness.codes is empty"
    assert len(witness.headers) > 0, "executionWitness.headers is empty"

    # statelessInputBytes is schema-prefixed guest input bytes.
    sib = block.stateless_input_bytes
    assert sib is not None and len(sib) > 0
    from ethereum.forks.amsterdam.stateless import (
        STATELESS_INPUT_SCHEMA_ID,
        STATELESS_INPUT_SCHEMA_ID_BYTES,
    )

    assert bytes(sib).startswith(STATELESS_INPUT_SCHEMA_ID_BYTES)

    sob = block.stateless_output_bytes
    assert sob is not None and len(sob) > 0

    from ethereum.forks.amsterdam.stateless_host import (
        deserialize_stateless_output,
    )
    from ethereum_types.bytes import Bytes as EthereumBytes
    from ethereum_types.numeric import U16, U64

    stateless_output = deserialize_stateless_output(EthereumBytes(bytes(sob)))
    assert stateless_output.successful_validation is True
    assert stateless_output.chain_id == U64(1)
    assert stateless_output.schema_id == U16(STATELESS_INPUT_SCHEMA_ID)

    engine_fixture_path = Path(
        "fixtures/blockchain_tests_engine/for_amsterdam/amsterdam/"
        "module_execution_witness/execution_witness.json"
    )
    assert engine_fixture_path.exists(), (
        f"{engine_fixture_path} does not exist"
    )

    engine_fixture_data = Fixtures.model_validate_json(
        engine_fixture_path.read_text()
    )

    assert len(engine_fixture_data) == 1, "Expected exactly one engine fixture"
    engine_fixture = next(iter(engine_fixture_data.values()))
    assert isinstance(engine_fixture, BlockchainEngineFixture)
    engine_payload = engine_fixture.payloads[0]

    engine_witness = engine_payload.execution_witness
    assert engine_witness is not None
    assert len(engine_witness.state) > 0, (
        "engine executionWitness.state is empty"
    )
    assert len(engine_witness.codes) > 0, (
        "engine executionWitness.codes is empty"
    )
    assert len(engine_witness.headers) > 0, (
        "engine executionWitness.headers is empty"
    )
    assert engine_witness == witness


def test_execution_witness_skip_stateless_validation(
    testdir: pytest.Testdir,
) -> None:
    """The skip marker omits stateless witness and byte outputs."""
    tests_dir = testdir.mkdir("tests")
    amsterdam_tests_dir = tests_dir.mkdir("amsterdam")
    test_module = amsterdam_tests_dir.join(
        "test_module_skip_stateless_validation.py"
    )
    test_module.write(test_module_execution_witness_skip_stateless)

    testdir.copy_example(
        name="src/execution_testing/cli/pytest_commands/pytest_ini_files/pytest-fill.ini"
    )
    args = [
        "-c",
        "pytest-fill.ini",
        "-v",
        "--until=Amsterdam",
        "-m",
        "blockchain_test",
        "--no-html",
    ]
    result = testdir.runpytest(*args)
    result.assert_outcomes(
        passed=1,
        failed=0,
        skipped=0,
        errors=0,
    )

    fixture_path = Path(
        "fixtures/blockchain_tests/for_amsterdam/amsterdam/"
        "module_skip_stateless_validation/skip_stateless_validation.json"
    )
    assert fixture_path.exists(), f"{fixture_path} does not exist"

    with open(fixture_path, "r") as f:
        fixture_data = json.load(f)

    assert len(fixture_data) == 1, "Expected exactly one fixture"
    fixture = next(iter(fixture_data.values()))
    block = fixture["blocks"][0]

    assert "executionWitness" not in block
    assert "statelessInputBytes" not in block
    assert "statelessOutputBytes" not in block


def test_execution_witness_rlp_modifier_omits_stateless_artifacts(
    testdir: pytest.Testdir,
) -> None:
    """RLP-mutated blocks should not expose canonical stateless artifacts."""
    tests_dir = testdir.mkdir("tests")
    amsterdam_tests_dir = tests_dir.mkdir("amsterdam")
    test_module = amsterdam_tests_dir.join(
        "test_module_execution_witness_rlp_modifier.py"
    )
    test_module.write(test_module_execution_witness_rlp_modifier)

    testdir.copy_example(
        name="src/execution_testing/cli/pytest_commands/pytest_ini_files/pytest-fill.ini"
    )
    args = [
        "-c",
        "pytest-fill.ini",
        "-v",
        "--until=Amsterdam",
        "-m",
        "blockchain_test",
        "--no-html",
    ]
    result = testdir.runpytest(*args)
    result.assert_outcomes(
        passed=1,
        failed=0,
        skipped=0,
        errors=0,
    )

    fixture_path = Path(
        "fixtures/blockchain_tests/for_amsterdam/amsterdam/"
        "module_execution_witness_rlp_modifier/"
        "execution_witness_rlp_modifier.json"
    )
    assert fixture_path.exists(), f"{fixture_path} does not exist"

    with open(fixture_path, "r") as f:
        fixture_data = json.load(f)

    assert len(fixture_data) == 1, "Expected exactly one fixture"
    fixture = next(iter(fixture_data.values()))
    block = fixture["blocks"][0]

    assert "executionWitness" not in block
    assert "statelessInputBytes" not in block
    assert "statelessOutputBytes" not in block


def test_execution_witness_rlp_modifier_rejects_stateless_intent(
    testdir: pytest.Testdir,
) -> None:
    """RLP modifiers cannot be combined with explicit stateless assertions."""
    tests_dir = testdir.mkdir("tests")
    amsterdam_tests_dir = tests_dir.mkdir("amsterdam")
    test_module = amsterdam_tests_dir.join(
        "test_module_execution_witness_rlp_modifier_stateless_intent.py"
    )
    test_module.write(
        test_module_execution_witness_rlp_modifier_stateless_intent
    )

    testdir.copy_example(
        name="src/execution_testing/cli/pytest_commands/pytest_ini_files/pytest-fill.ini"
    )
    args = ["-c", "pytest-fill.ini", "-v", "--until=Amsterdam", "--no-html"]
    result = testdir.runpytest(*args)
    assert result.ret != 0
    result.stdout.fnmatch_lines(
        [
            "*Blocks with rlp_modifier omit stateless artifacts because "
            "they are generated before the RLP mutation*"
        ]
    )


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

    from ethereum.crypto.hash import Hash32
    from ethereum.forks.amsterdam.stateless import (
        compute_new_payload_request_root,
    )
    from ethereum.forks.amsterdam.stateless_guest import (
        deserialize_stateless_input,
    )
    from ethereum.forks.amsterdam.stateless_host import (
        deserialize_stateless_output,
    )
    from ethereum.forks.amsterdam.stateless import (
        STATELESS_INPUT_SCHEMA_ID,
    )
    from ethereum_types.bytes import Bytes as EthereumBytes
    from ethereum_types.numeric import U16

    stateless_input = deserialize_stateless_input(
        EthereumBytes(bytes.fromhex(block["statelessInputBytes"][2:]))
    )
    stateless_output = deserialize_stateless_output(
        EthereumBytes(bytes.fromhex(block["statelessOutputBytes"][2:]))
    )

    assert stateless_output.successful_validation is True
    assert stateless_output.schema_id == U16(STATELESS_INPUT_SCHEMA_ID)
    assert stateless_output.new_payload_request_root != Hash32(b"\0" * 32)
    assert (
        stateless_output.new_payload_request_root
        == compute_new_payload_request_root(stateless_input)
    )


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

    from ethereum.crypto.hash import Hash32
    from ethereum.forks.amsterdam.stateless import (
        compute_new_payload_request_root,
    )
    from ethereum.forks.amsterdam.stateless_guest import (
        deserialize_stateless_input,
    )
    from ethereum.forks.amsterdam.stateless_host import (
        deserialize_stateless_output,
    )
    from ethereum.forks.amsterdam.stateless import (
        STATELESS_INPUT_SCHEMA_ID,
    )
    from ethereum_types.bytes import Bytes as EthereumBytes
    from ethereum_types.numeric import U16

    stateless_input = deserialize_stateless_input(
        EthereumBytes(bytes.fromhex(block["statelessInputBytes"][2:]))
    )
    stateless_output = deserialize_stateless_output(
        EthereumBytes(bytes.fromhex(block["statelessOutputBytes"][2:]))
    )

    assert stateless_output.successful_validation is False
    assert stateless_output.schema_id == U16(STATELESS_INPUT_SCHEMA_ID)
    assert stateless_output.new_payload_request_root != Hash32(b"\0" * 32)
    assert (
        stateless_output.new_payload_request_root
        == compute_new_payload_request_root(stateless_input)
    )
    assert len(stateless_input.witness.headers) == 1
    assert [
        "0x" + bytes(header).hex()
        for header in stateless_input.witness.headers
    ] == block["executionWitness"]["headers"]

    engine_fixture_path = Path(
        "fixtures/blockchain_tests_engine/for_amsterdam/amsterdam/"
        "module_execution_witness_soundness/"
        "execution_witness_soundness.json"
    )
    assert engine_fixture_path.exists(), (
        f"{engine_fixture_path} does not exist"
    )

    with open(engine_fixture_path, "r") as f:
        engine_fixture_data = json.load(f)

    engine_fixture = next(iter(engine_fixture_data.values()))
    engine_payload = engine_fixture["engineNewPayloads"][-1]
    assert engine_payload["executionWitnessMutated"] is True
    assert engine_payload["executionWitness"] == block["executionWitness"]


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
        tx = Transaction(
            gas_limit=block_gas_limit, sender=pre.fund_eoa()
        ).with_signature_and_sender()
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


test_module_benchmark = textwrap.dedent(
    """\
    from execution_testing import Account, Environment, TestAddress, Transaction

    def test_benchmark_one(state_test) -> None:
        state_test(
            env=Environment(),
            pre={TestAddress: Account(balance=1_000_000)},
            post={},
            tx=Transaction(gas_limit=0x5208),
        )
    """
)
"""Simple benchmark module with no explicit markers (state_test fixture)."""

test_module_benchmark_repricing = textwrap.dedent(
    """\
    import pytest

    from execution_testing import BenchmarkTestFiller, JumpLoopGenerator, Op

    @pytest.mark.repricing
    def test_repricing_one(benchmark_test: BenchmarkTestFiller) -> None:
        benchmark_test(
            target_opcode=Op.JUMPDEST,
            code_generator=JumpLoopGenerator(attack_block=Op.JUMPDEST),
        )

    def test_no_repricing(benchmark_test: BenchmarkTestFiller) -> None:
        benchmark_test(
            target_opcode=Op.JUMPDEST,
            code_generator=JumpLoopGenerator(attack_block=Op.JUMPDEST),
        )
    """
)
"""Benchmark module with repricing and non-repricing tests
(benchmark_test fixture, compatible with --fixed-opcode-count)."""


# Fill: exclusion & collection


@pytest.mark.usefixtures("paris_tests_dir", "benchmark_dir")
def test_benchmark_excluded_from_default_fill(
    testdir: pytest.Testdir,
    fill_base_args: list[str],
) -> None:
    """Verify normal fill excludes tests under benchmark/."""
    result = testdir.runpytest(*fill_base_args, "-v")
    result.assert_outcomes(
        passed=test_count_paris * 3,
        failed=0,
        skipped=0,
        errors=0,
    )


@pytest.mark.usefixtures("paris_tests_dir", "benchmark_dir")
def test_benchmark_not_collected_with_negated_repricing(
    testdir: pytest.Testdir,
    fill_base_args: list[str],
) -> None:
    """Verify ``-m 'not repricing'`` excludes benchmark tests."""
    result = testdir.runpytest(
        *fill_base_args, "--collect-only", "-q", "-m", "not repricing"
    )
    result.stdout.fnmatch_lines(["*test_paris_one*"])
    result.stdout.fnmatch_lines(["*test_paris_two*"])
    result.stdout.no_fnmatch_line("*test_benchmark_one*")


@pytest.mark.usefixtures("all_benchmark_dirs")
def test_benchmark_collected_when_targeted_directly(
    testdir: pytest.Testdir,
    fill_base_args: list[str],
) -> None:
    """Verify targeting tests/benchmark/ collects all subdirectories."""
    result = testdir.runpytest(
        *fill_base_args, "-v", "--fork", "Prague", "tests/benchmark"
    )
    # 3 modules * 1 test * 1 fork (Prague) * 3 formats = 9
    result.assert_outcomes(
        passed=9,
        failed=0,
        skipped=0,
        errors=0,
    )


# Fill: default mode & fixture output


@pytest.mark.usefixtures("benchmark_dir")
def test_benchmark_default_uses_gas_benchmark_mode(
    testdir: pytest.Testdir,
    fill_base_args: list[str],
) -> None:
    """Verify the default mode produces fixtures under for_prague/."""
    result = testdir.runpytest(
        *fill_base_args, "-v", "--fork", "Prague", "tests/benchmark"
    )
    # 1 test * 1 fork (Prague) * 3 formats = 3
    result.assert_outcomes(
        passed=3,
        failed=0,
        skipped=0,
        errors=0,
    )

    output_dir = Path(default_output_directory()).absolute()
    assert output_dir.exists()

    expected_fixture_files = [
        Path(
            "fixtures/blockchain_tests/for_prague/"
            "benchmark/module_benchmark/benchmark_one.json"
        ),
        Path(
            "fixtures/blockchain_tests_engine/for_prague/"
            "benchmark/module_benchmark/benchmark_one.json"
        ),
        Path(
            "fixtures/state_tests/for_prague/"
            "benchmark/module_benchmark/benchmark_one.json"
        ),
    ]
    for fixture_file in expected_fixture_files:
        assert fixture_file.exists(), f"{fixture_file} does not exist"


# Fill: subdir × benchmark-option × repricing matrix


@pytest.mark.parametrize("subdir", ["compute", "stateful"])
@pytest.mark.parametrize(
    "benchmark_option,benchmark_value",
    [
        pytest.param(
            "--gas-benchmark-values",
            "1",
            id="gas-benchmark-values",
        ),
        pytest.param(
            "--fixed-opcode-count",
            "1",
            id="fixed-opcode-count",
        ),
    ],
)
@pytest.mark.parametrize(
    "use_repricing",
    [
        pytest.param(True, id="repricing"),
        pytest.param(False, id="no-repricing"),
    ],
)
def test_benchmark_conftest_matrix(
    testdir: pytest.Testdir,
    benchmark_dir: Any,
    fill_base_args: list[str],
    subdir: str,
    benchmark_option: str,
    benchmark_value: str,
    use_repricing: bool,
) -> None:
    """Verify collection across subdir, benchmark option, and repricing.

    Dimensions (2 x 2 x 2 = 8 combinations):
      - subdir:           compute | stateful
      - benchmark option: --gas-benchmark-values | --fixed-opcode-count
      - repricing:        -m repricing | (all tests)
    """
    target_dir = benchmark_dir.mkdir(subdir)
    target_dir.join("test_module.py").write(test_module_benchmark_repricing)

    args = [
        *fill_base_args,
        "--collect-only",
        "-q",
        benchmark_option,
        benchmark_value,
    ]
    if use_repricing:
        args.extend(["-m", "repricing"])
    args.append(f"tests/benchmark/{subdir}")

    result = testdir.runpytest(*args)

    result.stdout.fnmatch_lines(["*test_repricing_one*"])
    if use_repricing:
        result.stdout.no_fnmatch_line("*test_no_repricing*")
    else:
        result.stdout.fnmatch_lines(["*test_no_repricing*"])


# Execute: exclusion & collection


@pytest.fixture()
def _mock_execute_rpc(
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[None, None, None]:
    """Mock EthRPC so execute-mode tests can collect without a real endpoint."""
    monkeypatch.setenv("RPC_ENDPOINT", "http://localhost:12345")
    with patch(
        "execution_testing.cli.pytest_commands.plugins.execute"
        ".rpc.remote.EthRPC"
    ) as mock_cls:
        mock_cls.return_value.chain_id.return_value = 1
        yield


@pytest.mark.usefixtures(
    "_mock_execute_rpc", "paris_tests_dir", "benchmark_dir"
)
def test_execute_benchmark_excluded_from_default_collection(
    testdir: pytest.Testdir,
    execute_base_args: list[str],
) -> None:
    """Verify default execute collection excludes benchmark/."""
    result = testdir.runpytest(*execute_base_args)
    result.stdout.fnmatch_lines(["*test_paris_one*"])
    result.stdout.fnmatch_lines(["*test_paris_two*"])
    result.stdout.no_fnmatch_line("*test_benchmark_one*")


@pytest.mark.usefixtures(
    "_mock_execute_rpc", "paris_tests_dir", "benchmark_dir"
)
def test_execute_benchmark_not_collected_with_negated_repricing(
    testdir: pytest.Testdir,
    execute_base_args: list[str],
) -> None:
    """Verify ``-m 'not repricing'`` excludes benchmark tests
    in execute mode."""
    result = testdir.runpytest(*execute_base_args, "-m", "not repricing")
    result.stdout.fnmatch_lines(["*test_paris_one*"])
    result.stdout.fnmatch_lines(["*test_paris_two*"])
    result.stdout.no_fnmatch_line("*test_benchmark_one*")


@pytest.mark.usefixtures("_mock_execute_rpc", "all_benchmark_dirs")
def test_execute_benchmark_collected_when_targeted_directly(
    testdir: pytest.Testdir,
    execute_base_args: list[str],
) -> None:
    """Verify targeting tests/benchmark/ collects all subdirectories
    in execute mode."""
    result = testdir.runpytest(*execute_base_args, "tests/benchmark")
    result.stdout.fnmatch_lines(["*test_module_benchmark*test_benchmark_one*"])
    result.stdout.fnmatch_lines(["*test_module_compute*test_benchmark_one*"])
    result.stdout.fnmatch_lines(["*test_module_stateful*test_benchmark_one*"])


@pytest.mark.usefixtures("_mock_execute_rpc", "benchmark_dir")
def test_execute_benchmark_default_collects_without_flags(
    testdir: pytest.Testdir,
    execute_base_args: list[str],
) -> None:
    """Verify benchmark tests are collected in execute mode without
    explicit benchmark flags."""
    result = testdir.runpytest(*execute_base_args, "tests/benchmark")
    result.stdout.fnmatch_lines(["*test_benchmark_one*"])


# Execute: subdir × benchmark-option × repricing matrix


@pytest.mark.parametrize("subdir", ["compute", "stateful"])
@pytest.mark.parametrize(
    "benchmark_option,benchmark_value",
    [
        pytest.param(
            "--gas-benchmark-values",
            "1",
            id="gas-benchmark-values",
        ),
        pytest.param(
            "--fixed-opcode-count",
            "1",
            id="fixed-opcode-count",
        ),
    ],
)
@pytest.mark.parametrize(
    "use_repricing",
    [
        pytest.param(True, id="repricing"),
        pytest.param(False, id="no-repricing"),
    ],
)
@pytest.mark.usefixtures("_mock_execute_rpc")
def test_execute_benchmark_conftest_matrix(
    testdir: pytest.Testdir,
    benchmark_dir: Any,
    execute_base_args: list[str],
    subdir: str,
    benchmark_option: str,
    benchmark_value: str,
    use_repricing: bool,
) -> None:
    """Verify collection across subdir, benchmark option, and repricing
    in execute mode.

    Dimensions (2 x 2 x 2 = 8 combinations):
      - subdir:           compute | stateful
      - benchmark option: --gas-benchmark-values | --fixed-opcode-count
      - repricing:        -m repricing | (all tests)
    """
    target_dir = benchmark_dir.mkdir(subdir)
    target_dir.join("test_module.py").write(test_module_benchmark_repricing)

    args = [*execute_base_args, benchmark_option, benchmark_value]
    if use_repricing:
        args.extend(["-m", "repricing"])
    args.append(f"tests/benchmark/{subdir}")

    result = testdir.runpytest(*args)

    result.stdout.fnmatch_lines(["*test_repricing_one*"])
    if use_repricing:
        result.stdout.no_fnmatch_line("*test_no_repricing*")
    else:
        result.stdout.fnmatch_lines(["*test_no_repricing*"])
