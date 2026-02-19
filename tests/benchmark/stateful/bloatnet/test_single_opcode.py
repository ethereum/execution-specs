"""
abstract: BloatNet single-opcode benchmark cases for state-related operations.

   These tests focus on individual EVM opcodes (SLOAD, SSTORE) to measure
   their performance when accessing many storage slots across pre-deployed
   contracts. Unlike multi-opcode tests, these isolate single operations
   to benchmark specific state-handling bottlenecks.
"""

from functools import partial
from typing import Callable, List

import pytest
from execution_testing import (
    EOA,
    AccessList,
    Address,
    Alloc,
    AuthorizationTuple,
    BenchmarkTestFiller,
    Block,
    Bytecode,
    Fork,
    Hash,
    IteratingBytecode,
    JumpLoopGenerator,
    Op,
    Storage,
    TestPhaseManager,
    Transaction,
    While,
)

from tests.benchmark.stateful.helpers import (
    APPROVE_SELECTOR,
    BALANCEOF_SELECTOR,
    SLOAD_TOKENS,
    SSTORE_TOKENS,
)

REFERENCE_SPEC_GIT_PATH = "DUMMY/bloatnet.md"
REFERENCE_SPEC_VERSION = "1.0"


# SLOAD BENCHMARK ARCHITECTURE:
#
#   [Pre-deployed ERC20 Contract] ──── Storage slots for balances
#           │
#           │  balanceOf(address) → SLOAD(keccak256(address || slot))
#           │
#   [Attack Contract] ──CALL──► ERC20.balanceOf(random_address)
#           │
#           └─► Loop(i=0 to N):
#                 1. Generate random address from counter
#                 2. CALL balanceOf(random_address) → forces cold SLOAD
#                 3. Most addresses have zero balance → empty storage slots
#
# WHY IT STRESSES CLIENTS:
#   - Each balanceOf() call forces a cold SLOAD on a likely-empty slot
#   - Storage slot = keccak256(address || balances_slot)
#   - Random addresses ensure maximum cache misses
#   - Tests client's sparse storage handling efficiency


# SSTORE BENCHMARK ARCHITECTURE:
#
#   [Pre-deployed ERC20 Contract] ──── Storage slots for allowances
#           │
#           │  approve(spender, amount)
#           │    → SSTORE(keccak256(spender || slot), amount)
#           │
#   [Attack Contract]
#       ──CALL──► ERC20.approve(counter_as_spender, counter_as_amount)
#           │
#           └─► Loop(i=0 to N):
#                 1. Use counter as both spender address and amount
#                 2. CALL approve(counter, counter) → forces cold SSTORE
#                 3. Writes to new allowance slots in sparse storage
#
# WHY IT STRESSES CLIENTS:
#   - Each approve() call forces an SSTORE to a new storage slot
#   - Storage slot = keccak256(
#       msg.sender || keccak256(spender || allowances_slot)
#     )
#   - Sequential counter ensures unique storage locations
#   - Tests client's ability to handle many storage writes
#   - Simulates real-world contract state accumulation over time


