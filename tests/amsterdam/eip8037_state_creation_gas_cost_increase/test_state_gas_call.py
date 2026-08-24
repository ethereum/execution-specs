"""
Test CALL state gas reservoir passing under EIP-8037.

The full state gas reservoir is passed to child call frames with no
63/64 rule. On child success, remaining state gas returns to the parent.
On revert, the frame's state gas is refilled in LIFO order: the portion
that spilled into `gas_left` returns there and the reservoir-funded
portion restores the reservoir. An exceptional halt likewise resets the
reservoir to its start-of-frame value, but the spilled portion stays
consumed as execution gas with the rest of `gas_left`.

All CALL-family opcodes (CALL, DELEGATECALL, STATICCALL) pass the
full reservoir to child frames.

Tests for [EIP-8037: State Creation Gas Cost Increase]
(https://eips.ethereum.org/EIPS/eip-8037).
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytecode,
    Fork,
    Header,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
    TransactionReceipt,
    compute_create_address,
)
from execution_testing.checklists import EIPChecklist

from .spec import init_code_at_high_bytes, ref_spec_8037

REFERENCE_SPEC_GIT_PATH = ref_spec_8037.git_path
REFERENCE_SPEC_VERSION = ref_spec_8037.version


@pytest.mark.valid_from("EIP8037")
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
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

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
        state_gas_reservoir=sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    post = {
        parent: Account(storage=parent_storage),
        child: Account(storage=child_storage),
    }
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("EIP8037")
def test_delegatecall_child_spill_not_double_charged(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test DELEGATECALL child state gas paid from `gas_left` is not recharged.

    With the gas limit pinned to the Amsterdam tx gas cap and no requested
    reservoir (`state_gas_reservoir=0`), the top-level frame starts with no
    state gas reservoir and the child pays for SSTOREs by spilling from
    `gas_left`. The parent frame must not charge the same state growth again
    at frame end.
    """
    child_code = sum(Op.SSTORE(i, i + 1) for i in range(6)) + Op.STOP
    child = pre.deploy_contract(code=child_code)

    caller = pre.deploy_contract(
        code=Op.POP(
            Op.DELEGATECALL(
                gas=Op.GAS,
                address=child,
                args_offset=0,
                args_size=0,
                ret_offset=0,
                ret_size=0,
            )
        )
    )

    tx = Transaction(
        to=caller,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
    )

    post = {
        caller: Account(storage={i: i + 1 for i in range(6)}),
    }
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("EIP8037")
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
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

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
        state_gas_reservoir=sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    post = {parent: Account(storage=parent_storage)}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("EIP8037")
