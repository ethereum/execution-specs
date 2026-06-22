"""
Tests for the EIP-8038 [State Access Gas Cost Increase](https://eips.ethereum.org/EIPS/eip-8038)
``CALL``-family regular-gas dimension.

Under EIP-8038 the call opcodes are repriced in their *regular* gas
dimension:

- account access costs ``COLD_ACCOUNT_ACCESS`` (3,000) cold or
  ``WARM_ACCESS`` (100) warm;
- a positive value transfer adds ``CALL_VALUE`` (``ACCOUNT_WRITE`` +
  ``CALL_STIPEND`` = 10,300), charged only by ``CALL``/``CALLCODE``;
- a value transfer to a *new* account additionally creates the account,
  whose ``GAS_NEW_ACCOUNT`` charge is the EIP-8037 *state* dimension and
  is asserted via the block header ``max(regular, state)`` accounting,
  never as regular gas;
- an EIP-7702 delegated target is double-accessed (target leaf plus
  delegation leaf), each access cold or warm independently.

These tests assert the EIP-8038 *regular* dimension; the EIP-8037
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
    Block,
    BlockchainTestFiller,
    Bytecode,
    CodeGasMeasure,
    Environment,
    Fork,
    Header,
    Op,
    StateTestFiller,
    Transaction,
)
from execution_testing.checklists import EIPChecklist

from .spec import ref_spec_8038

REFERENCE_SPEC_GIT_PATH = ref_spec_8038.git_path
REFERENCE_SPEC_VERSION = ref_spec_8038.version

pytestmark = pytest.mark.valid_from("Amsterdam")


def _runnable_call(
    call_opcode: Op, address: int | Bytecode | Address, value: int = 0
) -> Bytecode:
    """
    Build a runnable call to ``address`` for the given opcode.

    ``CALL``/``CALLCODE`` take a ``value`` argument;
    ``DELEGATECALL``/``STATICCALL`` do not.
    """
    if call_opcode in (Op.CALL, Op.CALLCODE):
        return call_opcode(
            gas=0,
            address=address,
            value=value,
            args_offset=0,
            args_size=0,
            ret_offset=0,
            ret_size=0,
        )
    return call_opcode(
        gas=0,
        address=address,
        args_offset=0,
        args_size=0,
        ret_offset=0,
        ret_size=0,
    )


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

    EIP-8038 charges ``COLD_ACCOUNT_ACCESS`` (3,000) cold and
    ``WARM_ACCESS`` (100) warm for all four call opcodes.
    """
    gas_costs = fork.gas_costs()

    target = pre.deploy_contract(Op.STOP)

    measured_code = _runnable_call(call_opcode, target)
    cost_metadata = call_opcode(address_warm=warm)
    measure_address = _measure_call(
        pre, fork, measured_code, call_opcode(address_warm=False)
    )

    expected_gas = (
        gas_costs.WARM_ACCESS if warm else gas_costs.COLD_ACCOUNT_ACCESS
    )
    # Cross-check the framework opcode model agrees with the formula.
    assert expected_gas == cost_metadata.gas_cost(fork)

    access_list = (
        [AccessList(address=target, storage_keys=[])] if warm else None
    )
    tx = Transaction(
        to=measure_address,
        sender=pre.fund_eoa(),
        gas_limit=1_000_000,
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

    ``CALL``/``CALLCODE`` add ``CALL_VALUE`` (10,300) on top of the
    access cost, where ``CALL_VALUE = ACCOUNT_WRITE + CALL_STIPEND``.
    ``DELEGATECALL``/``STATICCALL`` never transfer value, so they pay
    only the access cost regardless of any value argument. No new
    account is created (the target is alive), so no state gas is charged.

    The ``CALL_STIPEND`` (2,300) is forwarded to the callee; with a
    ``STOP`` callee it is unused and returned, so the gas *consumed* by
    the caller is ``access + ACCOUNT_WRITE`` while the *charged* schedule
    is ``access + CALL_VALUE``. Both are asserted.
    """
    gas_costs = fork.gas_costs()
    transfers_value = call_opcode in (Op.CALL, Op.CALLCODE)
    # Verify the EIP-8038 decomposition of the value-transfer charge.
    assert gas_costs.CALL_VALUE == gas_costs.ACCOUNT_WRITE + (
        gas_costs.CALL_STIPEND
    )

    # Alive target with balance so no account creation occurs.
    target = pre.deploy_contract(Op.STOP, balance=1)

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
        measured_code = _runnable_call(call_opcode, target)
        cost_metadata = call_opcode(address_warm=warm)
        own_cold = call_opcode(address_warm=False)

    # The measure contract needs balance to actually send the value.
    measure_address = _measure_call(
        pre, fork, measured_code, own_cold, balance=1
    )

    access_cost = (
        gas_costs.WARM_ACCESS if warm else gas_costs.COLD_ACCOUNT_ACCESS
    )
    # Charged schedule: access + CALL_VALUE (verified via the opcode
    # model). CALL gas is wholly regular under EIP-8038 (no state map).
    charged_gas = access_cost + (
        gas_costs.CALL_VALUE if transfers_value else 0
    )
    assert charged_gas == cost_metadata.gas_cost(fork)
    assert cost_metadata.state_cost(fork) == 0

    # Consumed gas: the STOP callee returns the forwarded CALL_STIPEND,
    # so the caller's measured consumption is access + ACCOUNT_WRITE for
    # value transfers, and just access otherwise.
    measured_gas = access_cost + (
        gas_costs.ACCOUNT_WRITE if transfers_value else 0
    )

    access_list = (
        [AccessList(address=target, storage_keys=[])] if warm else None
    )
    tx = Transaction(
        to=measure_address,
        sender=pre.fund_eoa(),
        gas_limit=1_000_000,
        access_list=access_list,
    )

    post = {measure_address: Account(storage={0: measured_gas})}
    state_test(env=env, pre=pre, post=post, tx=tx)


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
def test_callcode_value_to_nonexistent_no_new_account(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify CALLCODE value to a non-existent target charges CALL_VALUE
    but not GAS_NEW_ACCOUNT.

    ``CALLCODE`` runs the callee's code in the caller's own context, so
    the value never leaves the caller and no beneficiary account is
    created. The block ``gas_used`` therefore equals the regular tx
    cost with ``CALL_VALUE`` but with no 183,600 state-gas component.
    """
    gas_costs = fork.gas_costs()
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

    # CALLCODE-to-nonexistent regular charge: access + CALL_VALUE, no
    # NEW_ACCOUNT (asserted via the metadata-only opcode model).
    callcode_meta = Op.CALLCODE(address_warm=False, value_transfer=True)
    assert callcode_meta.gas_cost(fork) == gas_costs.COLD_ACCOUNT_ACCESS + (
        gas_costs.CALL_VALUE
    )
    # CALLCODE carries no state-gas (NEW_ACCOUNT) component.
    assert callcode_meta.state_cost(fork) == 0

    # Whole tx is regular gas; no NEW_ACCOUNT state component appears.
    # The CALLCODE forwards CALL_STIPEND to the callee, which (running in
    # the caller's own context with empty code) leaves it unused and
    # returns it, so consumed gas is the charge minus the stipend.
    expected_gas_used = (
        intrinsic + caller_code.gas_cost(fork) - gas_costs.CALL_STIPEND
    )
    # Guard the no-state assertion: NEW_ACCOUNT would dominate if charged.
    assert expected_gas_used < gas_costs.NEW_ACCOUNT

    tx = Transaction(
        to=caller,
        sender=pre.fund_eoa(),
        gas_limit=1_000_000,
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(txs=[tx], header_verify=Header(gas_used=expected_gas_used))
        ],
        post={caller: Account(balance=1)},
    )


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
def test_call_value_to_new_account_seam(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify the CALL value-to-new-account regular/state seam.

    The EIP-8038 *regular* dimension is ``COLD_ACCOUNT_ACCESS`` +
    ``CALL_VALUE`` = 13,300; the account creation charge
    ``GAS_NEW_ACCOUNT`` (183,600) lands in the EIP-8037 *state*
    dimension. The block header reflects ``max(regular, state)``, which
    is dominated by the state charge.
    """
    gas_costs = fork.gas_costs()
    new_account_state_gas = gas_costs.NEW_ACCOUNT
    intrinsic = fork.transaction_intrinsic_cost_calculator()()

    # Fresh, value-receiving target (state-empty, will be created).
    target = pre.fund_eoa(amount=0)

    # Metadata-bearing CALL so `caller_code.gas_cost(fork)` folds the
    # value transfer and account-creation charges; we then split off the
    # NEW_ACCOUNT state component for the 2D header accounting.
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

    # Regular dimension: access + value (NOT new account, which is the
    # state dimension). Asserted via the metadata-only opcode model.
    call_meta = Op.CALL(
        address_warm=False, value_transfer=True, account_new=True
    )
    call_regular = call_meta.gas_cost(fork) - new_account_state_gas
    assert call_regular == gas_costs.COLD_ACCOUNT_ACCESS + gas_costs.CALL_VALUE
    assert call_regular == 13_300

    # block_gas_used = max(block_regular, block_state). The CALL opcode
    # has no state-gas map, so its NEW_ACCOUNT charge spills as regular
    # gas in the bytecode total; strip it back out to isolate the
    # regular axis and re-add NEW_ACCOUNT explicitly on the state axis.
    tx_regular = intrinsic + caller_code.gas_cost(fork) - new_account_state_gas
    tx_state = new_account_state_gas
    expected_gas_used = max(tx_regular, tx_state)
    # State must dominate here, proving the 183,600 hit the state axis.
    assert expected_gas_used == new_account_state_gas

    tx = Transaction(
        to=caller,
        sender=pre.fund_eoa(),
        state_gas_reservoir=new_account_state_gas,
        gas_limit=1_000_000,
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(txs=[tx], header_verify=Header(gas_used=expected_gas_used))
        ],
        post={target: Account(balance=1)},
    )


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
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
    target_warm: bool,
    delegate_warm: bool,
) -> None:
    """
    Measure CALL to a 7702-delegated target: 2x2 double access.

    A CALL to an EIP-7702 delegated account reads two account leaves:
    the target's leaf and the delegation's leaf. Each is charged
    independently as ``WARM_ACCESS`` (100) or ``COLD_ACCOUNT_ACCESS``
    (3,000) by warmth.
    """
    gas_costs = fork.gas_costs()

    # Final code-bearing account that the delegation points at.
    delegate = pre.deploy_contract(Op.STOP)
    # EOA delegated (EIP-7702) to `delegate`.
    target = pre.fund_eoa(amount=0, delegation=delegate)

    measured_code = _runnable_call(Op.CALL, target)
    cost_metadata = Op.CALL(
        address_warm=target_warm,
        delegated_address=not delegate_warm,
        delegated_address_warm=delegate_warm,
    )
    measure_address = _measure_call(
        pre, fork, measured_code, Op.CALL(address_warm=False)
    )

    target_cost = (
        gas_costs.WARM_ACCESS if target_warm else gas_costs.COLD_ACCOUNT_ACCESS
    )
    delegate_cost = (
        gas_costs.WARM_ACCESS
        if delegate_warm
        else gas_costs.COLD_ACCOUNT_ACCESS
    )
    expected_gas = target_cost + delegate_cost
    assert expected_gas == cost_metadata.gas_cost(fork)

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
        gas_limit=1_000_000,
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
    inner_code = Op.POP(_runnable_call(call_opcode, target)) + Op.STOP
    inner = pre.deploy_contract(inner_code)

    # Exact regular gas for the inner frame: bytecode cost (which folds
    # the cold call cost via the default metadata) under EIP-8038.
    inner_gas_exact = inner_code.gas_cost(fork)
    if not sufficient_gas:
        inner_gas_exact -= 1

    caller_code = Op.SSTORE(0, Op.CALL(gas=inner_gas_exact, address=inner))
    caller = pre.deploy_contract(caller_code)

    tx = Transaction(
        to=caller,
        sender=pre.fund_eoa(),
        gas_limit=1_000_000,
    )

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
    entry, so a call to ``ADDRESS`` pays only ``WARM_ACCESS`` (100).
    """
    gas_costs = fork.gas_costs()

    # `Op.ADDRESS` is the call's address argument, embedded inside the
    # runnable call; the self address is in the accessed set on entry, so
    # the call is warm. The overhead subtracts the call's own cold cost,
    # leaving the ADDRESS push and the other arg pushes as overhead.
    measured_code = _runnable_call(call_opcode, Op.ADDRESS)
    measure_address = _measure_call(
        pre, fork, measured_code, call_opcode(address_warm=False)
    )

    expected_gas = call_opcode(address_warm=True).gas_cost(fork)
    assert expected_gas == gas_costs.WARM_ACCESS

    tx = Transaction(
        to=measure_address,
        sender=pre.fund_eoa(),
        gas_limit=1_000_000,
    )

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
    every transaction, so a call to one pays only ``WARM_ACCESS`` (100).
    The identity precompile (address 4) is used as the target.
    """
    gas_costs = fork.gas_costs()

    identity_precompile = Address(4)

    measured_code = _runnable_call(call_opcode, identity_precompile)
    measure_address = _measure_call(
        pre, fork, measured_code, call_opcode(address_warm=False)
    )

    expected_gas = call_opcode(address_warm=True).gas_cost(fork)
    assert expected_gas == gas_costs.WARM_ACCESS

    tx = Transaction(
        to=measure_address,
        sender=pre.fund_eoa(),
        gas_limit=1_000_000,
    )

    post = {measure_address: Account(storage={0: expected_gas})}
    state_test(env=env, pre=pre, post=post, tx=tx)
