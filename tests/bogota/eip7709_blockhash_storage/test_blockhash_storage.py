"""
Tests for [EIP-7709: Read BLOCKHASH from storage and update cost](https://eips.ethereum.org/EIPS/eip-7709).
"""

import pytest
from execution_testing import (
    AccessList,
    Account,
    Alloc,
    AuthorizationTuple,
    BalAccountExpectation,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    Bytecode,
    CodeGasMeasure,
    EIPChecklist,
    Environment,
    Fork,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
    compute_create_address,
)

from ...prague.eip7702_set_code_tx.spec import Spec as Spec7702
from .spec import Spec, ref_spec_7709

REFERENCE_SPEC_GIT_PATH = ref_spec_7709.git_path
REFERENCE_SPEC_VERSION = ref_spec_7709.version

pytestmark = pytest.mark.valid_from("EIP7709")


def _measure_blockhash(
    arg: int,
    fork: Fork,
    *,
    sstore_key: int = 0,
) -> CodeGasMeasure:
    """
    Build a ``CodeGasMeasure`` around ``Op.BLOCKHASH(arg)`` whose stored
    result at ``sstore_key`` is the bare ``BLOCKHASH`` opcode cost (with
    the ``PUSH`` argument wrapper subtracted out).
    """
    measured = Op.BLOCKHASH(arg)
    overhead = measured.gas_cost(fork) - Op.BLOCKHASH(
        key_warm=False,
        in_bounds=True,
    ).gas_cost(fork)
    return CodeGasMeasure(
        code=measured,
        overhead_cost=overhead,
        extra_stack_items=1,
        sstore_key=sstore_key,
    )