def test_reservoir_returned_on_oog(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test state gas reservoir is returned to parent on child OOG.

    The child runs out of execution gas. The parent recovers the
    reservoir and can use it for its own state operations.
    """
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

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
        state_gas_reservoir=sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    post = {parent: Account(storage=parent_storage)}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("EIP8037")
def test_reservoir_restored_after_child_spill_and_revert(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test all state gas recovered when child spills then reverts.

    The child performs two SSTOREs (zero-to-nonzero) but only one
    SSTORE's worth of state gas fits in the reservoir, so the second
    spills into `gas_left`. The child then REVERTs. Because state
    changes are rolled back, the state gas is refilled LIFO: the
    spilled portion returns to `gas_left` and the reservoir-funded
    portion restores the reservoir to its start value. The parent
    then performs two SSTOREs, drawing one from the restored
    reservoir and spilling the other from the recovered `gas_left`.
    """
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

    # Child does two SSTOREs then reverts — the second SSTORE's
    # state gas spills from the reservoir into `gas_left`
    child = pre.deploy_contract(
        code=(Op.SSTORE(0, 1) + Op.SSTORE(1, 1) + Op.REVERT(0, 0)),
    )

    parent_storage = Storage()
    parent = pre.deploy_contract(
        code=(
            Op.POP(Op.CALL(gas=500_000, address=child))
            # State gas recovered LIFO: the spilled SSTORE returns to
            # gas_left, the other restores the reservoir
            + Op.SSTORE(parent_storage.store_next(1), 1)
            + Op.SSTORE(parent_storage.store_next(1), 1)
        ),
    )

    # Reservoir = 1 SSTORE's worth of state gas — child will spill
    tx = Transaction(
        to=parent,
        state_gas_reservoir=sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    post = {parent: Account(storage=parent_storage)}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("EIP8037")
def test_reservoir_restored_after_child_spill_and_halt(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test parent gets reservoir back after child spill + halt.

    The child performs two SSTOREs (zero-to-nonzero), exhausting the
    reservoir and spilling into `gas_left`, then hits INVALID causing
    an exceptional halt. The child's halt resets its frame to (0,
    R0_child) — only the reservoir-portion is returned to the
    parent; the spilled gas stays burned (re-classified as execution).
    The parent does two SSTOREs: the first drains the recovered
    reservoir, the second spills from the parent's own `gas_left`.
    The receipt pins the halted child's whole budget as consumed, so
    a credit of the burned spill back to the parent is caught.
    """
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()()
    child_budget = 500_000

    # Child does two SSTOREs then halts
    child = pre.deploy_contract(
        code=(Op.SSTORE(0, 1) + Op.SSTORE(1, 1) + Op.INVALID),
    )

    parent_storage = Storage()
    parent_code = (
        Op.POP(Op.CALL(gas=child_budget, address=child))
        # First SSTORE drains the recovered reservoir; second
        # SSTORE spills from parent's gas_left (gas_limit_cap is
        # large enough to absorb it).
        + Op.SSTORE(parent_storage.store_next(1), 1)
        + Op.SSTORE(parent_storage.store_next(1), 1)
    )
    parent = pre.deploy_contract(code=parent_code)

    # The halted child burns its whole budget. The parent's own sets
    # and their state gas are inside `gas_cost`.
    expected_cumulative = (
        intrinsic_cost + parent_code.gas_cost(fork) + child_budget
    )

    # Reservoir = 1 SSTORE's worth of state gas — child will spill
    tx = Transaction(
        to=parent,
        state_gas_reservoir=sstore_state_gas,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=expected_cumulative,
        ),
    )

    post = {parent: Account(storage=parent_storage)}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("EIP8037")
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
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

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
        state_gas_reservoir=sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    post = {parent: Account(storage=parent_storage)}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("EIP8037")
def test_sequential_calls_reservoir_restored_between_reverts(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test reservoir restored across sequential child reverts.

    Parent calls child1, which uses the reservoir for an SSTORE and
    reverts, restoring the reservoir. It then calls child2, which
    reuses the restored reservoir and reverts, restoring it again.
    The parent then performs its own SSTORE from the restored
    reservoir.
    """
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

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
        state_gas_reservoir=sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    post = {parent: Account(storage=parent_storage)}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("EIP8037")
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
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

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
        state_gas_reservoir=sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    post = {
        a: Account(storage=a_storage),
        c: Account(storage=c_storage),
    }
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("EIP8037")
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
    # Target address that doesn't exist in pre-state
    target = pre.nonexistent_account()

    parent_storage = Storage()
    # Capture the CALL result in a pre-existing slot (2 -> 1) so the
    # instrumentation SSTORE modifies rather than creates a key and
    # adds no state gas; the reservoir then covers exactly the CALL's
    # new-account charge.
    slot = parent_storage.store_next(1)
    parent_code = Op.SSTORE(
        slot,
        Op.CALL(
            gas=100_000,
            address=target,
            value=1,
            value_transfer=True,
            account_new=True,
        ),
        original_value=2,
        current_value=2,
        new_value=1,
        key_warm=False,
    )
    parent = pre.deploy_contract(
        code=parent_code, balance=1, storage={slot: 2}
    )

    tx = Transaction(
        to=parent,
        state_gas_reservoir=parent_code.state_cost(fork),
        sender=pre.fund_eoa(),
    )

    post = {parent: Account(storage=parent_storage)}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("EIP8037")
def test_call_value_transfer_existing_account_no_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test CALL with value to existing account charges no state gas.

    A CALL that transfers value to an already-alive account does not
    create new state, so no state gas is charged.
    """
    # Existing target account
    target = pre.fund_eoa(amount=1)

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
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
    )

    post = {
        parent: Account(balance=0, storage=parent_storage),
        target: Account(balance=2),
    }
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("EIP8037")
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
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

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
        state_gas_reservoir=sstore_state_gas * 2,
        sender=pre.fund_eoa(),
    )

    post = {
        parent: Account(storage=parent_storage),
        child: Account(storage=child_storage),
    }
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("EIP8037")
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
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

    parent_storage = Storage()
    # Library code runs in parent's context — slot is reserved on
    # parent_storage so the post check uses the same source of truth.
    library = pre.deploy_contract(
        code=Op.SSTORE(parent_storage.store_next(1, "delegated"), 1),
    )

    parent = pre.deploy_contract(
        code=(Op.DELEGATECALL(gas=100_000, address=library)),
    )

    tx = Transaction(
        to=parent,
        state_gas_reservoir=sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    post = {parent: Account(storage=parent_storage)}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("EIP8037")
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
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

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
        state_gas_reservoir=sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    post = {parent: Account(storage=parent_storage)}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("EIP8037")
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
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

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
        state_gas_reservoir=reservoir_gas,
        sender=pre.fund_eoa(),
    )

    # Verify: slot 0 should hold a value <= TX_MAX_GAS_LIMIT
    # (gas_left is capped by TX_MAX_GAS_LIMIT - intrinsic.execution)
    # We can't check the exact value, but we verify the SSTORE
    # succeeded and the contract executed correctly
    post = {contract: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("EIP8037")
def test_call_insufficient_balance_returns_reservoir(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test CALL with insufficient balance returns the reservoir to parent.

    A value-bearing CALL to an existing account fails the balance check
    before entering the child frame; gas_left and state_gas_left are
    returned to the parent, which can still use the reservoir for a
    later SSTORE. The new-account variant (where NEW_ACCOUNT is charged
    then refilled on the same failure) is pinned by
    test_call_insufficient_balance_refunds_new_account_state_gas.
    """
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

    target = pre.deploy_contract(code=Op.STOP)
    reservoir = sstore_state_gas

    storage = Storage()
    contract = pre.deploy_contract(
        code=(
            # CALL with 1 wei — fails (contract has 0 balance)
            Op.SSTORE(
                storage.store_next(0, "call_fails"),
                Op.CALL(100_000, target, 1, 0, 0, 0, 0),
            )
            # Reservoir should be returned — SSTORE still works
            + Op.SSTORE(storage.store_next(1, "sstore_after"), 1)
        ),
    )

    tx = Transaction(
        to=contract,
        state_gas_reservoir=reservoir,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("EIP8037")
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
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

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
        state_gas_reservoir=sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    post = {contract: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("EIP8037")
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
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

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
        state_gas_reservoir=sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    post = {recursive: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("EIP8037")
def test_call_pre_charged_costs_excluded_from_forwarding(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify pre-charged CALL costs do not reduce the 63/64 forwarding budget.

    CALL charges access gas and memory expansion up front, before
    computing the 63/64 sub-call gas.  Those costs must not be
    subtracted again during the forwarding calculation.

    A wrapper contract receives a precise gas budget and calls a child
    with maximum gas and a large ret_size (triggering memory expansion).
    The child does a cold zero-to-nonzero SSTORE as proof of execution.
    The gas budget is tight enough that any double-counting of the
    pre-charged costs (access gas, memory expansion, or both) causes
    the child to OOG and the SSTORE to revert.
    """
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

    # Child: SSTORE(0, 1) as proof of execution
    child_storage = Storage()
    child_code = Op.SSTORE(child_storage.store_next(1, "child_ran"), 1)
    child = pre.deploy_contract(child_code)

    child_execution_gas = child_code.execution_cost(fork)

    # Memory expansion triggered by ret_size on the wrapper's CALL
    ret_size = 512 * 32  # 512 words
    memory_cost = fork.memory_expansion_gas_calculator()(new_bytes=ret_size)

    # Wrapper: CALL child requesting max gas with memory expansion. The
    # memory metadata makes `wrapper_code.execution_cost(fork)` fold the
    # cold access, the 7 argument pushes and the memory expansion.
    wrapper_code = Op.CALL(
        gas=0xFFFFFFFF,
        address=child,
        value=0,
        args_offset=0,
        args_size=0,
        ret_offset=0,
        ret_size=ret_size,
        new_memory_size=ret_size,
    )
    wrapper = pre.deploy_contract(wrapper_code)

    # After the up-front pre-charge, the wrapper has gas_remaining left.
    # The 63/64 rule should forward gas_remaining * 63/64 to the child —
    # just enough for its SSTORE.
    gas_remaining = child_execution_gas * 64 // 63 + memory_cost // 2

    wrapper_gas = wrapper_code.execution_cost(fork) + gas_remaining

    caller = pre.deploy_contract(
        Op.POP(Op.CALL(gas=wrapper_gas, address=wrapper))
    )

    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        to=caller,
        state_gas_reservoir=sstore_state_gas,
    )

    post = {
        child: Account(storage=child_storage),
    }

    state_test(pre=pre, tx=tx, post=post)


@pytest.mark.valid_from("EIP8037")
def test_call_new_account_header_gas_used(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify block gas accounting for CALL creating a new account.

    A contract CALLs a non-existent address with value, charging
    GAS_NEW_ACCOUNT state gas. The block must be accepted with
    correct 2D max(execution, state) accounting in the header.
    """
    target = pre.fund_eoa(amount=0)

    storage = Storage()
    # Capture the CALL result in a pre-existing slot (2 -> 1) so the
    # instrumentation SSTORE modifies rather than creates a key and
    # adds no state gas; the reservoir then covers exactly the CALL's
    # new-account charge.
    slot = storage.store_next(1, "call_succeeds")
    contract_code = Op.SSTORE(
        slot,
        Op.CALL(
            gas=100_000,
            address=target,
            value=1,
            value_transfer=True,
            account_new=True,
        ),
        original_value=2,
        current_value=2,
        new_value=1,
        key_warm=False,
    )
    contract = pre.deploy_contract(
        code=contract_code, balance=1, storage={slot: 2}
    )

    tx = Transaction(
        to=contract,
        state_gas_reservoir=contract_code.state_cost(fork),
        sender=pre.fund_eoa(),
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(txs=[tx]),
        ],
        post={contract: Account(storage=storage)},
    )


@pytest.mark.parametrize(
    "create_opcode",
    [
        pytest.param(Op.CREATE, id="create"),
        pytest.param(Op.CREATE2, id="create2"),
    ],
)
@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.valid_from("EIP8037")
def test_call_value_to_self_destructed_same_tx_account(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    create_opcode: Op,
) -> None:
    """
    Smoke test for CALL with value to a same transaction
    selfdestructed account.

    Confirms the happy path runs to completion. The account still
    has its CREATE nonce when the CALL runs, so it is neither empty
    nor nonexistent and the new account creation gate does not fire;
    end of the transaction destruction removes the account regardless
    and the value transferred is burned. Strict discrimination of
    the no charge behavior lives in
    `test_call_value_to_self_destructed_header_gas_used`.
    """
    inner_code = Op.SELFDESTRUCT(Op.ADDRESS)
    mstore_value, size = init_code_at_high_bytes(inner_code)

    storage = Storage()
    orchestrator_code = (
        Op.MSTORE(0, mstore_value)
        + (
            Op.CREATE2(1, 0, size, 0)
            if create_opcode == Op.CREATE2
            else Op.CREATE(1, 0, size)
        )
        + Op.MSTORE(0x20, Op.DUP1)
        + Op.POP
        + Op.SSTORE(
            storage.store_next(1, "call_succeeds"),
            Op.CALL(gas=Op.GAS, address=Op.MLOAD(0x20), value=1),
        )
    )
    orchestrator = pre.deploy_contract(code=orchestrator_code, balance=3)

    tx = Transaction(
        to=orchestrator,
        state_gas_reservoir=orchestrator_code.state_cost(fork),
        sender=pre.fund_eoa(),
    )

    post = {orchestrator: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "selfdestruct_beneficiary",
    [
        pytest.param("self", id="self_beneficiary"),
        pytest.param("external", id="external_beneficiary"),
    ],
)
@pytest.mark.parametrize(
    "create_opcode",
    [
        pytest.param(Op.CREATE, id="create"),
        pytest.param(Op.CREATE2, id="create2"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_call_value_to_self_destructed_header_gas_used(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    create_opcode: Op,
    selfdestruct_beneficiary: str,
) -> None:
    """
    Verify block gas accounting for CALL with value to a same
    transaction selfdestructed account.

    Reservoir is sized for the CREATE's state charge only. Under
    the spec no new account charge fires on the CALL, so block
    state gas used equals exactly the single account creation
    charge and the header reports that value. The created account
    is queued for destruction regardless of whether SELFDESTRUCT
    targeted itself or an external beneficiary, so the no charge
    behavior holds across both cases.
    """
    if selfdestruct_beneficiary == "self":
        inner_code = Op.SELFDESTRUCT(Op.ADDRESS)
    else:
        # Alive EOA so the SELFDESTRUCT itself does not charge a
        # new account state gas for the beneficiary.
        alive_beneficiary = pre.fund_eoa(amount=1)
        inner_code = Op.SELFDESTRUCT(alive_beneficiary)
    mstore_value, size = init_code_at_high_bytes(inner_code)

    orchestrator_code = (
        Op.MSTORE(0, mstore_value)
        + (
            Op.CREATE2(1, 0, size, 0)
            if create_opcode == Op.CREATE2
            else Op.CREATE(1, 0, size)
        )
        + Op.MSTORE(0x20, Op.DUP1)
        + Op.POP
        + Op.POP(Op.CALL(gas=Op.GAS, address=Op.MLOAD(0x20), value=1))
    )
    orchestrator = pre.deploy_contract(code=orchestrator_code, balance=3)

    tx = Transaction(
        to=orchestrator,
        state_gas_reservoir=orchestrator_code.state_cost(fork),
        sender=pre.fund_eoa(),
    )

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx])],
        post={},
    )


@pytest.mark.parametrize(
    "call_value",
    [
        pytest.param(1, id="one_wei"),
        pytest.param(10**18, id="one_ether"),
    ],
)
@pytest.mark.parametrize(
    "create_opcode",
    [
        pytest.param(Op.CREATE, id="create"),
        pytest.param(Op.CREATE2, id="create2"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_call_value_to_self_destructed_burns_value(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    create_opcode: Op,
    call_value: int,
) -> None:
    """
    Verify value transferred to a same transaction selfdestructed
    account is burned when end of the transaction destruction runs.

    The orchestrator funds the inner contract via CREATE, the
    initcode immediately selfdestructs, and then the orchestrator
    transfers more value into the now queued for destruction
    address. At the end of the transaction the account is removed
    and the accumulated balance is lost.
    """
    inner_code = Op.SELFDESTRUCT(Op.ADDRESS)
    mstore_value, size = init_code_at_high_bytes(inner_code)

    initial_balance = 2 * call_value
    orchestrator_code = (
        Op.MSTORE(0, mstore_value)
        + (
            Op.CREATE2(call_value, 0, size, 0)
            if create_opcode == Op.CREATE2
            else Op.CREATE(call_value, 0, size)
        )
        + Op.MSTORE(0x20, Op.DUP1)
        + Op.POP
        + Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=Op.MLOAD(0x20),
                value=call_value,
            )
        )
    )
    orchestrator = pre.deploy_contract(
        code=orchestrator_code, balance=initial_balance
    )
    created_address = compute_create_address(
        address=orchestrator,
        nonce=1,
        salt=0,
        initcode=bytes(inner_code),
        opcode=create_opcode,
    )

    tx = Transaction(
        to=orchestrator,
        state_gas_reservoir=orchestrator_code.state_cost(fork),
        sender=pre.fund_eoa(),
    )

    created_address_account = Account.NONEXISTENT
    if fork.is_eip_enabled(8246):
        created_address_account = Account(balance=call_value * 2)

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx])],
        post={
            created_address: created_address_account,
            orchestrator: Account(balance=0),
        },
    )


@pytest.mark.parametrize(
    "create_opcode",
    [
        pytest.param(Op.CREATE, id="create"),
        pytest.param(Op.CREATE2, id="create2"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_call_zero_value_to_self_destructed_same_tx_account(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    create_opcode: Op,
) -> None:
    """
    Verify CALL with zero value to a same transaction selfdestructed
    account charges no new account state gas.

    Value transfer gates the new account creation charge. Under the
    correct spec the block header reflects only the CREATE's single
    new account state gas charge. A spurious charge on the zero
    value CALL (value gate broken) would double the state gas
    component.
    """
    inner_code = Op.SELFDESTRUCT(Op.ADDRESS)
    mstore_value, size = init_code_at_high_bytes(inner_code)

    orchestrator_code = (
        Op.MSTORE(0, mstore_value)
        + (
            Op.CREATE2(1, 0, size, 0)
            if create_opcode == Op.CREATE2
            else Op.CREATE(1, 0, size)
        )
        + Op.MSTORE(0x20, Op.DUP1)
        + Op.POP
        + Op.POP(Op.CALL(gas=Op.GAS, address=Op.MLOAD(0x20), value=0))
    )
    orchestrator = pre.deploy_contract(code=orchestrator_code, balance=3)

    tx = Transaction(
        to=orchestrator,
        state_gas_reservoir=orchestrator_code.state_cost(fork),
        sender=pre.fund_eoa(),
    )

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx])],
        post={},
    )


