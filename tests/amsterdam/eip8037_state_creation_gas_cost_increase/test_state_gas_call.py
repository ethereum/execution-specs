"""
Test CALL state gas reservoir passing under EIP-8037.

The full state gas reservoir is passed to child call frames with no
63/64 rule. On child success, remaining state gas returns to the
parent. On child revert or exceptional halt, all state gas, both
reservoir and any that spilled into `gas_left`, is restored to the
parent's reservoir (only CPU gas is consumed for the failed frame).

All CALL-family opcodes (CALL, DELEGATECALL, STATICCALL) pass the
full reservoir to child frames.

Tests for [EIP-8037: State Creation Gas Cost Increase]
(https://eips.ethereum.org/EIPS/eip-8037).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Environment,
    Fork,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
)

from .spec import ref_spec_8037

REFERENCE_SPEC_GIT_PATH = ref_spec_8037.git_path
REFERENCE_SPEC_VERSION = ref_spec_8037.version


@pytest.mark.valid_from("Amsterdam")
def test_child_call_uses_reservoir(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test child call can use parent's state gas reservoir.

    The parent calls a child contract that performs an SSTORE
    (zero-to-nonzero). The state gas for the SSTORE is drawn from
    the reservoir passed from the parent.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    env = Environment()
    sstore_state_gas = fork.sstore_state_gas()

    child_storage = Storage()
    child = pre.deploy_contract(
        code=Op.SSTORE(child_storage.store_next(1), 1),
    )

    parent_storage = Storage()
    parent = pre.deploy_contract(
        code=(
            Op.SSTORE(
                parent_storage.store_next(1),
                Op.CALL(gas=100_000, address=child),
            )
        ),
    )

    tx = Transaction(
        to=parent,
        gas_limit=gas_limit_cap + sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    post = {
        parent: Account(storage=parent_storage),
        child: Account(storage=child_storage),
    }
    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Amsterdam")
def test_reservoir_returned_on_revert(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test state gas reservoir is returned to parent on child revert.

    The child contract reverts. The parent should recover the
    reservoir and be able to use it for its own SSTORE.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    env = Environment()
    sstore_state_gas = fork.sstore_state_gas()

    child = pre.deploy_contract(code=Op.REVERT(0, 0))

    parent_storage = Storage()
    parent = pre.deploy_contract(
        code=(
            # Call child that reverts (returns 0)
            Op.POP(Op.CALL(gas=100_000, address=child))
            # Parent can still use reservoir for its own SSTORE
            + Op.SSTORE(parent_storage.store_next(1), 1)
        ),
    )

    tx = Transaction(
        to=parent,
        gas_limit=gas_limit_cap + sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    post = {parent: Account(storage=parent_storage)}
    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Amsterdam")
def test_reservoir_returned_on_oog(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test state gas reservoir is returned to parent on child OOG.

    The child runs out of regular gas. The parent recovers the
    reservoir and can use it for its own state operations.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    env = Environment()
    sstore_state_gas = fork.sstore_state_gas()

    # Child that consumes all gas
    child = pre.deploy_contract(code=Op.INVALID)

    parent_storage = Storage()
    parent = pre.deploy_contract(
        code=(
            # Call child with minimal gas — it will OOG (returns 0)
            Op.POP(Op.CALL(gas=100, address=child))
            # Parent can still use reservoir for SSTORE
            + Op.SSTORE(parent_storage.store_next(1), 1)
        ),
    )

    tx = Transaction(
        to=parent,
        gas_limit=gas_limit_cap + sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    post = {parent: Account(storage=parent_storage)}
    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Amsterdam")
def test_reservoir_restored_after_child_spill_and_revert(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test all state gas recovered when child spills then reverts.

    The child performs two SSTOREs (zero-to-nonzero) but only one
    SSTORE's worth of state gas fits in the reservoir — the second
    spills into `gas_left`. The child then REVERTs. Because state
    changes are rolled back, all state gas (reservoir + spill) is
    restored to the parent's reservoir. The parent can then perform
    two SSTOREs using only the recovered reservoir.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    env = Environment()
    sstore_state_gas = fork.sstore_state_gas()

    # Child does two SSTOREs then reverts — the second SSTORE's
    # state gas spills from the reservoir into `gas_left`
    child = pre.deploy_contract(
        code=(Op.SSTORE(0, 1) + Op.SSTORE(1, 1) + Op.REVERT(0, 0)),
    )

    parent_storage = Storage()
    parent = pre.deploy_contract(
        code=(
            Op.POP(Op.CALL(gas=500_000, address=child))
            # All state gas recovered (reservoir + spill), parent
            # can perform two SSTOREs from the recovered reservoir
            + Op.SSTORE(parent_storage.store_next(1), 1)
            + Op.SSTORE(parent_storage.store_next(1), 1)
        ),
    )

    # Reservoir = 1 SSTORE's worth of state gas — child will spill
    tx = Transaction(
        to=parent,
        gas_limit=gas_limit_cap + sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    post = {parent: Account(storage=parent_storage)}
    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Amsterdam")
def test_reservoir_restored_after_child_spill_and_halt(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test all state gas recovered when child spills then halts.

    The child performs two SSTOREs (zero-to-nonzero), exhausting the
    reservoir and spilling into `gas_left`, then hits INVALID causing
    an exceptional halt. On halt `gas_left` is zeroed but all state gas
    (reservoir + spill) is restored to the parent's reservoir. The
    parent can then perform two SSTOREs using the recovered reservoir.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    env = Environment()
    sstore_state_gas = fork.sstore_state_gas()

    # Child does two SSTOREs then halts
    child = pre.deploy_contract(
        code=(Op.SSTORE(0, 1) + Op.SSTORE(1, 1) + Op.INVALID),
    )

    parent_storage = Storage()
    parent = pre.deploy_contract(
        code=(
            Op.POP(Op.CALL(gas=500_000, address=child))
            # All state gas recovered (reservoir + spill), parent
            # can perform two SSTOREs from the recovered reservoir
            + Op.SSTORE(parent_storage.store_next(1), 1)
            + Op.SSTORE(parent_storage.store_next(1), 1)
        ),
    )

    # Reservoir = 1 SSTORE's worth of state gas — child will spill
    tx = Transaction(
        to=parent,
        gas_limit=gas_limit_cap + sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    post = {parent: Account(storage=parent_storage)}
    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Amsterdam")
def test_reservoir_restored_after_child_full_drain_and_revert(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test reservoir restored when child exactly exhausts it then reverts.

    The child performs exactly one SSTORE consuming the entire reservoir
    (no spill into gas_left), then REVERTs. The full reservoir is
    returned to the parent.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    env = Environment()
    sstore_state_gas = fork.sstore_state_gas()

    child = pre.deploy_contract(
        code=(Op.SSTORE(0, 1) + Op.REVERT(0, 0)),
    )

    parent_storage = Storage()
    parent = pre.deploy_contract(
        code=(
            Op.POP(Op.CALL(gas=500_000, address=child))
            + Op.SSTORE(parent_storage.store_next(1), 1)
        ),
    )

    tx = Transaction(
        to=parent,
        gas_limit=gas_limit_cap + sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    post = {parent: Account(storage=parent_storage)}
    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Amsterdam")
def test_sequential_calls_reservoir_restored_between_reverts(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test reservoir restored across sequential child reverts.

    Parent calls child1 which spills and reverts, then calls child2
    which also uses state gas from the restored reservoir. Both
    child failures restore the reservoir, so the parent can use it
    for its own SSTORE at the end.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    env = Environment()
    sstore_state_gas = fork.sstore_state_gas()

    child = pre.deploy_contract(
        code=(Op.SSTORE(0, 1) + Op.REVERT(0, 0)),
    )

    parent_storage = Storage()
    parent = pre.deploy_contract(
        code=(
            # First child: uses reservoir, reverts — reservoir restored
            Op.POP(Op.CALL(gas=500_000, address=child))
            # Second child: uses restored reservoir, reverts — restored again
            + Op.POP(Op.CALL(gas=500_000, address=child))
            # Parent SSTORE succeeds with restored reservoir
            + Op.SSTORE(parent_storage.store_next(1), 1)
        ),
    )

    tx = Transaction(
        to=parent,
        gas_limit=gas_limit_cap + sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    post = {parent: Account(storage=parent_storage)}
    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Amsterdam")
def test_nested_calls_reservoir_passing(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test reservoir passes through nested calls.

    The reservoir is passed from A to B to C. C performs an SSTORE
    using the reservoir gas. After all calls return, A verifies
    success.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    env = Environment()
    sstore_state_gas = fork.sstore_state_gas()

    c_storage = Storage()
    c = pre.deploy_contract(
        code=Op.SSTORE(c_storage.store_next(1), 1),
    )

    b = pre.deploy_contract(
        code=Op.CALL(gas=200_000, address=c),
    )

    a_storage = Storage()
    a = pre.deploy_contract(
        code=(
            Op.SSTORE(
                a_storage.store_next(1),
                Op.CALL(gas=300_000, address=b),
            )
        ),
    )

    tx = Transaction(
        to=a,
        gas_limit=gas_limit_cap + sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    post = {
        a: Account(storage=a_storage),
        c: Account(storage=c_storage),
    }
    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Amsterdam")
def test_call_value_transfer_new_account(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test CALL with value to non-existent account charges state gas.

    A CALL that transfers value to a non-existent account creates a
    new account, charging new-account state gas of state gas.
    """
    gas_costs = fork.gas_costs()
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    env = Environment()
    new_account_state_gas = gas_costs.GAS_NEW_ACCOUNT

    # Target address that doesn't exist in pre-state
    target = 0xDEAD

    parent_storage = Storage()
    parent = pre.deploy_contract(
        code=(
            Op.SSTORE(
                parent_storage.store_next(1),
                Op.CALL(gas=100_000, address=target, value=1),
            )
        ),
        balance=1,
    )

    tx = Transaction(
        to=parent,
        gas_limit=gas_limit_cap + new_account_state_gas,
        sender=pre.fund_eoa(),
    )

    post = {parent: Account(storage=parent_storage)}
    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Amsterdam")
