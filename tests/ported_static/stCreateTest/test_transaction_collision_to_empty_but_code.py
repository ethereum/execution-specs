"""
Verify a contract-creation transaction whose target address already holds
code: the collision aborts the creation, consumes the whole gas limit,
transfers no value, and leaves the existing account untouched.

Ported from:
state_tests/stCreateTest/TransactionCollisionToEmptyButCodeFiller.json

@manually-enhanced: Do not overwrite. Budgets are derived from the fork
(bare intrinsic and a fully-funded creation); the post asserts the
colliding account's code, nonce, and unchanged zero balance.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    Header,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

# Any non-empty code at the target address triggers the collision.
COLLIDING_CODE = bytes.fromhex("1122334455")


@pytest.mark.ported_from(
    ["state_tests/stCreateTest/TransactionCollisionToEmptyButCodeFiller.json"],
)
@pytest.mark.valid_from("Berlin")
@pytest.mark.parametrize(
    "full_budget", [True, False], ids=["full-budget", "intrinsic-only"]
)
@pytest.mark.parametrize("tx_value", [0, 1], ids=["v0", "v1"])
@pytest.mark.pre_alloc_mutable
def test_transaction_collision_to_empty_but_code(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    full_budget: bool,
    tx_value: int,
) -> None:
    """Creation collision with code burns the whole gas limit."""
    # Init code that would store a flag if it ever ran.
    initcode = Op.SSTORE(
        key=0x1,
        value=0x1,
        key_warm=False,
        original_value=0,
        new_value=1,
    )

    intrinsic = fork.transaction_intrinsic_cost_calculator()(
        calldata=initcode,
        contract_creation=True,
        sends_value=tx_value > 0,
    )
    if full_budget:
        # Enough to fund the whole creation (even at the fresh-target
        # EIP-8037 price) — the collision must still consume all of it.
        gas_limit = (
            intrinsic
            + fork.transaction_top_frame_state_gas(contract_creation=True)
            + initcode.gas_cost(fork)
        )
    else:
        gas_limit = intrinsic

    sender = pre.fund_eoa()
    created = compute_create_address(address=sender, nonce=0)
    pre[created] = Account(code=COLLIDING_CODE)

    tx = Transaction(
        sender=sender,
        to=None,
        data=initcode,
        gas_limit=gas_limit,
        value=tx_value,
    )

    post = {
        sender: Account(nonce=1),
        # The colliding account is untouched: the init code never ran and
        # the transferred value never arrived.
        created: Account(storage={}, code=COLLIDING_CODE, nonce=0, balance=0),
    }

    state_test(
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=gas_limit),
    )