@pytest.mark.parametrize(
    "beneficiary_type",
    [
        pytest.param("eoa", id="eoa_beneficiary"),
        pytest.param("contract", id="contract_beneficiary"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_call_value_to_pre_existing_selfdestructed_account(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    beneficiary_type: str,
) -> None:
    """
    Verify CALL with value to a pre existing contract that ran
    SELFDESTRUCT charges no new account state gas.

    Per EIP-6780 a pre existing contract that executes SELFDESTRUCT
    is not queued for end of the transaction destruction, so a
    subsequent CALL sees an existing, code carrying account and the
    new account creation gate does not fire.

    Several cold SSTOREs after the CALLs make block state gas
    dominate the block execution gas component, so the block header
    reflects exactly `num_probes * sstore_state_gas`. A spurious
    new account charge on the value bearing CALL would push the
    header up by that charge, breaking the assertion.
    """
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

    # Enough probes that the combined probe state gas dominates the
    # transaction's execution gas component and the header reflects
    # block state gas alone.
    num_probes = 6
    probe_state_gas = num_probes * sstore_state_gas

    # Beneficiary must be alive so the target's SELFDESTRUCT itself
    # does not charge for creating a new beneficiary.
    beneficiary: Address = (
        pre.fund_eoa(amount=1)
        if beneficiary_type == "eoa"
        else pre.deploy_contract(code=Op.STOP)
    )
    target = pre.deploy_contract(
        code=Op.SELFDESTRUCT(beneficiary),
        balance=1,
    )

    probes = Bytecode()
    for slot in range(num_probes):
        probes += Op.SSTORE(slot, 1)
    orchestrator = pre.deploy_contract(
        code=(
            Op.POP(Op.CALL(gas=Op.GAS, address=target))
            + Op.POP(Op.CALL(gas=Op.GAS, address=target, value=1))
            + probes
        ),
        balance=3,
    )

    tx = Transaction(
        to=orchestrator,
        state_gas_reservoir=probe_state_gas,
        sender=pre.fund_eoa(),
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                header_verify=Header(gas_used=probe_state_gas),
            ),
        ],
        post={},
    )


@pytest.mark.parametrize(
    "reservoir_delta",
    [
        pytest.param(-1, id="reservoir_one_short"),
        pytest.param(0, id="reservoir_exact"),
        pytest.param(1, id="reservoir_one_over"),
    ],
)
@pytest.mark.parametrize(
    "child_termination",
    [
        pytest.param("revert", id="child_revert"),
        pytest.param("halt", id="child_halt"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_top_level_halt_burns_spilled_state_gas(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    child_termination: str,
    reservoir_delta: int,
) -> None:
    """
    Verify a top-level halt burns the spilled state gas, so only the
    start reservoir survives. The parent calls a child that reverts or
    halts, then INVALIDs at the top level.

    Under LIFO refills a frame's spilled state gas refills to
    `gas_left`, which the halt then zeros. Only the reservoir-funded
    portion survives, equal to the reservoir at frame start.

    That start value equals the sized reservoir R, so for every child
    failure mode and `reservoir_delta`:

        `state_gas_left_end = R`,
        `tx_gas_used = tx.gas - R = gas_limit_cap`.

    With the reservoir one short (`reservoir_delta == -1`) the child's
    SSTORE spills one unit from `gas_left`, which is refilled then
    burned by the halt. So `tx_gas_used` stays `gas_limit_cap`. The
    old behavior refunded the spill, giving `gas_limit_cap - 1`.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

    if child_termination == "revert":
        child_code: Bytecode = Op.SSTORE(0, 1) + Op.REVERT(0, 0)
    else:
        child_code = Op.SSTORE(0, 1) + Op.INVALID

    child = pre.deploy_contract(code=child_code)

    parent = pre.deploy_contract(
        code=(Op.POP(Op.CALL(gas=500_000, address=child)) + Op.INVALID),
    )

    reservoir = sstore_state_gas + reservoir_delta
    tx_gas = gas_limit_cap + reservoir

    tx = Transaction(
        to=parent,
        state_gas_reservoir=reservoir,
        sender=pre.fund_eoa(),
    )

    # LIFO refills: the spill refills to `gas_left` and is burned by
    # the halt. Only the sized reservoir survives, so
    # `tx_gas_used = gas_limit_cap`.
    state_gas_left_end = reservoir
    expected_gas_used = tx_gas - state_gas_left_end

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                header_verify=Header(gas_used=expected_gas_used),
            ),
        ],
        post={child: Account(storage={0: 0})},
    )


@pytest.mark.valid_from("EIP8037")
def test_callcode_value_no_new_account_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify CALLCODE with value does not charge new-account state
    gas, since the value stays with the caller.
    """
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

    target = pre.fund_eoa(amount=0)

    storage = Storage()
    contract = pre.deploy_contract(
        code=(
            Op.POP(
                Op.CALLCODE(
                    gas=Op.GAS,
                    address=target,
                    value=1,
                )
            )
            + Op.SSTORE(storage.store_next(1, "reservoir_ok"), 1)
        ),
        balance=10**18,
    )

    tx = Transaction(
        to=contract,
        state_gas_reservoir=sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    post = {
        contract: Account(storage=storage),
        target: Account.NONEXISTENT,
    }
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.with_all_create_opcodes()
@pytest.mark.valid_from("EIP8037")
def test_create_oog_during_state_gas_charge(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    create_opcode: Op,
) -> None:
    """
    Verify the parent reservoir is refunded when a child's CREATE
    OOGs while charging account-creation state gas. The grandchild
    SSTORE is forwarded only its execution stipend, so it succeeds
    only if the refund landed in the reservoir (not in `gas_left`).
    """
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

    init_code = Op.STOP
    inner_create_call = (
        create_opcode(value=0, offset=31, size=1, salt=0)
        if create_opcode == Op.CREATE2
        else create_opcode(value=0, offset=31, size=1)
    )

    inner = pre.deploy_contract(
        code=(
            Op.MSTORE(
                0,
                int.from_bytes(bytes(init_code), "big") << 248,
            )
            + Op.POP(inner_create_call)
        ),
    )

    grandchild_storage = Storage()
    grandchild_code = Op.SSTORE(grandchild_storage.store_next(1, "ran"), 1)
    grandchild = pre.deploy_contract(code=grandchild_code)

    grandchild_stipend = grandchild_code.execution_cost(fork)

    parent = pre.deploy_contract(
        code=(
            Op.POP(Op.CALL(gas=20_000, address=inner))
            + Op.POP(Op.CALL(gas=grandchild_stipend, address=grandchild))
        ),
    )

    tx = Transaction(
        to=parent,
        state_gas_reservoir=sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    state_test(
        pre=pre,
        post={grandchild: Account(storage=grandchild_storage)},
        tx=tx,
    )


@pytest.mark.valid_from("EIP8037")
def test_call_new_account_no_execution_account_creation_cost(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify CALL with value to a non-existent account does not
    charge an execution-gas account-creation cost on top of state gas.
    """
    target = pre.fund_eoa(amount=0)

    caller_code = (
        Op.POP(
            Op.CALL(
                gas=0,
                address=target,
                value=1,
                value_transfer=True,
                account_new=True,
            )
        )
        + Op.STOP
    )
    caller = pre.deploy_contract(code=caller_code, balance=1)

    # Tight budget: slack is less than the old pre-Amsterdam execution
    # account-creation cost, so any extra execution draw would OOG.
    intrinsic = fork.transaction_intrinsic_cost_calculator()()
    tx = Transaction(
        to=caller,
        gas_limit=(intrinsic + caller_code.gas_cost(fork) + 20_000),
        sender=pre.fund_eoa(),
    )

    state_test(pre=pre, post={target: Account(balance=1)}, tx=tx)


@pytest.mark.parametrize(
    "gas_delta",
    [pytest.param(0, id="exact_fit"), pytest.param(-1, id="one_short")],
)
@pytest.mark.valid_from("EIP8037")
def test_call_new_account_state_gas_boundary(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_delta: int,
) -> None:
    """
    Pin the CALL new-account state charge at its exact-fit spill
    boundary. At `exact_fit` the charge just fits and the target is
    materialized; one gas short the caller frame goes out of gas, so
    nothing is created and the value transfer is rolled back.
    """
    target = pre.nonexistent_account()
    caller_code = (
        Op.CALL(
            gas=0,
            address=target,
            value=1,
            value_transfer=True,
            account_new=True,
        )
        + Op.STOP
    )
    caller = pre.deploy_contract(code=caller_code, balance=1)

    exact_fit = (
        fork.transaction_intrinsic_cost_calculator()()
        + caller_code.gas_cost(fork)
    )
    post: dict
    if gas_delta == 0:
        gas_used = exact_fit - fork.call_value_stipend()
        post = {target: Account(balance=1), caller: Account(balance=0)}
    else:
        gas_used = exact_fit + gas_delta
        post = {target: Account.NONEXISTENT, caller: Account(balance=1)}

    tx = Transaction(
        to=caller,
        gas_limit=exact_fit + gas_delta,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(cumulative_gas_used=gas_used),
    )

    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "call_opcode,charge_via",
    [
        pytest.param(Op.CALL, "sstore", id="call_sstore_charge"),
        pytest.param(
            Op.DELEGATECALL, "sstore", id="delegatecall_sstore_charge"
        ),
        pytest.param(
            Op.CALL,
            "call_value_new_account",
            id="call_call_value_new_account_charge",
        ),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_child_failure_refunds_state_gas_to_reservoir_not_gas_left(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    call_opcode: Op,
    charge_via: str,
) -> None:
    """
    Verify state gas from a failing child is restored to the
    reservoir, so a sibling probe SSTORE can draw from it under a
    tight execution stipend. Covers SSTORE and CALL-value (new
    account) state-gas charge paths.
    """
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

    probe_storage = Storage()
    probe_code = Op.SSTORE(probe_storage.store_next(1, "probe_ran"), 1)

    if charge_via == "sstore":
        child_code: Bytecode = Op.SSTORE(0, 1) + Op.REVERT(0, 0)
        child_balance = 0
    else:
        fresh_target = pre.fund_eoa(amount=0)
        child_code = Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=fresh_target,
                value=1,
                value_transfer=True,
                account_new=True,
            )
        ) + Op.REVERT(0, 0)
        child_balance = 1
    child_state_charge = child_code.state_cost(fork)

    child = pre.deploy_contract(code=child_code, balance=child_balance)
    probe = pre.deploy_contract(probe_code)
    probe_stipend = probe_code.execution_cost(fork)

    parent = pre.deploy_contract(
        code=(
            Op.POP(call_opcode(gas=Op.GAS, address=child))
            + Op.POP(call_opcode(gas=probe_stipend, address=probe))
        ),
    )

    # Reservoir must cover the child's state charge (refunded on
    # REVERT) so the probe SSTORE can draw from it afterwards.
    reservoir = max(child_state_charge, sstore_state_gas)

    tx = Transaction(
        to=parent,
        state_gas_reservoir=reservoir,
        sender=pre.fund_eoa(),
    )

    # DELEGATECALL executes the callee in the caller's storage
    # context, so the probe's SSTORE lands on `parent` instead of
    # `probe`.
    if call_opcode == Op.DELEGATECALL:
        post: dict = {parent: Account(storage=probe_storage)}
    else:
        post = {probe: Account(storage=probe_storage)}

    state_test(
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=sstore_state_gas),
    )


@pytest.mark.valid_from("EIP8037")
def test_call_insufficient_balance_refunds_new_account_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Refill NEW_ACCOUNT state gas on a value CALL that fails the balance
    check before the child frame.
    """
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

    probe_storage = Storage()
    probe_code = Op.SSTORE(probe_storage.store_next(1, "probe_ran"), 1)
    probe = pre.deploy_contract(probe_code)

    probe_stipend = probe_code.execution_cost(fork)

    non_existent_account = pre.nonexistent_account()

    value_call = Op.CALL(
        gas=Op.GAS,
        address=non_existent_account,
        value=1,
        value_transfer=True,
        account_new=True,
    )
    parent = pre.deploy_contract(
        code=(
            Op.POP(value_call)
            + Op.POP(Op.CALL(gas=probe_stipend, address=probe))
        ),
        balance=0,
    )

    new_account_state_gas = value_call.state_cost(fork)
    assert new_account_state_gas >= sstore_state_gas
    reservoir = new_account_state_gas

    tx = Transaction(
        to=parent,
        state_gas_reservoir=reservoir,
        sender=pre.fund_eoa(),
    )

    post = {probe: Account(storage=probe_storage)}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("EIP8037")
def test_call_value_precompile_halt_refunds_new_account_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Refill NEW_ACCOUNT state gas on a value CALL to an unfunded
    precompile that halts in the child frame.
    """
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

    probe_storage = Storage()
    probe_code = Op.SSTORE(probe_storage.store_next(1, "probe_ran"), 1)
    probe = pre.deploy_contract(probe_code)

    probe_stipend = probe_code.execution_cost(fork)

    ecpairing = 0x08

    value_call = Op.CALL(
        1, ecpairing, 1, 0, 0, 0, 0, value_transfer=True, account_new=True
    )
    parent = pre.deploy_contract(
        code=(
            Op.POP(value_call)
            + Op.POP(Op.CALL(gas=probe_stipend, address=probe))
        ),
        balance=1,
    )

    new_account_state_gas = value_call.state_cost(fork)
    assert new_account_state_gas >= sstore_state_gas
    reservoir = new_account_state_gas

    tx = Transaction(
        to=parent,
        state_gas_reservoir=reservoir,
        sender=pre.fund_eoa(),
    )

    post = {probe: Account(storage=probe_storage)}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize("target_kind", ["new_account", "precompile"])
@pytest.mark.parametrize("reservoir", ["in_cap", "over_cap"])
@pytest.mark.valid_from("EIP8037")
def test_call_value_new_account_state_gas_consumed_on_caller_halt(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    reservoir: str,
    target_kind: str,
) -> None:
    """
    Consume a spilled NEW_ACCOUNT charge when the caller exceptionally halts.

    The caller value-CALLs a zero-balance `target`, charging `NEW_ACCOUNT`
    state gas in its own frame; with an empty reservoir the charge spills into
    `gas_left`. Two child outcomes share identical accounting: a plain new
    account, where the CALL materializes it and succeeds, and the bn256
    pairing precompile forwarded only the value stipend, where the CALL fails
    in the child and the charge is refilled to `gas_left` in LIFO order. The
    caller then hits `INVALID`; the halt burns all of `gas_left`, including
    the spilled charge, and resets the reservoir to its start-of-frame value.
    The sender pays the full execution budget: the whole `gas_limit` in-cap, or
    the EIP-7825 gas cap over-cap (the restored reservoir is refunded). The
    value transfer is rolled back, leaving `target` absent and the caller
    balance intact.

    Both `target_kind` variants assert the same totals by design; the
    child-failure refill itself is pinned by the probe in
    `test_call_value_precompile_halt_refunds_new_account_state_gas`.
    """
    value = 1
    # gas=0 forwards only the value stipend: ignored by the empty account
    # (CALL succeeds), far below the precompile base cost (CALL fails).
    target = (
        Address(0x08)
        if target_kind == "precompile"
        else pre.nonexistent_account()
    )
    caller_code = (
        Op.CALL(
            gas=0,
            address=target,
            value=value,
            value_transfer=True,
            account_new=True,
        )
        + Op.INVALID
    )
    caller = pre.deploy_contract(code=caller_code, balance=value)
    sender = pre.fund_eoa()

    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None

    if reservoir == "over_cap":
        # The excess over the EIP-7825 cap becomes the reservoir.
        gas_limit = gas_limit_cap + caller_code.state_cost(fork) // 2
        expected_gas_used = gas_limit_cap
    else:
        gas_limit = 1_000_000
        expected_gas_used = gas_limit

    tx = Transaction(
        to=caller,
        sender=sender,
        gas_limit=gas_limit,
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=expected_gas_used
        ),
    )

    post = {
        caller: Account(balance=value),
        target: Account.NONEXISTENT,
    }
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize("reservoir", ["in_cap", "over_cap"])
@pytest.mark.valid_from("EIP8037")
def test_call_value_new_account_state_gas_returned_on_caller_revert(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    reservoir: str,
) -> None:
    """
    Return a spilled NEW_ACCOUNT charge when the caller cleanly reverts.

    Same value CALL to the absent account `target` as the halt case, but the
    caller ends with `REVERT`. A revert refills the frame state gas in LIFO
    order: the spilled portion returns to `gas_left` and the reservoir-funded
    portion restores the reservoir, both refunded to the sender. The sender
    pays only the execution gas, the same value in-cap and over-cap,
    and the value transfer is rolled back.
    """
    value = 1
    target = pre.nonexistent_account()
    caller_code = Op.CALL(
        gas=0,
        address=target,
        value=value,
        value_transfer=True,
        account_new=True,
    ) + Op.REVERT(0, 0)
    caller = pre.deploy_contract(code=caller_code, balance=value)
    sender = pre.fund_eoa()

    # Only execution gas is billed: the spilled and reservoir-funded
    # parts of the NEW_ACCOUNT charge are both refunded, so the cost
    # matches in-cap and over-cap. `execution_cost` covers the pushes, cold
    # access and the value transfer (NEW_ACCOUNT lands in the state
    # dimension); the empty child returns its stipend unused.
    expected_gas_used = (
        fork.transaction_intrinsic_cost_calculator()()
        + caller_code.execution_cost(fork)
        - fork.call_value_stipend()
    )
    receipt = TransactionReceipt(cumulative_gas_used=expected_gas_used)

    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    gas_limit = (
        gas_limit_cap + caller_code.state_cost(fork) // 2
        if reservoir == "over_cap"
        else 1_000_000
    )

    tx = Transaction(
        to=caller,
        sender=sender,
        gas_limit=gas_limit,
        expected_receipt=receipt,
    )

    post = {
        caller: Account(balance=value),
        target: Account.NONEXISTENT,
    }
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("EIP8037")
def test_reverted_grandchild_spill_through_child_halt(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify a grandchild's reverted spill does not ride through the
    child's exceptional halt into the caller's accounting: the receipt
    pins that the sender pays the halted child's forwarded budget
    exactly once, not the grandchild's refilled spill on top.

    The tx gas limit sits below the EIP-7825 cap, so the reservoir is
    empty and the grandchild's set spills from `gas_left`.
    """
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()()
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)
    child_budget = 400_000

    grandchild = pre.deploy_contract(code=Op.SSTORE(0, 1) + Op.REVERT(0, 0))
    child = pre.deploy_contract(
        code=Op.POP(Op.CALL(gas=Op.GAS, address=grandchild)) + Op.INVALID,
    )

    storage = Storage()
    # The child call halts and returns 0, so the caller's first SSTORE
    # is a cold no-op (0 to 0) on a fresh slot rather than the cold set
    # `execution_cost` assumes by default.
    caller_code = Op.SSTORE.with_metadata(
        key_warm=False,
        original_value=0,
        current_value=0,
        new_value=0,
    )(
        storage.store_next(0, "child_halted"),
        Op.CALL(gas=child_budget, address=child),
    ) + Op.SSTORE(storage.store_next(1, "caller_completed"), 1)
    caller = pre.deploy_contract(code=caller_code)

    # The halted child consumes its whole forwarded budget as execution
    # gas; the caller's slot-1 set is the only surviving state charge.
    expected_cumulative = (
        intrinsic_cost
        + caller_code.execution_cost(fork)
        + child_budget
        + sstore_state_gas
    )

    tx = Transaction(
        to=caller,
        gas_limit=1_000_000,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=expected_cumulative,
        ),
    )

    post = {
        caller: Account(storage=storage),
        grandchild: Account(storage={0: 0}),
    }
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("EIP8037")
def test_soft_failed_value_call_refund_through_child_halt(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify a same-frame NEW_ACCOUNT charge-and-refund (a value CALL
    soft-failing the balance check) performed after a reverted child
    call, merged into a frame with its own spilled set that then
    exceptionally halts, charges the sender the halted frame's budget
    exactly once — pinned by the receipt.
    """
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()()
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)
    child_budget = 600_000

    grandchild = pre.deploy_contract(code=Op.SSTORE(0, 1) + Op.REVERT(0, 0))
    fresh = pre.nonexistent_account()
    # Zero balance: the value CALL soft-fails its balance check after
    # the up-front NEW_ACCOUNT state charge, refunded in-frame.
    middle = pre.deploy_contract(
        code=(
            Op.POP(Op.CALL(gas=Op.GAS, address=grandchild))
            + Op.POP(Op.CALL(gas=Op.GAS, address=fresh, value=1))
            + Op.STOP
        ),
    )
    child = pre.deploy_contract(
        code=(
            Op.SSTORE(0, 1)
            + Op.POP(Op.CALL(gas=Op.GAS, address=middle))
            + Op.INVALID
        ),
    )

    storage = Storage()
    # The child call halts and returns 0, so the caller's first SSTORE
    # is a cold no-op (0 to 0) on a fresh slot rather than the cold set
    # `execution_cost` assumes by default.
    caller_code = Op.SSTORE.with_metadata(
        key_warm=False,
        original_value=0,
        current_value=0,
        new_value=0,
    )(
        storage.store_next(0, "child_halted"),
        Op.CALL(gas=child_budget, address=child),
    ) + Op.SSTORE(storage.store_next(1, "caller_completed"), 1)
    caller = pre.deploy_contract(code=caller_code)

    # The halted child consumes its whole forwarded budget as execution
    # gas; the caller's slot-1 set is the only surviving state charge.
    expected_cumulative = (
        intrinsic_cost
        + caller_code.execution_cost(fork)
        + child_budget
        + sstore_state_gas
    )

    tx = Transaction(
        to=caller,
        gas_limit=1_000_000,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=expected_cumulative,
        ),
    )

    post = {
        caller: Account(storage=storage),
        child: Account(storage={0: 0}),
        fresh: Account.NONEXISTENT,
    }
    state_test(pre=pre, post=post, tx=tx)
