"""
Verify a CREATE2 two frames deep under out-of-gas pressure: the calldata
sets the grant a caller forwards to a creating contract, and the two
budgets decide whether the creation stands, the creator dies after it,
or the whole outer frame runs dry, each with a distinct post-state.

Ported from:
state_tests/stCreate2/RevertDepthCreate2OOGFiller.json
state_tests/stCreate2/RevertDepthCreate2OOGBerlinFiller.json

@manually-enhanced: Do not overwrite. The byte-identical Berlin twin is
folded in and every budget derives from fork composites. The creator
stores the CREATE2 result so a wrongly failed (or wrongly succeeding)
creation is visible beyond the created account, and every starved arm
completes the CREATE2 before running dry, so the rollback of a finished
creation is what each of them pins.
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
# Creator slots: 0x2/0x3 as ported, plus the CREATE2 result.
CREATOR_START_SLOT = 0x2
CREATOR_DONE_SLOT = 0x3
CREATE2_RESULT_SLOT = 0x5

# Gas the covered creator has left over after its completion marker.
CREATOR_SPARE = 1_000


@pytest.mark.ported_from(
    [
        "state_tests/stCreate2/RevertDepthCreate2OOGFiller.json",
        "state_tests/stCreate2/RevertDepthCreate2OOGBerlinFiller.json",
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
def test_revert_depth_create2_oog(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    creator_covered: bool,
    outer_covered: bool,
    tx_value: int,
) -> None:
    """Two stacked budgets decide how deep a nested CREATE2 gets."""
    # The creator: entry marker, an empty-init-code CREATE2 whose result
    # is stored (success leaves the created address plus one, a failure
    # leaves exactly one), and a completion marker.
    sstore_2 = Op.SSTORE(
        key=CREATOR_START_SLOT,
        value=0x8,
        key_warm=False,
        original_value=0,
        new_value=0x8,
    )
    result_store = Op.SSTORE(
        key=CREATE2_RESULT_SLOT,
        value=Op.ADD(
            0x1, Op.CREATE2(value=0x0, offset=0x0, size=0x0, salt=0x0)
        ),
        key_warm=False,
        original_value=0,
        new_value=0x1,
    )
    sstore_3 = Op.SSTORE(
        key=CREATOR_DONE_SLOT,
        value=0xC,
        key_warm=False,
        original_value=0,
        new_value=0xC,
    )
    creator = pre.deploy_contract(
        code=sstore_2 + result_store + sstore_3 + Op.STOP
    )

    # The empty-init-code child consumes nothing and returns its whole
    # grant, so the creator's needs are just its composite costs. A
    # starved creator gets through the CREATE2 and the result store and
    # dies on its completion marker, which it can only half afford.
    creator_needed = (
        sstore_2.gas_cost(fork)
        + result_store.gas_cost(fork)
        + sstore_3.gas_cost(fork)
    )
    if creator_covered:
        forwarded = creator_needed + CREATOR_SPARE
    else:
        forwarded = creator_needed - sstore_3.gas_cost(fork) // 2

    # The caller: entry marker, the CALL with its grant taken from
    # calldata (as in the ported filler), result store, completion
    # marker.
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
    caller = pre.deploy_contract(code=caller_code)

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
        # 1/64 retention and the creator's spare add up to cannot pay the
        # result store, so the caller dies after the creator returns.
        store_cost = sstore_1.gas_cost(fork) - call_code.gas_cost(fork)
        assert available // 64 + CREATOR_SPARE < store_cost, (
            "the retention must not afford the post-call store"
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

    created = compute_create2_address(creator, 0, b"")
    if not outer_covered:
        # The whole transaction ran dry after the CREATE2: only the code
        # survives.
        caller_account = Account(storage={}, code=caller_code, balance=0)
        creator_account = Account(storage={}, nonce=1)
        created_account: Account | None = Account.NONEXISTENT
    elif not creator_covered:
        # The creator died after its CREATE2 and was rolled back with
        # the creation and its nonce bump.
        caller_account = Account(
            storage={
                CALLER_START_SLOT: 0x1,
                CALL_RESULT_SLOT: 0x0,
                CALLER_DONE_SLOT: 0xC,
            },
            balance=tx_value,
        )
        creator_account = Account(storage={}, nonce=1)
        created_account = Account.NONEXISTENT
    else:
        caller_account = Account(
            storage={
                CALLER_START_SLOT: 0x1,
                CALL_RESULT_SLOT: 0x1,
                CALLER_DONE_SLOT: 0xC,
            },
            balance=tx_value,
        )
        creator_account = Account(
            storage={
                CREATOR_START_SLOT: 0x8,
                CREATE2_RESULT_SLOT: int.from_bytes(bytes(created), "big") + 1,
                CREATOR_DONE_SLOT: 0xC,
            },
            nonce=2,
        )
        created_account = Account(nonce=1, code=b"", balance=0)

    post = {
        sender: Account(nonce=1),
        caller: caller_account,
        creator: creator_account,
        created: created_account,
    }

    state_test(pre=pre, post=post, tx=tx)
