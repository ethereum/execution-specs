"""
Tests for the EIP-8038 [State Access Gas Cost Increase](https://eips.ethereum.org/EIPS/eip-8038)
``CALL``-family execution-gas dimension.

Under EIP-8038 the call opcodes are repriced in their *execution* gas
dimension:

- account access costs ``COLD_ACCOUNT_ACCESS`` cold or
  ``WARM_ACCESS`` warm;
- a positive value transfer adds ``CALL_VALUE`` (``ACCOUNT_WRITE`` +
  ``CALL_STIPEND``), charged only by ``CALL``/``CALLCODE``;
- a value transfer to a *new* account additionally creates the account,
  whose ``GAS_NEW_ACCOUNT`` charge is the EIP-8037 *state* dimension and
  is asserted via the block header ``max(execution, state)`` accounting,
  never as execution gas;
- an EIP-7702 delegated target is double-accessed (target leaf plus
  delegation leaf), each access cold or warm independently.

These tests assert the EIP-8038 *execution* dimension; the EIP-8037
*state* dimension for value-to-new-account is covered in
``eip8037_state_creation_gas_cost_increase/test_state_gas_call.py`` and
is only re-derived here at the seam to feed header gas accounting.
"""

import pytest
from execution_testing import (
    AccessList,
    Account,
    Address,
    Alloc,
    Bytecode,
    CodeGasMeasure,
    Environment,
    Fork,
    Header,
    Op,
    StateTestFiller,
    Transaction,
    TransactionReceipt,
)
from execution_testing.checklists import EIPChecklist

from .spec import ref_spec_8038

REFERENCE_SPEC_GIT_PATH = ref_spec_8038.git_path
REFERENCE_SPEC_VERSION = ref_spec_8038.version

pytestmark = pytest.mark.valid_from("Amsterdam")


