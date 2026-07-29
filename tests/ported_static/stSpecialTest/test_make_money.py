"""
Verify value flows tx -> caller -> callee when the CALL asks for an absurdly
oversized gas amount (near 2^256), which the EIP-150 63/64 cap must clamp.

Ported from:
state_tests/stSpecialTest/makeMoneyFiller.json

@manually-enhanced: Do not overwrite. Value flow tx->caller->callee expressed
as a relationship; dynamic addresses. The oversized CALL gas operand is the
original filler's point (clamping, not wrapping, of a near-2^256 ask) and
must stay explicit.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

INITIAL_BALANCE = 0xDE0B6B3A7640000
TX_VALUE = 10
CALL_VALUE = 0x17
# The ported filler asks for nearly 2^256 gas: a client computing e.g.
# `requested + stipend` in wrapping arithmetic would forward almost nothing
# and OOG the callee, so the 63/64 clamp itself is under test.
OVERSIZED_GAS_ASK = 2**256 - 20


@pytest.mark.ported_from(
    ["state_tests/stSpecialTest/makeMoneyFiller.json"],
)
@pytest.mark.valid_from("TangerineWhistle")
def test_make_money(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Value forwards tx -> caller -> callee; the callee records ORIGIN."""
    # Callee stores a sentinel and the transaction origin, proving its code
    # ran (not merely that value was transferred).
    callee = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.SSTORE(key=0x2, value=Op.ORIGIN),
        balance=INITIAL_BALANCE,
    )
    caller = pre.deploy_contract(
        code=Op.CALL(gas=OVERSIZED_GAS_ASK, address=callee, value=CALL_VALUE)
        + Op.STOP,
        balance=INITIAL_BALANCE,
    )

    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        to=caller,
        value=TX_VALUE,
        protected=fork.supports_protected_txs(),
    )

    post = {
        caller: Account(balance=INITIAL_BALANCE + TX_VALUE - CALL_VALUE),
        callee: Account(
            balance=INITIAL_BALANCE + CALL_VALUE,
            storage={1: 1, 2: sender},
        ),
    }

    state_test(pre=pre, post=post, tx=tx)