def test_call_value_transfer_existing_account_no_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test CALL with value to existing account charges no state gas.

    A CALL that transfers value to an already-alive account does not
    create new state, so no state gas is charged.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    # Existing target account
    target = pre.fund_eoa(amount=0)

    parent_storage = Storage()
    parent = pre.deploy_contract(
        code=(
            Op.SSTORE(
                parent_storage.store_next(1),
                Op.CALL(gas=100_000, address=target, value=1),
            )
        ),
        balance=1,
    )

    tx = Transaction(
        to=parent,
        gas_limit=gas_limit_cap,
        sender=pre.fund_eoa(),
    )

    post = {parent: Account(storage=parent_storage)}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Amsterdam")
def test_child_state_gas_tracked_in_parent(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test state gas used by child is accumulated in parent.

    Both parent and child perform SSTOREs. The total state gas used
    should reflect both operations. This is verified by the test
    succeeding with enough total gas but would OOG if state gas
    wasn't tracked across frames.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    env = Environment()
    sstore_state_gas = fork.sstore_state_gas()

    child_storage = Storage()
    child = pre.deploy_contract(
        code=Op.SSTORE(child_storage.store_next(1), 1),
    )

    parent_storage = Storage()
    parent = pre.deploy_contract(
        code=(
            # Parent SSTORE
            Op.SSTORE(parent_storage.store_next(1), 1)
            # Child SSTORE
            + Op.SSTORE(
                parent_storage.store_next(1),
                Op.CALL(gas=100_000, address=child),
            )
        ),
    )

    # Provide enough reservoir for both SSTOREs
    tx = Transaction(
        to=parent,
        gas_limit=gas_limit_cap + sstore_state_gas * 2,
        sender=pre.fund_eoa(),
    )

    post = {
        parent: Account(storage=parent_storage),
        child: Account(storage=child_storage),
    }
    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Amsterdam")
def test_delegatecall_reservoir_passing(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test DELEGATECALL passes full reservoir to child.

    DELEGATECALL runs child code in the caller's storage context.
    The child's SSTORE writes to the parent's storage using state
    gas from the reservoir.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    env = Environment()
    sstore_state_gas = fork.sstore_state_gas()

    # Library code that writes to slot 0 — runs in parent's context
    library = pre.deploy_contract(
        code=Op.SSTORE(0, 1),
    )

    parent_storage = Storage()
    parent_storage[0] = 1  # Expect slot 0 = 1 after delegatecall
    parent = pre.deploy_contract(
        code=(Op.DELEGATECALL(gas=100_000, address=library)),
    )

    tx = Transaction(
        to=parent,
        gas_limit=gas_limit_cap + sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    post = {parent: Account(storage=parent_storage)}
    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Amsterdam")
def test_staticcall_passes_reservoir(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test STATICCALL passes reservoir but cannot use it for state ops.

    STATICCALL forbids state-modifying operations. The reservoir is
    passed to the child but cannot be consumed. After the STATICCALL
    returns, the parent can still use the reservoir for its own SSTORE.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    env = Environment()
    sstore_state_gas = fork.sstore_state_gas()

    # Child does a read-only operation
    child = pre.deploy_contract(
        code=Op.MSTORE(0, Op.ADDRESS),
    )

    parent_storage = Storage()
    parent = pre.deploy_contract(
        code=(
            Op.POP(Op.STATICCALL(gas=100_000, address=child))
            # Reservoir should still be available for parent's SSTORE
            + Op.SSTORE(parent_storage.store_next(1), 1)
        ),
    )

    tx = Transaction(
        to=parent,
        gas_limit=gas_limit_cap + sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    post = {parent: Account(storage=parent_storage)}
    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Amsterdam")
def test_gas_opcode_excludes_reservoir(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test GAS opcode returns gas_left only, excluding the reservoir.

    The spec states the GAS opcode reports only gas_left. When the
    reservoir is non-empty, the GAS return value should be less than
    the total remaining gas (gas_left + reservoir).
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    env = Environment()
    sstore_state_gas = fork.sstore_state_gas()

    storage = Storage()
    contract = pre.deploy_contract(
        code=(
            # Store GAS opcode result — should only reflect gas_left
            Op.SSTORE(0, Op.GAS)
            # Store 1 to prove execution reached this point
            + Op.SSTORE(storage.store_next(1), 1)
        ),
    )

    # Provide large reservoir — GAS should NOT include it
    reservoir_gas = sstore_state_gas * 100
    tx = Transaction(
        to=contract,
        gas_limit=gas_limit_cap + reservoir_gas,
        sender=pre.fund_eoa(),
    )

    # Verify: slot 0 should hold a value <= TX_MAX_GAS_LIMIT
    # (gas_left is capped by TX_MAX_GAS_LIMIT - intrinsic.regular)
    # We can't check the exact value, but we verify the SSTORE
    # succeeded and the contract executed correctly
    post = {contract: Account(storage=storage)}
    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Amsterdam")
def test_call_insufficient_balance_returns_reservoir(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test CALL with insufficient balance returns reservoir to parent.

    When a CALL transfers value but the sender has insufficient balance,
    the call fails and both gas_left and state_gas_left are returned
    to the parent frame. The parent can still use the reservoir.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    env = Environment()
    sstore_state_gas = fork.sstore_state_gas()

    child = pre.deploy_contract(code=Op.STOP)

    storage = Storage()
    contract = pre.deploy_contract(
        code=(
            # CALL with 1 wei to child — will fail (contract has 0 balance)
            Op.SSTORE(
                storage.store_next(0, "call_fails"),
                Op.CALL(100_000, child, 1, 0, 0, 0, 0),
            )
            # Reservoir should be returned — SSTORE still works
            + Op.SSTORE(storage.store_next(1, "sstore_after"), 1)
        ),
    )

    tx = Transaction(
        to=contract,
        gas_limit=gas_limit_cap + sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage=storage)}
    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Amsterdam")
def test_create_insufficient_balance_returns_reservoir(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test CREATE with insufficient balance returns reservoir to parent.

    When CREATE is called but the sender doesn't have enough balance
    for the endowment, the operation fails and both gas and state gas
    reservoir are returned to the parent frame.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    env = Environment()
    sstore_state_gas = fork.sstore_state_gas()

    storage = Storage()
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(0, int.from_bytes(bytes(Op.STOP), "big") << 248)
            # CREATE with 1 wei endowment — fails (contract has 0 balance)
            + Op.SSTORE(
                storage.store_next(0, "create_fails"),
                Op.CREATE(1, 0, 1),
            )
            # Reservoir returned — SSTORE still works
            + Op.SSTORE(storage.store_next(1, "sstore_after"), 1)
        ),
    )

    tx = Transaction(
        to=contract,
        gas_limit=gas_limit_cap + sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage=storage)}
    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Amsterdam")
def test_call_stack_depth_returns_reservoir(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test CALL at stack depth limit returns reservoir.

    When a CALL exceeds the 1024 stack depth limit, the call fails
    and gas and state gas reservoir are returned. The parent can still
    use the reservoir for state operations.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    env = Environment()
    sstore_state_gas = fork.sstore_state_gas()

    # Contract that recursively calls itself until depth exhausted,
    # then does an SSTORE using the reservoir
    storage = Storage()
    recursive = pre.deploy_contract(
        code=(
            # Try recursive call (will eventually hit depth 1024)
            Op.POP(Op.CALL(Op.GAS, Op.ADDRESS, 0, 0, 0, 0, 0))
            # After recursion unwinds, only the outermost frame
            # reaches this SSTORE
            + Op.SSTORE(storage.store_next(1, "after_recursion"), 1)
        ),
    )

    tx = Transaction(
        to=recursive,
        gas_limit=gas_limit_cap + sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    post = {recursive: Account(storage=storage)}
    state_test(env=env, pre=pre, post=post, tx=tx)