def _measure_call(
    pre: Alloc,
    fork: Fork,
    measured_code: Bytecode,
    own_cold_cost: Bytecode,
    balance: int = 0,
) -> Address:
    """
    Deploy a ``CodeGasMeasure`` contract around ``measured_code``.

    The overhead subtracts the call opcode's OWN cold cost (computed from
    ``own_cold_cost``) so only the wrapping ``PUSH`` arguments remain in
    the overhead; the measured value isolates the opcode's gas. The call
    leaves exactly one stack item (its success flag).
    """
    overhead_cost = measured_code.gas_cost(fork) - own_cold_cost.gas_cost(fork)
    code_gas_measure = CodeGasMeasure(
        code=measured_code,
        overhead_cost=overhead_cost,
        extra_stack_items=1,
    )
    return pre.deploy_contract(code=code_gas_measure, balance=balance)


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.with_all_call_opcodes()
@pytest.mark.parametrize("warm", [False, True], ids=["cold", "warm"])
def test_call_access_gas(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    fork: Fork,
    call_opcode: Op,
    warm: bool,
) -> None:
    """
    Measure the access cost of every call opcode with no value transfer.

    EIP-8038 charges ``COLD_ACCOUNT_ACCESS`` cold and ``WARM_ACCESS``
    warm for all four call opcodes.
    """
    target = pre.deploy_contract(Op.STOP)

    measured_code = call_opcode(gas=0, address=target)
    cost_metadata = call_opcode(address_warm=warm)
    measure_address = _measure_call(
        pre, fork, measured_code, call_opcode(address_warm=False)
    )

    # The opcode's own cost is the expected access gas.
    expected_gas = cost_metadata.gas_cost(fork)

    access_list = (
        [AccessList(address=target, storage_keys=[])] if warm else None
    )
    tx = Transaction(
        to=measure_address,
        sender=pre.fund_eoa(),
        access_list=access_list,
    )

    post = {measure_address: Account(storage={0: expected_gas})}
    state_test(env=env, pre=pre, post=post, tx=tx)


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.with_all_call_opcodes()
@pytest.mark.parametrize("warm", [False, True], ids=["cold", "warm"])
def test_call_value_alive_target_gas(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    fork: Fork,
    call_opcode: Op,
    warm: bool,
) -> None:
    """
    Measure call cost with value transfer to an already-alive target.

    ``CALL``/``CALLCODE`` add ``CALL_VALUE`` on top of the
    access cost, where ``CALL_VALUE = ACCOUNT_WRITE + CALL_STIPEND``.
    ``DELEGATECALL``/``STATICCALL`` never transfer value, so they pay
    only the access cost regardless of any value argument. No new
    account is created (the target is alive), so no state gas is charged.

    The ``CALL_STIPEND`` is forwarded to the callee; with a
    ``STOP`` callee it is unused and returned, so the gas *consumed* by
    the caller is ``access + ACCOUNT_WRITE`` while the *charged* schedule
    is ``access + CALL_VALUE``. Both are asserted.
    """
    transfers_value = call_opcode in (Op.CALL, Op.CALLCODE)

    # The measured-vs-charged duality below hinges on the callee being a
    # pure `STOP`: it executes no opcodes, so the forwarded value-call
    # stipend is wholly unused and returned.
    callee = Op.STOP
    assert bytes(callee) == b"\x00"
    assert callee.gas_cost(fork) == 0

    # Alive target with balance so no account creation occurs.
    target = pre.deploy_contract(callee, balance=1)

    # Build the runnable call carrying the runtime metadata so that
    # `measured_code.gas_cost(fork)` accounts for the value transfer.
    if transfers_value:
        measured_code = call_opcode.with_metadata(
            address_warm=False, value_transfer=True
        )(
            gas=0,
            address=target,
            value=1,
            args_offset=0,
            args_size=0,
            ret_offset=0,
            ret_size=0,
        )
        cost_metadata = call_opcode(address_warm=warm, value_transfer=True)
        own_cold = call_opcode(address_warm=False, value_transfer=True)
    else:
        measured_code = call_opcode(gas=0, address=target)
        cost_metadata = call_opcode(address_warm=warm)
        own_cold = call_opcode(address_warm=False)

    # The measure contract needs balance to actually send the value.
    measure_address = _measure_call(
        pre, fork, measured_code, own_cold, balance=1
    )

    # CALL gas is wholly execution under EIP-8038 (no state map).
    assert cost_metadata.state_cost(fork) == 0

    # Consumed gas: the STOP callee returns the forwarded stipend, so the
    # caller's measured consumption is the opcode's charged cost minus the
    # stipend for value transfers, and just the access cost otherwise.
    measured_gas = cost_metadata.gas_cost(fork) - (
        fork.call_value_stipend() if transfers_value else 0
    )

    access_list = (
        [AccessList(address=target, storage_keys=[])] if warm else None
    )
    tx = Transaction(
        to=measure_address,
        sender=pre.fund_eoa(),
        access_list=access_list,
    )

    post = {measure_address: Account(storage={0: measured_gas})}
    state_test(env=env, pre=pre, post=post, tx=tx)


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
def test_callcode_value_to_nonexistent_no_new_account(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify CALLCODE value to a non-existent target charges CALL_VALUE
    but not GAS_NEW_ACCOUNT.

    ``CALLCODE`` runs the callee's code in the caller's own context, so
    the value never leaves the caller and no beneficiary account is
    created. The block ``gas_used`` therefore equals the execution tx
    cost with ``CALL_VALUE`` but with no ``GAS_NEW_ACCOUNT`` state-gas
    component.
    """
    intrinsic = fork.transaction_intrinsic_cost_calculator()()

    target = 0xDEAD  # non-existent

    # CALLCODE with value to a cold, non-existent target. The metadata
    # carries `value_transfer` so `caller_code.gas_cost(fork)` reflects
    # the CALL_VALUE charge; it must NOT carry `account_new` since the
    # value stays with the caller and no beneficiary leaf is created.
    callcode = Op.CALLCODE.with_metadata(
        address_warm=False, value_transfer=True
    )(
        gas=0,
        address=target,
        value=1,
        args_offset=0,
        args_size=0,
        ret_offset=0,
        ret_size=0,
    )
    caller_code = Op.POP(callcode) + Op.STOP
    caller = pre.deploy_contract(code=caller_code, balance=1)

    # CALLCODE carries no state-gas (NEW_ACCOUNT) component: the value
    # stays in the caller's own context, so no beneficiary is created.
    callcode_meta = Op.CALLCODE(address_warm=False, value_transfer=True)
    assert callcode_meta.state_cost(fork) == 0

    # Whole tx is execution gas; no NEW_ACCOUNT state component appears.
    # The CALLCODE forwards the value-call stipend to the callee, which
    # (running in the caller's own context with empty code) leaves it
    # unused and returns it, so consumed gas is the charge minus stipend.
    expected_gas_used = (
        intrinsic + caller_code.gas_cost(fork) - fork.call_value_stipend()
    )

    tx = Transaction(
        to=caller,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=expected_gas_used
        ),
    )

    state_test(pre=pre, post={caller: Account(balance=1)}, tx=tx)


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
def test_call_value_to_new_account_seam(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify the CALL value-to-new-account execution/state seam.

    The EIP-8038 *execution* dimension is ``COLD_ACCOUNT_ACCESS`` +
    ``CALL_VALUE``; the account creation charge ``GAS_NEW_ACCOUNT``
    lands in the EIP-8037 *state* dimension. The block header reflects
    ``max(execution, state)``, which is dominated by the state charge.
    """
    intrinsic = fork.transaction_intrinsic_cost_calculator()()

    # Fresh, value-receiving target (state-empty, will be created).
    target = pre.fund_eoa(amount=0)

    # Metadata-bearing CALL so its cost splits into the execution
    # (access + value transfer) and state (NEW_ACCOUNT) dimensions.
    call = Op.CALL.with_metadata(
        address_warm=False, value_transfer=True, account_new=True
    )(
        gas=0,
        address=target,
        value=1,
        args_offset=0,
        args_size=0,
        ret_offset=0,
        ret_size=0,
    )
    caller_code = Op.POP(call) + Op.STOP
    caller = pre.deploy_contract(code=caller_code, balance=1)

    new_account_state_gas = call.state_cost(fork)

    # block_gas_used = max(block_execution, block_state). The CALL's
    # NEW_ACCOUNT lands on the state axis; the execution axis is the
    # access plus value-transfer cost.
    tx_execution = intrinsic + caller_code.execution_cost(fork)
    tx_state = caller_code.state_cost(fork)
    expected_gas_used = max(tx_execution, tx_state)
    # State must dominate here, proving NEW_ACCOUNT hit the state axis.
    assert expected_gas_used == new_account_state_gas

    tx = Transaction(
        to=caller,
        sender=pre.fund_eoa(),
        state_gas_reservoir=new_account_state_gas,
    )

    state_test(
        pre=pre,
        post={target: Account(balance=1)},
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=expected_gas_used),
    )


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.with_all_call_opcodes()
@pytest.mark.parametrize(
    "target_warm", [False, True], ids=["target_cold", "target_warm"]
)
@pytest.mark.parametrize(
    "delegate_warm", [False, True], ids=["delegate_cold", "delegate_warm"]
)
def test_call_to_delegated_target_double_access(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    fork: Fork,
    call_opcode: Op,
    target_warm: bool,
    delegate_warm: bool,
) -> None:
    """
    Measure a call to a 7702-delegated target: 2x2 double access.

    The spec applies the delegation surcharge to every call opcode
    (``CALL``/``CALLCODE``/``DELEGATECALL``/``STATICCALL``), so each
    reads two account leaves: the target's leaf and the delegation's
    leaf. Each is charged independently as ``WARM_ACCESS`` or
    ``COLD_ACCOUNT_ACCESS`` by warmth. ``DELEGATECALL`` and
    ``STATICCALL`` carry no value but still pay the delegation
    surcharge.
    """
    # Final code-bearing account that the delegation points at.
    delegate = pre.deploy_contract(Op.STOP)
    # EOA delegated (EIP-7702) to `delegate`.
    target = pre.fund_eoa(amount=0, delegation=delegate)

    measured_code = call_opcode(gas=0, address=target)
    cost_metadata = call_opcode(
        address_warm=target_warm,
        delegated_address=True,
        delegated_address_warm=delegate_warm,
    )
    measure_address = _measure_call(
        pre, fork, measured_code, call_opcode(address_warm=False)
    )

    # The opcode's own cost folds the target and delegate accesses.
    expected_gas = cost_metadata.gas_cost(fork)

    # Warm the target and/or the delegate leaf via the access list.
    access_entries = []
    if target_warm:
        access_entries.append(AccessList(address=target, storage_keys=[]))
    if delegate_warm:
        access_entries.append(AccessList(address=delegate, storage_keys=[]))
    access_list = access_entries or None

    tx = Transaction(
        to=measure_address,
        sender=pre.fund_eoa(),
        access_list=access_list,
    )

    post = {measure_address: Account(storage={0: expected_gas})}
    state_test(env=env, pre=pre, post=post, tx=tx)


