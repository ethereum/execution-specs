"""
Verify DELEGATECALL propagates the caller frame's context (CALLVALUE, CALLER,
CALLDATA) into the delegate, after a value-bearing transaction.

Ported from:
state_tests/stDelegatecallTestHomestead/deleagateCallAfterValueTransferFiller.json

@manually-enhanced: Do not overwrite. DELEGATECALL context propagation
(CALLVALUE/CALLER/CALLDATA) run in the caller's storage; the ported test
transferred zero value (so "after value transfer" was vacuous) -> a non-zero
tx value is now sent so the callee observes it via CALLVALUE. Dynamic
addresses, gas forwarded via the default Op.GAS.
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

TRANSFERRED_VALUE = 0xA


@pytest.mark.ported_from(
    [
        "state_tests/stDelegatecallTestHomestead/deleagateCallAfterValueTransferFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("TangerineWhistle")
def test_deleagate_call_after_value_transfer(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """DELEGATECALL runs the callee's code in the caller's context."""
    # Delegated code records the environment it observes: it must see the
    # enclosing frame's CALLVALUE (the transferred value), the original CALLER
    # (the sender), and the delegate-call args as its calldata (0x1).
    delegate = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.CALLVALUE)
        + Op.SSTORE(key=0x1, value=Op.CALLER)
        + Op.SSTORE(key=0x2, value=Op.CALLDATALOAD(offset=0x0))
        + Op.STOP,
    )
    caller = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0x1)
        + Op.DELEGATECALL(
            address=delegate,
            args_offset=0x0,
            args_size=0x40,
            ret_offset=0x0,
            ret_size=0x40,
        )
        + Op.STOP,
    )

    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        to=caller,
        value=TRANSFERRED_VALUE,
        protected=fork.supports_protected_txs(),
    )

    post = {
        # DELEGATECALL preserves the enclosing frame's value, so the callee
        # sees CALLVALUE == the transferred value; its writes land in the
        # caller's storage, not the callee's.
        caller: Account(
            balance=TRANSFERRED_VALUE,
            storage={0: TRANSFERRED_VALUE, 1: sender, 2: 1},
        ),
        delegate: Account(storage={0: 0, 1: 0, 2: 0}),
    }

    state_test(pre=pre, post=post, tx=tx)
