"""Benchmark SSTORE operations on bloated and delegated storage."""

from functools import partial
from typing import Any, List

import pytest
from execution_testing import (
    EOA,
    Alloc,
    BenchmarkTestFiller,
    Block,
    Bytecode,
    Fork,
    Hash,
    IteratingBytecode,
    Op,
    RecipientType,
    TestPhaseManager,
    Transaction,
)

from tests.benchmark.helper.delegation import (
    build_delegated_storage_setup,
    run_bloated_eoa_benchmark,
)
from tests.benchmark.helper.enums import CacheStrategy
from tests.benchmark.helper.storage import (
    START_SLOT,
    access_list_generator,
    create_sstore_initializer,
    executor_calldata_generator,
    initializer_calldata_generator,
)


@pytest.mark.repricing
@pytest.mark.stub_parametrize("token_name", "bloated_eoa_")
@pytest.mark.parametrize("write_new_value", [False, True])
@pytest.mark.parametrize("existing_slots", [True, False])
@pytest.mark.parametrize("cache_strategy", [CacheStrategy.NO_CACHE])
def test_sstore_bloated(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    token_name: str,
    write_new_value: bool,
    existing_slots: bool,
    cache_strategy: CacheStrategy,
) -> None:
    """
    Benchmark SSTORE opcodes targeting an EOA with storage bloated.
    """
    sstore_metadata: dict[str, Any] = {}
    # If CACHE_TX, there would be one cold SLOAD before SSTORE
    sstore_metadata["key_warm"] = cache_strategy == CacheStrategy.CACHE_TX

    # SSTORE metadata matrix:
    #
    # existing_slots | write_new_value | original | current | new
    # ---------------+-----------------+----------+---------+-----
    # True           | True            | 1        | 1       | 2
    # True           | False           | 1        | 1       | 1
    # False          | True            | 0        | 0       | 1
    # False          | False           | 0        | 0       | 0

    initial_value = int(existing_slots)

    # When existing_slots is False, the initial value is always 0
    # Otherwise, the initial value starts at 1 instead.
    sstore_metadata["original_value"] = initial_value
    sstore_metadata["current_value"] = initial_value

    # If not writing a new value, the new value is the same as the current one
    # If writing a new value, the new value is current value + 1
    sstore_metadata["new_value"] = (
        initial_value if not write_new_value else initial_value + 1
    )

    setup = (
        Op.CALLDATALOAD(32)  # [end_slot]
        + Op.CALLDATALOAD(0)  # [counter, end_slot]
    )

    # stack element: [counter, end_slot]

    loop = Bytecode()
    loop += Op.JUMPDEST  # jump target

    # If CACHE_TX, warm the slot with a cold SLOAD before the SSTORE loop
    if cache_strategy == CacheStrategy.CACHE_TX:
        loop += Op.POP(Op.SLOAD(Op.DUP1, key_warm=False))

    sstore_op: Bytecode = Bytecode()
    if write_new_value:
        # s[counter] = counter + 1
        sstore_op = (
            Op.DUP1  # [counter, counter, end_slot]
            + Op.DUP1  # [counter, counter, counter, end_slot]
            + Op.PUSH1(1)  # [1, counter, counter, counter, end_slot]
            + Op.ADD  # [counter+1, counter, counter, end_slot]
            + Op.SWAP1  # [counter, counter+1, counter, end_slot]
            + Op.SSTORE(**sstore_metadata)  # [counter, end_slot]
        )
    else:
        # s[counter] = counter (existing slot) or 0 (non existing slot)
        push_value = Op.DUP1 if existing_slots else Op.PUSH1(0)
        sstore_op = (
            push_value  # [value, counter, end_slot]
            + Op.DUP2  # [counter, value, counter, end_slot]
            + Op.SSTORE(**sstore_metadata)  # [counter, end_slot]
        )

    loop += sstore_op

    # stack element: [counter, end_slot]

    loop += (
        Op.PUSH1(1)  # [1, counter, end_slot]
        + Op.ADD  # [counter+1, end_slot]
        + Op.DUP2  # [end_slot, counter+1, end_slot]
        + Op.DUP2  # [counter+1, end_slot, counter+1, end_slot]
        + Op.LT  # [counter+1<end_slot, counter+1, end_slot]
        + Op.PUSH1(len(setup))  # [dest, condition, counter+1, end_slot]
        + Op.JUMPI  # [counter+1, end_slot]
    )

    runtime_code = IteratingBytecode(
        setup=setup,
        iterating=loop,
        cleanup=Op.STOP,
    )

    authority = pre.stub_eoa(token_name)
    start_slot = 1 if existing_slots else START_SLOT

    def calldata_gen(iteration_count: int, start_iteration: int) -> bytes:
        return Hash(start_iteration) + Hash(start_iteration + iteration_count)

    def tx_generator(sender: EOA) -> list[Transaction]:
        return list(
            runtime_code.transactions_by_gas_limit(
                fork=fork,
                gas_limit=gas_benchmark_value,
                sender=sender,
                to=authority,
                start_iteration=start_slot,
                calldata=calldata_gen,
                recipient_type=RecipientType.DELEGATION_7702,
            )
        )

    run_bloated_eoa_benchmark(
        benchmark_test=benchmark_test,
        pre=pre,
        fork=fork,
        gas_benchmark_value=gas_benchmark_value,
        tx_gas_limit=tx_gas_limit,
        authority=authority,
        existing_slots=existing_slots,
        runtime_code=runtime_code,
        cache_strategy=cache_strategy,
        tx_generator=tx_generator,
    )


