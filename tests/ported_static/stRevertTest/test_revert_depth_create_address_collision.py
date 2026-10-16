"""
Verify revert propagation around a nested CREATE whose target address
collides with an existing contract, its own caller: the collision burns
the child's grant and bumps the creator's nonce without creating
anything, and the stacked budgets decide whether the creator survives
its aftermath, dies on it, or the caller or the whole transaction runs
dry after it.

Ported from:
state_tests/stRevertTest/RevertDepthCreateAddressCollisionFiller.json

@manually-enhanced: Do not overwrite. Restores the collision the machine
port lost: the caller is deployed at the creator's CREATE address (as in
the original filler). Grants and budgets derive from fork composites,
the collided account's code, nonce and storage are pinned in every arm,
and the creator's post-collision slack is sized so the burned grant is
what decides its fate.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    Hash,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

# Head room on top of the completion marker's cost in the starved
# creator's slack: had the collision returned the grant, the marker
# would be paid, but one 64th of the slack never covers it.
SLACK_MARGIN = 5_000
# What the covered creator keeps after its completion marker, on top of
# the EIP-2200 stipend gate that store must clear.
RETENTION_MARGIN = 100


@pytest.mark.ported_from(
    ["state_tests/stRevertTest/RevertDepthCreateAddressCollisionFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "scenario",
    ["creator_oog", "creator_ok", "caller_oog", "tx_oog"],
)
@pytest.mark.parametrize("tx_value", [1, 0], ids=["v1", "v0"])
# Keep the intentional collider out of other tests with the same creator.
@pytest.mark.pre_alloc_group("create_address_collision")
@pytest.mark.pre_alloc_mutable
def test_revert_depth_create_address_collision(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    scenario: str,
    tx_value: int,
) -> None:
    """A CREATE address collision leaves the collided account intact."""
    creator_store = Op.SSTORE(
        key=0x2, value=0x8, key_warm=False, original_value=0, new_value=8
    )
    # The target is alive, so no new-account state gas is charged.
    create_code = Op.POP(
        Op.CREATE(
            value=0x0,
            offset=0x0,
            size=0x0,
            init_code_size=0,
            new_memory_size=0,
            account_new=False,
        )
    )
    creator_tail = Op.SSTORE(
        key=0x3, value=0xC, key_warm=False, original_value=0, new_value=0xC
    )
    creator = pre.deploy_contract(
        code=creator_store + create_code + creator_tail + Op.STOP
    )

    head_store = Op.SSTORE(
        key=0x0, value=0x1, key_warm=False, original_value=0, new_value=1
    )
    call_code = Op.CALL(
        gas=Op.CALLDATALOAD(offset=0x0), address=creator, address_warm=False
    )
    call_store = Op.SSTORE(
        key=0x1,
        value=call_code,
        key_warm=False,
        original_value=0,
        new_value=1,
    )
    tail_store = Op.SSTORE(
        key=0x4, value=0xC, key_warm=False, original_value=0, new_value=0xC
    )
    caller_code = head_store + call_store + tail_store + Op.STOP
    # The caller sits exactly at the creator's CREATE address: the
    # nested creation collides with the very contract that called it.
    caller = pre.deploy_contract(
        code=caller_code,
        address=compute_create_address(address=creator, nonce=1),
    )

    # The collision consumes everything left after the CREATE's own
    # charges but one 64th, so the creator's fate is set by the slack
    # riding on top of its pre-collision costs.
    stipend = fork.gas_costs().CALL_STIPEND
    tail = creator_tail.gas_cost(fork)
    if scenario == "creator_ok":
        slack = 64 * (stipend + tail + RETENTION_MARGIN)
    else:
        slack = tail + SLACK_MARGIN
        assert slack // 64 < tail, "the retention must not afford the marker"
    ask = (creator_store + create_code).gas_cost(fork) + slack

    intrinsic_calculator = fork.transaction_intrinsic_cost_calculator()

    def overhead(data: Hash) -> int:
        """Return what the caller pays before its CALL."""
        return intrinsic_calculator(
            calldata=data,
            sends_value=tx_value > 0,
            return_cost_deducted_prior_execution=True,
        ) + head_store.gas_cost(fork)

    # Enough at the CALL that the EIP-150 clamp still grants the full
    # ask.
    available = -(-ask * 64 // 63) + 64
    assert available - available // 64 >= ask, "the full ask must be granted"
    data = Hash(ask)
    post_call = call_store.gas_cost(fork) + tail_store.gas_cost(fork)
    gas_limit = overhead(data) + post_call + available
    if scenario == "caller_oog":
        # An oversized ask is clamped to the EIP-150 cap: the creator
        # gets everything the caller has and still dies on the collision,
        # while the caller keeps one 64th, never enough for its stores.
        data = Hash(gas_limit)
        gas_limit = overhead(data) + post_call + available
        remaining = post_call + available
        granted = remaining - remaining // 64
        creator_left = granted - (creator_store + create_code).gas_cost(fork)
        assert creator_left // 64 < tail, "the creator must die"
        assert remaining // 64 < tail_store.gas_cost(fork), "caller must die"
    elif scenario == "tx_oog":
        # Nothing is budgeted for the caller's post-call stores: the
        # 1/64 retention cannot pay them, so the whole transaction runs
        # dry after the collision.
        gas_limit = overhead(data) + available
        assert available // 64 < tail_store.gas_cost(fork), "caller must die"

    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        to=caller,
        data=data,
        gas_limit=gas_limit,
        value=tx_value,
    )

    if scenario == "creator_ok":
        # The collision's signature: a nonce bump with nothing created,
        # a zero CREATE result, and the caller's account untouched.
        caller_account = Account(
            storage={0: 1, 1: 1, 4: 0xC},
            code=caller_code,
            balance=tx_value,
            nonce=1,
        )
        creator_account = Account(storage={2: 8, 3: 0xC}, nonce=2)
    elif scenario == "creator_oog":
        # The creator died on its completion marker and was rolled back,
        # including the collision's nonce bump.
        caller_account = Account(
            storage={0: 1, 1: 0, 4: 0xC},
            code=caller_code,
            balance=tx_value,
            nonce=1,
        )
        creator_account = Account(storage={}, nonce=1)
    else:
        # The transaction ran dry after the collision: only the code
        # survives.
        caller_account = Account(
            storage={}, code=caller_code, balance=0, nonce=1
        )
        creator_account = Account(storage={}, nonce=1)

    post = {
        sender: Account(nonce=1),
        caller: caller_account,
        creator: creator_account,
    }

    state_test(pre=pre, post=post, tx=tx)
