"""
Verify a CREATE2 whose target address holds a pre-existing account that
SELFDESTRUCTed earlier in the same transaction: the collision stands
(the account is only emptied, not freed), consuming the child's grant,
and the sized budget then runs the creating init code out of gas so the
whole creation transaction rolls back, including the selfdestruct's
balance transfer.

Ported from:
state_tests/stCreate2/create2collisionSelfdestructedOOGFiller.json

@manually-enhanced: Do not overwrite. Collider and beneficiary addresses
are computed instead of hardcoded, and the budget derives from fork
composites: the CREATE2's slack would fund the post-collision stores had
the creation gone through, so the rollback is attributable to the
collision's burned grant on every fork.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Fork,
    StateTestFiller,
    Transaction,
    compute_create2_address,
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

COLLIDER_BALANCE = 1
# Head room on top of the slack the CREATE2 finds when it runs.
SLACK_MARGIN = 5_000


@pytest.mark.ported_from(
    ["state_tests/stCreate2/create2collisionSelfdestructedOOGFiller.json"],
)
@pytest.mark.valid_from("Constantinople")
@pytest.mark.parametrize(
    "inner_initcode",
    [
        pytest.param(Bytecode(), id="empty_initcode"),
        pytest.param(
            Op.SSTORE(
                key=0x1,
                value=0x1,
                key_warm=False,
                original_value=0,
                new_value=1,
            ),
            id="storing_initcode",
        ),
        pytest.param(
            Op.MSTORE(offset=0x0, value=0x6001600155, new_memory_size=0x20)
            + Op.RETURN(offset=0x1B, size=0x5, code_deposit_size=0x5),
            id="depositing_initcode",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_create2collision_selfdestructed_oog(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    inner_initcode: Bytecode,
) -> None:
    """A selfdestructed account still collides, and its grant is lost."""
    sender = pre.fund_eoa()
    outer_created = compute_create_address(address=sender, nonce=0)

    # The collider occupies the CREATE2 target (which depends on the
    # init code below through its hash) and selfdestructs when called.
    # Its address is derived from the pre-funded sender, so the pre
    # allocation must stay mutable.
    beneficiary = pre.nonexistent_account()
    collider_work = Op.SELFDESTRUCT(
        address=beneficiary,
        address_warm=False,
        account_new=True,
    )
    collider = compute_create2_address(outer_created, 0, inner_initcode)
    pre.deploy_contract(
        code=collider_work,
        balance=COLLIDER_BALANCE,
        address=collider,
    )

    # The outer init code selfdestructs the collider, stages the child's
    # init code (never executed: the collision aborts before dispatch)
    # and runs the CREATE2 into the collision. The two stores after it
    # are the victims the burned grant leaves unaffordable.
    inner_bytes = bytes(inner_initcode)
    assert len(inner_bytes) <= 0x20, "inner init code must fit one word"
    call_code = Op.CALL(
        address=collider,
        address_warm=False,
        value_transfer=False,
        account_new=False,
    )
    setup = (
        Op.MSTORE(
            offset=0x0,
            value=int.from_bytes(inner_bytes, "big"),
            new_memory_size=0x20,
        )
        if inner_bytes
        else Bytecode()
    )
    create2_code = Op.CREATE2(
        value=0x0,
        offset=0x20 - len(inner_bytes) if inner_bytes else 0x0,
        size=len(inner_bytes),
        salt=0x0,
        new_memory_size=0x20 if inner_bytes else 0x0,
        old_memory_size=0x20 if inner_bytes else 0x0,
        init_code_size=len(inner_bytes),
        account_new=False,
    )
    victim_stores = Op.SSTORE(
        key=0x0,
        value=0x112233,
        key_warm=False,
        original_value=0,
        new_value=0x112233,
    ) + Op.SSTORE(
        key=0x1,
        value=0x112233,
        key_warm=False,
        original_value=0,
        new_value=0x112233,
    )
    outer_initcode = (
        Op.POP(call_code) + setup + Op.POP(create2_code) + victim_stores
    )

    # The slack is what the CREATE2 finds when it runs. It would pay for
    # the victims even if a client let the creation through (freeing the
    # selfdestructed target, so charging it as a new account, and running
    # the child), so only the collision's burn can starve them. The
    # collider is alive at the CREATE2 (only emptied by its selfdestruct),
    # so no new-account state gas is charged there.
    new_account_state = Op.CREATE2(
        value=0x0, offset=0x0, size=0x0, salt=0x0
    ).state_cost(fork)
    slack = (
        victim_stores.gas_cost(fork)
        + new_account_state
        + inner_initcode.gas_cost(fork)
        + SLACK_MARGIN
    )
    gas_limit = (
        fork.transaction_intrinsic_cost_calculator()(
            calldata=outer_initcode,
            contract_creation=True,
            return_cost_deducted_prior_execution=True,
        )
        + fork.transaction_top_frame_state_gas(contract_creation=True)
        + call_code.gas_cost(fork)
        + collider_work.gas_cost(fork)
        + setup.gas_cost(fork)
        + create2_code.gas_cost(fork)
        + slack
    )
    # The collision leaves one 64th of the slack: never the victims.
    assert slack // 64 < victim_stores.gas_cost(fork), (
        "the collision's leavings must not afford the victim stores"
    )

    tx = Transaction(
        sender=sender,
        to=None,
        data=outer_initcode,
        gas_limit=gas_limit,
    )

    post = {
        sender: Account(nonce=1),
        # Rolled back wholesale: the collider keeps its code and its
        # balance, the beneficiary was never credited, nothing created.
        collider: Account(
            code=collider_work,
            balance=COLLIDER_BALANCE,
            nonce=1,
        ),
        beneficiary: Account.NONEXISTENT,
        outer_created: Account.NONEXISTENT,
    }

    state_test(pre=pre, post=post, tx=tx)