@pytest.mark.parametrize("token_name", SLOAD_TOKENS)
def test_sload_empty_erc20_balanceof(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    token_name: str,
) -> None:
    """Benchmark SLOAD using ERC20 balanceOf on bloatnet."""
    # Stub Account
    erc20_address = pre.deploy_contract(
        code=Bytecode(),
        stub=f"test_sload_empty_erc20_balanceof_{token_name}",
    )

    # MEM[0] = function selector
    # MEM[32] = starting address offset
    setup = (
        Op.MSTORE(
            0,
            BALANCEOF_SELECTOR,
            # gas accounting
            old_memory_size=0,
            new_memory_size=32,
        )
        + Op.MSTORE(
            32,
            Op.CALLDATALOAD(32),  # Address Offset
            # gas accounting
            old_memory_size=32,
            new_memory_size=64,
        )
        + Op.CALLDATALOAD(0)  # [num_calls]
    )

    loop = While(
        body=Op.POP(
            Op.CALL(
                address=erc20_address,
                value=0,
                args_offset=28,
                args_size=36,
                ret_offset=0,
                ret_size=0,
                # gas accounting
                address_warm=True,
            )
        )
        + Op.MSTORE(32, Op.ADD(Op.MLOAD(32), 1)),
        condition=Op.PUSH1(1)  # [1, num_calls]
        + Op.SWAP1  # [num_calls, 1]
        + Op.SUB  # [num_calls-1]
        + Op.DUP1  # [num_calls-1, num_calls-1]
        + Op.ISZERO  # [num_calls-1==0, num_calls-1]
        + Op.ISZERO,  # [num_calls-1!=0, num_calls-1]
    )

    # Contract Deployment
    code = setup + loop
    attack_contract_address = pre.deploy_contract(code=code)

    # Gas Accounting
    setup_cost = setup.gas_cost(fork)
    loop_cost = loop.gas_cost(fork)

    access_list = [AccessList(address=erc20_address, storage_keys=[])]
    intrinsic_gas_with_access_list = (
        fork.transaction_intrinsic_cost_calculator()(
            access_list=access_list,
            calldata=b"\xff" * 64,
        )
    )

    # ERC20 balanceOf bytecode structure:
    function_dispatch = (
        # Selector dispatch
        Op.PUSH4(BALANCEOF_SELECTOR)
        + Op.EQ
        + Op.JUMPI
        # Function body
        + Op.JUMPDEST
        + Op.CALLDATALOAD(4)
        + Op.MSTORE(0)
        + Op.MSTORE(32, 0)
        + Op.SHA3(
            0,
            64,
            # gas accounting
            data_size=64,
            old_memory_size=0,
            new_memory_size=64,
        )
        + Op.SLOAD
        # Return value
        + Op.MSTORE(0)
        + Op.RETURN(0, 32)
    )

    function_dispatch_cost = function_dispatch.gas_cost(fork)

    # Transaction Loops
    txs = []
    gas_remaining = gas_benchmark_value
    slot_offset = 0

    while gas_remaining > intrinsic_gas_with_access_list:
        gas_available = min(gas_remaining, tx_gas_limit)

        if gas_available < intrinsic_gas_with_access_list + setup_cost:
            break

        num_calls = (
            gas_available - intrinsic_gas_with_access_list - setup_cost
        ) // (function_dispatch_cost + loop_cost)

        if num_calls == 0:
            break

        calldata = Hash(num_calls) + Hash(slot_offset)

        txs.append(
            Transaction(
                gas_limit=gas_available,
                data=calldata,
                to=attack_contract_address,
                sender=pre.fund_eoa(),
                access_list=access_list,
            )
        )

        gas_remaining -= gas_available
        slot_offset += num_calls

    benchmark_test(
        pre=pre,
        blocks=[Block(txs=txs)],
    )


