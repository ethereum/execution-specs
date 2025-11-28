"""Pytest plugin to recover funds from a failed remote execution."""

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Generator, Literal

import pytest

from execution_testing.base_types import Address, HexNumber
from execution_testing.forks import Paris
from execution_testing.forks.helpers import Fork
from execution_testing.test_types import EOA


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add command-line options to pytest."""
    recover_group = parser.getgroup(
        "execute", "Arguments defining fund recovery behavior."
    )
    recover_group.addoption(
        "--start-eoa-index",
        action="store",
        dest="start_eoa_index",
        type=HexNumber,
        required=True,
        default=None,
        help=("Starting private key index to use for EOA generation."),
    )
    recover_group.addoption(
        "--destination",
        action="store",
        dest="destination",
        type=Address,
        required=True,
        default=None,
        help=("Address to send the recovered funds to."),
    )
    recover_group.addoption(
        "--max-index",
        action="store",
        dest="max_index",
        type=int,
        default=100,
        help=("Maximum private key index to use for EOA generation."),
    )


@pytest.fixture(scope="session")
def destination(request: pytest.FixtureRequest) -> Address:
    """Get the destination address."""
    return request.config.option.destination


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Pytest hook used to dynamically generate test cases."""
    max_index = metafunc.config.option.max_index
    start_eoa_index = metafunc.config.option.start_eoa_index

    print(
        f"Generating {max_index} test cases starting from index {start_eoa_index}"  # noqa: E501
    )

    indexes_keys = [
        (index, EOA(key=start_eoa_index + index)) for index in range(max_index)
    ]

    metafunc.parametrize(
        ["index", "eoa"],
        indexes_keys,
        ids=[f"{index}-{eoa}" for index, eoa in indexes_keys],
    )


@pytest.fixture(scope="session")
def session_fork() -> Fork:
    """Return a default fork for the recover command."""
    return Paris


@pytest.fixture(scope="session")
def transactions_per_block() -> Literal[1]:
    """Return the number of transactions per block for the recover command."""
    return 1


@pytest.fixture(scope="session")
def session_temp_folder() -> Generator[Path, Any, None]:
    """Return a temporary folder for the session."""
    with TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)
