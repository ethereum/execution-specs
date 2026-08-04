"""
The test check if the create transaction is reject if the origin's...

(and would overflow if increased by 1).

Ported from:
state_tests/stCreateTest/CreateTransactionHighNonceFiller.yml

@manually-enhanced: Do not overwrite. `tx_gas` was raised from 90 000
to 500 000 so the transaction clears the EIP-8037 intrinsic-gas floor
on Amsterdam and the validator can actually reach the NONCE_IS_MAX
check the test asserts. Pre-Amsterdam the floor is lower, so the same
budget still triggers the same exception path.
"""

import pytest
from execution_testing import (
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
    TransactionException,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

from tests.ported_static.post_state_resolution import (
    resolve_expect_post,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stCreateTest/CreateTransactionHighNonceFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="-v0",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            0,
            0,
            1,
            id="-v1",
            marks=pytest.mark.exception_test,
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_create_transaction_high_nonce(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """The test check if the create transaction is reject if the origin's..."""
    sender = pre.fund_eoa(amount=0x5AF3107A4000, nonce=18446744073709551615)

    env = Environment(
        fee_recipient=sender,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": -1, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {},
            "expect_exception": {
                ">=Cancun": TransactionException.NONCE_IS_MAX
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Op.RETURN(offset=0x0, size=0x1),
    ]
    # Original budget (90 000) is below the EIP-8037 intrinsic-gas
    # floor for a create tx on Amsterdam, so the tx is rejected for
    # `INTRINSIC_GAS_TOO_LOW` before the NONCE_IS_MAX check this test
    # asserts ever runs. Bump on Amsterdam to clear the floor; pre-
    # EIP-8037 forks keep the original.
    nonce_check_tx_gas = 90000
    if fork.is_eip_enabled(8037):
        nonce_check_tx_gas = 500000
    tx_gas = [nonce_check_tx_gas]
    tx_value = [0, 1]

    tx = Transaction(
        sender=sender,
        to=None,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        nonce=18446744073709551615,
        error=TransactionException.NONCE_IS_MAX,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
