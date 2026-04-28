"""Pytest plugin that defines options and fixtures for client exceptions."""

from pathlib import Path
from typing import Dict, List

import pytest
from hive.client import ClientType

from execution_testing.exceptions import (
    ExceptionMapper,
    ExternalExceptionMapper,
    extend_exception_mapper,
    load_external_exception_mapper,
)
from execution_testing.fixtures import (
    BlockchainFixtureCommon,
)

from .helpers.exceptions import EXCEPTION_MAPPERS


def pytest_addoption(parser: pytest.Parser) -> None:
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
            "Comma-separated list of client names and/or forks which should "
            "NOT use strict exception matching."
        ),
    )
    consume_group.addoption(
        "--exception-mapper",
        action="append",
        dest="external_exception_mappers",
        default=[],
        metavar="CLIENT=PATH",
        help=(
            "Extend a client's built-in exception mapper with a YAML mapper "
            "file. Can be repeated, e.g. "
            "--exception-mapper geth=../go-ethereum/eest-exceptions.yaml."
        ),
    )


def _parse_external_exception_mapper_options(
    options: List[str],
) -> Dict[str, ExternalExceptionMapper]:
    """Load external exception mapper files from CLIENT=PATH options."""
    external_mappers: Dict[str, ExternalExceptionMapper] = {}
    for option in options:
        if "=" not in option:
            raise ValueError(
                "--exception-mapper must use CLIENT=PATH syntax"
            )
        client, path_string = option.split("=", 1)
        client = client.strip().lower()
        path_string = path_string.strip()
        if not client or not path_string:
            raise ValueError(
                "--exception-mapper must use non-empty CLIENT=PATH values"
            )
        external_mappers[client] = load_external_exception_mapper(
            Path(path_string).expanduser()
        )
    return external_mappers


def _client_key_matches(
    configured_key: str,
    hive_client_name: str,
    built_in_key: str,
) -> bool:
    """Return whether an external mapper key applies to a Hive client."""
    configured_key = configured_key.lower()
    hive_client_name = hive_client_name.lower()
    built_in_key = built_in_key.lower()
    return (
        configured_key in hive_client_name
        or configured_key == built_in_key
        or (configured_key == "geth" and built_in_key == "go-ethereum")
    )


def get_configured_exception_mapper(
    client_name: str,
    external_exception_mappers: Dict[str, ExternalExceptionMapper],
) -> ExceptionMapper | None:
    """Return the built-in mapper extended with a matching external mapper."""
    normalized_client_name = client_name.lower()
    for client_key, built_in_mapper in EXCEPTION_MAPPERS.items():
        if client_key not in normalized_client_name:
            continue
        external_mapper = None
        for configured_key, mapper in external_exception_mappers.items():
            if _client_key_matches(
                configured_key, client_name, client_key
            ):
                external_mapper = mapper
                break
        return extend_exception_mapper(built_in_mapper, external_mapper)
    return None


@pytest.fixture(scope="session")
def client_exception_mapper_cache() -> Dict[str, ExceptionMapper | None]:
    """Cache for exception mappers by client type."""
    return {}


@pytest.fixture(scope="session")
def external_exception_mappers(
    request: pytest.FixtureRequest,
) -> Dict[str, ExternalExceptionMapper]:
    """Load external exception mapper files requested on the command line."""
    return _parse_external_exception_mapper_options(
        request.config.getoption("external_exception_mappers")
    )


@pytest.fixture(scope="function")
def client_exception_mapper(
    client_type: ClientType,
    client_exception_mapper_cache: Dict[str, ExceptionMapper | None],
    external_exception_mappers: Dict[str, ExternalExceptionMapper],
) -> ExceptionMapper | None:
    """Return the exception mapper for the client type, with caching."""
    if client_type.name not in client_exception_mapper_cache:
        client_exception_mapper_cache[client_type.name] = (
            get_configured_exception_mapper(
                client_type.name,
                external_exception_mappers,
            )
        )

    return client_exception_mapper_cache[client_type.name]


@pytest.fixture(scope="session")
def disable_strict_exception_matching(
    request: pytest.FixtureRequest,
) -> List[str]:
    """
    Return the list of clients or forks that should NOT use strict exception
    matching.
    """
    config_string = request.config.getoption(
        "disable_strict_exception_matching"
    )
    return config_string.split(",") if config_string else []


@pytest.fixture(scope="function")
def client_strict_exception_matching(
    client_type: ClientType,
    disable_strict_exception_matching: List[str],
) -> bool:
    """Return True if the client type should use strict exception matching."""
    return not any(
        client.lower() in client_type.name.lower()
        for client in disable_strict_exception_matching
    )


@pytest.fixture(scope="function")
def fork_strict_exception_matching(
    fixture: BlockchainFixtureCommon,
    disable_strict_exception_matching: List[str],
) -> bool:
    """Return True if the fork should use strict exception matching."""
    # NOTE: `in` makes it easier for transition forks ("Prague" in
    # "CancunToPragueAtTime15k")
    return not any(
        s.lower() in str(fixture.fork).lower()
        for s in disable_strict_exception_matching
    )


@pytest.fixture(scope="function")
def strict_exception_matching(
    client_strict_exception_matching: bool,
    fork_strict_exception_matching: bool,
) -> bool:
    """Return True if the test should use strict exception matching."""
    return client_strict_exception_matching and fork_strict_exception_matching
