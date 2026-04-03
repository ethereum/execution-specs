"""Pytest configuration for the json infra tests."""

from pathlib import Path
from typing import Callable

from _pytest.config.argparsing import Parser
from _pytest.nodes import Item
from pytest import Collector, Config, Session, fixture

from ethereum_spec_tools.evm_tools.t8n import ForkCache

from . import FORKS
from .helpers import FixturesFile, FixtureTestItem
from .helpers.select_tests import extract_affected_forks
from .stash_keys import desired_forks_key, fork_cache_key


@fixture()
def root_relative() -> Callable[[str | Path], Path]:
    """
    A fixture that provides a function to resolve a path relative to
    `conftest.py`.
    """

    def _(path: str | Path) -> Path:
        return Path(__file__).parent / path

    return _


def pytest_addoption(parser: Parser) -> None:
    """
    Accept custom options in pytest.
    """
    parser.addoption(
        "--optimized",
        dest="optimized",
        default=False,
        action="store_const",
        const=True,
        help="Use optimized state and ethash",
    )

    parser.addoption(
        "--evm_trace",
        dest="evm_trace",
        default=False,
        action="store_const",
        const=True,
        help="Create an evm trace",
    )

    parser.addoption(
        "--from",
        action="store",
        dest="forks_from",
        default="",
        type=str,
        help="Run tests from and including the specified fork.",
    )

    parser.addoption(
        "--until",
        action="store",
        dest="forks_until",
        default="",
        type=str,
        help="Run tests until and including the specified fork.",
    )

    parser.addoption(
        "--fork",
        action="store",
        dest="single_fork",
        default="",
        help="Only run tests for the specified fork.",
    )

    parser.addoption(
        "--file-list",
        action="store",
        dest="file_list",
        help=(
            "Only run tests relevant to a list of file paths in the "
            "repository. This option specifies the path to a file which "
            "contains a list of relevant paths."
        ),
    )

    parser.addoption(
        "--tests-file",
        dest="tests_path",
        type=Path,
        help="Path to a file containing test ids, one per line",
    )


def pytest_configure(config: Config) -> None:
    """
    Configure the ethereum module and log levels to output evm trace.
    """
    if config.getoption("optimized"):
        import ethereum_optimized

        ethereum_optimized.monkey_patch(None)

    if config.getoption("evm_trace"):
        import ethereum.trace
        from ethereum_spec_tools.evm_tools.t8n.evm_trace.eip3155 import (
            Eip3155Tracer,
        )

        # Replace the function in the module
        ethereum.trace.set_evm_trace(Eip3155Tracer())

    # Process fork range options
    optimized = config.getoption("optimized")
    desired_fork = config.getoption("single_fork", "")
    forks_from = config.getoption("forks_from", "")
    forks_until = config.getoption("forks_until", "")
    file_list = config.getoption("file_list", None)

    desired_forks = []
    all_forks = list(FORKS.keys())
    if desired_fork:
        if desired_fork not in all_forks:
            raise ValueError(f"Unknown fork: {desired_fork}")
        desired_forks.append(desired_fork)
    elif forks_from or forks_until:
        # Determine start and end indices
        start_idx = 0
        end_idx = len(all_forks)

        if forks_from:
            try:
                start_idx = all_forks.index(forks_from)
            except ValueError as e:
                raise ValueError(f"Unknown fork: {forks_from}") from e

        if forks_until:
            try:
                # +1 to include the until fork
                end_idx = all_forks.index(forks_until) + 1
            except ValueError as e:
                raise ValueError(f"Unknown fork: {forks_until}") from e

        # Validate the fork range
        if start_idx >= end_idx:
            raise ValueError(f"{forks_until} is before {forks_from}")

        # Extract the fork range
        desired_forks = all_forks[start_idx:end_idx]
    elif file_list:
        desired_forks = extract_affected_forks(
            config.rootpath, file_list, optimized
        )
    else:
        desired_forks = all_forks

    if not any(desired_forks):
        print("No fork specific tests will be run!!!")
    else:
        fork_list_str = ", ".join(desired_forks)
        print(f"Running tests for the following forks: {fork_list_str}")

    config.stash[desired_forks_key] = desired_forks


def pytest_collection_modifyitems(config: Config, items: list[Item]) -> None:
    """Filter test items."""
    tests_path = config.getoption("tests_path", None)
    if tests_path is None:
        return

    with open(tests_path) as f:
        test_ids = set(x.removesuffix("\n") for x in f.readlines())

    selected = []
    deselected = []
    for item in items:
        if item.nodeid in test_ids:
            selected.append(item)
            test_ids.remove(item.nodeid)
        else:
            deselected.append(item)

    if deselected:
        config.hook.pytest_deselected(items=deselected)
        items[:] = selected  # keep only what matches


def pytest_sessionstart(session: Session) -> None:
    """Initialize the fork cache at session start."""
    fork_cache = ForkCache()
    fork_cache.__enter__()
    session.stash[fork_cache_key] = fork_cache


def pytest_sessionfinish(session: Session, exitstatus: int) -> None:
    """Clean up the fork cache at session finish."""
    del exitstatus
    session.stash[fork_cache_key].__exit__()
    del session.stash[fork_cache_key]


def pytest_collect_file(
    file_path: Path, parent: Collector
) -> Collector | None:
    """
    Pytest hook that collects test cases from fixture JSON files.
    """
    if file_path.suffix == ".json":
        return FixturesFile.from_parent(parent, path=file_path)
    return None


def pytest_runtest_teardown(item: Item, nextitem: Item) -> None:
    """
    Drop cache from a `FixtureTestItem` if the next one is not of the
    same type or does not belong to the same fixtures file.
    """
    if isinstance(item, FixtureTestItem):
        if (
            nextitem is None
            or not isinstance(nextitem, FixtureTestItem)
            or item.fixtures_file != nextitem.fixtures_file
        ):
            item.fixtures_file.clear_data_cache()
