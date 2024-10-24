"""
Pytest test to recover funds from a failed remote execution.
"""

import pytest

from ethereum_test_base_types import Address
from ethereum_test_rpc import EthRPC
from ethereum_test_types import EOA, Transaction


@pytest.fixture(scope="session")
def gas_price(eth_rpc: EthRPC) -> int:
    """
    Get the gas price for the funding transactions.
    """
    return eth_rpc.gas_price()


def test_recover_funds(
    destination: Address,
    index: int,
    eoa: EOA,
    gas_price: int,
    eth_rpc: EthRPC,
) -> None:
    """
    Recover funds from a failed remote execution.
    """
    remaining_balance = eth_rpc.get_balance(eoa)
    refund_gas_limit = 21_000
    tx_cost = refund_gas_limit * gas_price
    if remaining_balance < tx_cost:
        pytest.skip(f"Balance {remaining_balance} is less than the transaction cost {tx_cost}")

    refund_tx = Transaction(
        sender=eoa,
        to=destination,
        gas_limit=refund_gas_limit,
        gas_price=gas_price,
        value=remaining_balance - tx_cost,
    ).with_signature_and_sender()

    eth_rpc.send_wait_transaction(refund_tx)
    print(f"Recovered {remaining_balance} from {eoa} to {destination}")
