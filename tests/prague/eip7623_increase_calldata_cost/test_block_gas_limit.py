"""
Test [EIP-7623: Increase calldata cost](https://eips.ethereum.org/EIPS/eip-7623)
interaction with the block gas limit.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytes,
    Environment,
    Fork,
    Header,
    Transaction,
    TransactionException,
)

from .spec import ref_spec_7623

REFERENCE_SPEC_GIT_PATH = ref_spec_7623.git_path
REFERENCE_SPEC_VERSION = ref_spec_7623.version

pytestmark = [
    pytest.mark.valid_from("Prague"),
    pytest.mark.valid_until("Osaka"),
]

BLOCK_GAS_LIMIT = 10_000_000
FLOOR_TX_COUNT = 2
FLOOR_TX_DATA = Bytes(b"\xff" * 100_000)


@pytest.mark.parametrize(
    "probe_gas_delta",
    [
        pytest.param(0, id="fits_floor_inclusive_gas_used"),
        pytest.param(
            1,
            id="exceeds_floor_inclusive_gas_used",
            marks=pytest.mark.exception_test,
        ),
    ],
)
def test_tx_gas_limit_after_floor_priced_txs(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    probe_gas_delta: int,
) -> None:
    """
    Test that the gas available to a transaction is the block gas limit minus
    the block gas used so far, including the calldata floor charged to the
    preceding transactions.

    The preceding transactions pay the data floor, so their execution gas is
    well below their gas used. The probe transaction's gas limit fits into the
    gas left after execution gas but must be checked against the gas left
    after the floor-inclusive gas used.
    """
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()
    floor_cost = fork.transaction_data_floor_cost_calculator()(
        data=FLOOR_TX_DATA
    )
    execution_cost = intrinsic_cost(
        calldata=FLOOR_TX_DATA, return_cost_deducted_prior_execution=True
    )
    assert floor_cost > execution_cost

    floor_block_gas_used = FLOOR_TX_COUNT * floor_cost
    probe_gas_limit = BLOCK_GAS_LIMIT - floor_block_gas_used + probe_gas_delta
    assert probe_gas_limit <= BLOCK_GAS_LIMIT - FLOOR_TX_COUNT * execution_cost

    receiver = pre.fund_eoa(amount=0)
    floor_txs = [
        Transaction(
            to=receiver,
            data=FLOOR_TX_DATA,
            gas_limit=floor_cost,
            sender=pre.fund_eoa(),
        )
        for _ in range(FLOOR_TX_COUNT)
    ]
    exceeds = probe_gas_delta > 0
    probe_tx = Transaction(
        to=receiver,
        value=1,
        gas_limit=probe_gas_limit,
        sender=pre.fund_eoa(),
        error=TransactionException.GAS_ALLOWANCE_EXCEEDED if exceeds else None,
    )

    blockchain_test(
        genesis_environment=Environment(gas_limit=BLOCK_GAS_LIMIT),
        pre=pre,
        post={} if exceeds else {receiver: Account(balance=1)},
        blocks=[
            Block(
                txs=[*floor_txs, probe_tx],
                exception=TransactionException.GAS_ALLOWANCE_EXCEEDED
                if exceeds
                else None,
                header_verify=None
                if exceeds
                else Header(gas_used=floor_block_gas_used + 21_000),
            )
        ],
    )
