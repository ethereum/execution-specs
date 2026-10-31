"""
Measurement instrument: what intrinsic cost does a transaction actually pay?

The contract stores `FROZEN_LIMIT - GAS`, which equals the intrinsic charge
plus the handful of opcodes executed before `GAS`. Its FAILURES ARE THE
MEASUREMENT: the one param that passes is the true value on that fork.
"""

import pytest
from execution_testing import Account, Alloc, Op, StateTestFiller, Transaction

FROZEN_LIMIT = 1_000_000


@pytest.mark.parametrize(
    "v", [12002, 15002, 18002, 21002]
)
@pytest.mark.valid_from("Berlin")
def test_intrinsic(state_test: StateTestFiller, pre: Alloc, v: int) -> None:
    """Probe."""
    c = pre.deploy_contract(Op.SSTORE(0, Op.SUB(FROZEN_LIMIT, Op.GAS)) + Op.STOP)
    tx = Transaction(to=c, gas_limit=FROZEN_LIMIT, sender=pre.fund_eoa())
    state_test(pre=pre, post={c: Account(storage={0: v})}, tx=tx)