@EIPChecklist.Opcode.Test.ExecutionContext.BlockContext()
@EIPChecklist.Opcode.Test.GasUsage.Normal()
@EIPChecklist.Opcode.Test.GasUsage.ExtraGas()
@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.pre_alloc_mutable
@pytest.mark.parametrize(
    "current_block,query_block,in_bounds",
    [
        pytest.param(2, 0, True, id="in_window_genesis_slot"),
        pytest.param(
            Spec.BLOCKHASH_SERVE_WINDOW,
            0,
            True,
            id="oldest_in_window_block",
        ),
        pytest.param(
            Spec.BLOCKHASH_SERVE_WINDOW + 1,
            0,
            False,
            id="one_past_serve_window",
        ),
        pytest.param(
            Spec.HISTORY_SERVE_WINDOW + 2,
            Spec.HISTORY_SERVE_WINDOW,
            True,
            id="ring_buffer_wrap_around_slot_zero",
        ),
        pytest.param(
            Spec.HISTORY_SERVE_WINDOW + 3,
            Spec.HISTORY_SERVE_WINDOW + 1,
            True,
            id="ring_buffer_wrap_around_slot_one",
        ),
    ],
)
def test_blockhash_reads_from_history_storage_state(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    current_block: int,
    query_block: int,
    in_bounds: bool,
) -> None:
    """
    Prove that ``BLOCKHASH(arg)`` reads directly from the EIP-2935
    ``HISTORY_STORAGE_ADDRESS`` state slot ``arg % HISTORY_SERVE_WINDOW``
    when ``arg`` is in ``[current_block - 256, current_block - 1]``.

    Seeding ``HISTORY_STORAGE_ADDRESS`` storage with a synthetic sentinel
    value at a non-parent slot (``query_block < current_block - 1``, so the
    EIP-2935 block-start system write to slot ``(current_block - 1) % 8191``
    does not overwrite it) proves the opcode resolves its result from
    contract storage rather than client header lookaside. When ``arg`` is
    one block older than the 256-block window, ``BLOCKHASH(arg)`` must
    return ``0`` and charge only the 20-gas constant even though the
    underlying ring-buffer slot in ``HISTORY_STORAGE_ADDRESS`` is populated.
    """
    ring_slot = query_block % Spec.HISTORY_SERVE_WINDOW
    sentinel_hash = 0xCAFEBABE_DEADBEEF_12345678_9ABCDEF0
    pre[Spec.HISTORY_STORAGE_ADDRESS] = Account(
        storage={ring_slot: sentinel_hash}
    )

    expected_gas = Op.BLOCKHASH(
        key_warm=False,
        in_bounds=in_bounds,
    ).gas_cost(fork)
    expected_value = sentinel_hash if in_bounds else 0

    storage = Storage()
    gas_slot = storage.store_next(expected_gas, "measured_blockhash_gas")
    val_slot = storage.store_next(expected_value, "blockhash_return_value")

    code = _measure_blockhash(
        query_block,
        fork,
        sstore_key=gas_slot,
    ) + Op.SSTORE(val_slot, Op.BLOCKHASH(query_block))

    # Pre-seed val_slot with a non-zero canary so an expected_value of 0 is
    # distinguishable from a skipped SSTORE.
    contract = pre.deploy_contract(code=code, storage={val_slot: 0xDEAD})
    tx = Transaction(sender=pre.fund_eoa(), to=contract)

    state_test(
        env=Environment(number=current_block),
        pre=pre,
        tx=tx,
        post={contract: Account(storage=storage)},
    )


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@EIPChecklist.Opcode.Test.GasUsage.Normal()
@EIPChecklist.Opcode.Test.GasUsage.ExtraGas()
@pytest.mark.parametrize(
    "warm_source",
    [
        pytest.param("cold", id="cold"),
        pytest.param("prior_blockhash", id="warm_by_prior_blockhash"),
        pytest.param("access_list", id="warm_by_access_list"),
    ],
)
def test_blockhash_gas_cold_and_warm_sources(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    warm_source: str,
) -> None:
    """
    Measure ``BLOCKHASH(0)`` at block 1 when slot 0 of
    ``HISTORY_STORAGE_ADDRESS`` is cold vs pre-warmed.

    1. A prior ``BLOCKHASH(0)`` in the same transaction, or
    2. An EIP-2930 transaction access list entry for
       ``(HISTORY_STORAGE_ADDRESS, 0)``.
    """
    is_warm = warm_source != "cold"
    expected_gas = Op.BLOCKHASH(
        key_warm=is_warm,
        in_bounds=True,
    ).gas_cost(fork)

    warmup_prefix = (
        Op.POP(Op.BLOCKHASH(0))
        if warm_source == "prior_blockhash"
        else Bytecode()
    )
    access_list = (
        [
            AccessList(
                address=Spec.HISTORY_STORAGE_ADDRESS,
                storage_keys=[0],
            )
        ]
        if warm_source == "access_list"
        else None
    )

    contract = pre.deploy_contract(
        code=warmup_prefix + _measure_blockhash(0, fork, sstore_key=0),
    )
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract,
        access_list=access_list,
    )

    state_test(
        env=Environment(number=1),
        pre=pre,
        tx=tx,
        post={contract: Account(storage={0: expected_gas})},
    )


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
def test_blockhash_cross_warming_with_history_contract(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify bidirectional slot-warming between ``BLOCKHASH`` and direct
    ``CALL``s to ``HISTORY_STORAGE_ADDRESS`` in Block 2.

    1. **Contract -> Opcode warming (slot 0):** Calling
       ``HISTORY_STORAGE_ADDRESS`` with input ``0`` executes ``SLOAD(0)``
       inside the system contract, warming ``(HISTORY_STORAGE_ADDRESS, 0)``
       so a subsequent ``BLOCKHASH(0)`` pays ``120`` gas (warm) instead of
       ``2120`` gas (cold) and returns the exact same hash.
    2. **Opcode -> Contract warming (slot 1):** Executing ``BLOCKHASH(1)``
       first pays ``2120`` gas (cold) and warms
       ``(HISTORY_STORAGE_ADDRESS, 1)``, so a subsequent ``CALL`` to
       ``HISTORY_STORAGE_ADDRESS`` with input ``1`` costs
       ``SLOAD(cold) - SLOAD(warm)`` (2000 gas) less than the cold ``CALL``
       for slot 0.
    """
    cold_blockhash_gas = Op.BLOCKHASH(
        key_warm=False,
        in_bounds=True,
    ).gas_cost(fork)
    warm_blockhash_gas = Op.BLOCKHASH(
        key_warm=True,
        in_bounds=True,
    ).gas_cost(fork)
    sload_delta = Op.SLOAD(key_warm=False).gas_cost(fork) - Op.SLOAD(
        key_warm=True
    ).gas_cost(fork)

    call_history = Op.CALL(
        gas=50_000,
        address=Spec.HISTORY_STORAGE_ADDRESS,
        args_offset=0,
        args_size=32,
        ret_offset=32,
        ret_size=32,
    )

    storage = Storage()
    call_delta_slot = storage.store_next(
        sload_delta,
        "history_call_cold_minus_warm_sload_delta",
    )
    hash_eq_1_slot = storage.store_next(1, "blockhash_1_matches_contract")
    warm_bh_gas_slot = storage.store_next(
        warm_blockhash_gas,
        "blockhash_0_gas_after_history_call",
    )
    cold_bh_gas_slot = storage.store_next(
        cold_blockhash_gas,
        "blockhash_1_cold_gas_before_history_call",
    )
    hash_eq_0_slot = storage.store_next(1, "blockhash_0_matches_contract")

    code = (
        # Pre-warm the HISTORY_STORAGE_ADDRESS account itself so both CALLs
        # pay warm account access and differ only in their internal SLOAD.
        Op.POP(Op.BALANCE(Spec.HISTORY_STORAGE_ADDRESS))
        + Op.MSTORE(0, 0)
        + Op.MSTORE(32, 0)
        + CodeGasMeasure(
            code=call_history,
            overhead_cost=0,
            extra_stack_items=1,
            sstore_key=call_delta_slot,
        )
        + Op.SSTORE(hash_eq_0_slot, Op.EQ(Op.MLOAD(32), Op.BLOCKHASH(0)))
        + _measure_blockhash(0, fork, sstore_key=warm_bh_gas_slot)
        # Now test the reverse direction on slot 1 (Block 1 hash):
        # measure cold BLOCKHASH(1) first, then measure CALL(input=1).
        + _measure_blockhash(1, fork, sstore_key=cold_bh_gas_slot)
        + Op.MSTORE(0, 1)
        + CodeGasMeasure(
            code=call_history,
            overhead_cost=0,
            extra_stack_items=1,
            sstore_key=hash_eq_1_slot,
        )
        + Op.SSTORE(
            call_delta_slot,
            Op.SUB(Op.SLOAD(call_delta_slot), Op.SLOAD(hash_eq_1_slot)),
        )
        + Op.SSTORE(hash_eq_1_slot, Op.EQ(Op.MLOAD(32), Op.BLOCKHASH(1)))
    )
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()

    blocks = [
        Block(txs=[]),
        Block(txs=[Transaction(sender=sender, to=contract)]),
    ]

    blockchain_test(
        pre=pre,
        blocks=blocks,
        post={contract: Account(storage=storage)},
    )


@EIPChecklist.Opcode.Test.OutOfBounds.Verify.Max()
@EIPChecklist.Opcode.Test.OutOfBounds.Verify.MaxPlusOne()
@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.parametrize(
    "query_block",
    [
        pytest.param(0, id="genesis_well_before_window"),
        pytest.param(43, id="one_before_serve_window_boundary"),
        pytest.param(300, id="current_block_number"),
        pytest.param(301, id="current_block_plus_one"),
        pytest.param(
            299 + Spec.HISTORY_SERVE_WINDOW,
            id="future_block_colliding_ring_buffer_slot",
        ),
        pytest.param(2**64 - 1, id="max_u64"),
        pytest.param(2**64, id="max_u64_plus_one"),
        pytest.param(2**256 - 1, id="max_u256"),
    ],
)
def test_blockhash_out_of_bounds_gas_and_no_slot_warming(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    query_block: int,
) -> None:
    """
    Test out-of-window ``BLOCKHASH(query_block)`` at ``env.number = 300``.

    1. Returns ``0``.
    2. Costs ``Op.BLOCKHASH(in_bounds=False).gas_cost(fork)`` (20 gas).
    3. Does **not** warm ``(HISTORY_STORAGE_ADDRESS, query_block % 8191)``
       even when ``query_block % 8191`` collides with an in-window block's
       ring-buffer slot (such as ``299 + 8191 == 8490``, whose modulo 8191
       is slot ``299``): a subsequent in-bounds ``BLOCKHASH(299)`` still
       pays the full cold cost (2120 gas).
    """
    current_block = 300
    in_bounds_parent = current_block - 1
    oob_gas = Op.BLOCKHASH(in_bounds=False).gas_cost(fork)
    cold_in_bounds_gas = Op.BLOCKHASH(
        key_warm=False,
        in_bounds=True,
    ).gas_cost(fork)

    storage = Storage()
    oob_val_slot = storage.store_next(0, "oob_return_value")
    oob_gas_slot = storage.store_next(oob_gas, "oob_gas_cost")
    parent_gas_slot = storage.store_next(
        cold_in_bounds_gas,
        "subsequent_in_bounds_parent_still_cold",
    )

    code = (
        Op.SSTORE(oob_val_slot, Op.BLOCKHASH(query_block))
        + _measure_blockhash(query_block, fork, sstore_key=oob_gas_slot)
        + _measure_blockhash(
            in_bounds_parent,
            fork,
            sstore_key=parent_gas_slot,
        )
    )
    contract = pre.deploy_contract(
        code=code,
        storage={oob_val_slot: 0xDEAD},
    )
    tx = Transaction(sender=pre.fund_eoa(), to=contract)

    state_test(
        env=Environment(number=current_block),
        pre=pre,
        tx=tx,
        post={contract: Account(storage=storage)},
    )


@EIPChecklist.GasCostChanges.Test.OutOfGas()
@EIPChecklist.Opcode.Test.GasUsage.OutOfGasExecution()
@EIPChecklist.Opcode.Test.GasUsage.OrderOfOperations.Exact()
@EIPChecklist.Opcode.Test.GasUsage.OrderOfOperations.Oog()
@EIPChecklist.Opcode.Test.ExceptionalAbort()
@pytest.mark.parametrize(
    "in_bounds,pre_warm",
    [
        pytest.param(True, False, id="in_bounds_cold_2120"),
        pytest.param(True, True, id="in_bounds_warm_120"),
        pytest.param(False, False, id="out_of_bounds_20"),
    ],
)
@pytest.mark.parametrize(
    "gas_delta,call_succeeds",
    [
        pytest.param(0, True, id="exact_gas_succeeds"),
        pytest.param(-1, False, id="minus_one_gas_oog"),
    ],
)
def test_blockhash_out_of_gas_boundaries(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    in_bounds: bool,
    pre_warm: bool,
    gas_delta: int,
    call_succeeds: bool,
) -> None:
    """
    Test exact two-sided gas boundaries (``exact`` vs ``exact - 1``) for
    ``BLOCKHASH`` across all three gas regimes.

    * In-bounds cold (``2120`` vs ``2119``),
    * In-bounds warm (``120`` vs ``119``), and
    * Out-of-bounds (``20`` vs ``19``).

    Additionally, after the sub-call returns in the in-bounds cold case,
    the caller measures ``BLOCKHASH(0)`` itself: when the sub-call succeeded
    (``2120`` gas), slot 0 is now warm (``120`` gas) in the caller; when the
    sub-call ran out of gas at ``2119`` gas (which exceeds the 20-gas base
    fee but falls 1 gas short of the 2100 cold storage access charge), any
    slot warming is rolled back and the caller still observes a cold read
    (``2120`` gas).
    """
    query_block = 0 if in_bounds else 1
    push_op = Op.PUSH1(query_block)
    blockhash_cost = Op.BLOCKHASH(
        key_warm=pre_warm,
        in_bounds=in_bounds,
    ).gas_cost(fork)
    subcall_budget = push_op.gas_cost(fork) + blockhash_cost + gas_delta

    callee = pre.deploy_contract(code=push_op + Op.BLOCKHASH + Op.STOP)

    expected_post_subcall_gas = Op.BLOCKHASH(
        key_warm=(pre_warm or (in_bounds and call_succeeds)),
        in_bounds=True,
    ).gas_cost(fork)

    storage = Storage()
    status_slot = storage.store_next(
        1 if call_succeeds else 0,
        "subcall_status",
    )
    outer_gas_slot = storage.store_next(
        expected_post_subcall_gas,
        "outer_blockhash_gas_after_subcall",
    )

    caller_code = Op.SSTORE(
        status_slot,
        Op.CALL(gas=subcall_budget, address=callee),
    ) + _measure_blockhash(0, fork, sstore_key=outer_gas_slot)

    caller = pre.deploy_contract(
        code=caller_code,
        storage={status_slot: 0xDEAD},
    )
    access_list = (
        [AccessList(address=Spec.HISTORY_STORAGE_ADDRESS, storage_keys=[0])]
        if pre_warm
        else None
    )
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=caller,
        access_list=access_list,
    )

    state_test(
        env=Environment(number=1),
        pre=pre,
        tx=tx,
        post={caller: Account(storage=storage)},
    )


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@EIPChecklist.Opcode.Test.ExceptionalAbort()
@pytest.mark.parametrize(
    "abort_op",
    [
        pytest.param(Op.REVERT(0, 0), id="subcall_revert"),
        pytest.param(Op.INVALID, id="subcall_invalid_opcode"),
    ],
)
def test_blockhash_warmth_rolls_back_on_subcall_abort(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    abort_op: Bytecode,
) -> None:
    """
    Warmth acquired by an in-bounds ``BLOCKHASH(0)`` inside a child frame
    that subsequently ``REVERT``s or aborts via ``INVALID`` must roll back:
    a ``BLOCKHASH(0)`` executed afterwards in the parent frame is still
    charged the cold access cost (``2120`` gas).
    """
    cold_gas = Op.BLOCKHASH(key_warm=False, in_bounds=True).gas_cost(fork)
    child = pre.deploy_contract(code=Op.POP(Op.BLOCKHASH(0)) + abort_op)

    storage = Storage()
    status_slot = storage.store_next(0, "aborted_subcall_status")
    gas_slot = storage.store_next(cold_gas, "parent_blockhash_still_cold")

    parent_code = Op.SSTORE(
        status_slot,
        Op.CALL(gas=50_000, address=child),
    ) + _measure_blockhash(0, fork, sstore_key=gas_slot)

    parent = pre.deploy_contract(
        code=parent_code,
        storage={status_slot: 0xDEAD},
    )
    tx = Transaction(sender=pre.fund_eoa(), to=parent)

    state_test(
        env=Environment(number=1),
        pre=pre,
        tx=tx,
        post={parent: Account(storage=storage)},
    )


@EIPChecklist.Opcode.Test.StackUnderflow()
@EIPChecklist.Opcode.Test.StackOverflow()
@EIPChecklist.Opcode.Test.ExceptionalAbort()
@pytest.mark.parametrize(
    "stack_depth,call_succeeds",
    [
        pytest.param(0, False, id="stack_underflow_empty"),
        pytest.param(1, True, id="stack_single_item"),
        pytest.param(1024, True, id="stack_at_1024_limit"),
    ],
)
def test_blockhash_stack_bounds(
    state_test: StateTestFiller,
    pre: Alloc,
    stack_depth: int,
    call_succeeds: bool,
) -> None:
    """
    Test ``BLOCKHASH`` stack bounds: an empty stack causes a stack underflow
    abort, while 1 and 1024 items on the stack succeed because ``BLOCKHASH``
    pops 1 item and pushes 1 item.
    """
    callee = pre.deploy_contract(
        code=Op.PUSH1(0) * stack_depth + Op.BLOCKHASH + Op.STOP
    )
    caller = pre.deploy_contract(
        code=Op.SSTORE(0, Op.CALL(gas=100_000, address=callee)),
        storage={0: 0xDEAD},
    )
    tx = Transaction(sender=pre.fund_eoa(), to=caller)

    state_test(
        env=Environment(number=1),
        pre=pre,
        tx=tx,
        post={caller: Account(storage={0: 1 if call_succeeds else 0})},
    )


@EIPChecklist.Opcode.Test.ExecutionContext.Call()
@EIPChecklist.Opcode.Test.ExecutionContext.Callcode()
@EIPChecklist.Opcode.Test.ExecutionContext.Delegatecall()
@EIPChecklist.Opcode.Test.ExecutionContext.Staticcall()
@pytest.mark.pre_alloc_mutable
@pytest.mark.with_all_call_opcodes
def test_blockhash_call_contexts(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    call_opcode: Op,
) -> None:
    """
    Test that ``BLOCKHASH(0)`` resolves the storage value from
    ``HISTORY_STORAGE_ADDRESS`` and warms slot 0 across ``CALL``,
    ``CALLCODE``, ``DELEGATECALL``, and ``STATICCALL`` frames.
    """
    sentinel = 0x1122334455667788
    pre[Spec.HISTORY_STORAGE_ADDRESS] = Account(storage={0: sentinel})
    warm_gas = Op.BLOCKHASH(key_warm=True, in_bounds=True).gas_cost(fork)

    callee = pre.deploy_contract(
        code=Op.MSTORE(0, Op.BLOCKHASH(0)) + Op.RETURN(0, 32)
    )
    storage = Storage()
    status_slot = storage.store_next(1, "call_status")
    ret_slot = storage.store_next(sentinel, "returned_blockhash")
    warm_gas_slot = storage.store_next(
        warm_gas,
        "parent_blockhash_warm_after_child_call",
    )

    caller_code = (
        Op.SSTORE(
            status_slot,
            call_opcode(
                gas=100_000,
                address=callee,
                ret_offset=0,
                ret_size=32,
            ),
        )
        + Op.SSTORE(ret_slot, Op.MLOAD(0))
        + _measure_blockhash(0, fork, sstore_key=warm_gas_slot)
    )
    caller = pre.deploy_contract(code=caller_code)
    tx = Transaction(sender=pre.fund_eoa(), to=caller)

    state_test(
        env=Environment(number=2),
        pre=pre,
        tx=tx,
        post={caller: Account(storage=storage)},
    )


@EIPChecklist.Opcode.Test.ExecutionContext.SetCode()
@pytest.mark.pre_alloc_mutable
def test_blockhash_set_code(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test ``BLOCKHASH`` executed inside an EIP-7702 set-code delegated account.
    """
    sentinel = 0xAABBCCDDEEFF0011
    pre[Spec.HISTORY_STORAGE_ADDRESS] = Account(storage={0: sentinel})
    cold_gas = Op.BLOCKHASH(key_warm=False, in_bounds=True).gas_cost(fork)
    warm_gas = Op.BLOCKHASH(key_warm=True, in_bounds=True).gas_cost(fork)

    auth_signer = pre.fund_eoa(amount=0)
    delegate_code = (
        _measure_blockhash(0, fork, sstore_key=0)
        + _measure_blockhash(0, fork, sstore_key=1)
        + Op.SSTORE(2, Op.BLOCKHASH(0))
    )
    delegate_target = pre.deploy_contract(code=delegate_code)

    tx = Transaction(
        to=auth_signer,
        authorization_list=[
            AuthorizationTuple(
                address=delegate_target,
                nonce=0,
                signer=auth_signer,
            ),
        ],
        sender=pre.fund_eoa(),
    )

    state_test(
        env=Environment(number=2),
        pre=pre,
        tx=tx,
        post={
            delegate_target: Account(storage={}),
            auth_signer: Account(
                nonce=1,
                code=Spec7702.delegation_designation(delegate_target),
                storage={0: cold_gas, 1: warm_gas, 2: sentinel},
            ),
        },
    )


@EIPChecklist.Opcode.Test.ExecutionContext.Initcode.Behavior()
@EIPChecklist.Opcode.Test.ExecutionContext.Initcode.Behavior.Tx()
@EIPChecklist.Opcode.Test.ExecutionContext.Initcode.Behavior.Opcode()
@pytest.mark.pre_alloc_mutable
@pytest.mark.parametrize(
    "create_opcode",
    [
        pytest.param(None, id="create_tx"),
        pytest.param(Op.CREATE, id="create_opcode"),
        pytest.param(Op.CREATE2, id="create2_opcode"),
    ],
)
def test_blockhash_initcode(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    create_opcode: Op | None,
) -> None:
    """
    Test ``BLOCKHASH`` inside contract creation initcode (both transaction
    creation and ``CREATE``/``CREATE2`` opcodes).
    """
    sentinel = 0x9988776655443322
    pre[Spec.HISTORY_STORAGE_ADDRESS] = Account(storage={0: sentinel})
    cold_gas = Op.BLOCKHASH(key_warm=False, in_bounds=True).gas_cost(fork)
    warm_gas = Op.BLOCKHASH(key_warm=True, in_bounds=True).gas_cost(fork)

    init_code = (
        _measure_blockhash(0, fork, sstore_key=0)
        + _measure_blockhash(0, fork, sstore_key=1)
        + Op.SSTORE(2, Op.BLOCKHASH(0))
    )
    sender = pre.fund_eoa()

    if create_opcode is None:
        created_address = compute_create_address(address=sender, nonce=0)
        tx = Transaction(
            to=None,
            data=init_code,
            sender=sender,
        )
    else:
        factory_code = (
            Op.CALLDATACOPY(offset=0, size=len(init_code))
            + create_opcode(offset=0, size=len(init_code))
            + Op.STOP
        )
        factory = pre.deploy_contract(code=factory_code)
        created_address = compute_create_address(
            address=factory,
            nonce=1,
            initcode=init_code,
            opcode=create_opcode,
        )
        tx = Transaction(
            to=factory,
            data=init_code,
            sender=sender,
        )

    state_test(
        env=Environment(number=2),
        pre=pre,
        tx=tx,
        post={
            created_address: Account(
                storage={0: cold_gas, 1: warm_gas, 2: sentinel}
            )
        },
    )


@EIPChecklist.Opcode.Test.ExecutionContext.BlockContext()
def test_blockhash_block_access_list_reads_and_oog(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify EIP-7928 Block Access List (BAL) interactions for EIP-7709
    ``BLOCKHASH``.

    * In Block 3:
      - ``BLOCKHASH(0)`` (in-bounds non-parent block) reads slot ``0`` from
        ``HISTORY_STORAGE_ADDRESS`` and records ``0`` in ``storage_reads``.
      - ``BLOCKHASH(2)`` (in-bounds parent block) reads slot ``2``, which was
        already written by the EIP-2935 system call at the start of Block 3
        (in ``storage_changes``), so slot ``2`` is NOT duplicated in
        ``storage_reads``.
      - ``BLOCKHASH(999)`` (out-of-bounds) does not touch storage and does
        NOT record ``999`` in ``storage_reads``.
      - A sub-call that executes ``BLOCKHASH(1)`` with only 100 gas (enough
        for ``G_BLOCKHASH = 20`` but OOG on ``G_COLD_SLOAD = 2100``) aborts
        before reading storage, so slot ``1`` is NOT recorded in
        ``storage_reads``.
    """
    sender = pre.fund_eoa()
    oog_callee = pre.deploy_contract(code=Op.PUSH1(1) + Op.BLOCKHASH + Op.STOP)

    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(0, Op.ISZERO(Op.BLOCKHASH(0)))
            + Op.SSTORE(1, Op.ISZERO(Op.BLOCKHASH(2)))
            + Op.SSTORE(2, Op.BLOCKHASH(999))
            + Op.SSTORE(3, Op.CALL(gas=100, address=oog_callee))
        ),
        storage={0: 0xDEAD, 1: 0xDEAD, 2: 0xDEAD, 3: 0xDEAD},
    )

    blocks = [
        Block(txs=[]),
        Block(txs=[]),
        Block(
            txs=[Transaction(sender=sender, to=contract)],
            expected_block_access_list=BlockAccessListExpectation(
                account_expectations={
                    Spec.HISTORY_STORAGE_ADDRESS: BalAccountExpectation(
                        storage_reads=[0],
                    ),
                }
            ),
        ),
    ]

    blockchain_test(
        pre=pre,
        blocks=blocks,
        post={
            contract: Account(
                storage={0: 0, 1: 0, 2: 0, 3: 0},
            ),
        },
    )
