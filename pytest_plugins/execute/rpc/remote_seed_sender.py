"""Seed sender on a remote execution client."""

import pytest

from ethereum_test_base_types import Hash, Number
from ethereum_test_rpc import EthRPC
from ethereum_test_types import EOA


def pytest_addoption(parser):
    """Add command-line options to pytest."""
    remote_seed_sender_group = parser.getgroup(
        "remote_seed_sender",
        "Arguments for the remote seed sender",
    )

    remote_seed_sender_group.addoption(
        "--rpc-seed-key",
        action="store",
        required=True,
        dest="rpc_seed_key",
        help=(
            "Seed key used to fund all sender keys. This account must have a balance of at least "
            "`sender_key_initial_balance` * `workers` + gas fees. It should also be "
            "exclusively used by this command because the nonce is only checked once and if "
            "it's externally increased, the seed transactions might fail."
        ),
    )


@pytest.fixture(scope="session")
def seed_sender(request, eth_rpc: EthRPC) -> EOA:
    """Create seed sender account by checking its balance and nonce."""
    rpc_seed_key = Hash(request.config.getoption("rpc_seed_key"))
    # check the nonce through the rpc client
    seed_sender = EOA(key=rpc_seed_key)
    seed_sender.nonce = Number(eth_rpc.get_transaction_count(seed_sender))
    return seed_sender
