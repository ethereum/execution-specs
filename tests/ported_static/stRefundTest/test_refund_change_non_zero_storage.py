"""
Test_refund_change_non_zero_storage.

Ported from:
state_tests/stRefundTest/refund_changeNonZeroStorageFiller.json

@manually-enhanced: Do not overwrite. The post-state asserts the sender
balance, which equals its start minus `gas_used * gas_price`. The
contract resets one warm-after-cold storage slot from a non-zero value
to another non-zero value (1 -> 23); EIP-8038 raises this cold
SSTORE-reset charge from 5000 to 13000. There is no storage-clear
refund, so `gas_used` rises by exactly the charge delta. Derive that
delta from the fork gas model (0 pre-EIP-8037) and subtract
`gas_price * delta` from the Cancun balance; do not hardcode the
Amsterdam value.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stRefundTest/refund_changeNonZeroStorageFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_refund_change_non_zero_storage(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test_refund_change_non_zero_storage."""
    coinbase = Address(0xEB201D2887816E041F6E807E804F64F3A7A226FE)
    sender = pre.fund_eoa(amount=0x3C336080)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[coinbase] = Account(balance=0, nonce=1)
    # Source: lll
    # { [[ 1 ]] 23 }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x17) + Op.STOP,
        storage={1: 1},
        balance=0xDE0B6B3A7640000,
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=228500,
        value=10,
    )

    # EIP-8038 raises the cold SSTORE-reset charge (non-zero to non-zero);
    # with no storage-clear refund, gas_used rises by the full delta.
    cold_reset_delta = (
        Op.SSTORE.with_metadata(
            key_warm=False, original_value=1, current_value=1, new_value=23
        ).gas_cost(fork)
        - 5000
    )

    post = {
        target: Account(storage={1: 23}, balance=0xDE0B6B3A764000A),
        coinbase: Account(balance=0),
        sender: Account(balance=0x3C2F689A - 10 * cold_reset_delta, nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
