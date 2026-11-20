"""
Calldepth with balance too low.

Ported from:
state_tests/stCallCreateCallCodeTest/Call1024BalanceTooLowFiller.json
state_tests/stCallCreateCallCodeTest/Callcode1024BalanceTooLowFiller.json
state_tests/stDelegatecallTestHomestead/Call1024BalanceTooLowFiller.json
state_tests/stDelegatecallTestHomestead/Delegatecall1024Filler.json

@manually-enhanced: Do not overwrite. Opcodes merged; every case reaches a
balance too low.
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
TX_VALUE = 10


@pytest.mark.ported_from(
    [
        "state_tests/stCallCreateCallCodeTest/Call1024BalanceTooLowFiller.json",  # noqa: E501
        "state_tests/stCallCreateCallCodeTest/Callcode1024BalanceTooLowFiller.json",  # noqa: E501
        "state_tests/stDelegatecallTestHomestead/Call1024BalanceTooLowFiller.json",  # noqa: E501
        "state_tests/stDelegatecallTestHomestead/Delegatecall1024Filler.json",
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.parametrize(
    "opcode, balance",
    [
        pytest.param(Op.CALL, 1024, id="call1024_balance_too_low"),
        pytest.param(Op.CALL, 500, id="call_balance_too_low"),
        pytest.param(Op.CALLCODE, 1024, id="callcode1024_balance_too_low"),
        pytest.param(Op.CALLCODE, 500, id="callcode_balance_too_low"),
        pytest.param(Op.DELEGATECALL, 1024, id="delegatecall1024"),
    ],
)
def test_call1024_balance_too_low(
    state_test: StateTestFiller,
    pre: Alloc,
    opcode: Op,
    balance: int,
) -> None:
    """
    Count the frame, then recurse into ADDRESS sending the count as value.

    The recursion stops at the call depth limit, or earlier when the
    value exceeds the contract's balance. DELEGATECALL sends no value.
    """
    env = Environment(gas_limit=HIGH_GAS_LIMIT)
    sender = pre.fund_eoa(amount=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)

    if opcode == Op.DELEGATECALL:
        recurse = Op.DELEGATECALL(gas=0xFFFFFFFFFFF, address=Op.ADDRESS)
    else:
        recurse = opcode(
            gas=0xFFFFFFFFFFF, address=Op.ADDRESS, value=Op.SLOAD(0)
        )
    target = pre.deploy_contract(
        code=Op.SSTORE(0, Op.ADD(Op.SLOAD(0), 1)) + Op.SSTORE(1, recurse),
        balance=balance,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        gas_limit=9214364837600034817,
        value=TX_VALUE,
    )

    # The value sent to self never leaves the contract, so the deepest
    # frame is the first whose count exceeds the balance, if any.
    frames = MAX_CALL_DEPTH + 1
    if opcode != Op.DELEGATECALL:
        frames = min(frames, balance + TX_VALUE + 1)
    post = {
        target: Account(storage={0: frames, 1: 1}, balance=balance + TX_VALUE)
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
