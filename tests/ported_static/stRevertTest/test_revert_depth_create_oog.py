"""
Verify revert propagation around a nested CREATE that runs out of gas:
a sub-call either funds its CREATE-then-store sequence completely, or
runs out of gas after the CREATE, reverting the created account but not
the caller. A starved outer budget reverts everything after the
sub-call ran, a completed creation included.

Ported from:
state_tests/stRevertTest/RevertDepthCreateOOGFiller.json

@manually-enhanced: Do not overwrite. The sub-call grants and both
transaction budgets derive from fork composites (EIP-8037 state gas is
tracked instead of pinned), all addresses are dynamic, every account
including the created one is pinned in each arm, and the starved arms
run the CREATE before the transaction dies.
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

# Gas left in the creator frame after its CREATE: enough to reach the
# following store, never enough to pay for it.
PARTIAL_MARGIN = 5_000
# Head room on top of a derived budget.
BUDGET_MARGIN = 5_000


@pytest.mark.ported_from(
    ["state_tests/stRevertTest/RevertDepthCreateOOGFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "full_grant",
    [False, True],
    ids=["partial_grant", "full_grant"],
)
@pytest.mark.parametrize(
    "ample_budget",
    [False, True],
    ids=["starved", "ample"],
)
@pytest.mark.parametrize("tx_value", [1, 0], ids=["v1", "v0"])
def test_revert_depth_create_oog(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    full_grant: bool,
    ample_budget: bool,
    tx_value: int,
) -> None:
    """An out-of-gas CREATE frame reverts alone, a starved caller in full."""
    creator_store = Op.SSTORE(
        key=0x2, value=0x8, key_warm=False, original_value=0, new_value=8
    )
    create_code = Op.POP(
        Op.CREATE(
            value=0x0,
            offset=0x0,
            size=0x0,
            init_code_size=0,
            new_memory_size=0,
        )
    )
    creator_tail = Op.SSTORE(
        key=0x3, value=0xC, key_warm=False, original_value=0, new_value=0xC
    )
    creator_code = creator_store + create_code + creator_tail + Op.STOP
    creator = pre.deploy_contract(code=creator_code)
    created = compute_create_address(address=creator, nonce=1)

    # The grant covers the creator completely, or only up to and
    # including its CREATE, leaving too little for the following store.
    if full_grant:
        grant = creator_code.gas_cost(fork) + BUDGET_MARGIN
        inner_consumed = creator_code.gas_cost(fork)
    else:
        grant = (creator_store + create_code).gas_cost(fork) + PARTIAL_MARGIN
        inner_consumed = grant
    inner_succeeds = ample_budget and full_grant
    inner_fails_reaching_create = ample_budget and not full_grant

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
        new_value=1 if inner_succeeds else 0,
    )
    tail_store = Op.SSTORE(
        key=0x4, value=0xC, key_warm=False, original_value=0, new_value=0xC
    )
    caller = pre.deploy_contract(
        code=head_store + call_store + tail_store + Op.STOP
    )

    data = Hash(grant)
    intrinsic = fork.transaction_intrinsic_cost_calculator()(
        calldata=data,
        sends_value=tx_value > 0,
        return_cost_deducted_prior_execution=True,
    )
    if ample_budget:
        gas_limit = (
            intrinsic
            + head_store.gas_cost(fork)
            + call_store.gas_cost(fork)
            + inner_consumed
            + tail_store.gas_cost(fork)
            + BUDGET_MARGIN
        )
        # The requested grant must fit under the EIP-150 63/64 cap.
        available = (
            gas_limit
            - intrinsic
            - head_store.gas_cost(fork)
            - call_code.gas_cost(fork)
        )
        assert grant <= available - available // 64, "grant must be granted"
    else:
        # The grant is granted in full but nothing is budgeted for the
        # caller's post-call stores: the 1/64 retention plus whatever the
        # creator hands back cannot pay them, so the whole transaction
        # runs dry after the creator ran.
        available = -(-grant * 64 // 63) + 64
        assert grant <= available - available // 64, "grant must be granted"
        creator_spare = grant - inner_consumed
        assert available // 64 + creator_spare < tail_store.gas_cost(fork), (
            "caller must die"
        )
        gas_limit = (
            intrinsic
            + head_store.gas_cost(fork)
            + call_code.gas_cost(fork)
            + available
        )

    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        to=caller,
        data=data,
        gas_limit=gas_limit,
        value=tx_value,
    )

    post: dict
    if inner_succeeds:
        post = {
            created: Account(nonce=1),
            caller: Account(storage={0: 1, 1: 1, 4: 0xC}, balance=tx_value),
            creator: Account(storage={2: 8, 3: 0xC}),
        }
    elif inner_fails_reaching_create:
        post = {
            created: Account.NONEXISTENT,
            caller: Account(storage={0: 1, 4: 0xC}, balance=tx_value),
            creator: Account(storage={}),
        }
    else:
        post = {
            created: Account.NONEXISTENT,
            caller: Account(storage={}, balance=0),
            creator: Account(storage={}),
        }

    state_test(pre=pre, post=post, tx=tx)
