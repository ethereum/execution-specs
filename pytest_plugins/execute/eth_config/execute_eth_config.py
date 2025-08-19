"""Pytest test to verify a client's configuration using `eth_config` RPC endpoint."""

import time

import pytest

from ethereum_test_rpc import EthConfigResponse, EthRPC

from .types import NetworkConfig


@pytest.fixture(scope="session")
def eth_config_response(eth_rpc: EthRPC) -> EthConfigResponse | None:
    """Get the `eth_config` response from the client to be verified by all tests."""
    return eth_rpc.config()


@pytest.fixture(scope="session")
def network(request: pytest.FixtureRequest) -> NetworkConfig:
    """Get the network that will be used to verify all tests."""
    return request.config.network  # type: ignore


@pytest.fixture(scope="session")
def current_time() -> int:
    """Get the `eth_config` response from the client to be verified by all tests."""
    return int(time.time())


@pytest.fixture(scope="session")
def expected_eth_config(network: NetworkConfig, current_time: int) -> EthConfigResponse:
    """Calculate the current fork value to verify against the client's response."""
    return network.get_eth_config(current_time)


def test_eth_config_current(
    eth_config_response: EthConfigResponse | None,
    expected_eth_config: EthConfigResponse,
) -> None:
    """Validate `current` field of the `eth_config` RPC endpoint."""
    assert eth_config_response is not None, "Client did not return a valid `eth_config` response."
    assert eth_config_response.current is not None, (
        "Client did not return a valid `current` fork config."
    )
    expected_current = expected_eth_config.current
    assert eth_config_response.current == expected_current, (
        "Client's `current` fork config does not match expected value: "
        f"{eth_config_response.current.model_dump_json(indent=2)} != "
        f"{expected_current.model_dump_json(indent=2)}"
    )


def test_eth_config_current_fork_id(
    eth_config_response: EthConfigResponse | None,
    expected_eth_config: EthConfigResponse,
) -> None:
    """Validate `forkId` field within the `current` configuration object."""
    assert eth_config_response is not None, "Client did not return a valid `eth_config` response."
    assert eth_config_response.current is not None, (
        "Client did not return a valid `current` fork config."
    )
    assert eth_config_response.current.fork_id is not None, (
        "Client did not return a valid `forkId` in the current fork config."
    )
    assert eth_config_response.current.fork_id == expected_eth_config.current.fork_id, (
        "Client's `current.forkId` does not match expected value: "
        f"{eth_config_response.current.fork_id} != "
        f"{expected_eth_config.current.fork_id}"
    )


def test_eth_config_next(
    eth_config_response: EthConfigResponse | None,
    expected_eth_config: EthConfigResponse,
) -> None:
    """Validate `next` field of the `eth_config` RPC endpoint."""
    assert eth_config_response is not None, "Client did not return a valid `eth_config` response."
    expected_next = expected_eth_config.next
    if expected_next is None:
        assert eth_config_response.next is None, (
            "Client returned a `next` fork config but expected None."
        )
    else:
        assert eth_config_response.next is not None, (
            "Client did not return a valid `next` fork config."
        )
        assert eth_config_response.next == expected_next, (
            "Client's `next` fork config does not match expected value: "
            f"{eth_config_response.next.model_dump_json(indent=2)} != "
            f"{expected_next.model_dump_json(indent=2)}"
        )


def test_eth_config_next_fork_id(
    eth_config_response: EthConfigResponse | None,
    expected_eth_config: EthConfigResponse,
) -> None:
    """Validate `forkId` field within the `next` configuration object."""
    assert eth_config_response is not None, "Client did not return a valid `eth_config` response."
    expected_next = expected_eth_config.next
    if expected_next is None:
        assert eth_config_response.next is None, (
            "Client returned a `next` fork config but expected None."
        )
    else:
        assert eth_config_response.next is not None, (
            "Client did not return a valid `next` fork config."
        )
        expected_next_fork_id = expected_next.fork_id
        if expected_next_fork_id is None:
            assert eth_config_response.next.fork_id is None, (
                "Client returned a `next.forkId` but expected None."
            )
        else:
            received_fork_id = eth_config_response.next.fork_id
            assert received_fork_id is not None, "Client did not return a valid `next.forkId`."
            assert received_fork_id == expected_next_fork_id, (
                "Client's `next.forkId` does not match expected value: "
                f"{received_fork_id} != "
                f"{expected_next_fork_id}"
            )


def test_eth_config_last(
    eth_config_response: EthConfigResponse | None,
    expected_eth_config: EthConfigResponse,
) -> None:
    """Validate `last` field of the `eth_config` RPC endpoint."""
    expected_last = expected_eth_config.last
    assert eth_config_response is not None, "Client did not return a valid `eth_config` response."
    if expected_last is None:
        assert eth_config_response.last is None, (
            "Client returned a `last` fork config but expected None."
        )
    else:
        assert eth_config_response.last is not None, (
            "Client did not return a valid `last` fork config."
        )
        assert eth_config_response.last == expected_last, (
            "Client's `last` fork config does not match expected value: "
            f"{eth_config_response.last.model_dump_json(indent=2)} != "
            f"{expected_last.model_dump_json(indent=2)}"
        )


def test_eth_config_last_fork_id(
    eth_config_response: EthConfigResponse | None,
    expected_eth_config: EthConfigResponse,
) -> None:
    """Validate `forkId` field within the `last` configuration object."""
    assert eth_config_response is not None, "Client did not return a valid `eth_config` response."
    expected_last = expected_eth_config.last
    if expected_last is None:
        assert eth_config_response.last is None, (
            "Client returned a `last` fork config but expected None."
        )
    else:
        assert eth_config_response.last is not None, (
            "Client did not return a valid `last` fork config."
        )
        expected_last_fork_id = expected_last.fork_id
        if expected_last_fork_id is None:
            assert eth_config_response.last.fork_id is None, (
                "Client returned a `last.forkId` but expected None."
            )
        else:
            received_fork_id = eth_config_response.last.fork_id
            assert received_fork_id is not None, "Client did not return a valid `last.forkId`."
            assert received_fork_id == expected_last_fork_id, (
                "Client's `last.forkId` does not match expected value: "
                f"{received_fork_id} != "
                f"{expected_last_fork_id}"
            )
