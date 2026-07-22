"""
Test_make_money.

Ported from:
state_tests/stSpecialTest/makeMoneyFiller.json

@manually-enhanced: Do not overwrite. Value flow tx->caller->callee expressed
as a relationship; dynamic addresses, gas forwarded via the default Op.GAS.
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
        code=Op.CALL(address=callee, value=CALL_VALUE) + Op.STOP,
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
