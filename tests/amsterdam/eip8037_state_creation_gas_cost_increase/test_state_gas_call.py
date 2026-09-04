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
    CodeGasMeasure,
    Conditional,
    Fork,
    Header,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
    TransactionReceipt,
    WhileGas,
    compute_create_address,
)
from execution_testing.checklists import EIPChecklist

from .spec import init_code_at_high_bytes, ref_spec_8037

REFERENCE_SPEC_GIT_PATH = ref_spec_8037.git_path
REFERENCE_SPEC_VERSION = ref_spec_8037.version


@pytest.mark.parametrize("funding", ["reservoir", "spill"])
@pytest.mark.parametrize(
    "sufficient_gas",
    ["sufficient_gas", "insufficient_execute", "insufficient_state"],
)
@pytest.mark.valid_from("EIP8037")
def test_child_call_uses_reservoir(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    sufficient_gas: str,
    funding: str,
) -> None:
    """
    Test child call can use parent's state gas reservoir.

    Parent calls child SSTORE. Test two modes:
    reservoir (uses parent's state gas) vs spill (uses forwarded gas).
    Both test behavior when gas runs out.
    """
    child_storage = Storage()
    code = Op.SSTORE(
        child_storage.store_next(
            1 if sufficient_gas == "sufficient_gas" else 0
        ),
        1,
        # gas accounting
        original_value=0,
        new_value=1,
    )

    state_gas = code.state_cost(fork)
    execution_gas = code.execution_cost(fork)
    if sufficient_gas == "insufficient_execute":
        execution_gas -= 1
    elif sufficient_gas == "insufficient_state":
        state_gas -= 1

    if funding == "spill":
        child_gas = execution_gas + state_gas
        reservoir = 0
    else:
        child_gas = execution_gas
        reservoir = state_gas

    child = pre.deploy_contract(
        code=code,
    )

    parent_storage = Storage()
    parent = pre.deploy_contract(
        code=(
            Op.SSTORE(
                parent_storage.store_next(
                    1 if sufficient_gas == "sufficient_gas" else 0
                ),
                Op.CALL(gas=child_gas, address=child),
            )
        )
    )

    tx = Transaction(
        to=parent,
        state_gas_reservoir=reservoir,
        sender=pre.fund_eoa(),
    )

    post = {
        parent: Account(storage=parent_storage),
        child: Account(storage=child_storage),
    }
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize("funding", ["spill", "mixed"])
@pytest.mark.valid_from("EIP8037")
def test_delegatecall_child_spill_not_double_charged(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    funding: str,
) -> None:
    """
    Test DELEGATECALL child state gas paid from `gas_left` is not recharged.

    With the gas limit pinned to the Amsterdam tx gas cap and no requested
    reservoir (`state_gas_reservoir=0`), the top-level frame starts with no
    state gas reservoir and the child pays for SSTOREs by spilling from
    `gas_left`. The parent frame must not charge the same state growth again
    at frame end: the header bills the storage sets once, in the state
    dimension, so a second charge surfaces as inflated `gas_used`.

    `mixed` funds one set from the reservoir and spills the rest, so the
    header must stay put however the charge is split.
    """
    num_sstores = 6
    child_code = (
        sum(
            Op.SSTORE(
                i,
                1,
                # gas accounting
                original_value=0,
                new_value=1,
            )
            for i in range(num_sstores)
        )
        + Op.STOP
    )

    child = pre.deploy_contract(code=child_code)

    caller_code = Op.POP(
        Op.DELEGATECALL(
            gas=Op.GAS,
            address=child,
            args_offset=0,
            args_size=0,
            ret_offset=0,
            ret_size=0,
        )
    )
    caller = pre.deploy_contract(code=caller_code)

    state_gas = child_code.state_cost(fork)
    execution_gas = (
        fork.transaction_intrinsic_cost_calculator()()
        + caller_code.execution_cost(fork)
        + child_code.execution_cost(fork)
    )
    expected_gas_used = max(execution_gas, state_gas)
    assert expected_gas_used == state_gas, (
        "expected state gas to dominate execution gas"
    )

    if funding == "mixed":
        reservoir = Op.SSTORE(new_value=1).state_cost(fork)
    else:
        reservoir = 0

    tx = Transaction(
        to=caller,
        state_gas_reservoir=reservoir,
        sender=pre.fund_eoa(),
    )

    post = {
        caller: Account(storage=dict.fromkeys(range(num_sstores), 1)),
    }
    state_test(
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=expected_gas_used),
    )


