"""
DELEGATECALL keeps the caller and value of the enclosing frame.

Ported from:
state_tests/stTransitionTest/delegatecallBeforeTransitionFiller.json
state_tests/stTransitionTest/delegatecallAtTransitionFiller.json
state_tests/stTransitionTest/delegatecallAfterTransitionFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stTransitionTest/delegatecallBeforeTransitionFiller.json",
        "state_tests/stTransitionTest/delegatecallAtTransitionFiller.json",
        "state_tests/stTransitionTest/delegatecallAfterTransitionFiller.json",
    ],
)
@pytest.mark.valid_from("Cancun")
def test_delegatecall_transition(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """DELEGATECALL keeps the caller and value of the enclosing frame."""
    sender = pre.fund_eoa()
    tx_value = 17

    callee = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=Op.CALLER)
        + Op.SSTORE(key=0x2, value=Op.CALLVALUE)
        + Op.STOP,
        balance=23,
    )
    target = pre.deploy_contract(
        code=Op.SSTORE(
            key=0x0,
            value=Op.DELEGATECALL(
                address=callee,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x2,
            ),
        )
        + Op.STOP,
    )

    tx = Transaction(sender=sender, to=target, value=tx_value)

    post = {
        target: Account(storage={0: 1, 1: sender, 2: tx_value}),
        callee: Account(storage={}, balance=23),
    }

    state_test(pre=pre, post=post, tx=tx)
