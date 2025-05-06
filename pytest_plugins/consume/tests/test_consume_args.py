"""Test the consume plugins with various cli arguments."""

import re
import shutil
from pathlib import Path
from typing import List

import pytest
from click.testing import CliRunner
from pytest import Pytester, TempPathFactory

from cli.pytest_commands.fill import fill


@pytest.fixture(scope="module")
def test_paths() -> list[Path]:
    """Specify the test paths to be filled."""
    return [
        Path("tests/istanbul/eip1344_chainid/test_chainid.py"),
    ]


@pytest.fixture(scope="module")
def consume_test_case_ids() -> list[str]:
    """Hard-coded expected output of `consume direct --collectonly -q`."""
    return [
        "src/pytest_plugins/consume/direct/test_via_direct.py::test_fixture[CollectOnlyFixtureConsumer-tests/istanbul/eip1344_chainid/test_chainid.py::test_chainid[fork_Cancun-blockchain_test_from_state_test]]",
        "src/pytest_plugins/consume/direct/test_via_direct.py::test_fixture[CollectOnlyFixtureConsumer-tests/istanbul/eip1344_chainid/test_chainid.py::test_chainid[fork_Paris-blockchain_test_from_state_test]]",
        "src/pytest_plugins/consume/direct/test_via_direct.py::test_fixture[CollectOnlyFixtureConsumer-tests/istanbul/eip1344_chainid/test_chainid.py::test_chainid[fork_Shanghai-blockchain_test_from_state_test]]",
        "src/pytest_plugins/consume/direct/test_via_direct.py::test_fixture[CollectOnlyFixtureConsumer-tests/istanbul/eip1344_chainid/test_chainid.py::test_chainid[fork_Cancun-state_test]]",
        "src/pytest_plugins/consume/direct/test_via_direct.py::test_fixture[CollectOnlyFixtureConsumer-tests/istanbul/eip1344_chainid/test_chainid.py::test_chainid[fork_Paris-state_test]]",
        "src/pytest_plugins/consume/direct/test_via_direct.py::test_fixture[CollectOnlyFixtureConsumer-tests/istanbul/eip1344_chainid/test_chainid.py::test_chainid[fork_Shanghai-state_test]]",
    ]


@pytest.fixture(scope="module")
def fill_fork_from() -> str:
    """Specify the value for `fill`'s `--from` argument."""
    return "Paris"


@pytest.fixture(scope="module")
def fill_fork_until() -> str:
    """Specify the value for `fill`'s `--until` argument."""
    return "Cancun"


@pytest.fixture(scope="module")
def fixtures_dir(tmp_path_factory: TempPathFactory) -> Path:
    """Define the temporary test fixture directory for fill output."""
    return tmp_path_factory.mktemp("fixtures")


@pytest.fixture(autouse=True, scope="module")
def fill_tests(
    fixtures_dir: Path, fill_fork_from: str, fill_fork_until: str, test_paths: List[Path]
) -> None:
    """Run fill to generate test fixtures for use with testing consume."""
    fill_result = CliRunner().invoke(
        fill,
        [
            "-c",
            "pytest.ini",
            "--skip-evm-dump",
            "-m",
            "not blockchain_test_engine",
            f"--from={fill_fork_from}",
            f"--until={fill_fork_until}",
            f"--output={str(fixtures_dir)}",
            *[str(p) for p in test_paths],
            # if we fill many tests, it might help to add -n 8/auto
        ],
    )
    assert fill_result.exit_code == 0, f"Fill command failed:\n{fill_result.output}"


@pytest.fixture(autouse=True, scope="function")
def test_fixtures(pytester: Pytester, fixtures_dir: Path, fill_tests: None) -> List[Path]:
    """
    Copy test fixtures from the regular temp path to the pytester temporary dir.

    We intentionally copy the `.meta/index.json` file to test its compatibility with consume.
    """
    test_fixtures = []
    for json_file in fixtures_dir.rglob("*.json"):
        target_dir = Path(pytester.path) / json_file.parent
        if not target_dir.exists():
            target_dir.mkdir(parents=True)
        pytester.copy_example(name=json_file.as_posix())
        shutil.move(json_file.name, target_dir / json_file.name)
        if ".meta" not in str(json_file):
            test_fixtures.append(json_file)
    return test_fixtures


@pytest.fixture(autouse=True)
def copy_consume_test_paths(pytester: Pytester):
    """Specify and copy the consume test paths to the testdir."""
    local_test_paths = [Path("src/pytest_plugins/consume/direct/test_via_direct.py")]
    for test_path in local_test_paths:
        target_dir = Path(pytester.path) / test_path.parent
        target_dir.mkdir(parents=True, exist_ok=True)
        pytester.copy_example(name=str(test_path))
        pytester.copy_example(name=str(test_path.parent / "conftest.py"))
        shutil.move(test_path.name, target_dir / test_path.name)
        shutil.move("conftest.py", target_dir / "conftest.py")


single_test_id = "src/pytest_plugins/consume/direct/test_via_direct.py::test_fixture[CollectOnlyFixtureConsumer-tests/istanbul/eip1344_chainid/test_chainid.py::test_chainid[fork_Shanghai-state_test]]"  # noqa: E501


@pytest.mark.parametrize(
    "extra_args, expected_filter_pattern",
    [
        pytest.param(
            ["--collect-only", "-q"],
            re.compile(r".*"),
            id="no_extra_args",
        ),
        pytest.param(
            ["--collect-only", "-q", "--sim.limit", ".*fork_Cancun.*"],
            re.compile(".*Cancun.*"),
            id="sim_limit_regex",
        ),
        pytest.param(
            ["--sim.limit", "collectonly:.*fork_Cancun.*"],
            re.compile(".*Cancun.*"),
            id="sim_limit_collect_only_regex",
        ),
        pytest.param(
            [
                "--collect-only",
                "-q",
                "--sim.limit",
                f"id:{single_test_id}",
            ],
            re.compile(re.escape(f"{single_test_id}")),
            id="sim_limit_id",
        ),
        pytest.param(
            [
                "--sim.limit",
                f"collectonly:id:{single_test_id}",
            ],
            re.compile(
                re.compile(re.escape(f"{single_test_id}")),
            ),
            id="sim_limit_collect_only_id",
        ),
    ],
)
def test_consume_simlimit_collectonly(
    pytester: Pytester,
    fixtures_dir: Path,
    consume_test_case_ids: List[str],
    extra_args: List[str],
    expected_filter_pattern: re.Pattern,
) -> None:
    """Test consume's --sim.limit argument in collect-only mode."""
    ini_file = "pytest-consume.ini"
    pytester.copy_example(name=ini_file)
    consume_test_path = "src/pytest_plugins/consume/direct/test_via_direct.py"
    args = [
        "-c",
        ini_file,
        "--input",
        str(fixtures_dir),
        consume_test_path,
        *extra_args,
    ]
    result = pytester.runpytest(*args)
    assert result.ret == 0
    stdout_lines = str(result.stdout).splitlines()
    test_id_pattern = r"^(?:\s*)([^:\s]+\.py::[^:\s]+(?:::[^:\s]+)?)(?:\[[^\]]*\])?(?:\s*)$"
    collected_test_ids = [
        line for line in stdout_lines if line.strip() and re.match(test_id_pattern, line)
    ]
    expected_collected_test_ids = [
        line for line in consume_test_case_ids if expected_filter_pattern.search(line)
    ]
    assert set(collected_test_ids) == set(expected_collected_test_ids)
