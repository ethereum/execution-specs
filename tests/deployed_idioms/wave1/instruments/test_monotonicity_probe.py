"""
Measurement instrument: does the second GAS reading exceed the first, when a
DELEGATECALLed child clears a slot the parent freshly set?

Stores GT(g1, g2) -- 1 if strictly decreasing (monotonic). Parametrised over
the expectation so the FAILING param tells us the real value per fork.
"""

import pytest
from execution_testing import Account, Alloc, Op, StateTestFiller, Transaction

SLOT_X = 0x01
SLOT_M = 0x02


@pytest.mark.parametrize("expect", [0, 1])
@pytest.mark.valid_from("Berlin")
def test_monotonic(state_test: StateTestFiller, pre: Alloc, expect: int) -> None:
    """Probe."""
    clearer = pre.deploy_contract(Op.SSTORE(SLOT_X, 0) + Op.STOP)
    caller = pre.deploy_contract(
        Op.SSTORE(SLOT_X, 1)
        + Op.MSTORE(0, Op.GAS)
        + Op.POP(Op.DELEGATECALL(gas=Op.GAS, address=clearer))
        + Op.MSTORE(0x20, Op.GAS)
        + Op.SSTORE(SLOT_M, Op.GT(Op.MLOAD(0), Op.MLOAD(0x20)))
        + Op.STOP
    )
    tx = Transaction(to=caller, state_gas_reservoir=0, sender=pre.fund_eoa())
    state_test(
        pre=pre,
        post={caller: Account(storage={SLOT_X: 0, SLOT_M: expect})},
        tx=tx,
    )