@pytest.mark.valid_from("EIP8037")
def test_reservoir_returned_on_revert(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test state gas reservoir is returned to parent on child revert.

    The child draws the whole reservoir for an SSTORE then reverts,
    restoring it. Repeating that leaves the parent with only one
    SSTORE's execution cost, so its own SSTORE has nothing to spill
    from and lands only if the restores went back to the reservoir.
    """
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

    child_code = Op.SSTORE(0, 1) + Op.REVERT(0, 0)
    child = pre.deploy_contract(code=child_code)

    parent_storage = Storage()
    final_sstore = Op.SSTORE(parent_storage.store_next(1), 1)

    child_gas = child_code.execution_cost(fork)
    parent_code = (
        WhileGas(
            body=Op.POP(
                Op.CALL(
                    gas=child_gas,
                    address=child,
                    # gas accounting
                    address_warm=True,
                    inner_call_cost=child_gas,
                )
            ),
            fork=fork,
            extra_gas=final_sstore.execution_cost(fork),
        )
        + final_sstore
    )
    parent = pre.deploy_contract(code=parent_code)

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

    The child draws the whole reservoir for an SSTORE then halts on its
    last gas, restoring it. Repeating that leaves the parent with only
    one SSTORE's execution cost, so its own SSTORE has nothing to spill
    from: it lands only if the reservoir came back.
    """
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

    child_code = Op.SSTORE(0, 1) + Op.INVALID
    child = pre.deploy_contract(code=child_code)

    parent_storage = Storage()
    final_sstore = Op.SSTORE(parent_storage.store_next(1), 1)
    # Without this metadata `WhileGas` sizes an iteration from the call
    # opcode alone, misses the forwarded gas, and exits too low.
    child_gas = child_code.execution_cost(fork)
    parent_code = (
        WhileGas(
            body=Op.POP(
                Op.CALL(
                    gas=child_gas,
                    address=child,
                    # gas accounting
                    address_warm=True,
                    inner_call_cost=child_gas,
                )
            ),
            fork=fork,
            extra_gas=final_sstore.execution_cost(fork),
        )
        + final_sstore
    )
    parent = pre.deploy_contract(code=parent_code)

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
    portion restores the reservoir to its start value. The parent then
    calls a probe handed only its SSTORE's execution cost, so the probe
    has no `gas_left` to spill from and succeeds only if the reservoir
    itself was restored.
    """
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

    child_code = Op.SSTORE(0, 1) + Op.SSTORE(1, 1) + Op.REVERT(0, 0)
    child = pre.deploy_contract(code=child_code)
    # Exactly enough for both SSTOREs: the reservoir funds the first and
    # the second spills.
    child_gas = child_code.execution_cost(fork) + sstore_state_gas

    probe_code = Op.SSTORE(0, 1)
    probe = pre.deploy_contract(code=probe_code)
    probe_gas = probe_code.execution_cost(fork)

    parent_storage = Storage()
    probe_slot = parent_storage.store_next(1, "probe_succeeds")
    parent_code = Op.POP(Op.CALL(gas=child_gas, address=child)) + Op.SSTORE(
        probe_slot,
        Op.CALL(gas=probe_gas, address=probe),
        original_value=1,
        current_value=1,
        new_value=1,
        key_warm=False,
    )
    parent = pre.deploy_contract(code=parent_code, storage={probe_slot: 1})

    execution_gas = (
        fork.transaction_intrinsic_cost_calculator()()
        + parent_code.execution_cost(fork)
        + child_code.execution_cost(fork)
        + probe_gas
    )
    expected_gas_used = max(execution_gas, sstore_state_gas)

    tx = Transaction(
        to=parent,
        state_gas_reservoir=sstore_state_gas,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=execution_gas + sstore_state_gas,
        ),
    )

    post = {
        parent: Account(storage=parent_storage),
        probe: Account(storage={0: 1}),
    }
    state_test(
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=expected_gas_used),
    )


@pytest.mark.parametrize(
    "call_opcode",
    [Op.CALL, Op.CALLCODE, Op.DELEGATECALL],
)
@pytest.mark.valid_from("EIP8037")
def test_reservoir_restored_after_child_spill_and_halt(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    call_opcode: Op,
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

    child_code = Op.SSTORE(0xDEAD, 1) + Op.SSTORE(0xBEAF, 1) + Op.INVALID
    child = pre.deploy_contract(code=child_code)
    # Exactly enough for both SSTOREs: the reservoir funds the first and
    # the second spills, leaving nothing for the INVALID to burn.
    child_gas = child_code.execution_cost(fork) + sstore_state_gas

    probe_code = Op.SSTORE(0, 1)
    probe_gas = probe_code.execution_cost(fork)
    funded_probe = pre.deploy_contract(code=probe_code)
    starved_probe = pre.deploy_contract(code=probe_code)

    parent_storage = Storage()
    funded_slot = parent_storage.store_next(1)
    starved_slot = parent_storage.store_next(0)
    parent_code = (
        Op.POP(call_opcode(gas=child_gas, address=child))
        + Op.SSTORE(
            funded_slot,
            Op.CALL(gas=probe_gas, address=funded_probe),
            # gas accounting
            original_value=1,
            current_value=1,
            new_value=1,
            key_warm=False,
        )
        + Op.SSTORE(
            starved_slot,
            Op.CALL(gas=probe_gas, address=starved_probe),
            # gas accounting
            original_value=1,
            current_value=1,
            new_value=0,
            key_warm=False,
        )
    )
    parent = pre.deploy_contract(
        code=parent_code, storage={funded_slot: 1, starved_slot: 1}
    )

    execution_gas = (
        fork.transaction_intrinsic_cost_calculator()()
        + parent_code.execution_cost(fork)
        + child_gas
        + 2 * probe_gas
    )
    expected_gas_used = max(execution_gas, sstore_state_gas)

    # Recording the starved probe's failure clears its slot, which earns
    # an execution refund the sender-facing receipt is net of.
    gas_used_before_refund = execution_gas + sstore_state_gas
    refund = min(
        gas_used_before_refund // fork.max_refund_quotient(),
        parent_code.refund(fork),
    )

    tx = Transaction(
        to=parent,
        state_gas_reservoir=sstore_state_gas,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=gas_used_before_refund - refund,
        ),
    )

    post = {
        parent: Account(storage=parent_storage),
        funded_probe: Account(storage={funded_slot: 1}),
        starved_probe: Account(storage={starved_slot: 0}),
    }
    state_test(
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=expected_gas_used),
    )


@pytest.mark.parametrize(
    "sufficent_gas",
    [
        pytest.param(False, id="insufficient_gas"),
        pytest.param(True, id="sufficient_gas"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_reservoir_restored_after_child_full_drain_and_revert(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    sufficent_gas: bool,
) -> None:
    """
    Test reservoir restored when child exactly exhausts it then reverts.

    The child is granted only its execution cost, so its single SSTORE
    must draw the whole state charge from the reservoir, then REVERTs.
    The parent then calls a probe handed only its SSTORE's execution
    cost, so the probe has no `gas_left` to spill from and succeeds
    only if the full reservoir came back.
    """
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

    child_code = Op.SSTORE(0, 1) + Op.REVERT(0, 0)
    child = pre.deploy_contract(code=child_code)
    child_gas = child_code.execution_cost(fork)

    probe_code = Op.SSTORE(0, 1)
    probe = pre.deploy_contract(code=probe_code)
    probe_gas = probe_code.execution_cost(fork)
    if not sufficent_gas:
        probe_gas -= 1

    parent_storage = Storage()
    probe_slot = parent_storage.store_next(
        2 if sufficent_gas else 1, "probe_succeeds"
    )
    parent_code = Op.POP(Op.CALL(gas=child_gas, address=child)) + Op.SSTORE(
        probe_slot,
        Op.ADD(Op.CALL(gas=probe_gas, address=probe), 1),
        # gas accounting
        original_value=1,
        current_value=1,
        new_value=2 if sufficent_gas else 1,
        key_warm=False,
    )
    parent = pre.deploy_contract(code=parent_code, storage={probe_slot: 1})

    execution_gas = (
        fork.transaction_intrinsic_cost_calculator()()
        + parent_code.execution_cost(fork)
        + child_gas
        + probe_gas
    )
    expected_gas_used = max(
        execution_gas, sstore_state_gas if sufficent_gas else 0
    )

    tx = Transaction(
        to=parent,
        state_gas_reservoir=sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    post = {
        parent: Account(storage=parent_storage),
        probe: Account(storage={0: 1 if sufficent_gas else 0}),
    }
    state_test(
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=expected_gas_used),
    )


@pytest.mark.parametrize(
    "sufficent_gas",
    [
        pytest.param(False, id="insufficient_gas"),
        pytest.param(True, id="sufficient_gas"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_sequential_calls_reservoir_restored_between_reverts(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    sufficent_gas: bool,
) -> None:
    """
    Test reservoir restored across sequential child reverts.

    Parent calls the child twice; each run uses the reservoir for an
    SSTORE and reverts, restoring it. The parent then calls a probe
    handed only its SSTORE's execution cost, so the probe has no
    `gas_left` to spill from and succeeds only if both restores landed
    in the reservoir rather than in `gas_left`.
    """
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

    child_code = Op.SSTORE(0, 1) + Op.REVERT(0, 0)
    child = pre.deploy_contract(code=child_code)
    child_gas = child_code.execution_cost(fork)

    probe_code = Op.SSTORE(0, 1)
    probe = pre.deploy_contract(code=probe_code)
    probe_gas = probe_code.execution_cost(fork)
    if not sufficent_gas:
        probe_gas -= 1

    parent_storage = Storage()
    probe_slot = parent_storage.store_next(
        2 if sufficent_gas else 1, "probe_succeeds"
    )
    parent_code = (
        Op.POP(Op.CALL(gas=child_gas, address=child))
        + Op.POP(Op.CALL(gas=child_gas, address=child, address_warm=True))
        + Op.SSTORE(
            probe_slot,
            Op.ADD(Op.CALL(gas=probe_gas, address=probe), 1),
            # gas accounting
            original_value=1,
            current_value=1,
            new_value=2 if sufficent_gas else 1,
            key_warm=False,
        )
    )
    parent = pre.deploy_contract(code=parent_code, storage={probe_slot: 1})

    execution_gas = (
        fork.transaction_intrinsic_cost_calculator()()
        + parent_code.execution_cost(fork)
        + 2 * child_gas
        + probe_gas
    )
    expected_gas_used = max(
        execution_gas, sstore_state_gas if sufficent_gas else 0
    )

    tx = Transaction(
        to=parent,
        state_gas_reservoir=sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    post = {
        parent: Account(storage=parent_storage),
        probe: Account(storage={0: 1 if sufficent_gas else 0}),
    }
    state_test(
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=expected_gas_used),
    )


@pytest.mark.parametrize(
    "sufficient_gas",
    [
        pytest.param(False, id="insufficient_gas"),
        pytest.param(True, id="sufficient_gas"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_nested_calls_reservoir_passing(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    sufficient_gas: bool,
) -> None:
    """
    Test reservoir passes through nested calls.

    The reservoir is passed from A to B to C. C performs an SSTORE
    using the reservoir gas. After all calls return, A verifies
    success. C is handed only its execution cost, so one gas less
    halts it before the SSTORE and leaves the reservoir untouched.
    """
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

    c_storage = Storage()
    c_code = Op.SSTORE(c_storage.store_next(1 if sufficient_gas else 0), 1)
    c = pre.deploy_contract(code=c_code)
    c_gas = c_code.execution_cost(fork)
    if not sufficient_gas:
        c_gas -= 1

    # Each hop forwards only execution gas; the reservoir rides along in
    # full, so C's SSTORE lands only if it reached the bottom frame. B
    # gets 64/63 of C's need because a frame may forward at most 63/64
    # of the gas it holds.
    b_code = Op.CALL(gas=c_gas, address=c)
    b = pre.deploy_contract(code=b_code)

    a_storage = Storage()
    call_slot = a_storage.store_next(1, "nested_call_succeeds")
    a_code = Op.SSTORE(
        call_slot,
        Op.CALL(address=b),
        # gas accounting
        original_value=1,
        current_value=1,
        new_value=1,
        key_warm=False,
    )
    a = pre.deploy_contract(code=a_code, storage={call_slot: 1})

    execution_gas = (
        fork.transaction_intrinsic_cost_calculator()()
        + a_code.execution_cost(fork)
        + b_code.execution_cost(fork)
        + c_gas
    )
    expected_gas_used = max(
        execution_gas, sstore_state_gas if sufficient_gas else 0
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
    state_test(
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=expected_gas_used),
    )


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
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
    # The slot already holds the value the CALL returns, so the
    # recording SSTORE is a no-op write that adds no state gas; the
    # reservoir then covers exactly the CALL's new-account charge.
    call_slot = parent_storage.store_next(1)
    parent_code = Op.SSTORE(
        call_slot,
        Op.CALL(
            gas=0,
            address=target,
            value=1,
            value_transfer=True,
            account_new=True,
        ),
        # gas accounting
        original_value=1,
        current_value=1,
        new_value=1,
        key_warm=False,
    )
    parent = pre.deploy_contract(
        code=parent_code, balance=1, storage={call_slot: 1}
    )

    state_gas = parent_code.state_cost(fork)
    # The codeless target returns the forwarded value-call stipend
    # unused, so it is charged but never consumed.
    execution_gas = (
        fork.transaction_intrinsic_cost_calculator()()
        + parent_code.execution_cost(fork)
        - fork.call_value_stipend()
    )
    expected_gas_used = max(execution_gas, state_gas)
    assert expected_gas_used == state_gas, (
        "expected state gas to dominate execution gas"
    )

    tx = Transaction(
        to=parent,
        state_gas_reservoir=state_gas,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=execution_gas + state_gas
        ),
    )

    post = {
        parent: Account(storage=parent_storage),
        target: Account(balance=1),
    }
    state_test(
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=expected_gas_used),
    )


@pytest.mark.valid_from("EIP8037")
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
    # Existing target account
    target = pre.fund_eoa(amount=1)

    parent_storage = Storage()

    call_slot = parent_storage.store_next(1)
    parent_code = Op.SSTORE(
        call_slot,
        Op.CALL(gas=0, address=target, value=1, value_transfer=True),
        original_value=1,
        current_value=1,
        new_value=1,
        key_warm=False,
    )
    parent = pre.deploy_contract(
        code=parent_code, balance=1, storage={call_slot: 1}
    )

    state_gas = parent_code.state_cost(fork)
    execution_gas = (
        fork.transaction_intrinsic_cost_calculator()()
        + parent_code.execution_cost(fork)
        - fork.call_value_stipend()
    )
    expected_gas_used = max(execution_gas, state_gas)
    assert state_gas == 0 and expected_gas_used == execution_gas, (
        "expected no state gas and execution gas to dominate"
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
    state_test(
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=expected_gas_used),
    )


@pytest.mark.valid_from("EIP8037")
def test_child_state_gas_tracked_in_parent(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test state gas used by child is accumulated in parent.

    Both parent and child perform SSTOREs, and the reservoir is sized
    for exactly those two. A probe handed only its SSTORE's execution
    cost then finds the reservoir empty and fails; it would succeed if
    the child's draw had gone unrecorded in the parent.
    """
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

    child_storage = Storage()
    child_code = Op.SSTORE(child_storage.store_next(1), 1)
    child = pre.deploy_contract(code=child_code)
    child_gas = child_code.execution_cost(fork)

    probe_code = Op.SSTORE(0, 1)
    probe = pre.deploy_contract(code=probe_code)
    probe_gas = probe_code.execution_cost(fork)

    parent_storage = Storage()
    probe_slot = parent_storage.store_next(0, "probe_fails")
    parent_code = (
        Op.SSTORE(parent_storage.store_next(1, "parent"), 1)
        + Op.POP(Op.CALL(gas=child_gas, address=child))
        + Op.SSTORE(
            probe_slot,
            Op.CALL(gas=probe_gas, address=probe),
            # gas accounting
            original_value=1,
            current_value=1,
            new_value=0,
            key_warm=False,
        )
    )
    parent = pre.deploy_contract(code=parent_code, storage={probe_slot: 1})

    # Sized for the parent's and the child's SSTORE and nothing more, so
    # the probe finds the reservoir empty with no gas_left to spill from.
    tx = Transaction(
        to=parent,
        state_gas_reservoir=sstore_state_gas * 2,
        sender=pre.fund_eoa(),
    )

    post = {
        parent: Account(storage=parent_storage),
        child: Account(storage=child_storage),
        probe: Account(storage={0: 0}),
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
    The child's SSTORE writes to the parent's storage using state gas
    from the reservoir, emptying it. A probe handed only its SSTORE's
    execution cost then fails, proving the draw was real.
    """
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

    parent_storage = Storage()
    # Library code runs in parent's context — slot is reserved on
    # parent_storage so the post check uses the same source of truth.
    library_code = Op.SSTORE(parent_storage.store_next(1), 1)
    library = pre.deploy_contract(code=library_code)

    probe_code = Op.SSTORE(0, 1)
    probe = pre.deploy_contract(code=probe_code)
    probe_gas = probe_code.execution_cost(fork)

    probe_slot = parent_storage.store_next(0, "probe_fails")
    parent_code = Op.POP(
        Op.DELEGATECALL(gas=library_code.execution_cost(fork), address=library)
    ) + Op.SSTORE(
        probe_slot,
        Op.CALL(gas=probe_gas, address=probe),
        # gas accounting
        original_value=1,
        current_value=1,
        new_value=0,
        key_warm=False,
    )
    parent = pre.deploy_contract(code=parent_code, storage={probe_slot: 1})

    tx = Transaction(
        to=parent,
        state_gas_reservoir=sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    post = {
        parent: Account(storage=parent_storage),
        probe: Account(storage={0: 0}),
    }
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "child_action,reservoir_shortfall",
    [
        pytest.param("write_rejected", 0, id="write_rejected"),
        pytest.param("read_only", 0, id="read_only"),
        pytest.param("create", 0, id="create_exact"),
        pytest.param("create", 1, id="create_one_short"),
        pytest.param("create2", 0, id="create2_exact"),
        pytest.param("create2", 1, id="create2_one_short"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_staticcall_passes_reservoir(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    child_action: str,
    reservoir_shortfall: int,
) -> None:
    """Preserve the reservoir across successful and rejected static calls."""
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

    if child_action == "read_only":
        child_code: Bytecode = Op.POP(Op.SLOAD(0, key_warm=False))
        static_result = 1
    elif child_action == "write_rejected":
        child_code = Op.SSTORE(0, 1)
        static_result = 0
    else:
        create_opcode = Op.CREATE if child_action == "create" else Op.CREATE2
        child_code = create_opcode(value=0, offset=0, size=0, init_code_size=0)
        static_result = 0
    child = pre.deploy_contract(code=child_code)
    child_gas = child_code.execution_cost(fork)
    creating = child_action in ("create", "create2")
    if creating:
        # Fund a misplaced account charge far enough to expose spill handling.
        child_gas += child_code.state_cost(fork)
        assert child_code.state_cost(fork) > sstore_state_gas
    probe_succeeds = reservoir_shortfall == 0

    probe_code = Op.SSTORE(0, 1)
    probe = pre.deploy_contract(code=probe_code)
    probe_gas = probe_code.execution_cost(fork)

    parent_storage = Storage()
    static_slot = parent_storage.store_next(
        static_result + 1, "staticcall_result"
    )
    # The probe receives execution gas only: exact reservoir succeeds;
    # one short must fail, exposing either lost gas or an inflated reservoir.
    probe_slot = parent_storage.store_next(1 + probe_succeeds, "probe_result")
    parent_code = Op.SSTORE(
        static_slot,
        Op.ADD(Op.STATICCALL(gas=child_gas, address=child), 1),
        # gas accounting
        original_value=1,
        current_value=1,
        new_value=static_result + 1,
        key_warm=False,
    ) + Op.SSTORE(
        probe_slot,
        Op.ADD(Op.CALL(gas=probe_gas, address=probe), 1),
        # gas accounting
        original_value=1,
        current_value=1,
        new_value=1 + probe_succeeds,
        key_warm=False,
    )
    parent = pre.deploy_contract(
        code=parent_code, storage={static_slot: 1, probe_slot: 1}
    )

    execution_gas = (
        fork.transaction_intrinsic_cost_calculator()()
        + parent_code.execution_cost(fork)
        + child_gas
        + probe_gas
    )
    state_gas = sstore_state_gas if probe_succeeds else 0
    expected_gas_used = max(execution_gas, state_gas)
    if not creating:
        assert expected_gas_used == state_gas, (
            "expected state gas to dominate execution gas"
        )

    tx = Transaction(
        to=parent,
        state_gas_reservoir=sstore_state_gas - reservoir_shortfall,
        sender=pre.fund_eoa(),
    )

    post: dict[Address, Account | None] = {
        parent: Account(storage=parent_storage),
        child: Account(nonce=1, storage={0: 0}),
        probe: Account(storage={0: int(probe_succeeds)}),
    }
    if creating:
        created = compute_create_address(
            address=child, nonce=1, salt=0, initcode=b"", opcode=create_opcode
        )
        post[created] = Account.NONEXISTENT
    state_test(
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=expected_gas_used),
    )


@pytest.mark.valid_from("EIP8037")
def test_gas_opcode_excludes_reservoir(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test GAS opcode returns gas_left only, excluding the reservoir.

    Measuring GAS either side of a call whose child spends the
    reservoir yields the execution gas alone. Had GAS reported the
    reservoir too, the difference would be inflated by the child's
    state charge.
    """
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

    child_code = Op.SSTORE(0, 1)
    child = pre.deploy_contract(code=child_code)
    child_gas = child_code.execution_cost(fork)

    # GAS before and after a call whose child spends the reservoir. The
    # difference is the execution gas alone; had GAS reported the
    # reservoir too, it would be inflated by the child's state charge.
    measured_code = Op.CALL(gas=child_gas, address=child)
    measured_gas = measured_code.execution_cost(fork) + child_gas
    contract = pre.deploy_contract(
        code=CodeGasMeasure(
            code=measured_code,
            overhead_cost=0,
            extra_stack_items=1,
        ),
    )

    tx = Transaction(
        to=contract,
        state_gas_reservoir=sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    post = {
        contract: Account(storage={0: measured_gas}),
        child: Account(storage={0: 1}),
    }
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
    returned to the parent. A probe handed only its SSTORE's execution
    cost then succeeds, proving the reservoir came back rather than the
    gas landing in `gas_left`. The new-account variant (where
    NEW_ACCOUNT is charged then refilled on the same failure) is pinned
    by test_call_insufficient_balance_refunds_new_account_state_gas.
    """
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

    target = pre.deploy_contract(code=Op.STOP)

    probe_code = Op.SSTORE(0, 1)
    probe = pre.deploy_contract(code=probe_code)
    probe_gas = probe_code.execution_cost(fork)

    storage = Storage()
    call_slot = storage.store_next(0, "call_fails")
    probe_slot = storage.store_next(1, "probe_succeeds")
    contract_code = Op.SSTORE(
        call_slot, Op.CALL(gas=0, address=target, value=1)
    ) + Op.SSTORE(
        probe_slot,
        Op.CALL(gas=probe_gas, address=probe),
        # gas accounting
        original_value=1,
        current_value=1,
        new_value=1,
        key_warm=False,
    )
    contract = pre.deploy_contract(code=contract_code, storage={probe_slot: 1})

    # The probe is handed only its execution cost, so its SSTORE lands
    # only if the failed call handed the reservoir back intact.
    tx = Transaction(
        to=contract,
        state_gas_reservoir=sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    post = {
        contract: Account(storage=storage),
        probe: Account(storage={0: 1}),
    }
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
    reservoir are returned to the parent frame. A probe handed only its
    SSTORE's execution cost then succeeds, proving the state gas came
    back to the reservoir rather than to `gas_left`.
    """
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

    init_code = Op.STOP
    mstore_value, init_code_size = init_code_at_high_bytes(init_code)

    probe_code = Op.SSTORE(0, 1)
    probe = pre.deploy_contract(code=probe_code)
    probe_gas = probe_code.execution_cost(fork)

    storage = Storage()
    create_slot = storage.store_next(0, "create_fails")
    probe_slot = storage.store_next(1, "probe_succeeds")
    contract_code = (
        Op.MSTORE(0, mstore_value)
        + Op.SSTORE(create_slot, Op.CREATE(1, 0, init_code_size))
        + Op.SSTORE(
            probe_slot,
            Op.CALL(gas=probe_gas, address=probe),
            # gas accounting
            original_value=1,
            current_value=1,
            new_value=1,
            key_warm=False,
        )
    )
    contract = pre.deploy_contract(code=contract_code, storage={probe_slot: 1})

    tx = Transaction(
        to=contract,
        state_gas_reservoir=sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    post = {
        contract: Account(storage=storage),
        probe: Account(storage={0: 1}),
    }
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("EIP8037")
def test_call_stack_depth_returns_reservoir(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test a deep self-recursing call chain returns the reservoir.

    Each frame recurses while it has the gas to, and the bottom one
    instead draws the whole reservoir for an SSTORE and reverts,
    restoring it. A probe in the top frame, handed only its SSTORE's
    execution cost, then succeeds only if that restore travelled back
    up the entire unwind.
    """
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

    # Recurse while there is comfortably more gas than the bottom frame
    # needs. Gas shrinks by only 1/64 per level, so the frame that first
    # falls below the threshold still holds well over `bottom_gas`.
    bottom = Op.SSTORE(0, 1) + Op.REVERT(0, 0)
    bottom_gas = bottom.execution_cost(fork)
    driver_code = Conditional(
        condition=Op.GT(Op.GAS, 2 * bottom_gas),
        if_true=Op.POP(Op.CALL(Op.GAS, Op.ADDRESS, 0, 0, 0, 0, 0)),
        if_false=bottom,
    )
    driver = pre.deploy_contract(code=driver_code)

    probe_code = Op.SSTORE(0, 1)
    probe = pre.deploy_contract(code=probe_code)
    probe_gas = probe_code.execution_cost(fork)

    storage = Storage()
    probe_slot = storage.store_next(1, "probe_succeeds")
    caller_code = Op.POP(Op.CALL(gas=Op.GAS, address=driver)) + Op.SSTORE(
        probe_slot,
        Op.CALL(gas=probe_gas, address=probe),
        # gas accounting
        original_value=1,
        current_value=1,
        new_value=1,
        key_warm=False,
    )
    caller = pre.deploy_contract(code=caller_code, storage={probe_slot: 1})

    tx = Transaction(
        to=caller,
        state_gas_reservoir=sstore_state_gas,
        sender=pre.fund_eoa(),
    )

    post = {
        caller: Account(storage=storage),
        probe: Account(storage={0: 1}),
    }
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


@pytest.mark.parametrize(
    "create_opcode",
    [
        pytest.param(Op.CREATE, id="create"),
        pytest.param(Op.CREATE2, id="create2"),
    ],
)
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
    nor nonexistent and the new account creation gate does not fire.
    End of the transaction destruction then clears its nonce, code and
    storage but leaves the balance in place. Strict discrimination of
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
        + Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=Op.MLOAD(0x20),
                value=1,
                # gas accounting
                value_transfer=True,
            )
        )
    )
    orchestrator = pre.deploy_contract(code=orchestrator_code, balance=3)
    created = compute_create_address(
        address=orchestrator,
        nonce=1,
        salt=0,
        initcode=bytes(inner_code),
        opcode=create_opcode,
    )

    state_gas = orchestrator_code.state_cost(fork)
    # The codeless target returns the forwarded value-call stipend
    # unused, so it is charged but never consumed.
    execution_gas = (
        fork.transaction_intrinsic_cost_calculator()()
        + orchestrator_code.execution_cost(fork)
        + inner_code.execution_cost(fork)
        - fork.call_value_stipend()
    )
    expected_gas_used = max(execution_gas, state_gas)
    assert expected_gas_used == state_gas, (
        "expected state gas to dominate execution gas"
    )

    tx = Transaction(
        to=orchestrator,
        state_gas_reservoir=state_gas,
        sender=pre.fund_eoa(),
    )

    # End of transaction destruction clears the nonce, code and storage
    # but leaves every wei the account received in place.
    swept = 0 if selfdestruct_beneficiary == "self" else 1
    post: dict = {
        orchestrator: Account(balance=1),
        created: Account(balance=2 - swept, nonce=0, code=b"", storage={}),
    }
    if selfdestruct_beneficiary != "self":
        post[alive_beneficiary] = Account(balance=1 + swept)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(txs=[tx], header_verify=Header(gas_used=expected_gas_used))
        ],
        post=post,
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

    # The reservoir already pins the gas limit, and is sized for the
    # CREATE's single account creation. Pinning the header is what
    # proves the zero-value CALL added no second charge.
    state_gas = orchestrator_code.state_cost(fork)
    execution_gas = (
        fork.transaction_intrinsic_cost_calculator()()
        + orchestrator_code.execution_cost(fork)
        + inner_code.execution_cost(fork)
    )
    expected_gas_used = max(execution_gas, state_gas)
    assert expected_gas_used == state_gas, (
        "expected state gas to dominate execution gas"
    )

    tx = Transaction(
        to=orchestrator,
        state_gas_reservoir=state_gas,
        sender=pre.fund_eoa(),
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(txs=[tx], header_verify=Header(gas_used=expected_gas_used))
        ],
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

    probe_storage = Storage()
    probe_code = Bytecode()
    for _ in range(num_probes):
        probe_code += Op.SSTORE(probe_storage.store_next(1), 1)

    probe = pre.deploy_contract(code=probe_code)
    probe_gas = probe_code.execution_cost(fork)

    orchestrator = pre.deploy_contract(
        code=(
            Op.POP(Op.CALL(gas=Op.GAS, address=target))
            + Op.POP(Op.CALL(gas=Op.GAS, address=target, value=1))
            + Op.POP(Op.CALL(gas=probe_gas, address=probe))
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
        post={probe: Account(storage=probe_storage)},
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
        code=(
            Op.POP(
                Op.CALL(
                    gas=child_code.execution_cost(fork) - reservoir_delta,
                    address=child,
                )
            )
            + Op.INVALID
        ),
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
    contract_code = Op.POP(
        Op.CALLCODE(
            gas=Op.GAS,
            address=target,
            value=1,
            value_transfer=True,
        )
    ) + Op.SSTORE(storage.store_next(1, "reservoir_ok"), 1)
    contract = pre.deploy_contract(code=contract_code, balance=10**18)

    state_gas = contract_code.state_cost(fork)
    # The codeless callee returns the forwarded value-call stipend
    # unused, so it is charged but never consumed.
    execution_gas = (
        fork.transaction_intrinsic_cost_calculator()()
        + contract_code.execution_cost(fork)
        - fork.call_value_stipend()
    )
    expected_gas_used = max(execution_gas, state_gas)
    assert expected_gas_used == state_gas == sstore_state_gas, (
        "expected only the SSTORE's state gas, dominating execution gas"
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
    state_test(
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=expected_gas_used),
    )


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

    inner_code = Op.MSTORE(0, init_code_at_high_bytes(init_code)[0]) + Op.POP(
        inner_create_call
    )
    inner = pre.deploy_contract(code=inner_code)

    grandchild_storage = Storage()
    grandchild_code = Op.SSTORE(grandchild_storage.store_next(1, "ran"), 1)
    grandchild = pre.deploy_contract(code=grandchild_code)

    grandchild_stipend = grandchild_code.execution_cost(fork)

    parent = pre.deploy_contract(
        code=(
            Op.POP(Op.CALL(gas=inner_code.execution_cost(fork), address=inner))
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

    # Exactly the intrinsic cost plus both gas dimensions the code
    # needs, so any extra execution draw OOGs.
    tx = Transaction(
        to=caller,
        gas_limit=(
            fork.transaction_intrinsic_cost_calculator()()
            + caller_code.gas_cost(fork)
        ),
        sender=pre.fund_eoa(),
    )

    state_test(pre=pre, post={target: Account(balance=1)}, tx=tx)


@pytest.mark.parametrize(
    "gas_delta",
    [pytest.param(0, id="exact_fit"), pytest.param(-1, id="one_short")],
)
@EIPChecklist.GasCostChanges.Test.OutOfGas()
@pytest.mark.valid_from("EIP8037")
def test_call_new_account_state_gas_boundary(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_delta: int,
) -> None:
    """
    Pin the CALL new-account state charge at its exact-fit boundary.

    With `gas_limit` set explicitly the transaction has no reservoir, so
    the charge spills from `gas_left`. At `exact_fit` the target is
    materialized; one gas short the caller frame goes out of gas and the
    value transfer is rolled back.
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

    state_gas = caller_code.state_cost(fork)
    execution_gas = (
        fork.transaction_intrinsic_cost_calculator()()
        + caller_code.execution_cost(fork)
    )
    exact_fit = execution_gas + state_gas

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
        pytest.param(
            Op.DELEGATECALL,
            "call_value_new_account",
            id="delegatecall_call_value_new_account_charge",
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

    delegated = call_opcode == Op.DELEGATECALL
    child = pre.deploy_contract(
        code=child_code, balance=0 if delegated else child_balance
    )
    probe = pre.deploy_contract(probe_code)
    probe_stipend = probe_code.execution_cost(fork)

    parent = pre.deploy_contract(
        code=(
            Op.POP(call_opcode(gas=Op.GAS, address=child))
            + Op.POP(call_opcode(gas=probe_stipend, address=probe))
        ),
        balance=child_balance if delegated else 0,
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
    if delegated:
        post: dict = {parent: Account(storage=probe_storage)}
    else:
        post = {probe: Account(storage=probe_storage)}

    state_test(
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=sstore_state_gas),
    )


@pytest.mark.parametrize("depth", ["top", "child"])
@pytest.mark.parametrize(
    "funding",
    [
        pytest.param("reservoir", id="reservoir"),
        pytest.param("mixed", id="mixed"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_call_insufficient_balance_refunds_new_account_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    funding: str,
    depth: str,
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
    assert new_account_state_gas > sstore_state_gas
    if funding == "mixed":
        reservoir = sstore_state_gas
    else:
        reservoir = new_account_state_gas

    if depth == "child":
        target = pre.deploy_contract(
            code=Op.POP(Op.CALL(gas=Op.GAS, address=parent))
        )
    else:
        target = parent

    tx = Transaction(
        to=target,
        state_gas_reservoir=reservoir,
        sender=pre.fund_eoa(),
    )

    post = {probe: Account(storage=probe_storage)}
    state_test(
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=sstore_state_gas),
    )


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


@pytest.mark.parametrize("reservoir", ["in_cap", "over_cap", "full"])
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
    if reservoir == "full":
        gas_limit = gas_limit_cap + caller_code.state_cost(fork)
    elif reservoir == "over_cap":
        gas_limit = gas_limit_cap + caller_code.state_cost(fork) // 2
    else:
        gas_limit = 1_000_000

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
