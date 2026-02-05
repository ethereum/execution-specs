"""
abstract: BloatNet single-opcode benchmark cases for state-related operations.

   These tests focus on individual EVM opcodes (SLOAD, SSTORE) to measure
   their performance when accessing many storage slots across pre-deployed
   contracts. Unlike multi-opcode tests, these isolate single operations
   to benchmark specific state-handling bottlenecks.
"""

import json
import math
from pathlib import Path
from typing import Tuple

import pytest
from execution_testing import (
    AccessList,
    Account,
    Address,
    Alloc,
    AuthorizationTuple,
    BenchmarkTestFiller,
    Block,
    BlockchainTestFiller,
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

REFERENCE_SPEC_GIT_PATH = "DUMMY/bloatnet.md"
REFERENCE_SPEC_VERSION = "1.0"

# ERC20 function selectors
BALANCEOF_SELECTOR = 0x70A08231  # balanceOf(address)
APPROVE_SELECTOR = 0x095EA7B3  # approve(address,uint256)
ALLOWANCE_SELECTOR = 0xDD62ED3E  # allowance(address,address)

# Load token names from stubs.json for test parametrization
_STUBS_FILE = Path(__file__).parent / "stubs.json"
with open(_STUBS_FILE) as f:
    _STUBS = json.load(f)

# Extract unique token names for each test type
SLOAD_TOKENS = [
    k.replace("test_sload_empty_erc20_balanceof_", "")
    for k in _STUBS.keys()
    if k.startswith("test_sload_empty_erc20_balanceof_")
]
SSTORE_TOKENS = [
    k.replace("test_sstore_erc20_approve_", "")
    for k in _STUBS.keys()
    if k.startswith("test_sstore_erc20_approve_")
]


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


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize("token_name", SLOAD_TOKENS)
def test_sload_empty_erc20_balanceof(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    token_name: str,
) -> None:
    """
    BloatNet SLOAD benchmark using ERC20 balanceOf queries on random
    addresses.

    This test:
    1. Uses a single ERC20 contract specified by token_name parameter
    2. Allocates full gas budget to that contract
    3. Queries balanceOf() incrementally starting by 0 and increasing by 1
       (thus forcing SLOADs to non-existing addresses)
    4. Splits into multiple transactions if gas_benchmark_value > tx_gas_limit
       (EIP-7825 compliance)
    """
    stub_name = f"test_sload_empty_erc20_balanceof_{token_name}"
    gas_costs = fork.gas_costs()

    # Calculate gas costs
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(calldata=b"")

    # Fixed overhead per iteration (loop mechanics, independent of warm/cold)
    loop_overhead = (
        # Attack contract loop overhead
        gas_costs.G_VERY_LOW * 2  # MLOAD counter (3*2)
        + gas_costs.G_VERY_LOW * 2  # MSTORE selector (3*2)
        + gas_costs.G_VERY_LOW * 3  # MLOAD + MSTORE address (3*3)
        + gas_costs.G_BASE  # POP (2)
        + gas_costs.G_BASE * 3  # SUB + MLOAD + MSTORE counter decrement
        + gas_costs.G_BASE * 2  # ISZERO * 2 for loop condition (2*2)
        + gas_costs.G_MID  # JUMPI (8)
    )

    # ERC20 internal gas (same for all calls)
    erc20_internal_gas = (
        gas_costs.G_VERY_LOW  # PUSH4 selector (3)
        + gas_costs.G_BASE  # EQ selector match (2)
        + gas_costs.G_MID  # JUMPI to function (8)
        + gas_costs.G_JUMPDEST  # JUMPDEST at function start (1)
        + gas_costs.G_VERY_LOW * 2  # CALLDATALOAD arg (3*2)
        + gas_costs.G_KECCAK_256  # keccak256 static (30)
        + gas_costs.G_KECCAK_256_WORD * 2  # keccak256 dynamic 64 bytes
        + gas_costs.G_COLD_SLOAD  # Cold SLOAD - always cold
        + gas_costs.G_VERY_LOW * 3  # MSTORE result + RETURN setup (3*3)
        # RETURN costs 0 gas
    )

    # First call is COLD (2600), subsequent are WARM (100)
    warm_call_cost = (
        loop_overhead + gas_costs.G_WARM_ACCOUNT_ACCESS + erc20_internal_gas
    )
    cold_warm_diff = (
        gas_costs.G_COLD_ACCOUNT_ACCESS - gas_costs.G_WARM_ACCOUNT_ACCESS
    )

    # Deploy ERC20 contract using stub
    # In execute mode: stub points to already-deployed contract on chain
    # In fill mode: empty bytecode is deployed as placeholder
    erc20_address = pre.deploy_contract(
        code=Bytecode(),
        stub=stub_name,
    )

    # Calculate number of transactions needed (EIP-7825 compliance)
    num_txs = max(1, math.ceil(gas_benchmark_value / tx_gas_limit))

    # Calculate total calls based on full gas budget
    total_available_gas = gas_benchmark_value - (intrinsic_gas * num_txs)
    total_calls = int((total_available_gas - cold_warm_diff) // warm_call_cost)
    calls_per_tx = total_calls // num_txs

    # Log test requirements
    print(
        f"Token: {token_name}, "
        f"Total gas budget: {gas_benchmark_value / 1_000_000:.1f}M gas, "
        f"{total_calls} balanceOf calls across {num_txs} transaction(s)."
    )

    # Build transactions
    txs = []
    post = {}
    calls_remaining = total_calls

    for i in range(num_txs):
        # Last tx gets remaining calls
        tx_calls = calls_per_tx if i < num_txs - 1 else calls_remaining
        calls_remaining -= tx_calls

        # Build attack code for this transaction
        attack_code: Bytecode = (
            Op.JUMPDEST  # Entry point
            + Op.MSTORE(offset=0, value=BALANCEOF_SELECTOR)
            + Op.MSTORE(offset=32, value=tx_calls)
            + While(
                condition=Op.MLOAD(32) + Op.ISZERO + Op.ISZERO,
                body=(
                    Op.CALL(
                        address=erc20_address,
                        value=0,
                        args_offset=28,
                        args_size=36,
                        ret_offset=0,
                        ret_size=0,
                    )
                    + Op.POP
                    + Op.MSTORE(offset=32, value=Op.SUB(Op.MLOAD(32), 1))
                ),
            )
        )

        # Deploy attack contract for this tx
        attack_address = pre.deploy_contract(code=attack_code)

        # Calculate gas for this transaction
        this_tx_gas = min(
            tx_gas_limit, gas_benchmark_value - (i * tx_gas_limit)
        )

        txs.append(
            Transaction(
                to=attack_address,
                gas_limit=this_tx_gas,
                sender=pre.fund_eoa(),
            )
        )

        # Add to post-state
        post[attack_address] = Account(storage={})

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=txs)],
        post=post,
    )


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize("token_name", SSTORE_TOKENS)
def test_sstore_erc20_approve(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    token_name: str,
) -> None:
    """
    BloatNet SSTORE benchmark using ERC20 approve to write to storage.

    This test:
    1. Uses a single ERC20 contract specified by token_name parameter
    2. Allocates full gas budget to that contract
    3. Calls approve(spender, amount) incrementally (counter as spender)
    4. Forces SSTOREs to allowance mapping storage slots
    5. Splits into multiple transactions if gas_benchmark_value > tx_gas_limit
       (EIP-7825 compliance)
    """
    stub_name = f"test_sstore_erc20_approve_{token_name}"
    gas_costs = fork.gas_costs()

    # Calculate gas costs
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(calldata=b"")

    # Fixed overhead per iteration (loop mechanics, independent of warm/cold)
    loop_overhead = (
        # Attack contract loop body operations
        gas_costs.G_VERY_LOW  # MSTORE selector at memory[32] (3)
        + gas_costs.G_LOW  # MLOAD counter (5)
        + gas_costs.G_VERY_LOW  # MSTORE spender at memory[64] (3)
        + gas_costs.G_BASE  # POP call result (2)
        # Counter decrement: MSTORE(0, SUB(MLOAD(0), 1))
        + gas_costs.G_LOW  # MLOAD counter (5)
        + gas_costs.G_VERY_LOW  # PUSH1 1 (3)
        + gas_costs.G_VERY_LOW  # SUB (3)
        + gas_costs.G_VERY_LOW  # MSTORE counter back (3)
        # While loop condition check
        + gas_costs.G_LOW  # MLOAD counter (5)
        + gas_costs.G_BASE  # ISZERO (2)
        + gas_costs.G_BASE  # ISZERO (2)
        + gas_costs.G_MID  # JUMPI back to loop start (8)
    )

    # ERC20 internal gas (same for all calls)
    # Note: SSTORE cost is 22100 for cold slot, zero-to-non-zero
    # (20000 base + 2100 cold access)
    erc20_internal_gas = (
        gas_costs.G_VERY_LOW  # PUSH4 selector (3)
        + gas_costs.G_BASE  # EQ selector match (2)
        + gas_costs.G_MID  # JUMPI to function (8)
        + gas_costs.G_JUMPDEST  # JUMPDEST at function start (1)
        + gas_costs.G_VERY_LOW  # CALLDATALOAD spender (3)
        + gas_costs.G_VERY_LOW  # CALLDATALOAD amount (3)
        + gas_costs.G_KECCAK_256  # keccak256 static (30)
        + gas_costs.G_KECCAK_256_WORD * 2  # keccak256 dynamic 64 bytes
        + gas_costs.G_COLD_SLOAD  # Cold SLOAD for allowance check (2100)
        + gas_costs.G_STORAGE_SET  # SSTORE base cost (20000)
        + gas_costs.G_COLD_SLOAD  # Additional cold storage access (2100)
        + gas_costs.G_VERY_LOW  # PUSH1 1 for return value (3)
        + gas_costs.G_VERY_LOW  # MSTORE return value (3)
        + gas_costs.G_VERY_LOW  # PUSH1 32 for return size (3)
        + gas_costs.G_VERY_LOW  # PUSH1 0 for return offset (3)
        # RETURN costs 0 gas
    )

    # First call is COLD (2600), subsequent are WARM (100)
    warm_call_cost = (
        loop_overhead + gas_costs.G_WARM_ACCOUNT_ACCESS + erc20_internal_gas
    )
    cold_warm_diff = (
        gas_costs.G_COLD_ACCOUNT_ACCESS - gas_costs.G_WARM_ACCOUNT_ACCESS
    )

    # Deploy ERC20 contract using stub
    erc20_address = pre.deploy_contract(
        code=Bytecode(),
        stub=stub_name,
    )

    # Calculate number of transactions needed (EIP-7825 compliance)
    num_txs = max(1, math.ceil(gas_benchmark_value / tx_gas_limit))

    # Calculate total calls based on full gas budget
    total_available_gas = gas_benchmark_value - (intrinsic_gas * num_txs)
    total_calls = int((total_available_gas - cold_warm_diff) // warm_call_cost)
    calls_per_tx = total_calls // num_txs

    # Log test requirements
    print(
        f"Token: {token_name}, "
        f"Total gas budget: {gas_benchmark_value / 1_000_000:.1f}M gas, "
        f"{total_calls} approve calls across {num_txs} transaction(s)."
    )

    # Build transactions
    txs = []
    post = {}
    calls_remaining = total_calls

    for i in range(num_txs):
        # Last tx gets remaining calls
        tx_calls = calls_per_tx if i < num_txs - 1 else calls_remaining
        calls_remaining -= tx_calls

        # Build attack code for this transaction
        attack_code: Bytecode = (
            Op.JUMPDEST  # Entry point
            + Op.MSTORE(offset=0, value=APPROVE_SELECTOR)
            + Op.MSTORE(offset=32, value=tx_calls)
            + While(
                condition=Op.MLOAD(32) + Op.ISZERO + Op.ISZERO,
                body=(
                    # Store spender at memory[64] (counter as spender/amount)
                    Op.MSTORE(offset=64, value=Op.MLOAD(32))
                    # Call approve(spender, amount) on ERC20 contract
                    + Op.CALL(
                        address=erc20_address,
                        value=0,
                        args_offset=28,
                        args_size=68,
                        ret_offset=0,
                        ret_size=0,
                    )
                    + Op.POP
                    + Op.MSTORE(offset=32, value=Op.SUB(Op.MLOAD(32), 1))
                ),
            )
        )

        # Deploy attack contract for this tx
        attack_address = pre.deploy_contract(code=attack_code)

        # Calculate gas for this transaction
        this_tx_gas = min(
            tx_gas_limit, gas_benchmark_value - (i * tx_gas_limit)
        )

        txs.append(
            Transaction(
                to=attack_address,
                gas_limit=this_tx_gas,
                sender=pre.fund_eoa(),
            )
        )

        # Add to post-state
        post[attack_address] = Account(storage={})

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=txs)],
        post=post,
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
    # Stack after SUB: [index, current] where current goes from index+num-1 down to index
    loop = (
        Op.JUMPDEST
        + Op.PUSH1(1)  # [index, current, 1]
        + Op.SWAP1  # [index, 1, current]
        + Op.SUB  # [index, current - 1]
        + Op.SSTORE(
            Op.DUP1,  # key = current - 1 (top of stack after decrement)
            init_val,
            key_warm=False,
            original_value=0,
            current_value=0,
            new_value=init_val,
        )
        # After SSTORE: [index, current - 1]
        # Continue while current - 1 > index
        + Op.JUMPI(len(prefix), Op.GT(Op.DUP1, Op.DUP2))
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

    loop = Op.JUMPDEST
    # Loop Body: Store Value at Start Slot + Counter
    if sloads_before_sstore:
        loop += Op.DUP1  # [counter, counter, value, end_slot]
        loop += Op.SLOAD(key_warm=key_warm)
        loop += Op.POP
        loop += Op.DUP2  # [value, counter, value, end_slot]
        loop += Op.DUP2  # [counter, value, counter, value, end_slot]
        loop += Op.SSTORE(
            key_warm=True,
            original_value=original_value,
            current_value=original_value,
            new_value=new_value,
        )
    else:
        loop += Op.DUP2  # [value, counter, value, end_slot]
        loop += Op.DUP2  # [counter, value, counter, value, end_slot]
        loop += Op.SSTORE(  # STORAGE[counter, value] = value
            key_warm=key_warm,
            original_value=original_value,
            current_value=original_value,
            new_value=new_value,
        )

    # Loop Post: Increment Counter
    loop += Op.PUSH1(1)
    loop += Op.ADD
    # [counter + 1, value, end_slot]

    # Loop Condition: Counter < end_slot
    loop += Op.DUP3  # [end_slot, counter + 1, value, end_slot]
    loop += Op.DUP2  # [counter + 1, end_slot, counter + 1, value, end_slot]
    loop += Op.LT  # [counter + 1 < end_slot, counter + 1, value, end_slot]
    loop += Op.ISZERO
    loop += Op.ISZERO
    loop += Op.PUSH1(len(setup))
    loop += Op.JUMPI
    # [counter + 1, value, end_slot]

    cleanup = Op.STOP

    return IteratingBytecode(setup=setup, iterating=loop, cleanup=cleanup)


def sstore_helper_contract(
    *,
    sloads_before_sstore: bool,
    key_warm: bool,
    original_value: int,
    new_value: int,
) -> Tuple[Bytecode, Bytecode, Bytecode]:
    """
    Storage contract for benchmark slot access.

    # Calldata Layout:
    # - CALLDATA[0..31]: Starting slot
    # - CALLDATA[32..63]: Ending slot
    # - CALLDATA[64..95]: Value to write

    Returns:
    - setup: Bytecode of the setup of the contract
    - loop: Bytecode of the loop of the contract
    - cleanup: Bytecode of the cleanup of the contract

    """
    setup = Bytecode()
    loop = Bytecode()
    cleanup = Bytecode()

    setup += (
        Op.CALLDATALOAD(32)  # end_slot
        + Op.CALLDATALOAD(64)  # value
        + Op.CALLDATALOAD(0)  # start_slot = counter
    )
    # [counter, value, end_slot]

    loop += Op.JUMPDEST
    # Loop Body: Store Value at Start Slot + Counter
    if sloads_before_sstore:
        loop += Op.DUP1  # [counter, counter, value, end_slot]
        loop += Op.SLOAD(key_warm=key_warm)
        loop += Op.POP
        loop += Op.DUP2  # [value, counter, value, end_slot]
        loop += Op.DUP2  # [counter, value, counter, value, end_slot]
        loop += Op.SSTORE(
            key_warm=True,
            original_value=original_value,
            new_value=new_value,
        )
    else:
        loop += Op.DUP2  # [value, counter, value, end_slot]
        loop += Op.DUP2  # [counter, value, counter, value, end_slot]
        loop += Op.SSTORE(  # STORAGE[counter, value] = value
            key_warm=key_warm,
            original_value=original_value,
            new_value=new_value,
        )

    # Loop Post: Increment Counter
    loop += Op.PUSH1(1)
    loop += Op.ADD
    # [counter + 1, value, end_slot]

    # Loop Condition: Counter < Num Slots
    loop += Op.DUP3  # [end_slot, counter + 1, value, end_slot]
    loop += Op.DUP2  # [counter + 1, end_slot, counter + 1, value, end_slot]
    loop += Op.LT  # [counter + 1 < end_slot, counter + 1, value, end_slot]
    loop += Op.ISZERO
    loop += Op.ISZERO
    loop += Op.PUSH1(len(setup))
    loop += Op.JUMPI
    # [counter + 1, value, end_slot]

    # Cleanup: Stop
    cleanup += Op.STOP

    return setup, loop, cleanup


@pytest.mark.parametrize("use_access_list", [True, False])
@pytest.mark.parametrize("sloads_before_sstore", [True, False])
@pytest.mark.parametrize(
    "initial_value,write_value",
    [
        pytest.param(0, 0, id="zero_to_zero"),
        pytest.param(0, 0xDEADBEEF, id="zero_to_nonzero"),
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
    use_access_list: bool,
    sloads_before_sstore: bool,
    initial_value: int,
    write_value: int,
) -> None:
    """
    Benchmark SSTORE instruction with various configurations using EIP-7702 delegation.

    The authority EOA delegates to:
    - StorageInitializer: storage[i] = initial_value for each slot (if initial_value != 0)
    - BenchmarkExecutor: performs the benchmark operation (SSTORE)

    Variants:
    - use_access_list: Warm storage slots via access list
    - sloads_before_sstore: Number of SLOADs per slot before SSTORE
    - initial_value/write_value: Storage transitions
      (zero_to_zero, zero_to_nonzero, nonzero_to_zero, nonzero_to_nonzero)
    """
    executor_code = create_sstore_executor(
        sloads_before_sstore=sloads_before_sstore,
        key_warm=use_access_list,
        original_value=initial_value,
        new_value=write_value,
    )
    initializer_code = create_sstore_initializer(initial_value)

    executor_addr = pre.deploy_contract(code=executor_code)
    initializer_addr = pre.deploy_contract(code=initializer_code)

    # Calldata generator for the executor
    def executor_calldata_generator(
        iteration_count: int, start_iteration: int
    ) -> bytes:
        return (
            Hash(start_iteration)
            + Hash(start_iteration + iteration_count)
            + Hash(write_value)
        )

    # Calldata generator for the initializer
    def initializer_calldata_generator(
        iteration_count: int, start_iteration: int
    ) -> bytes:
        return Hash(start_iteration) + Hash(iteration_count)

    # Number of slots that can be processed in the execution phase
    num_target_slots = sum(
        executor_code.tx_iterations_by_gas_limit(
            fork=fork,
            gas_limit=gas_benchmark_value,
            calldata=executor_calldata_generator,
            start_iteration=1,
        )
    )

    blocks = []
    delegation_sender = pre.fund_eoa()

    # Single authority EOA for all storage operations
    authority = pre.fund_eoa(amount=0)
    authority_nonce = 0

    # Setup phase: initialize storage slots (only if initial_value != 0)
    with TestPhaseManager.setup():
        setup_txs = []

        if initial_value != 0:
            # Authorize to initializer
            setup_txs.append(
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
            )
            authority_nonce += 1

            # Run initialization transactions
            setup_txs += list(
                initializer_code.transactions_by_total_iteration_count(
                    fork=fork,
                    total_iterations=num_target_slots,
                    sender=pre.fund_eoa(),
                    to=authority,
                    start_iteration=1,
                    calldata=initializer_calldata_generator,
                )
            )

        # Authorize to executor
        setup_txs.append(
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
        )

        blocks.append(Block(txs=setup_txs))

    # Access list generator for warming storage slots
    def access_list_generator(
        iteration_count: int, start_iteration: int
    ) -> list[AccessList] | None:
        if use_access_list:
            storage_keys = [
                Hash(i)
                for i in range(
                    start_iteration, start_iteration + iteration_count
                )
            ]
            return [
                AccessList(
                    address=authority,
                    storage_keys=storage_keys,
                )
            ]
        return None

    # Execution phase: run benchmark
    expected_gas_used = 0

    with TestPhaseManager.execution():
        exec_txs = list(
            executor_code.transactions_by_gas_limit(
                fork=fork,
                gas_limit=gas_benchmark_value,
                sender=pre.fund_eoa(),
                to=authority,
                calldata=executor_calldata_generator,
                start_iteration=1,
                access_list=access_list_generator,
            )
        )

        # Calculate expected gas accounting for refunds
        refund_per_iteration = executor_code.iterating.refund(fork)

        for exec_tx in exec_txs:
            tx_gas_cost = exec_tx.gas_cost
            if refund_per_iteration > 0:
                # Estimate iteration count
                per_iteration_gross = executor_code.iterating.gas_cost(fork)
                overhead = executor_code.setup.gas_cost(
                    fork
                ) + executor_code.cleanup.gas_cost(fork)
                iteration_count = (
                    tx_gas_cost - overhead
                ) // per_iteration_gross
                # Apply 20% refund cap
                total_refund = refund_per_iteration * iteration_count
                max_refund = tx_gas_cost // 5
                actual_refund = min(total_refund, max_refund)
                expected_gas_used += tx_gas_cost - actual_refund
            else:
                expected_gas_used += tx_gas_cost

    blocks.append(Block(txs=exec_txs))

    benchmark_test(
        blocks=blocks,
        expected_benchmark_gas_used=expected_gas_used,
    )


def sload_helper_contract(
    *, key_warm: bool
) -> Tuple[Bytecode, Bytecode, Bytecode]:
    """
    Storage contract for benchmark slot access.

    # Calldata Layout:
    # - CALLDATA[0..31]: Starting slot
    # - CALLDATA[32..63]: Ending slot
    """
    setup = Bytecode()
    loop = Bytecode()
    cleanup = Bytecode()

    setup += Op.CALLDATALOAD(32)  # end_slot
    setup += Op.CALLDATALOAD(0)  # start slot = counter
    # [counter, end_slot]

    loop += Op.JUMPDEST

    # Loop Body: Load key from storage
    loop += Op.DUP1
    loop += Op.SLOAD(key_warm=key_warm)
    loop += Op.POP
    # [counter, end_slot]

    # Loop Post: Increment Counter
    loop += Op.PUSH1(1)
    loop += Op.ADD
    # [counter + 1, end_slot]

    # Loop Condition: Counter < Num Slots
    loop += Op.DUP2  # [end_slot, counter + 1, end_slot]
    loop += Op.DUP2  # [counter + 1, end_slot, counter + 1, end_slot]
    loop += Op.LT  # [counter + 1 < end_slot, counter + 1, end_slot]
    loop += Op.ISZERO
    loop += Op.ISZERO
    loop += Op.PUSH1(len(setup))
    loop += Op.JUMPI
    # [counter + 1, value, end_slot]

    # Cleanup: Stop
    cleanup += Op.STOP

    return setup, loop, cleanup


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

    loop = Op.JUMPDEST
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
    loop += Op.ISZERO
    loop += Op.ISZERO
    loop += Op.PUSH1(len(setup))
    loop += Op.JUMPI
    # [counter + 1, end_slot]

    cleanup = Op.STOP

    return IteratingBytecode(setup=setup, iterating=loop, cleanup=cleanup)


@pytest.mark.parametrize("warm_slots", [False, True])
@pytest.mark.parametrize("storage_keys_pre_set", [False, True])
def test_storage_sload_benchmark(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    warm_slots: bool,
    storage_keys_pre_set: bool,
    tx_gas_limit: int,
) -> None:
    """
    Benchmark SLOAD instruction with various configurations using EIP-7702 delegation.

    The authority EOA delegates to:
    - StorageInitializer: storage[i] = 1 for each slot (if storage_keys_pre_set)
    - BenchmarkExecutor: performs the benchmark operation (SLOAD)

    Variants:
    - warm_slots: Warm storage slots via access list
    - storage_keys_pre_set: Whether the storage keys are pre-set
    """
    executor_code = create_sload_executor(key_warm=warm_slots)
    initializer_code = create_sstore_initializer(init_val=1)

    executor_addr = pre.deploy_contract(code=executor_code)
    initializer_addr = pre.deploy_contract(code=initializer_code)

    # Calldata generator for the executor
    def executor_calldata_generator(
        iteration_count: int, start_iteration: int
    ) -> bytes:
        return Hash(start_iteration) + Hash(start_iteration + iteration_count)

    # Calldata generator for the initializer
    def initializer_calldata_generator(
        iteration_count: int, start_iteration: int
    ) -> bytes:
        return Hash(start_iteration) + Hash(iteration_count)

    # Number of slots that can be processed in the execution phase
    num_target_slots = sum(
        executor_code.tx_iterations_by_gas_limit(
            fork=fork,
            gas_limit=gas_benchmark_value,
            calldata=executor_calldata_generator,
            start_iteration=1,
        )
    )

    blocks = []
    delegation_sender = pre.fund_eoa()

    # Single authority EOA for all storage operations
    authority = pre.fund_eoa(amount=0)
    authority_nonce = 0

    # Setup phase: initialize storage slots (only if storage_keys_pre_set)
    with TestPhaseManager.setup():
        setup_txs = []

        if storage_keys_pre_set:
            # Authorize to initializer
            setup_txs.append(
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
            )
            authority_nonce += 1

            # Run initialization transactions
            setup_txs += list(
                initializer_code.transactions_by_total_iteration_count(
                    fork=fork,
                    total_iterations=num_target_slots,
                    sender=pre.fund_eoa(),
                    to=authority,
                    start_iteration=1,
                    calldata=initializer_calldata_generator,
                )
            )

        # Authorize to executor
        setup_txs.append(
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
        )

        blocks.append(Block(txs=setup_txs))

    # Access list generator for warming storage slots
    def access_list_generator(
        iteration_count: int, start_iteration: int
    ) -> list[AccessList] | None:
        if warm_slots:
            storage_keys = [
                Hash(i)
                for i in range(
                    start_iteration, start_iteration + iteration_count
                )
            ]
            return [
                AccessList(
                    address=authority,
                    storage_keys=storage_keys,
                )
            ]
        return None

    # Execution phase: run benchmark
    expected_gas_used = 0

    with TestPhaseManager.execution():
        exec_txs = list(
            executor_code.transactions_by_gas_limit(
                fork=fork,
                gas_limit=gas_benchmark_value,
                sender=pre.fund_eoa(),
                to=authority,
                calldata=executor_calldata_generator,
                start_iteration=1,
                access_list=access_list_generator,
            )
        )

        for exec_tx in exec_txs:
            expected_gas_used += exec_tx.gas_cost

    blocks.append(Block(txs=exec_txs))

    benchmark_test(
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
