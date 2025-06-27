"""Pytest plugin that defines options and fixtures for client exceptions."""

from typing import List

import pytest
from hive.client import ClientType

from ethereum_test_exceptions import ExceptionMapper
from ethereum_test_fixtures import (
    BlockchainFixtureCommon,
)

from .helpers.exceptions import EXCEPTION_MAPPERS


def pytest_addoption(parser):
    """Hive simulator specific consume command line options."""
    consume_group = parser.getgroup(
        "consume", "Arguments related to consuming fixtures via a client"
    )
    consume_group.addoption(
        "--disable-strict-exception-matching",
        action="store",
        dest="disable_strict_exception_matching",
        default="",
        help=(
            "Comma-separated list of client names and/or forks which should NOT use strict "
            "exception matching."
        ),
    )


@pytest.fixture(scope="session")
def client_exception_mapper_cache():
    """Cache for exception mappers by client type."""
    return {}


@pytest.fixture(scope="function")
def client_exception_mapper(
    client_type: ClientType, client_exception_mapper_cache
) -> ExceptionMapper | None:
    """Return the exception mapper for the client type, with caching."""
    if client_type.name not in client_exception_mapper_cache:
        for client in EXCEPTION_MAPPERS:
            if client in client_type.name:
                client_exception_mapper_cache[client_type.name] = EXCEPTION_MAPPERS[client]
                break
        else:
            client_exception_mapper_cache[client_type.name] = None

    return client_exception_mapper_cache[client_type.name]


@pytest.fixture(scope="session")
def disable_strict_exception_matching(request: pytest.FixtureRequest) -> List[str]:
    """Return the list of clients or forks that should NOT use strict exception matching."""
    config_string = request.config.getoption("disable_strict_exception_matching")
    return config_string.split(",") if config_string else []


@pytest.fixture(scope="function")
def client_strict_exception_matching(
    client_type: ClientType,
    disable_strict_exception_matching: List[str],
) -> bool:
    """Return True if the client type should use strict exception matching."""
    return not any(
        client.lower() in client_type.name.lower() for client in disable_strict_exception_matching
    )


@pytest.fixture(scope="function")
def fork_strict_exception_matching(
    fixture: BlockchainFixtureCommon,
    disable_strict_exception_matching: List[str],
) -> bool:
    """Return True if the fork should use strict exception matching."""
    # NOTE: `in` makes it easier for transition forks ("Prague" in "CancunToPragueAtTime15k")
    return not any(
        s.lower() in str(fixture.fork).lower() for s in disable_strict_exception_matching
    )


@pytest.fixture(scope="function")
def strict_exception_matching(
    client_strict_exception_matching: bool,
    fork_strict_exception_matching: bool,
) -> bool:
    """Return True if the test should use strict exception matching."""
    return client_strict_exception_matching and fork_strict_exception_matching