def create_sstore_executor(
    sloads_before_sstore: bool,
    key_warm: bool,
    original_value: int,
    new_value: int,
) -> IteratingBytecode:
    """
    Create a contract that executes SSTORE benchmark operations.

    - CALLDATA[0..32] start slot (index)
    - CALLDATA[32..64] ending slot (end_slot)
    - CALLDATA[64..96] value to write

    Returns: IteratingBytecode representing the benchmark executor.
    """
    setup = (
        Op.CALLDATALOAD(32)  # end_slot
        + Op.CALLDATALOAD(64)  # value
        + Op.CALLDATALOAD(0)  # start_slot = counter
    )
    # [counter, value, end_slot]

    loop = Bytecode()
    loop += Op.JUMPDEST
    # Loop Body: Store Value at Start Slot + Counter
    if sloads_before_sstore:
        loop += Op.DUP1  # [counter, counter, value, end_slot]
        loop += Op.SLOAD(
            # gas accounting
            key_warm=key_warm
        )
        loop += Op.POP
        loop += Op.DUP2  # [value, counter, value, end_slot]
        loop += Op.DUP2  # [counter, value, counter, value, end_slot]
        loop += Op.SSTORE(  # STORAGE[counter] = value
            key_warm=True,
            original_value=original_value,
            current_value=original_value,
            new_value=new_value,
        )
    else:
        loop += Op.DUP2  # [value, counter, value, end_slot]
        loop += Op.DUP2  # [counter, value, counter, value, end_slot]
        loop += Op.SSTORE(  # STORAGE[counter] = value
            key_warm=key_warm,
            original_value=original_value,
            current_value=original_value,
            new_value=new_value,
        )
    # [counter, value, end_slot]

    # Loop Post: Increment Counter
    loop += Op.PUSH1(1)
    loop += Op.ADD
    # [counter + 1, value, end_slot]

    # Loop Condition: Counter < end_slot
    loop += Op.DUP3  # [end_slot, counter + 1, value, end_slot]
    loop += Op.DUP2  # [counter + 1, end_slot, counter + 1, value, end_slot]
    loop += Op.LT  # [counter + 1 < end_slot, counter + 1, value, end_slot]
    loop += Op.PUSH1(len(setup))
    loop += Op.JUMPI
    # [counter + 1, value, end_slot]

    cleanup = Bytecode()
    cleanup += Op.STOP

    return IteratingBytecode(setup=setup, iterating=loop, cleanup=cleanup)


def create_sstore_dirty_executor(
    write_values: List[int],
    key_warm: bool,
    initial_value: int,
) -> IteratingBytecode:
    """
    Create executor that writes multiple values to each slot.

    Exercise dirty state transitions by performing a sequence of SSTOREs
    to the same slot within a single loop iteration. After the first
    SSTORE, the slot is warm and subsequent writes hit the dirty
    (100 gas) path when original != current.

    - CALLDATA[0..32] start slot (index)
    - CALLDATA[32..64] ending slot (end_slot)

    Return an IteratingBytecode for the dirty-write benchmark executor.
    """
    setup = (
        Op.CALLDATALOAD(32)  # end_slot
        + Op.CALLDATALOAD(0)  # start_slot = counter
    )
    # Stack: [counter, end_slot]

    loop = Bytecode()
    loop += Op.JUMPDEST

    for i, val in enumerate(write_values):
        is_first = i == 0
        current_val = initial_value if is_first else write_values[i - 1]
        # DUP2 reaches counter through the pushed value
        loop += Op.SSTORE(
            Op.DUP2,
            val,
            key_warm=key_warm if is_first else True,
            original_value=initial_value,
            current_value=current_val,
            new_value=val,
        )
    # Stack after all writes: [counter, end_slot]

    # Increment counter
    loop += Op.PUSH1(1)
    loop += Op.ADD
    # [counter + 1, end_slot]

    # Loop while counter + 1 < end_slot
    loop += Op.DUP2
    loop += Op.DUP2
    loop += Op.LT
    loop += Op.PUSH1(len(setup))
    loop += Op.JUMPI

    cleanup = Bytecode()
    cleanup += Op.STOP

    return IteratingBytecode(setup=setup, iterating=loop, cleanup=cleanup)


