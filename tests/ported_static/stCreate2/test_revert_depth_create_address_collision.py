"""
Verify a CREATE2 that collides with a live account, its own caller: the
collision burns the child's grant and bumps the creator's nonce without
creating anything, and the two stacked budgets decide whether the
creator survives its aftermath, dies on it, or the whole outer frame
runs dry after it.

Ported from:
state_tests/stCreate2/RevertDepthCreateAddressCollisionFiller.json
state_tests/stCreate2/RevertDepthCreateAddressCollisionBerlinFiller.json

@manually-enhanced: Do not overwrite. The byte-identical Berlin twin is
folded in, and the legacy fillers' vacancy is repaired: they kept the
collider at contract_1's CREATE address while the code runs CREATE2, so
nothing ever collided. The caller now occupies the CREATE2 target, the
creator pre-writes its result slot so the post-collision store is a
dirty-warm write its 1/64 retention can afford, every arm reaches the
collision, and all budgets derive from fork composites.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    Hash,
    StateTestFiller,
    Transaction,
    compute_create2_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

# Caller slots (as in the ported filler).
CALLER_START_SLOT = 0x0
CALL_RESULT_SLOT = 0x1
CALLER_DONE_SLOT = 0x4
# Creator slots: 0x2 as ported, plus the pre-written CREATE2 result.
CREATOR_START_SLOT = 0x2
CREATE2_RESULT_SLOT = 0x5
# Pre-written sentinel, overwritten by the CREATE2 result plus one: a
# surviving creator must show 1 (collision), never 0xFF or an address.
RESULT_PREWRITE = 0xFF

# Post-collision slack for the starved-creator arm: retains under 1/64th
# of the EIP-2200 stipend, so the result store cannot run.
STARVED_SLACK = 10_000
# What the covered creator keeps after its result store, on top of the
# EIP-2200 stipend gate that store must clear.
RETENTION_MARGIN = 100


@pytest.mark.ported_from(
    [
        "state_tests/stCreate2/RevertDepthCreateAddressCollisionFiller.json",
        "state_tests/stCreate2/RevertDepthCreateAddressCollisionBerlinFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Constantinople")
@pytest.mark.parametrize(
    "creator_covered",
    [
        pytest.param(False, id="creator_oog"),
        pytest.param(True, id="creator_ok"),
    ],
)
@pytest.mark.parametrize(
    "outer_covered",
    [
        pytest.param(False, id="outer_oog"),
        pytest.param(True, id="outer_ok"),
    ],
)
@pytest.mark.parametrize("tx_value", [1, 0])
@pytest.mark.pre_alloc_mutable
def test_revert_depth_create_address_collision(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    creator_covered: bool,
    outer_covered: bool,
    tx_value: int,
) -> None:
    """A CREATE2 collision burns the grant; budgets decide what's left."""
    # The creator: entry marker, result-slot pre-write, then the CREATE2
    # aimed at the caller's (occupied) address, whose result overwrites
    # the sentinel as a dirty-warm store the 1/64 retention can pay.
    sstore_2 = Op.SSTORE(
        key=CREATOR_START_SLOT,
        value=0x8,
        key_warm=False,
        original_value=0,
        new_value=0x8,
    )
    sentinel_store = Op.SSTORE(
        key=CREATE2_RESULT_SLOT,
        value=RESULT_PREWRITE,
        key_warm=False,
        original_value=0,
        new_value=RESULT_PREWRITE,
    )
    create2_code = Op.CREATE2(
        value=0x0,
        offset=0x0,
        size=0x0,
        salt=0x0,
        account_new=False,
    )
    result_store = Op.SSTORE(
        key=CREATE2_RESULT_SLOT,
        value=Op.ADD(0x1, create2_code),
        key_warm=True,
        original_value=0,
        current_value=RESULT_PREWRITE,
        new_value=0x1,
    )
    creator = pre.deploy_contract(
        code=sstore_2 + sentinel_store + result_store + Op.STOP
    )

    # The caller occupies the creator's CREATE2 target (this is the
    # repaired collision, and why the pre allocation must stay mutable).
    sstore_0 = Op.SSTORE(
        key=CALLER_START_SLOT,
        value=0x1,
        key_warm=False,
        original_value=0,
        new_value=0x1,
    )
    call_code = Op.CALL(
        gas=Op.CALLDATALOAD(offset=0x0),
        address=creator,
        address_warm=False,
        value_transfer=False,
        account_new=False,
    )
    sstore_1 = Op.SSTORE(
        key=CALL_RESULT_SLOT,
        value=call_code,
        key_warm=False,
        original_value=0,
        new_value=0x1,
    )
    sstore_4 = Op.SSTORE(
        key=CALLER_DONE_SLOT,
        value=0xC,
        key_warm=False,
        original_value=0,
        new_value=0xC,
    )
    caller_code = sstore_0 + sstore_1 + sstore_4 + Op.STOP
    caller = compute_create2_address(creator, 0, b"")
    pre.deploy_contract(code=caller_code, address=caller)

    # The collision consumes everything left after the CREATE2's charges
    # but one 64th (the live target means no new-account state gas moves
    # in either direction), so the creator's fate is set by the slack
    # riding on top of its pre-collision costs.
    create2_charge = create2_code.gas_cost(fork)
    result_tail = result_store.gas_cost(fork) - create2_charge
    stipend = fork.gas_costs().CALL_STIPEND
    if creator_covered:
        slack = 64 * (stipend + result_tail + RETENTION_MARGIN)
    else:
        slack = STARVED_SLACK
        assert slack // 64 <= stipend, (
            "the retention must not afford the result store"
        )
    forwarded = (
        sstore_2.gas_cost(fork)
        + sentinel_store.gas_cost(fork)
        + create2_charge
        + slack
    )

    tx_data = Hash(forwarded)
    overhead = fork.transaction_intrinsic_cost_calculator()(
        calldata=tx_data,
        sends_value=tx_value > 0,
        return_cost_deducted_prior_execution=True,
    ) + sstore_0.gas_cost(fork)
    # Enough at the CALL that the EIP-150 clamp still grants the full
    # ask.
    available = -(-forwarded * 64 // 63) + 64
    assert available - available // 64 >= forwarded, (
        "the full ask must be granted"
    )
    if outer_covered:
        gas_limit = (
            overhead
            + sstore_1.gas_cost(fork)
            + sstore_4.gas_cost(fork)
            + available
        )
    else:
        # Nothing is budgeted for the caller's post-call stores: what the
        # 1/64 retention and a surviving creator's leftovers add up to
        # cannot pay the completion marker, so the caller dies after the
        # collision.
        creator_spare = stipend + RETENTION_MARGIN if creator_covered else 0
        assert available // 64 + creator_spare < sstore_4.gas_cost(fork), (
            "the retention must not afford the post-call stores"
        )
        gas_limit = overhead + available

    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        to=caller,
        data=tx_data,
        gas_limit=gas_limit,
        value=tx_value,
    )

    if not outer_covered:
        # The whole transaction ran dry after the collision: only the
        # code survives.
        caller_account = Account(
            storage={}, code=caller_code, balance=0, nonce=1
        )
        creator_account = Account(storage={}, nonce=1)
    elif not creator_covered:
        # The creator reached the collision but died on its aftermath
        # and was rolled back — including the collision's nonce bump.
        caller_account = Account(
            storage={
                CALLER_START_SLOT: 0x1,
                CALL_RESULT_SLOT: 0x0,
                CALLER_DONE_SLOT: 0xC,
            },
            code=caller_code,
            balance=tx_value,
            nonce=1,
        )
        creator_account = Account(storage={}, nonce=1)
    else:
        # The collision's signature: a nonce bump with nothing created,
        # a zero CREATE2 result, and the caller's account untouched.
        caller_account = Account(
            storage={
                CALLER_START_SLOT: 0x1,
                CALL_RESULT_SLOT: 0x1,
                CALLER_DONE_SLOT: 0xC,
            },
            code=caller_code,
            balance=tx_value,
            nonce=1,
        )
        creator_account = Account(
            storage={
                CREATOR_START_SLOT: 0x8,
                CREATE2_RESULT_SLOT: 0x1,
            },
            nonce=2,
        )

    post = {
        sender: Account(nonce=1),
        caller: caller_account,
        creator: creator_account,
    }

    state_test(pre=pre, post=post, tx=tx)
