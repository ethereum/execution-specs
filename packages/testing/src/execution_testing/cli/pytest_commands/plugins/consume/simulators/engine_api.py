"""Pytest fixtures for Engine API RPC clients."""

import pytest
from hive.client import Client

from execution_testing.exceptions import ExceptionMapper
from execution_testing.rpc import EngineRPC


@pytest.fixture(scope="function")
def engine_rpc(
    client: Client, client_exception_mapper: ExceptionMapper | None
) -> EngineRPC:
    """
    Initialize Engine RPC client for the execution client under test.

    Provide a configured EngineRPC instance that communicates
    with the client's Engine API endpoint (port 8551). If an
    exception mapper is available, it will be used for response
    validation to map client-specific error messages to standard
    exception types.

    Args:
        client: The Hive client instance to connect to.
        client_exception_mapper: Optional exception mapper.

    Returns:
        Configured EngineRPC instance for making Engine API calls.

    """
    if client_exception_mapper:
        return EngineRPC(
            f"http://{client.ip}:8551",
            response_validation_context={
                "exception_mapper": client_exception_mapper,
            },
        )
    return EngineRPC(f"http://{client.ip}:8551")
