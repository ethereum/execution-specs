"""
Verify that changing a storage slot from one non-zero value to another
earns no refund.

Ported from:
state_tests/stRefundTest/refund_changeNonZeroStorageFiller.json

@manually-enhanced: Do not overwrite. The gas used is derived from the fork:
intrinsic cost plus the cold non-zero to non-zero SSTORE, with no refund. The
fee recipient's priority fee and block reward are checked with `Tip` and
`BlockReward`.
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
    ["state_tests/stRefundTest/refund_changeNonZeroStorageFiller.json"],
)
@pytest.mark.valid_from("Frontier")
@pytest.mark.execute(
    pytest.mark.skip(reason="requires env.fee_recipient as block coinbase")
)
def test_refund_change_non_zero_storage(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Reset a cold storage slot from 1 to 23 and charge the full cost."""
    sender = pre.fund_eoa()

    code = Op.SSTORE(
        key=0x1, value=0x17, key_warm=False, original_value=1, new_value=23
    )
    assert code.refund(fork) == 0
    target = pre.deploy_contract(
        code=code + Op.STOP,
        storage={1: 1},
    )

    tx = Transaction(
        sender=sender,
        to=target,
        gas_limit=228500,
        value=10,
        protected=fork.supports_protected_txs(),
    )

    gas_used = fork.transaction_intrinsic_cost_calculator()(
        sends_value=True
    ) + code.gas_cost(fork)

    post = {
        target: Account(storage={1: 23}, balance_change=tx.value),
        sender: Account(balance_change=-tx.value - GasFee(tx, gas=gas_used)),
    }
    post[Environment().fee_recipient] = Account(
        balance_change=Tip(tx, gas=gas_used) + BlockReward(tx)
    )

    state_test(pre=pre, post=post, tx=tx)
