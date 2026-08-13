"""
Verify a contract-creation transaction whose target address already holds
code or a non-zero nonce: the collision aborts the creation, consumes the
whole gas limit, transfers no value, and leaves the existing account
untouched.

A target holding only a balance is not a collision -- creation proceeds --
which is `test_transaction_collision_to_empty2`.

Ported from:
state_tests/stCreateTest/TransactionCollisionToEmptyButCodeFiller.json
state_tests/stCreateTest/TransactionCollisionToEmptyButNonceFiller.json

@manually-enhanced: Do not overwrite. Budgets are derived from the fork
(bare intrinsic and a fully-funded creation); the post asserts the
colliding account's code, nonce, and unchanged zero balance. The two
fillers, which differ only in which field the target already holds, are
folded into one parametrize.
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
    [
        "state_tests/stCreateTest/TransactionCollisionToEmptyButCodeFiller.json",  # noqa: E501
        "state_tests/stCreateTest/TransactionCollisionToEmptyButNonceFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Berlin")
@pytest.mark.parametrize("collision", ["code", "nonce"])
@pytest.mark.parametrize(
    "full_budget", [True, False], ids=["full-budget", "intrinsic-only"]
)
@pytest.mark.parametrize("tx_value", [0, 1], ids=["v0", "v1"])
@pytest.mark.pre_alloc_mutable
def test_transaction_collision(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    collision: str,
    full_budget: bool,
    tx_value: int,
) -> None:
    """Creation collision burns the whole gas limit whatever the budget."""
    # Init code that would store a flag if it ever ran.
    initcode = Op.SSTORE(
        key=0x1,
        value=0x1,
        key_warm=False,
        original_value=0,
        new_value=1,
    )

    # No `return_cost_deducted_prior_execution` here: this is the floor a
    # transaction must clear to be valid at all, not a budget for execution.
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

    # The target is empty but for the one field that makes it collide. The
    # same account is the expected post-state, which is the whole point:
    # nothing about it changes.
    colliding_account = Account(
        code=COLLIDING_CODE if collision == "code" else b"",
        nonce=1 if collision == "nonce" else 0,
        balance=0,
        storage={},
    )

    sender = pre.fund_eoa()
    created = compute_create_address(address=sender, nonce=0)
    pre[created] = colliding_account

    tx = Transaction(
        sender=sender,
        to=None,
        data=initcode,
        gas_limit=gas_limit,
        value=tx_value,
    )

    post = {
        sender: Account(nonce=1),
        # Untouched: the init code never ran and the value never arrived.
        created: colliding_account,
    }

    state_test(
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=gas_limit),
    )