@pytest.mark.parametrize("access_warm", [True, False])
@pytest.mark.parametrize("sloads_before_sstore", [True, False])
@pytest.mark.parametrize(
    "initial_value,write_value",
    [
        pytest.param(0, 0, id="zero_to_zero"),
        pytest.param(0, 0xDEADBEEF, id="zero_to_nonzero"),
        # TODO: Resolve refund mechanism
        # pytest.param(0xDEADBEEF, 0, id="nonzero_to_zero"),
        pytest.param(0xDEADBEEF, 0xBEEFBEEF, id="nonzero_to_diff"),
        pytest.param(0xDEADBEEF, 0xDEADBEEF, id="nonzero_to_same"),
    ],
)
def test_sstore_variants(
    benchmark_test: BenchmarkTestFiller,
    fork: Fork,
    pre: Alloc,
    tx_gas_limit: int,
    gas_benchmark_value: int,
    access_warm: bool,
    sloads_before_sstore: bool,
    initial_value: int,
    write_value: int,
) -> None:
    """
    Benchmark SSTORE instruction with various configurations.

    Uses EIP-7702 delegation. The authority EOA delegates to:

    - StorageInitializer: storage[i] = initial_value (initial_value != 0)
    - BenchmarkExecutor: performs the benchmark operation (SSTORE)

    Variants:

    - access_warm: Warm storage slots via access list
    - sloads_before_sstore: SLOADs per slot before SSTORE
    - initial_value/write_value: Storage transitions
      (zero_to_zero, zero_to_nonzero, nonzero_to_zero, nonzero_to_nonzero)
    """
    # Initial Storage Construction
    initializer_code = create_sstore_initializer(initial_value)
    initializer_addr = pre.deploy_contract(code=initializer_code)

    # Actual Benchmark Execution
    executor_code = create_sstore_executor(
        sloads_before_sstore=sloads_before_sstore,
        key_warm=access_warm,
        original_value=initial_value,
        new_value=write_value,
    )
    executor_addr = pre.deploy_contract(code=executor_code)

    authority = pre.fund_eoa(amount=0)
    authority_nonce = 0

    delegation_sender = pre.fund_eoa()

    calldata_gen = partial(
        executor_calldata_generator, write_value=write_value
    )
    access_list_gen = partial(
        access_list_generator, access_warm=access_warm, authority=authority
    )

    # Number of slots that can be processed in the execution phase
    num_target_slots = sum(
        executor_code.tx_iterations_by_gas_limit(
            fork=fork,
            gas_limit=gas_benchmark_value,
            calldata=calldata_gen,
            access_list=access_list_gen,
            start_iteration=1,
            recipient_type=RecipientType.DELEGATION_7702,
        )
    )

    # Setup phase: initialize storage slots (if initial_value != 0)
    with TestPhaseManager.setup():
        blocks = build_delegated_storage_setup(
            pre=pre,
            fork=fork,
            tx_gas_limit=tx_gas_limit,
            block_gas_budget=gas_benchmark_value,
            needs_init=initial_value != 0,
            num_target_slots=num_target_slots,
            initializer_code=initializer_code,
            initializer_addr=initializer_addr,
            executor_addr=executor_addr,
            authority=authority,
            authority_nonce=authority_nonce,
            delegation_sender=delegation_sender,
            initializer_calldata_generator=initializer_calldata_generator,
        )

    # Execution phase
    expected_gas_used = 0

    with TestPhaseManager.execution():
        exec_txs = list(
            executor_code.transactions_by_gas_limit(
                fork=fork,
                gas_limit=gas_benchmark_value,
                sender=pre.fund_eoa(),
                to=authority,
                calldata=calldata_gen,
                start_iteration=1,
                access_list=access_list_gen,
                recipient_type=RecipientType.DELEGATION_7702,
            )
        )

        expected_gas_used = sum(tx.gas_cost for tx in exec_txs)

    blocks.append(Block(txs=exec_txs))

    benchmark_test(
        pre=pre,
        blocks=blocks,
        expected_benchmark_gas_used=expected_gas_used,
    )


# SSTORE DIRTY TRANSITIONS BENCHMARK ARCHITECTURE:
#
#   [Authority EOA]
#       │
#       │ Phase 1: Delegate to StorageInitializer
#       │   ──► SSTORE(slot, initial_value) for N slots
#       │
#       │ Phase 2: Delegate to DirtyExecutor
#       │   ──► For each slot:
#       │         SSTORE(slot, v1) → SSTORE(slot, v2) → ...
#       │
# WHY IT STRESSES CLIENTS:
#   - Multiple writes per slot exercise EIP-2200/EIP-3529 refund
#     branching: clean (original==current) vs dirty (original!=current)
#   - Oscillation causes refund counter to swing up/down each write
#   - Refund cap (gas_used/5) saturates with enough iterations
#   - Tests correct tracking of original vs current vs new values


