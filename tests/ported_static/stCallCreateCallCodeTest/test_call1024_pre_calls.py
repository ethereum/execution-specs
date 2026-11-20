"""
Calldepth with subcall.

Ported from:
state_tests/stCallCreateCallCodeTest/Call1024PreCallsFiller.json
state_tests/stDelegatecallTestHomestead/Call1024PreCallsFiller.json

@manually-enhanced: Do not overwrite. CALL and DELEGATECALL merged; the target
is funded to the depth limit.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

from tests.ported_static.constants import HIGH_GAS_LIMIT

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

MAX_CALL_DEPTH = 1024
GAS_LIMITED_TX_GAS = 9_193_697_319_756
GAS_LIMITED_FRAMES = 989


@pytest.mark.ported_from(
    [
        "state_tests/stCallCreateCallCodeTest/Call1024PreCallsFiller.json",
        "state_tests/stDelegatecallTestHomestead/Call1024PreCallsFiller.json",
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.parametrize("opcode", [Op.CALL, Op.DELEGATECALL])
@pytest.mark.parametrize(
    "tx_gas",
    [
        pytest.param(11_937_600_034_817, id="depth_limit"),
        pytest.param(9_214_364_837_600_034_817, id="depth_limit_max_gas"),
        pytest.param(GAS_LIMITED_TX_GAS, id="gas_limited"),
    ],
)
def test_call1024_pre_calls(
    state_test: StateTestFiller,
    pre: Alloc,
    opcode: Op,
    tx_gas: int,
) -> None:
    """
    Send value twice, count the frame, then recurse into ADDRESS.

    With enough gas the recursion stops at the call depth limit, where
    the value calls fail. With less gas it stops earlier, at a depth
    pinned for the Cancun/Prague gas schedule, where they succeed.
    """
    env = Environment(gas_limit=HIGH_GAS_LIMIT)
    sender = pre.fund_eoa(amount=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
    recipient = pre.fund_eoa()

    target = pre.deploy_contract(
        code=Op.SSTORE(2, Op.CALL(gas=0xFFFF, address=recipient, value=1))
        + Op.SSTORE(3, Op.CALL(gas=0xFFFF, address=recipient, value=1))
        + Op.SSTORE(0, Op.ADD(Op.SLOAD(0), 1))
        + Op.SSTORE(1, opcode(gas=0xFFFFFFFFFFF, address=Op.ADDRESS))
        + Op.STOP,
        balance=2 * (MAX_CALL_DEPTH + 1),
    )

    tx = Transaction(sender=sender, to=target, gas_limit=tx_gas, value=10)

    if tx_gas == GAS_LIMITED_TX_GAS:
        storage = {0: GAS_LIMITED_FRAMES, 1: 1, 2: 1, 3: 1}
    else:
        storage = {0: MAX_CALL_DEPTH + 1, 1: 1, 2: 0, 3: 0}
    post = {target: Account(storage=storage)}

    state_test(env=env, pre=pre, post=post, tx=tx)
