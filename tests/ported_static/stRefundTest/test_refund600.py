"""
Verify the EIP-3529 refund cap over six storage clears: the sender's final
balance reflects the executed gas minus the capped refund.

Ported from:
state_tests/stRefundTest/refund600Filler.json

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

CONTRACT_BALANCE = 0xDE0B6B3A7640000
INITIAL_BALANCE = 10**18
GAS_PRICE = 10


@pytest.mark.ported_from(
    ["state_tests/stRefundTest/refund600Filler.json"],
)
@pytest.mark.valid_from("London")
def test_refund600(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Six storage clears refund gas up to the EIP-3529 cap."""
    code = (
        Op.POP(Op.SLOAD(key=0x1, key_warm=False))
        + Op.POP(Op.SLOAD(key=0x2, key_warm=False))
        # EXP(2, 0xFFFF) wraps to 0 mod 2^256, so this store is a no-op.
        + Op.SSTORE(
            key=0xA,
            value=Op.EXP(0x2, 0xFFFF, exponent=0xFFFF),
            key_warm=False,
            original_value=0,
            new_value=0,
        )
        + Op.SSTORE(
            key=0xB,
            value=Op.BALANCE(address=Op.ADDRESS, address_warm=True),
            key_warm=False,
            original_value=0,
            new_value=1,
        )
        + Op.SSTORE(
            key=0x1, value=0x0, key_warm=True, original_value=1, new_value=0
        )
        + Op.SSTORE(
            key=0x2, value=0x0, key_warm=True, original_value=1, new_value=0
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
        + Op.SSTORE(
            key=0x6, value=0x0, key_warm=False, original_value=1, new_value=0
        )
    )
    target = pre.deploy_contract(
        code=code + Op.STOP,
        storage={1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1},
        balance=CONTRACT_BALANCE,
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

    # EIP-3529 caps the refund at a fifth of the executed gas.
    refund = min(code.refund(fork), executed // 5)
    gas_used = executed - refund

    post = {
        target: Account(
            storage={0xA: 0, 0xB: CONTRACT_BALANCE},
        ),
        sender: Account(balance=INITIAL_BALANCE - gas_used * GAS_PRICE),
    }

    state_test(pre=pre, post=post, tx=tx)
