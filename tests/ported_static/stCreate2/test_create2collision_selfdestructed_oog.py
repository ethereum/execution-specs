"""
Verify a CREATE2 whose target address holds a pre-existing account that
SELFDESTRUCTed earlier in the same transaction: the collision stands
(the account is only emptied, not freed), consuming the child's grant,
and the sized budget then runs the creating init code out of gas so the
whole creation transaction rolls back — including the selfdestruct's
balance transfer.

Ported from:
state_tests/stCreate2/create2collisionSelfdestructedOOGFiller.json

@manually-enhanced: Do not overwrite. Collider and beneficiary addresses
are computed instead of hardcoded, the budget is derived from fork
composites, and the post-collision work is sized above the collision's
1/64 retention on every fork (the alive collider means the CREATE2
charges — and refunds — no new-account state gas).
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
# Gas left for the collision to consume: the CREATE2's child grant. Its
# 1/64 retention (plus any state refund) must stay below the two-store
# victim cost, which the guard below asserts.
CHILD_GRANT_SLACK = 30_000


@pytest.mark.ported_from(
    ["state_tests/stCreate2/create2collisionSelfdestructedOOGFiller.json"],
)
@pytest.mark.valid_from("Constantinople")
@pytest.mark.parametrize(
    "inner_initcode",
    [
        pytest.param(Bytecode(), id="empty_initcode"),
        pytest.param(Op.SSTORE(key=0x1, value=0x1), id="storing_initcode"),
        pytest.param(
            Op.MSTORE(offset=0x0, value=0x6001600155)
            + Op.RETURN(offset=0x1B, size=0x5),
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
    # init code below through its hash) and selfdestructs when called;
    # its address is derived from the pre-funded sender, so the pre
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
    # and runs the CREATE2 into the collision; the two stores after it
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

    # The budget covers everything up to and including the CREATE2's own
    # charges plus the slack the collision consumes; the guard proves
    # the victims exceed what the collision leaves behind, so the outer
    # frame must die and the whole creation rolls back. The collider is
    # alive at the CREATE2 (only emptied by its selfdestruct), so no
    # new-account state gas is charged — or refunded — there.
    gas_limit = (
        fork.transaction_intrinsic_cost_calculator()(
            calldata=outer_initcode,
            contract_creation=True,
        )
        + fork.transaction_top_frame_state_gas(contract_creation=True)
        + call_code.gas_cost(fork)
        + collider_work.gas_cost(fork)
        + setup.gas_cost(fork)
        + create2_code.gas_cost(fork)
        + CHILD_GRANT_SLACK
    )
    leftover = CHILD_GRANT_SLACK // 64
    assert leftover + 2_500 < victim_stores.gas_cost(fork), (
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
