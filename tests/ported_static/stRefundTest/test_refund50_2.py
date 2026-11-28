"""
Verify the refund cap over five storage clears: the sender's final
balance reflects the executed gas minus the capped refund.

Ported from:
state_tests/stRefundTest/refund50_2Filler.json

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


@pytest.mark.ported_from(
    ["state_tests/stRefundTest/refund50_2Filler.json"],
)
@pytest.mark.valid_from("Frontier")
@pytest.mark.execute(
    pytest.mark.skip(reason="requires env.fee_recipient as block coinbase")
)
def test_refund50_2(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Five storage clears refund gas up to the fork's cap."""
    # Two cold slots go from zero to one, then five cold slots that were
    # set in the pre-state are cleared.
    cold_set = Op.SSTORE.with_metadata(
        key_warm=False, original_value=0, current_value=0, new_value=1
    )
    cold_clear = Op.SSTORE.with_metadata(
        key_warm=False, original_value=1, current_value=1, new_value=0
    )
    code = (
        cold_set(key=0xA, value=0x1)
        + cold_set(key=0xB, value=0x1)
        + cold_clear(key=0x1, value=0x0)
        + cold_clear(key=0x2, value=0x0)
        + cold_clear(key=0x3, value=0x0)
        + cold_clear(key=0x4, value=0x0)
        + cold_clear(key=0x5, value=0x0)
    )
    target = pre.deploy_contract(
        code=code + Op.STOP,
        storage={1: 1, 2: 1, 3: 1, 4: 1, 5: 1},
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
    # gas. On EIP-8037 forks the repriced fresh sets lift that cap above
    # the five clears' refund, which then binds instead.
    refund = min(code.refund(fork), executed // fork.max_refund_quotient())
    gas_used = executed - refund

    post = {
        target: Account(storage={0xA: 1, 0xB: 1}),
        sender: Account(balance_change=-GasFee(tx, gas=gas_used)),
    }
    post[Environment().fee_recipient] = Account(
        balance_change=Tip(tx, gas=gas_used) + BlockReward(tx)
    )

    state_test(pre=pre, post=post, tx=tx)
