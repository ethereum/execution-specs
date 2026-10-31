"""
Measurement instrument: intrinsic cost by transaction shape.

EIP-2780 decomposed a flat 21,000 into TX_BASE + a recipient-dependent
component, so the intrinsic charge now varies with the transaction's shape.
FAILURES ARE THE MEASUREMENT.
"""

import pytest
from execution_testing import Account, Alloc, Op, StateTestFiller, Transaction

L = 1_000_000


@pytest.mark.parametrize("val", [0, 1])
@pytest.mark.parametrize("v", [12002, 15002, 21002, 27002])
@pytest.mark.valid_from("Berlin")
def test_shape(state_test: StateTestFiller, pre: Alloc, v: int, val: int) -> None:
    """Probe."""
    c = pre.deploy_contract(Op.SSTORE(0, Op.SUB(L, Op.GAS)) + Op.STOP)
    tx = Transaction(
        to=c, gas_limit=L, value=val, sender=pre.fund_eoa(amount=10**18)
    )
    state_test(pre=pre, post={c: Account(storage={0: v})}, tx=tx)
