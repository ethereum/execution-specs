"""
Verify a storage-clear refund earned inside a sub-call is credited to
the transaction: the sender's final balance reflects the executed gas
minus the refund.

Ported from:
state_tests/stRefundTest/refund_CallAFiller.json

@manually-enhanced: Do not overwrite. The sub-call forwards all gas
instead of a schedule-sized constant, and the sender's balance, refund cap
and budget derive from the fork (`code.gas_cost` / `code.refund`
composites), so EIP-8037's repriced stores are tracked instead of pinned.
The legacy transaction value and the caller balance it pinned are dropped
as incidental to the refund.
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

INITIAL_BALANCE = 10**18
GAS_PRICE = 10


@pytest.mark.ported_from(
    ["state_tests/stRefundTest/refund_CallAFiller.json"],
)
@pytest.mark.valid_from("Berlin")
def test_refund_call_a(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """A callee's storage clear is credited to the transaction refund."""
    callee_code = Op.SSTORE(
        key=0x1, value=0x0, key_warm=False, original_value=1, new_value=0
    )
    callee = pre.deploy_contract(
        code=callee_code + Op.STOP,
        storage={1: 1},
    )

    # The caller's own slot 1 stays set: the callee clears its own storage.
    caller_code = Op.SSTORE(
        key=0x0,
        value=Op.CALL(address=callee, address_warm=False),
        key_warm=False,
        original_value=0,
        new_value=1,
    )
    caller = pre.deploy_contract(
        code=caller_code + Op.STOP,
        storage={1: 1},
    )

    intrinsic = fork.transaction_intrinsic_cost_calculator()()
    executed = (
        intrinsic + caller_code.gas_cost(fork) + callee_code.gas_cost(fork)
    )
    gas_limit = executed + 5_000

    sender = pre.fund_eoa(amount=INITIAL_BALANCE)
    tx = Transaction(
        sender=sender,
        to=caller,
        gas_limit=gas_limit,
        gas_price=GAS_PRICE,
    )

    # The refund is capped at a fork-defined fraction of the executed
    # gas. A single clear stays well under it, so the earned refund is
    # what the balance pins.
    refund = min(
        caller_code.refund(fork) + callee_code.refund(fork),
        executed // fork.max_refund_quotient(),
    )
    gas_used = executed - refund

    post = {
        caller: Account(storage={0: 1, 1: 1}),
        callee: Account(storage={}),
        sender: Account(balance=INITIAL_BALANCE - gas_used * GAS_PRICE),
    }

    state_test(pre=pre, post=post, tx=tx)
