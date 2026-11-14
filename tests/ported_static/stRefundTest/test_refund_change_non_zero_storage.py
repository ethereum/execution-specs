"""
Test_refund_change_non_zero_storage.

Ported from:
state_tests/stRefundTest/refund_changeNonZeroStorageFiller.json

@manually-enhanced: Do not overwrite. The post-state asserts the sender
fee, `gas_used * gas_price`. The contract resets one warm-after-cold
storage slot from a non-zero value to another non-zero value (1 -> 23);
EIP-8038 raises this cold SSTORE-reset charge. There is no storage-clear
refund, so `gas_used` rises by exactly the charge delta. Derive that
delta from the fork gas model (0 pre-EIP-8037) and add it to the Cancun
gas used; do not hardcode the Amsterdam value.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    GasFee,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Cancun, Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stRefundTest/refund_changeNonZeroStorageFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_refund_change_non_zero_storage(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test_refund_change_non_zero_storage."""
    sender = pre.fund_eoa()

    # Source: lll
    # { [[ 1 ]] 23 }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x17) + Op.STOP,
        storage={1: 1},
    )

    tx = Transaction(
        sender=sender,
        to=target,
        gas_limit=228500,
        value=10,
    )

    # EIP-8038 raises the cold SSTORE-reset charge (non-zero to non-zero);
    # with no storage-clear refund, gas_used rises by the full delta.
    cold_reset = Op.SSTORE.with_metadata(
        key_warm=False, original_value=1, current_value=1, new_value=23
    )
    cold_reset_delta = cold_reset.gas_cost(fork) - cold_reset.gas_cost(Cancun)

    post = {
        target: Account(storage={1: 23}, balance_change=tx.value),
        sender: Account(
            balance_change=-tx.value - GasFee(tx, gas=26006 + cold_reset_delta)
        ),
    }

    state_test(pre=pre, post=post, tx=tx)
