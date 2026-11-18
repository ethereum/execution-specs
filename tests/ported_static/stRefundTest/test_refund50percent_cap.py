"""
Verify the refund cap over six storage clears: the sender's final
balance reflects the executed gas minus the capped refund.

Ported from:
state_tests/stRefundTest/refund50percentCapFiller.json

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
    GasFee,
    StateTestFiller,
    Tip,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

CONTRACT_BALANCE = 0xDE0B6B3A7640000


@pytest.mark.ported_from(
    ["state_tests/stRefundTest/refund50percentCapFiller.json"],
)
@pytest.mark.valid_from("Frontier")
@pytest.mark.execute(
    pytest.mark.skip(reason="requires env.fee_recipient as block coinbase")
)
def test_refund50percent_cap(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
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
        + Op.SSTORE(
            key=0xA,
            value=Op.EXP(0x2, 0xFF, exponent=0xFF),
            key_warm=False,
            original_value=0,
            new_value=2**255,
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
    gas_limit = executed + 5_000

    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        to=target,
        gas_limit=gas_limit,
        protected=fork.supports_protected_txs(),
    )

    # The refund is capped at a fork-defined fraction of the executed
    # gas.
    refund = min(code.refund(fork), executed // fork.max_refund_quotient())
    gas_used = executed - refund

    post = {
        target: Account(
            storage={0xA: 2**255, 0xB: CONTRACT_BALANCE},
        ),
        sender: Account(balance_change=-GasFee(tx, gas=gas_used)),
    }

    post[Environment().fee_recipient] = Account(
        balance_change=Tip(tx, gas=gas_used) + BlockReward(tx)
    )

    state_test(pre=pre, post=post, tx=tx)
