"""Pytest plugin to run the execute in remote-rpc-mode."""

import pytest

from ethereum_test_rpc import EngineRPC, EthRPC
from ethereum_test_types import TransactionDefaults


def pytest_addoption(parser):
    """Add command-line options to pytest."""
    remote_rpc_group = parser.getgroup("remote_rpc", "Arguments defining remote RPC configuration")
    remote_rpc_group.addoption(
        "--rpc-endpoint",
        required=True,
        action="store",
        dest="rpc_endpoint",
        help="RPC endpoint to an execution client",
    )
    remote_rpc_group.addoption(
        "--rpc-chain-id",
        action="store",
        dest="rpc_chain_id",
        required=True,
        type=int,
        default=None,
        help="ID of the chain where the tests will be executed.",
    )
    remote_rpc_group.addoption(
        "--tx-wait-timeout",
        action="store",
        dest="tx_wait_timeout",
        type=int,
        default=60,
        help="Maximum time in seconds to wait for a transaction to be included in a block",
    )


@pytest.fixture(scope="session")
def engine_rpc() -> EngineRPC | None:
    """Execute remote command does not have access to the engine RPC."""
    return None


@pytest.fixture(autouse=True, scope="session")
def rpc_endpoint(request) -> str:
    """Return remote RPC endpoint to be used to make requests to the execution client."""
    return request.config.getoption("rpc_endpoint")


@pytest.fixture(autouse=True, scope="session")
def chain_id(request) -> int:
    """Return chain id where the tests will be executed."""
    chain_id = request.config.getoption("rpc_chain_id")
    if chain_id is not None:
        TransactionDefaults.chain_id = chain_id
    return chain_id


@pytest.fixture(autouse=True, scope="session")
def eth_rpc(request, rpc_endpoint: str) -> EthRPC:
    """Initialize ethereum RPC client for the execution client under test."""
    tx_wait_timeout = request.config.getoption("tx_wait_timeout")
    return EthRPC(rpc_endpoint, transaction_wait_timeout=tx_wait_timeout)
