"""
Verify the refund cap over five storage clears: the sender's final
balance reflects the executed gas minus the capped refund.

Ported from:
state_tests/stRefundTest/refund50_2Filler.json

@manually-enhanced: Do not overwrite. The sender's balance, the refund cap
and the transaction budget all derive from the fork (`code.gas_cost` /
`code.refund` composites), so EIP-8037's repriced stores and any future
refund change are tracked instead of pinned.
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
    ["state_tests/stRefundTest/refund50_2Filler.json"],
)
@pytest.mark.valid_from("Berlin")
def test_refund50_2(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Five storage clears refund gas up to the fork's cap."""
    code = (
        Op.SSTORE(
            key=0xA, value=0x1, key_warm=False, original_value=0, new_value=1
        )
        + Op.SSTORE(
            key=0xB, value=0x1, key_warm=False, original_value=0, new_value=1
        )
        + Op.SSTORE(
            key=0x1, value=0x0, key_warm=False, original_value=1, new_value=0
        )
        + Op.SSTORE(
            key=0x2, value=0x0, key_warm=False, original_value=1, new_value=0
        )
        + Op.SSTORE(
            key=0x3, value=0x0, key_warm=False, original_value=1, new_value=0
        )
        + Op.SSTORE(
            key=0x4, value=0x0, key_warm=False, original_value=1, new_value=0
        )
        + Op.SSTORE(
            key=0x5, value=0x0, key_warm=False, original_value=1, new_value=0
        )
    )
    target = pre.deploy_contract(
        code=code + Op.STOP,
        storage={1: 1, 2: 1, 3: 1, 4: 1, 5: 1},
    )

    intrinsic = fork.transaction_intrinsic_cost_calculator()()
    executed = intrinsic + code.gas_cost(fork)
    gas_limit = executed + 5_000

    sender = pre.fund_eoa(amount=INITIAL_BALANCE)
    tx = Transaction(
        sender=sender,
        to=target,
        gas_limit=gas_limit,
        gas_price=GAS_PRICE,
    )

    # The refund is capped at a fork-defined fraction of the executed
    # gas. On EIP-8037 forks the repriced fresh sets lift that cap above
    # the five clears' refund, which then binds instead.
    refund = min(code.refund(fork), executed // fork.max_refund_quotient())
    gas_used = executed - refund

    post = {
        target: Account(storage={0xA: 1, 0xB: 1}),
        sender: Account(balance=INITIAL_BALANCE - gas_used * GAS_PRICE),
    }

    state_test(pre=pre, post=post, tx=tx)