@pytest.mark.parametrize("token_name", SSTORE_TOKENS)
def test_sstore_erc20_approve(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    token_name: str,
) -> None:
    """Benchmark SSTORE using ERC20 approve on bloatnet."""
    # Stub Account
    erc20_address = pre.deploy_contract(
        code=Bytecode(),
        stub=f"test_sstore_erc20_approve_{token_name}",
    )

    # MEM[0] = function selector
    # MEM[32] = starting address offset
    setup = (
        Op.MSTORE(
            0,
            APPROVE_SELECTOR,
            # gas accounting
            old_memory_size=0,
            new_memory_size=32,
        )
        + Op.MSTORE(
            32,
            Op.CALLDATALOAD(32),  # Address Offset
            # gas accounting
            old_memory_size=32,
            new_memory_size=64,
        )
        + Op.CALLDATALOAD(0)  # [num_calls]
    )

    loop = While(
        body=(
            Op.MSTORE(64, Op.MLOAD(32))
            + Op.POP(
                Op.CALL(
                    address=erc20_address,
                    value=0,
                    args_offset=28,
                    args_size=68,
                    ret_offset=0,
                    ret_size=0,
                    # gas accounting
                    address_warm=True,
                )
            )
            + Op.MSTORE(32, Op.ADD(Op.MLOAD(32), 1))
        ),
        condition=Op.PUSH1(1)  # [1, num_calls]
        + Op.SWAP1  # [num_calls, 1]
        + Op.SUB  # [num_calls-1]
        + Op.DUP1  # [num_calls-1, num_calls-1]
        + Op.ISZERO  # [num_calls-1==0, num_calls-1]
        + Op.ISZERO,  # [num_calls-1!=0, num_calls-1]
    )

    # Contract Deployment
    code = setup + loop
    attack_contract_address = pre.deploy_contract(code=code)

    # Gas Accounting
    setup_cost = setup.gas_cost(fork)
    loop_cost = loop.gas_cost(fork)
    access_list = [AccessList(address=erc20_address, storage_keys=[])]
    intrinsic_gas_with_access_list = (
        fork.transaction_intrinsic_cost_calculator()(
            access_list=access_list,
            calldata=b"\xff" * 64,
        )
    )

    function_dispatch = (
        # Selector dispatch
        Op.PUSH4(APPROVE_SELECTOR)
        + Op.EQ
        + Op.JUMPI
        # Function body
        + Op.JUMPDEST
        + Op.CALLDATALOAD(4)
        + Op.CALLDATALOAD(36)
        + Op.MSTORE(0, Op.CALLER)
        + Op.MSTORE(32, 1)
        + Op.SHA3(
            0,
            64,
            # gas accounting
            data_size=64,
            old_memory_size=0,
            new_memory_size=64,
        )
        + Op.MSTORE(32)
        + Op.MSTORE(0, Op.CALLDATALOAD(4))
        + Op.SHA3(
            0,
            64,
            # gas accounting
            data_size=64,
        )
        + Op.DUP1
        + Op.SLOAD.with_metadata(access_warm=False)
        + Op.POP
        + Op.SSTORE
        # Return true
        + Op.PUSH1(1)
        + Op.MSTORE(0)
        + Op.PUSH1(32)
        + Op.PUSH1(0)
        + Op.RETURN(0, 32)
    )

    function_dispatch_cost = function_dispatch.gas_cost(fork)

    # Transaction Loops
    txs = []
    gas_remaining = gas_benchmark_value
    slot_offset = 0

    while gas_remaining > intrinsic_gas_with_access_list:
        gas_available = min(gas_remaining, tx_gas_limit)

        if gas_available < intrinsic_gas_with_access_list + setup_cost:
            break

        num_calls = (
            gas_available - intrinsic_gas_with_access_list - setup_cost
        ) // (function_dispatch_cost + loop_cost)

        if num_calls == 0:
            break

        calldata = Hash(num_calls) + Hash(slot_offset)

        txs.append(
            Transaction(
                gas_limit=gas_available,
                data=calldata,
                to=attack_contract_address,
                sender=pre.fund_eoa(),
                access_list=access_list,
            )
        )

        gas_remaining -= gas_available
        slot_offset += num_calls

    benchmark_test(
        pre=pre,
        blocks=[Block(txs=txs)],
    )


def create_sstore_initializer(init_val: int) -> IteratingBytecode:
    """
    Create a contract that initializes storage slots from calldata parameters.

    - CALLDATA[0..32] start slot (index)
    - CALLDATA[32..64] slot count (num)

    storage[i] = init_val for i in [index, index + num).

    Returns: IteratingBytecode representing the storage initializer.
    """
    # Setup: [index, index + num]
    prefix = (
        Op.CALLDATALOAD(0)  # [index]
        + Op.DUP1  # [index, index]
        + Op.CALLDATALOAD(32)  # [index, index, num]
        + Op.ADD  # [index, index + num]
    )

    # Loop: decrement counter and store at current position
    # Stack after subtraction: [index, current]
    # where current goes from index+num-1 down to index
    loop = (
        Op.JUMPDEST
        + Op.PUSH1(1)  # [index, current, 1]
        + Op.SWAP1  # [index, 1, current]
        + Op.SUB  # [index, current - 1]
        + Op.SSTORE(  # STORAGE[current-1] = initial_value
            Op.DUP2,
            init_val,
            key_warm=False,
            # gas accounting
            original_value=0,
            current_value=0,
            new_value=init_val,
        )
        # After SSTORE: [index, current - 1]
        # Continue while current - 1 > index
        + Op.JUMPI(len(prefix), Op.GT(Op.DUP2, Op.DUP2))
    )

    return IteratingBytecode(setup=prefix, iterating=loop)


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


def access_list_generator(
    iteration_count: int,
    start_iteration: int,
    access_warm: bool,
    authority: Address,
) -> list[AccessList] | None:
    """Access list generator for warming storage slots."""
    if access_warm:
        storage_keys = [
            Hash(i)
            for i in range(start_iteration, start_iteration + iteration_count)
        ]
        return [AccessList(address=authority, storage_keys=storage_keys)]
    return None


