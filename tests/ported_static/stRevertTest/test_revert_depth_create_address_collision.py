"""
Verify revert propagation around a nested CREATE whose target address
collides with an existing contract - its own caller: the creating frame
always fails and the collided account survives untouched, while the
caller completes only when its budget covers the forfeited grant.

Ported from:
state_tests/stRevertTest/RevertDepthCreateAddressCollisionFiller.json

@manually-enhanced: Do not overwrite. Restores the collision the machine
port lost: the caller is deployed at the creator's CREATE address (as in
the original filler). Grants and budgets derive from fork composites and
the collided account's code, nonce and storage are pinned in every arm.
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

# Gas left in the creator frame when its CREATE executes: the collision
# consumes it, so the following store can never be paid.
BURN_MARGIN = 5_000
# Head room on top of a derived budget.
BUDGET_MARGIN = 5_000
# Gas left at the caller's call site in the starved arm: too little for
# any frame to complete.
STARVE_MARGIN = 1_000


@pytest.mark.ported_from(
    ["state_tests/stRevertTest/RevertDepthCreateAddressCollisionFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "oversized_ask",
    [False, True],
    ids=["modest_ask", "oversized_ask"],
)
@pytest.mark.parametrize(
    "ample_budget",
    [False, True],
    ids=["starved", "ample"],
)
@pytest.mark.parametrize("tx_value", [1, 0], ids=["v1", "v0"])
@pytest.mark.pre_alloc_mutable
def test_revert_depth_create_address_collision(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    oversized_ask: bool,
    ample_budget: bool,
    tx_value: int,
) -> None:
    """A CREATE address collision leaves the collided account intact."""
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
    creator = pre.deploy_contract(
        code=creator_store + create_code + creator_tail + Op.STOP
    )

    head_store = Op.SSTORE(
        key=0x0, value=0x1, key_warm=False, original_value=0, new_value=1
    )
    call_code = Op.CALL(
        gas=Op.CALLDATALOAD(offset=0x0), address=creator, address_warm=False
    )
    # The creator's frame always fails, so the call result is always 0.
    call_store = Op.SSTORE(
        key=0x1,
        value=call_code,
        key_warm=False,
        original_value=0,
        new_value=0,
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

    intrinsic_calculator = fork.transaction_intrinsic_cost_calculator()
    modest_grant = (creator_store + create_code).gas_cost(fork) + BURN_MARGIN
    gas_limit = (
        intrinsic_calculator(
            calldata=Hash(modest_grant),
            sends_value=tx_value > 0,
            return_cost_deducted_prior_execution=True,
        )
        + head_store.gas_cost(fork)
        + call_store.gas_cost(fork)
        + modest_grant
        + tail_store.gas_cost(fork)
        + BUDGET_MARGIN
    )
    # An oversized ask is clamped to the EIP-150 63/64 cap, leaving the
    # caller only 1/64 of its remaining gas: it can never complete.
    grant = gas_limit if oversized_ask else modest_grant
    data = Hash(grant)
    intrinsic = intrinsic_calculator(
        calldata=data,
        sends_value=tx_value > 0,
        return_cost_deducted_prior_execution=True,
    )
    if ample_budget:
        available = (
            gas_limit
            - intrinsic
            - head_store.gas_cost(fork)
            - call_code.gas_cost(fork)
        )
        if oversized_ask:
            store_costs = (
                call_store.gas_cost(fork)
                - call_code.gas_cost(fork)
                + tail_store.gas_cost(fork)
            )
            assert available // 64 < store_costs, "caller must fail"
        else:
            assert grant <= available - available // 64, "grant is granted"
    else:
        # The caller reaches its call with only STARVE_MARGIN left: the
        # creator halts at its first store and the retained 1/64 cannot
        # pass the EIP-2200 stipend check, so everything reverts.
        gas_limit = (
            intrinsic
            + head_store.gas_cost(fork)
            + call_code.gas_cost(fork)
            + STARVE_MARGIN
        )
        assert STARVE_MARGIN - STARVE_MARGIN // 64 <= 2300, "creator halts"
        assert STARVE_MARGIN // 64 <= 2300, "caller store must halt"

    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        to=caller,
        data=data,
        gas_limit=gas_limit,
        value=tx_value,
    )

    caller_completes = ample_budget and not oversized_ask
    post = {
        # The collided account survives with its code and nonce intact.
        caller: Account(
            code=caller_code,
            nonce=1,
            storage={0: 1, 4: 0xC} if caller_completes else {},
            balance=tx_value if caller_completes else 0,
        ),
        creator: Account(storage={}),
    }

    state_test(pre=pre, post=post, tx=tx)
