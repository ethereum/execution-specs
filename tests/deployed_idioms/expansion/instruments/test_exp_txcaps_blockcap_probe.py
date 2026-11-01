"""
Measurement instrument: the block-level cap on a transaction's gas limit.

At Amsterdam `check_tx_fits_block` tests TWO dimensions
(amsterdam/vm/gas.py:1081-1086):

    if min(TX_MAX_GAS_LIMIT, tx_gas) > execution_gas_available: reject
    if tx_gas             > state_gas_available:                reject

So the EIP-7825 cap softens the EXECUTION dimension only. The full `tx.gas`
-- reservoir included -- is still measured against the block's state-gas
budget. A batcher that reads EIP-7825 as "my execution demand is capped, so
I can ask for as much gas as I like" is wrong.

FAILURES ARE THE MEASUREMENT.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Environment,
    Op,
    StateTestFiller,
    Transaction,
    TransactionException,
)

BLOCK = 20_000_000  # above 2**24, so the execution dimension always fits


@pytest.mark.parametrize(
    "tx_gas,err",
    [
        pytest.param(BLOCK, None, id="at_block_limit"),
        pytest.param(
            BLOCK + 1,
            TransactionException.GAS_ALLOWANCE_EXCEEDED,
            id="one_over_block_limit",
            marks=pytest.mark.exception_test,
        ),
    ],
)
@pytest.mark.valid_from("Amsterdam")
def test_block_dim(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas: int,
    err: TransactionException | None,
) -> None:
    """Probe."""
    c = pre.deploy_contract(Op.SSTORE(0, 1) + Op.STOP)
    tx = Transaction(
        to=c,
        gas_limit=tx_gas,
        sender=pre.fund_eoa(amount=10**19),
        error=err,
    )
    state_test(
        env=Environment(gas_limit=BLOCK),
        pre=pre,
        post={c: Account(storage={0: 0 if err else 1})},
        tx=tx,
    )