def executor_calldata_generator(
    iteration_count: int,
    start_iteration: int,
    write_value: int | None = None,
) -> bytes:
    """
    Calldata generator for executor operations.

    Generates: Hash(start) + Hash(start + count) [+ Hash(write_value)]
    """
    result = Hash(start_iteration) + Hash(start_iteration + iteration_count)
    if write_value is not None:
        result += Hash(write_value)
    return result


def initializer_calldata_generator(
    iteration_count: int, start_iteration: int
) -> bytes:
    """Calldata generator for the storage: Hash(start) + Hash(count)."""
    return Hash(start_iteration) + Hash(iteration_count)


def pack_transactions_into_blocks(
    transactions: List[Transaction],
    gas_limit: int,
) -> List[Block]:
    """
    Pack transactions into blocks without exceeding gas_limit per block.

    Greedily adds transactions to the current block until adding another
    would exceed the gas limit, then starts a new block.
    """
    if not transactions:
        return []

    blocks: List[Block] = []
    current_txs: List[Transaction] = []
    current_gas = 0

    for tx in transactions:
        if current_gas + tx.gas_limit > gas_limit and current_txs:
            blocks.append(Block(txs=current_txs))
            current_txs = []
            current_gas = 0

        current_txs.append(tx)
        current_gas += tx.gas_limit

    if current_txs:
        blocks.append(Block(txs=current_txs))

    return blocks


def build_delegated_storage_setup(
    *,
    pre: Alloc,
    fork: Fork,
    tx_gas_limit: int,
    needs_init: bool,
    num_target_slots: int,
    initializer_code: IteratingBytecode,
    initializer_addr: Address,
    executor_addr: Address,
    authority: EOA,
    authority_nonce: int,
    delegation_sender: EOA,
    initializer_calldata_generator: Callable[[int, int], bytes],
) -> List[Block]:
    """
    Build setup blocks for delegated storage benchmarks.

    Returns:
        List of blocks for the setup phase.

    """
    blocks: List[Block] = []

    if needs_init:
        # Block 1: Authorize to initializer
        blocks.append(
            Block(
                txs=[
                    Transaction(
                        to=delegation_sender,
                        gas_limit=tx_gas_limit,
                        sender=delegation_sender,
                        authorization_list=[
                            AuthorizationTuple(
                                address=initializer_addr,
                                nonce=authority_nonce,
                                signer=authority,
                            ),
                        ],
                    )
                ]
            )
        )
        authority_nonce += 1

        # Calculate max slots per transaction based on gas cost
        iteration_cost = initializer_code.tx_gas_limit_by_iteration_count(
            fork=fork,
            iteration_count=1,
            start_iteration=1,
            calldata=initializer_calldata_generator,
        )
        iteration_count = max(1, tx_gas_limit // iteration_cost)

        init_txs: List[Transaction] = []
        for start in range(1, num_target_slots + 1, iteration_count):
            chunk_size = min(iteration_count, num_target_slots - start + 1)
            init_txs.extend(
                initializer_code.transactions_by_total_iteration_count(
                    fork=fork,
                    total_iterations=chunk_size,
                    sender=pre.fund_eoa(),
                    to=authority,
                    start_iteration=start,
                    calldata=initializer_calldata_generator,
                )
            )

        # Pack init transactions into blocks
        blocks.extend(pack_transactions_into_blocks(init_txs, tx_gas_limit))

    # Final block: Authorize to executor
    blocks.append(
        Block(
            txs=[
                Transaction(
                    to=delegation_sender,
                    gas_limit=tx_gas_limit,
                    sender=delegation_sender,
                    authorization_list=[
                        AuthorizationTuple(
                            address=executor_addr,
                            nonce=authority_nonce,
                            signer=authority,
                        ),
                    ],
                )
            ]
        )
    )

    return blocks


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
        )
    )

    # Setup phase: initialize storage slots (if initial_value != 0)
    with TestPhaseManager.setup():
        blocks = build_delegated_storage_setup(
            pre=pre,
            fork=fork,
            tx_gas_limit=tx_gas_limit,
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
            )
        )

        expected_gas_used = sum(tx.gas_cost for tx in exec_txs)

    blocks.append(Block(txs=exec_txs))

    benchmark_test(
        pre=pre,
        blocks=blocks,
        expected_benchmark_gas_used=expected_gas_used,
    )


