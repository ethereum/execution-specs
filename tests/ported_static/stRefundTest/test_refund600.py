"""
Verify the refund cap over six storage clears: the sender's final
balance reflects the executed gas minus the capped refund.

Ported from:
state_tests/stRefundTest/refund600Filler.json

@manually-enhanced: Do not overwrite. The sender's balance, the refund cap and
the transaction budget all derive from the fork (`code.gas_cost` /
`code.refund` composites), so EIP-8037's repriced stores and any future refund
change are tracked instead of pinned. The fee recipient's priority fee and
block reward are checked with `Tip` and `BlockReward`.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    BlockReward,
    Environment,
    Fork,
    Op,
    StateTestFiller,
    Tip,
    Transaction,
    TransactionReceipt,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

CONTRACT_BALANCE = 0x1


@pytest.mark.ported_from(
    ["state_tests/stRefundTest/refund600Filler.json"],
)
@pytest.mark.valid_from("Frontier")
@pytest.mark.execute(
    pytest.mark.skip(reason="requires env.fee_recipient as block coinbase")
)
def test_refund600(
    state_test: StateTestFiller, pre: Alloc, fork: Fork
) -> None:
    """Six storage clears refund gas up to the fork's cap."""
    # Slots 1 and 2 are warmed by the SLOADs before being cleared; the
    # other four clears touch cold slots.
    warm_clear = Op.SSTORE.with_metadata(
        key_warm=True, original_value=1, current_value=1, new_value=0
    )
    cold_clear = Op.SSTORE.with_metadata(
        key_warm=False, original_value=1, current_value=1, new_value=0
    )
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
        + warm_clear(key=0x1, value=0x0)
        + warm_clear(key=0x2, value=0x0)
        + cold_clear(key=0x3, value=0x0)
        + cold_clear(key=0x4, value=0x0)
        + cold_clear(key=0x5, value=0x0)
        + cold_clear(key=0x6, value=0x0)
    )
    target = pre.deploy_contract(
        code=code + Op.STOP,
        storage={1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1},
        balance=CONTRACT_BALANCE,
    )

    intrinsic = fork.transaction_intrinsic_cost_calculator()()
    executed = intrinsic + code.gas_cost(fork)

    sender = pre.fund_eoa()

    # The refund is capped at a fork-defined fraction of the executed
    # gas: half before EIP-3529, a fifth from it on.
    refund = min(code.refund(fork), executed // fork.max_refund_quotient())
    gas_used = executed - refund
    tx = Transaction(
        sender=sender,
        to=target,
        expected_receipt=TransactionReceipt(cumulative_gas_used=gas_used),
        protected=fork.supports_protected_txs(),
    )

    post = {target: Account(storage={0xA: 0, 0xB: CONTRACT_BALANCE})}

    post[Environment().fee_recipient] = Account(
        balance_change=Tip(tx, gas=gas_used) + BlockReward(tx)
    )

    state_test(pre=pre, post=post, tx=tx)
