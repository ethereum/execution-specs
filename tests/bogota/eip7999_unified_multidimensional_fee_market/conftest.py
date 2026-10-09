"""Pytest (plugin) definitions local to EIP-7999 tests."""

from typing import List

import pytest
from execution_testing import (
    Address,
    Alloc,
    Environment,
    Fork,
    RecipientType,
)
from execution_testing.test_types.block_types import DEFAULT_BASE_FEE

SENDER_BALANCE = 10**18


@pytest.fixture
def env() -> Environment:
    """Default environment."""
    return Environment()


@pytest.fixture
def base_fees(fork: Fork, env: Environment) -> List[int]:
    """
    Base fees of the block a state test executes in, one per resource.

    Priced as the framework prices a parent-less environment: the EVM
    base fee is the environment's base fee and the blob base fee follows
    its excess blob gas.
    """
    base_fee_per_gas = (
        int(env.base_fee_per_gas)
        if env.base_fee_per_gas is not None
        else DEFAULT_BASE_FEE
    )
    excess_blob_gas = (
        int(env.excess_blob_gas) if env.excess_blob_gas is not None else 0
    )
    excess_gas = fork.initial_excess_gas_calculator()(
        base_fee_per_gas=base_fee_per_gas, excess_blob_gas=excess_blob_gas
    )
    return fork.base_fees_calculator()(excess_gas=excess_gas)


@pytest.fixture
def sender(pre: Alloc) -> Address:
    """Sender funded well beyond any fee in these tests."""
    return pre.fund_eoa(amount=SENDER_BALANCE)


@pytest.fixture
def recipient(pre: Alloc) -> Address:
    """An existing EOA, so a value transfer creates no account."""
    return pre.fund_eoa(amount=1)


def transfer_gas(fork: Fork, calldata: bytes = b"") -> int:
    """
    Return the EVM gas a value transfer to an existing EOA consumes: the
    intrinsic cost less the calldata gas, which the calldata resource
    prices.
    """
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()(
        calldata=calldata,
        sends_value=True,
        recipient_type=RecipientType.EOA,
    )
    return intrinsic_cost - fork.calldata_gas_calculator()(data=calldata)


def receipt_gas(fork: Fork, evm_gas_used: int, calldata: bytes = b"") -> int:
    """
    Return the receipt's gas used: the EVM gas plus the calldata gas, which
    receipts keep counting as before EIP-7999.
    """
    return evm_gas_used + fork.calldata_gas_calculator()(data=calldata)