def create_sload_executor(key_warm: bool) -> IteratingBytecode:
    """
    Create a contract that executes SLOAD benchmark operations.

    - CALLDATA[0..32] start slot (index)
    - CALLDATA[32..64] ending slot (end_slot)

    Returns: IteratingBytecode representing the benchmark executor.
    """
    setup = (
        Op.CALLDATALOAD(32)  # end_slot
        + Op.CALLDATALOAD(0)  # start_slot = counter
    )
    # [counter, end_slot]

    loop = Bytecode()
    loop += Op.JUMPDEST
    # Loop Body: Load from current slot
    loop += Op.DUP1  # [counter, counter, end_slot]
    loop += Op.SLOAD(key_warm=key_warm)
    loop += Op.POP  # [counter, end_slot]

    # Loop Post: Increment Counter
    loop += Op.PUSH1(1)
    loop += Op.ADD
    # [counter + 1, end_slot]

    # Loop Condition: Counter < end_slot
    loop += Op.DUP2  # [end_slot, counter + 1, end_slot]
    loop += Op.DUP2  # [counter + 1, end_slot, counter + 1, end_slot]
    loop += Op.LT  # [counter + 1 < end_slot, counter + 1, end_slot]
    loop += Op.PUSH1(len(setup))
    loop += Op.JUMPI
    # [counter + 1, end_slot]

    cleanup = Bytecode()
    cleanup += Op.STOP

    return IteratingBytecode(setup=setup, iterating=loop, cleanup=cleanup)


@pytest.mark.parametrize("access_warm", [True, False])
@pytest.mark.parametrize("storage_keys_pre_set", [True, False])
def test_storage_sload_benchmark(
    benchmark_test: BenchmarkTestFiller,
    fork: Fork,
    pre: Alloc,
    tx_gas_limit: int,
    gas_benchmark_value: int,
    access_warm: bool,
    storage_keys_pre_set: bool,
) -> None:
    """
    Benchmark SLOAD instruction with various configurations.

    Uses EIP-7702 delegation. The authority EOA delegates to:
    - StorageInitializer: storage[i] = 1 (if storage_keys_pre_set)
    - BenchmarkExecutor: performs the benchmark operation (SLOAD)

    Variants:
    - access_warm: Warm storage slots via access list
    - storage_keys_pre_set: Whether the storage keys are pre-set
    """
    # Initial Storage Construction
    initializer_code = create_sstore_initializer(init_val=1)
    initializer_addr = pre.deploy_contract(code=initializer_code)

    # Actual Benchmark Execution
    executor_code = create_sload_executor(key_warm=access_warm)
    executor_addr = pre.deploy_contract(code=executor_code)

    authority = pre.fund_eoa(amount=0)
    authority_nonce = 0

    delegation_sender = pre.fund_eoa()

    calldata_gen = partial(executor_calldata_generator)
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
        )
    )

    # Setup phase: initialize storage slots (if storage_keys_pre_set)
    with TestPhaseManager.setup():
        blocks = build_delegated_storage_setup(
            pre=pre,
            fork=fork,
            tx_gas_limit=tx_gas_limit,
            needs_init=storage_keys_pre_set,
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
            )
        )

        expected_gas_used = sum(tx.gas_cost for tx in exec_txs)

    blocks.append(Block(txs=exec_txs))

    benchmark_test(
        pre=pre,
        blocks=blocks,
        expected_benchmark_gas_used=expected_gas_used,
    )


@pytest.mark.parametrize("storage_keys_pre_set", [False, True])
def test_storage_sload_same_key_benchmark(
    benchmark_test: BenchmarkTestFiller,
    storage_keys_pre_set: bool,
) -> None:
    """
    Benchmark SLOAD instruction when loading the same key over and over.

    Variants:
    - storage_keys_pre_set: The key is pre-set to a non-zero value.
    """
    contract_storage = Storage()
    if storage_keys_pre_set:
        contract_storage[1] = 1

    benchmark_test(
        target_opcode=Op.SLOAD,
        code_generator=JumpLoopGenerator(
            setup=Op.PUSH1(1) if storage_keys_pre_set else Op.PUSH0,
            attack_block=Op.SLOAD,
            contract_storage=contract_storage,
        ),
    )
