"""Seed sender on a remote execution client."""

import os
from typing import Generator

import pytest

from execution_testing.base_types import Number
from execution_testing.logging import get_logger
from execution_testing.rpc import EthRPC
from execution_testing.test_types import EOA

logger = get_logger(__name__)


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add command-line options to pytest."""
    remote_seed_sender_group = parser.getgroup(
        "remote_seed_sender",
        "Arguments for the remote seed sender",
    )

    remote_seed_sender_group.addoption(
        "--rpc-seed-key",
        action="store",
        required=False,
        dest="rpc_seed_key",
        help=(
            "Seed key used to fund all sender keys. This account must have a balance of at least "
            "`sender_key_initial_balance` * `workers` + gas fees. It should also be "
            "exclusively used by this command because the nonce is only checked once and if "
            "it's externally increased, the seed transactions might fail. "
            "Can also be set via RPC_SEED_KEY environment variable."
        ),
    )


@pytest.fixture(scope="session")
def seed_key(
    request: pytest.FixtureRequest, eth_rpc: EthRPC
) -> Generator[EOA, None, None]:
    """
    Get the seed key from the command flags and create the EOA account object
    with the updated nonce value from the network.
    """
    rpc_seed_key = request.config.getoption("rpc_seed_key") or os.environ.get(
        "RPC_SEED_KEY"
    )
    if rpc_seed_key is None:
        pytest.fail(
            "Seed key must be provided via --rpc-seed-key or RPC_SEED_KEY "
            "environment variable"
        )
    # check the nonce through the rpc client
    seed_key = EOA(key=rpc_seed_key)
    seed_key.nonce = Number(eth_rpc.get_transaction_count(seed_key))

    # Record the start balance of the worker key
    start_balance = eth_rpc.get_balance(seed_key)

    yield seed_key

    final_balance = eth_rpc.get_balance(seed_key)
    used_balance = start_balance - final_balance
    logger.info(f"Seed used balance={used_balance / 10**18:.18f}")