@pytest.mark.parametrize("access_warm", [True, False])
@pytest.mark.parametrize(
    "initial_value,write_values",
    [
        pytest.param(
            0xDEADBEEF,
            [0, 0xDEADBEEF, 0, 0xDEADBEEF],
            id="oscillation_4x",
        ),
        pytest.param(
            0xDEADBEEF,
            [0, 0xDEADBEEF, 0, 0xDEADBEEF, 0, 0xDEADBEEF],
            id="oscillation_6x",
        ),
        pytest.param(
            0xDEADBEEF,
            [0xBEEFBEEF, 0xCAFECAFE, 0xDEADBEEF],
            id="triple_write_restore",
        ),
        pytest.param(
            0xDEADBEEF,
            [0],
            id="mass_clear",
        ),
        pytest.param(
            0,
            [1, 0, 1, 0],
            id="oscillation_4x_from_zero",
            marks=pytest.mark.skip(
                reason="net-zero state gas; degenerates to an "
                "execution-gas loop"
            ),
        ),
        pytest.param(
            0,
            [1],
            id="mass_set_from_zero",
        ),
    ],
)
def test_sstore_dirty_transitions(
    benchmark_test: BenchmarkTestFiller,
    fork: Fork,
    pre: Alloc,
    tx_gas_limit: int,
    gas_benchmark_value: int,
    access_warm: bool,
    initial_value: int,
    write_values: List[int],
) -> None:
    """
    Benchmark SSTORE dirty state transitions.

    Exercise EIP-2200/EIP-3529 refund logic by writing the same slot
    multiple times per iteration. Uses EIP-7702 delegation: authority
    EOA delegates to initializer then to dirty-write executor.

    Variants:

    - oscillation: X→0→X→0, alternates a clean change (slot access plus
      `STORAGE_WRITE`) with a dirty one (slot access only)
    - triple_write_restore: X→B→C→X, all SSTORE branches
    - mass_clear: X→0, maximum per-slot refund generation
    """
    # Initial Storage Construction
    initializer_code = create_sstore_initializer(initial_value)
    initializer_addr = pre.deploy_contract(code=initializer_code)

    # Benchmark Executor — multi-write per slot
    executor_code = create_sstore_dirty_executor(
        write_values=write_values,
        key_warm=access_warm,
        initial_value=initial_value,
    )
    executor_addr = pre.deploy_contract(code=executor_code)

    authority = pre.fund_eoa(amount=0)
    authority_nonce = 0

    delegation_sender = pre.fund_eoa()

    calldata_gen = partial(executor_calldata_generator)
    access_list_gen = partial(
        access_list_generator,
        access_warm=access_warm,
        authority=authority,
    )

    # Number of slots processable in execution phase
    num_target_slots = sum(
        executor_code.tx_iterations_by_gas_limit(
            fork=fork,
            gas_limit=gas_benchmark_value,
            calldata=calldata_gen,
            access_list=access_list_gen,
            start_iteration=1,
            recipient_type=RecipientType.DELEGATION_7702,
        )
    )

    # Setup phase: initialize all slots to initial_value
    with TestPhaseManager.setup():
        blocks = build_delegated_storage_setup(
            pre=pre,
            fork=fork,
            tx_gas_limit=tx_gas_limit,
            block_gas_budget=gas_benchmark_value,
            needs_init=initial_value != 0,
            num_target_slots=num_target_slots,
            initializer_code=initializer_code,
            initializer_addr=initializer_addr,
            executor_addr=executor_addr,
            authority=authority,
            authority_nonce=authority_nonce,
            delegation_sender=delegation_sender,
            initializer_calldata_generator=(initializer_calldata_generator),
        )

    # Execution phase — no expected_benchmark_gas_used because
    # refund cap (gas_used/5) makes actual consumption non-trivial
    with TestPhaseManager.execution():
        exec_txs = list(
            executor_code.transactions_by_gas_limit(
                fork=fork,
                gas_limit=gas_benchmark_value,
                sender=pre.fund_eoa(),
                to=authority,
                calldata=calldata_gen,
                start_iteration=1,
                access_list=access_list_gen,
                recipient_type=RecipientType.DELEGATION_7702,
            )
        )

    blocks.append(Block(txs=exec_txs))

    benchmark_test(
        pre=pre,
        blocks=blocks,
        skip_gas_used_validation=True,
    )
