"""
Pytest test to verify a client's configuration using `eth_config` RPC endpoint.
"""

import json
import time
from hashlib import sha256
from typing import Dict, List

import pytest

from ethereum_test_rpc import EthConfigResponse, EthRPC
from pytest_plugins.custom_logging import get_logger

from .execute_types import NetworkConfig

logger = get_logger(__name__)


@pytest.fixture(scope="function")
def eth_config_response(eth_rpc: List[EthRPC]) -> EthConfigResponse | None:
    """
    Get the `eth_config` response from the client to be verified by all tests.
    """
    for rpc in eth_rpc:
        try:
            response = rpc.config()
            if response is not None:
                return response
        except Exception:
            pass
    else:
        raise Exception("Could not connect to any RPC client.")


@pytest.fixture(scope="function")
def network(request: pytest.FixtureRequest) -> NetworkConfig:
    """Get the network that will be used to verify all tests."""
    return request.config.network  # type: ignore


@pytest.fixture(scope="function")
def current_time() -> int:
    """
    Get the `eth_config` response from the client to be verified by all tests.
    """
    return int(time.time())


@pytest.fixture(scope="function")
def expected_eth_config(
    network: NetworkConfig, current_time: int
) -> EthConfigResponse:
    """
    Calculate the current fork value to verify against the client's response.
    """
    return network.get_eth_config(current_time)


def test_eth_config_current(
    eth_config_response: EthConfigResponse | None,
    expected_eth_config: EthConfigResponse,
) -> None:
    """Validate `current` field of the `eth_config` RPC endpoint."""
    assert eth_config_response is not None, (
        "Client did not return a valid `eth_config` response."
    )
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
    assert eth_config_response is not None, (
        "Client did not return a valid `eth_config` response."
    )
    assert eth_config_response.current is not None, (
        "Client did not return a valid `current` fork config."
    )
    assert eth_config_response.current.fork_id is not None, (
        "Client did not return a valid `forkId` in the current fork config."
    )
    assert (
        eth_config_response.current.fork_id
        == expected_eth_config.current.fork_id
    ), (
        "Client's `current.forkId` does not match expected value: "
        f"{eth_config_response.current.fork_id} != "
        f"{expected_eth_config.current.fork_id}"
    )


def test_eth_config_next(
    eth_config_response: EthConfigResponse | None,
    expected_eth_config: EthConfigResponse,
) -> None:
    """Validate `next` field of the `eth_config` RPC endpoint."""
    assert eth_config_response is not None, (
        "Client did not return a valid `eth_config` response."
    )
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
    assert eth_config_response is not None, (
        "Client did not return a valid `eth_config` response."
    )
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
            assert received_fork_id is not None, (
                "Client did not return a valid `next.forkId`."
            )
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
    assert eth_config_response is not None, (
        "Client did not return a valid `eth_config` response."
    )
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
    assert eth_config_response is not None, (
        "Client did not return a valid `eth_config` response."
    )
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
            assert received_fork_id is not None, (
                "Client did not return a valid `last.forkId`."
            )
            assert received_fork_id == expected_last_fork_id, (
                "Client's `last.forkId` does not match expected value: "
                f"{received_fork_id} != "
                f"{expected_last_fork_id}"
            )


def test_eth_config_majority(
    all_rpc_endpoints: Dict[str, List[EthRPC]],
) -> None:
    """
    Queries devnet exec clients for their eth_config and fails if not all have
    the same response.
    """
    responses = dict()  # Dict[exec_client_name : response] # noqa: C408
    client_to_url_used_dict = dict()  # noqa: C408
    for exec_client in all_rpc_endpoints.keys():
        # try only as many consensus+exec client combinations until you receive
        # a response if all combinations for a given exec client fail we panic
        for eth_rpc_target in all_rpc_endpoints[exec_client]:
            try:
                response = eth_rpc_target.config(timeout=5)
                if response is None:
                    logger.warning(
                        f"Got 'None' as eth_config response from {eth_rpc_target}"
                    )
                    continue
            except Exception as e:
                logger.warning(
                    f"When trying to get eth_config from {eth_rpc_target} a problem occurred: {e}"
                )
                continue

            response_str = json.dumps(
                response.model_dump(mode="json"), sort_keys=True
            )
            responses[exec_client] = response_str
            client_to_url_used_dict[exec_client] = (
                eth_rpc_target.url
            )  # remember which cl+el combination was used
            logger.info(f"Response of {exec_client}: {response_str}\n\n")

            break  # no need to gather more responses for this client

    assert len(responses.keys()) == len(all_rpc_endpoints.keys()), (
        "Failed to get an eth_config response "
        f" from each specified execution client. Full list of execution clients is "
        f"{all_rpc_endpoints.keys()} but we were only able to gather eth_config responses "
        f"from: {responses.keys()}\n"
        "Will try again with a different consensus-execution client combination for "
        "this execution client"
    )
    # determine hashes of client responses
    client_to_hash_dict = {}  # Dict[exec_client : response hash] # noqa: C408
    for client in responses.keys():
        response_bytes = responses[client].encode("utf-8")
        response_hash = sha256(response_bytes).digest().hex()
        logger.info(f"Response hash of client {client}: {response_hash}")
        client_to_hash_dict[client] = response_hash

    # if not all responses have the same hash there is a critical consensus
    # issue
    expected_hash = ""
    for h in client_to_hash_dict.keys():
        if expected_hash == "":
            expected_hash = client_to_hash_dict[h]
            continue

        assert client_to_hash_dict[h] == expected_hash, (
            "Critical consensus issue: Not all eth_config responses are the "
            " same!\n"
            "Here is an overview of client response hashes:\n"
            + "\n\t".join(f"{k}: {v}" for k, v in client_to_hash_dict.items())
            + "\n\n"
            "Here is an overview of which URLs were contacted:\n\t"
            + "\n\t".join(
                f"{k}: @{v.split('@')[1]}"
                for k, v in client_to_url_used_dict.items()
            )
            + "\n\n"
            # log which cl+el combinations were used without leaking full url
            "Here is a dump of all client responses:\n"
            + "\n\n".join(f"{k}: {v}" for k, v in responses.items())
        )
    assert expected_hash != ""

    logger.info(
        "All clients returned the same eth_config response. Test has been passed!"
    )
