"""
A pytest plugin that configures the consume command to act as a test runner
for "direct" client fixture consumer interfaces.

For example, via go-ethereum's `evm blocktest` or `evm statetest` commands.
"""

import json
import tempfile
from pathlib import Path
from typing import List

import pytest

from ethereum_clis.fixture_consumer_tool import FixtureConsumerTool
from ethereum_test_base_types import to_json
from ethereum_test_fixtures.consume import TestCaseIndexFile, TestCaseStream
from ethereum_test_fixtures.file import Fixtures

from ..consume import FixturesSource


def pytest_addoption(parser):  # noqa: D103
    consume_group = parser.getgroup(
        "consume_direct", "Arguments related to consuming fixtures via a client"
    )

    consume_group.addoption(
        "--fixture-consumer-bin",
        action="append",
        dest="fixture_consumer_bin",
        type=list,
        default=[Path("evm")],
        help=(
            "Path to a geth evm executable that provides `blocktest` or `statetest`. "
            "Flag can be used multiple times to specify multiple fixture consumer binaries."
            "Default: First 'evm' entry in PATH."
        ),
    )
    consume_group.addoption(
        "--traces",
        action="store_true",
        dest="consumer_collect_traces",
        default=False,
        help="Collect traces of the execution information from the fixture consumer tool.",
    )
    debug_group = parser.getgroup("debug", "Arguments defining debug behavior")
    debug_group.addoption(
        "--dump-dir",
        action="store",
        dest="base_dump_dir",
        type=Path,
        default=None,
        help="Path to dump the fixture consumer tool debug output.",
    )


def pytest_configure(config):  # noqa: D103
    fixture_consumers = []
    for fixture_consumer_bin_path in config.getoption("fixture_consumer_bin"):
        fixture_consumers.append(
            FixtureConsumerTool.from_binary_path(
                binary_path=Path(fixture_consumer_bin_path),
                trace=config.getoption("consumer_collect_traces"),
            )
        )
    config.fixture_consumers = fixture_consumers


@pytest.fixture(scope="function")
def test_dump_dir(request, fixture_path: Path, fixture_name: str) -> Path | None:
    """The directory to write evm debug output to."""
    base_dump_dir = request.config.getoption("base_dump_dir")
    if not base_dump_dir:
        return None
    if len(fixture_name) > 142:
        # ensure file name is not too long for eCryptFS
        fixture_name = fixture_name[:70] + "..." + fixture_name[-70:]
    return base_dump_dir / fixture_path.stem / fixture_name.replace("/", "-")


@pytest.fixture
def fixture_path(test_case: TestCaseIndexFile | TestCaseStream, fixtures_source: FixturesSource):
    """
    Path to the current JSON fixture file.

    If the fixture source is stdin, the fixture is written to a temporary json file.
    """
    if fixtures_source == "stdin":
        assert isinstance(test_case, TestCaseStream)
        temp_dir = tempfile.TemporaryDirectory()
        fixture_path = Path(temp_dir.name) / f"{test_case.id.replace('/', '_')}.json"
        fixtures = Fixtures({test_case.id: test_case.fixture})
        with open(fixture_path, "w") as f:
            json.dump(to_json(fixtures), f, indent=4)
        yield fixture_path
        temp_dir.cleanup()
    else:
        assert isinstance(test_case, TestCaseIndexFile)
        yield fixtures_source / test_case.json_path


@pytest.fixture(scope="function")
def fixture_name(test_case: TestCaseIndexFile | TestCaseStream):
    """Name of the current fixture."""
    return test_case.id


def pytest_generate_tests(metafunc):
    """Parametrize test cases for every fixture consumer."""
    metafunc.parametrize(
        "fixture_consumer",
        (
            pytest.param(fixture_consumer, id=str(fixture_consumer.__class__.__name__))
            for fixture_consumer in metafunc.config.fixture_consumers
        ),
    )


def pytest_collection_modifyitems(items: List):
    """
    Modify collected item names to remove the test cases that cannot be consumed by the
    given fixture consumer.
    """
    for item in items[:]:  # use a copy of the list, as we'll be modifying it
        fixture_consumer = item.callspec.params["fixture_consumer"]
        fixture_format = item.callspec.params["fixture_format"]
        if not fixture_consumer.can_consume(fixture_format):
            items.remove(item)