@EIPChecklist.GasCostChanges.Test.OutOfGas()
@pytest.mark.with_all_call_opcodes()
@pytest.mark.parametrize(
    "sufficient_gas", [True, False], ids=["sufficient", "insufficient"]
)
def test_call_exact_gas_oog(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    fork: Fork,
    call_opcode: Op,
    sufficient_gas: bool,
) -> None:
    """
    Drive a cold call at exactly its gas (success) and one gas short (OOG).

    The caller forwards exactly enough gas for the inner call opcode (its
    cold access cost plus the wrapping pushes). One gas short forces the
    inner call to halt out-of-gas before executing, so the outer SSTORE
    records 0; with the exact amount it records 1.
    """
    target = pre.deploy_contract(Op.STOP)

    # Inner contract just performs the cold call to `target`.
    inner_code = call_opcode(gas=0, address=target) + Op.STOP
    inner = pre.deploy_contract(inner_code)

    # Exact execution gas for the inner frame: bytecode cost (which folds
    # the cold call cost via the default metadata) under EIP-8038.
    inner_gas_exact = inner_code.gas_cost(fork)
    if not sufficient_gas:
        inner_gas_exact -= 1

    caller_code = Op.SSTORE(0, Op.CALL(gas=inner_gas_exact, address=inner))
    caller = pre.deploy_contract(caller_code)

    tx = Transaction(to=caller, sender=pre.fund_eoa())

    post = {caller: Account(storage={0: 1 if sufficient_gas else 0})}
    state_test(env=env, pre=pre, post=post, tx=tx)


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.with_all_call_opcodes()
def test_call_self_is_warm(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    fork: Fork,
    call_opcode: Op,
) -> None:
    """
    Verify a self-call is warm: the executing account is pre-warmed.

    The current target is in the accessed-addresses set on message
    entry, so a call to ``ADDRESS`` pays only ``WARM_ACCESS``.
    """
    # `Op.ADDRESS` is the call's address argument, embedded inside the
    # runnable call; the self address is in the accessed set on entry, so
    # the call is warm. The overhead subtracts the call's own cold cost,
    # leaving the ADDRESS push and the other arg pushes as overhead.
    measured_code = call_opcode(gas=0, address=Op.ADDRESS)
    measure_address = _measure_call(
        pre, fork, measured_code, call_opcode(address_warm=False)
    )

    expected_gas = call_opcode(address_warm=True).gas_cost(fork)

    tx = Transaction(to=measure_address, sender=pre.fund_eoa())

    post = {measure_address: Account(storage={0: expected_gas})}
    state_test(env=env, pre=pre, post=post, tx=tx)


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.parametrize(
    "sufficient_gas", [True, False], ids=["sufficient", "insufficient"]
)
def test_call_forwarded_gas_63_64(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    sufficient_gas: bool,
) -> None:
    """
    Verify the 63/64 forwarding budget is computed after the repriced
    cold access charge.

    A wrapper performs a cold, zero-value ``CALL`` requesting maximum
    gas. The spec charges the repriced ``COLD_ACCOUNT_ACCESS``
    up front and only then forwards ``floor(63/64 * gas_left)`` to the
    child. The wrapper is handed an exact budget so that, net of the
    access charge, ``gas_left`` equals ``child_execution * 64 // 63``;
    forwarding then yields exactly the child's execution need
    (``child_execution``) and its cold ``SSTORE`` takes effect. With one
    gas less the floor drops below ``child_execution`` and the child OOGs,
    so the slot stays zero. This pins that the floor is taken over
    ``gas_left`` already net of the post-8038 cold access cost (not
    before it, and not double-charging it).
    """
    sstore_state_gas = Op.SSTORE(new_value=1).state_cost(fork)

    # Child: a single cold zero-to-nonzero SSTORE as proof of execution.
    # Its execution need is the two operand pushes plus the cold storage
    # write (the state portion is funded separately via the reservoir,
    # which is passed to the child in full with no 63/64 rule).
    child_code = Op.SSTORE(0, 1)
    child = pre.deploy_contract(child_code)
    child_execution = child_code.execution_cost(fork)

    # Smallest budget whose 63/64 floor still reaches `child_execution`.
    forward_budget = child_execution * 64 // 63
    if not sufficient_gas:
        forward_budget -= 1

    # Wrapper: cold zero-value CALL requesting max gas (so the forwarded
    # amount is bound by `gas_left`, not by the request). ret_size=0
    # avoids any memory-expansion term.
    wrapper_call = Op.CALL(
        gas=0xFFFFFFFF,
        address=child,
        value=0,
        args_offset=0,
        args_size=0,
        ret_offset=0,
        ret_size=0,
    )
    wrapper = pre.deploy_contract(wrapper_call)

    # At the wrapper's CALL the cold access charge is deducted first
    # (folded with the operand pushes into its execution cost), leaving
    # exactly `forward_budget` as `gas_left` for the 63/64 floor.
    wrapper_gas = wrapper_call.execution_cost(fork) + forward_budget

    # Outer caller hands the wrapper exactly `wrapper_gas`.
    caller = pre.deploy_contract(
        Op.POP(Op.CALL(gas=wrapper_gas, address=wrapper))
    )

    tx = Transaction(
        to=caller,
        sender=pre.fund_eoa(),
        state_gas_reservoir=sstore_state_gas,
    )

    # Child SSTORE lands only when the forwarded floor reaches its need.
    post = {child: Account(storage={0: 1 if sufficient_gas else 0})}
    state_test(pre=pre, post=post, tx=tx)


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
def test_account_warmth_reverts_on_subcall_revert(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Account warmth acquired inside a reverted sub-call does not persist.

    An inner contract reads an address's ``BALANCE`` via
    ``DELEGATECALL`` (so the warmed address belongs to the shared
    accessed-addresses set) then ``REVERT``s. Back in the outer frame,
    that same address's first ``BALANCE`` is cold again and is charged
    ``COLD_ACCOUNT_ACCESS``, proving the warm-address set is
    rolled back on revert (mirrors the ``SLOAD`` warmth-revert case for
    the account dimension).
    """
    cold_gas = Op.BALANCE(address_warm=False).gas_cost(fork)

    # Address whose warmth we probe; left out of the access list so its
    # first runtime touch is cold.
    probed = pre.fund_eoa(amount=1)

    # Inner: warm `probed` by reading its balance, then revert.
    inner = pre.deploy_contract(
        code=Op.POP(Op.BALANCE(probed)) + Op.REVERT(0, 0),
    )

    # Outer: DELEGATECALL inner (which warms `probed` in the shared
    # accessed set, then reverts, discarding that warmth), then measure
    # its own first BALANCE of `probed`, which must be cold again.
    measured_code = Op.BALANCE(probed)
    overhead_cost = measured_code.gas_cost(fork) - Op.BALANCE(
        address_warm=False
    ).gas_cost(fork)
    outer_code: Bytecode = Op.POP(
        Op.DELEGATECALL(gas=100_000, address=inner)
    ) + CodeGasMeasure(
        code=measured_code,
        overhead_cost=overhead_cost,
        extra_stack_items=1,
    )
    outer = pre.deploy_contract(code=outer_code)

    tx = Transaction(to=outer, sender=pre.fund_eoa())

    # Slot 0 holds the measured (cold) BALANCE read.
    post = {outer: Account(storage={0: cold_gas})}
    state_test(env=env, pre=pre, post=post, tx=tx)


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
def test_call_to_double_delegated_target_single_hop(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify delegation resolution is single-hop: A -> B -> C charges two.

    ``target`` (A) is an EOA delegated to ``mid`` (B), which is itself
    an EOA delegated to ``final`` (C), a code-bearing account. A cold
    ``CALL`` to ``target`` reads exactly two account leaves -- the
    target's and its delegation's -- and is charged
    ``2 * COLD_ACCOUNT_ACCESS``. The chain is not followed a
    second hop, so ``final``'s leaf is not charged. Both the framework
    opcode model and a runtime ``CodeGasMeasure`` confirm the value.
    """
    # A -> B -> C delegation chain. `mid` is an EOA whose code is the
    # 7702 delegation designator pointing at `final`; `target` delegates
    # to `mid` in turn.
    final = pre.deploy_contract(Op.STOP)
    mid = pre.fund_eoa(amount=0, delegation=final)
    target = pre.fund_eoa(amount=0, delegation=mid)

    # Framework model: cold target leaf + cold delegation leaf, no third
    # access for the second hop.
    cost_metadata = Op.CALL(
        address_warm=False,
        delegated_address=True,
        delegated_address_warm=False,
    )
    # Cold target leaf plus cold delegation leaf; no state gas.
    expected_gas = cost_metadata.gas_cost(fork)
    assert cost_metadata.state_cost(fork) == 0

    measured_code = Op.CALL(gas=0, address=target)
    measure_address = _measure_call(
        pre, fork, measured_code, Op.CALL(address_warm=False)
    )

    tx = Transaction(to=measure_address, sender=pre.fund_eoa())

    post = {measure_address: Account(storage={0: expected_gas})}
    state_test(env=env, pre=pre, post=post, tx=tx)


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.with_all_call_opcodes()
def test_call_precompile_is_warm(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    fork: Fork,
    call_opcode: Op,
) -> None:
    """
    Verify a call to a precompile is warm from the start.

    Precompiles are part of the accessed-addresses set from the start of
    every transaction, so a call to one pays only ``WARM_ACCESS``.
    The identity precompile (address 4) is used as the target.
    """
    identity_precompile = Address(4)

    measured_code = call_opcode(gas=0, address=identity_precompile)
    measure_address = _measure_call(
        pre, fork, measured_code, call_opcode(address_warm=False)
    )

    expected_gas = call_opcode(address_warm=True).gas_cost(fork)

    tx = Transaction(to=measure_address, sender=pre.fund_eoa())

    post = {measure_address: Account(storage={0: expected_gas})}
    state_test(env=env, pre=pre, post=post, tx=tx)


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.parametrize(
    "value", [0, 1], ids=["no_value_no_stipend", "value_grants_stipend"]
)
def test_call_value_stipend_is_usable(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    value: int,
) -> None:
    """
    The ``CALL`` value-transfer stipend ``CALL_STIPEND`` is
    forwarded to the callee and usable for execution.

    The caller forwards ``gas=0``, so the callee receives only the stipend
    when a positive value is sent, and nothing otherwise. The
    callee runs a small amount of work (well under the stipend) then
    stops:
    with the stipend the call succeeds (returns 1); without value (no
    stipend, zero forwarded gas) the work runs out of gas and the call
    fails (returns 0). This proves the stipend is not merely returned but
    is spendable by the callee.
    """
    # ~250 gas of cheap work: comfortably within the stipend, far
    # above the zero gas forwarded when no value (so no stipend) is sent.
    work = (Op.PUSH1(0) + Op.POP) * 50 + Op.STOP
    callee = pre.deploy_contract(code=work)

    caller = pre.deploy_contract(
        code=Op.SSTORE(0, Op.CALL(0, callee, value, 0, 0, 0, 0)),
        balance=1,
    )

    tx = Transaction(to=caller, sender=pre.fund_eoa())

    # 1 when the stipend funded the callee's work, 0 when it ran out.
    post = {caller: Account(storage={0: 1 if value else 0})}
    state_test(env=env, pre=pre, post=post, tx=tx)
