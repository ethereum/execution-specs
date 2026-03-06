"""
abstract: BloatNet single-opcode benchmark cases for state-related operations.

   These tests focus on individual EVM opcodes (SLOAD, SSTORE) to measure
   their performance when accessing many storage slots across pre-deployed
   contracts. Unlike multi-opcode tests, these isolate single operations
   to benchmark specific state-handling bottlenecks.
"""

from enum import Enum, auto
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
    CreatePreimageLayout,
    Fork,
    Hash,
    IteratingBytecode,
    JumpLoopGenerator,
    Op,
    SequentialAddressLayout,
    Storage,
    TestPhaseManager,
    Transaction,
    While,
    keccak256,
)

from tests.benchmark.stateful.helpers import (
    ALLOWANCE_SELECTOR,
    APPROVE_SELECTOR,
    BALANCEOF_SELECTOR,
    DECREMENT_COUNTER_CONDITION,
    MINT_SELECTOR,
    SLOAD_TOKENS,
    SSTORE_MINT_TOKENS,
    SSTORE_TOKENS,
    CacheStrategy,
    build_cache_strategy_blocks,
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
@pytest.mark.parametrize("existing_slots", [False, True])
@pytest.mark.parametrize("cache_strategy", list(CacheStrategy))
def test_sload_erc20_balanceof(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    token_name: str,
    existing_slots: bool,
    cache_strategy: CacheStrategy,
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

    call_balance_of = Op.POP(
        Op.CALL(
            address=erc20_address,
            value=0,
            args_offset=32 - 4,
            args_size=32 + 4,
            ret_offset=0,
            ret_size=0,
            # gas accounting
            address_warm=True,
        )
    )

    cache_loop = (
        call_balance_of
        if cache_strategy == CacheStrategy.CACHE_TX
        else Bytecode()
    )

    loop = While(
        body=call_balance_of
        # Do the same call again for the cached variant
        + cache_loop
        + Op.MSTORE(32, Op.ADD(Op.MLOAD(32), 1)),
        condition=DECREMENT_COUNTER_CONDITION,
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
        + Op.MSTORE(0, Op.CALLDATALOAD(4))
        + Op.MSTORE(32, 0)
        + Op.MSTORE(
            0,
            Op.SLOAD(
                Op.SHA3(
                    0,
                    64,
                    # gas accounting
                    data_size=64,
                    old_memory_size=0,
                    new_memory_size=64,
                )
            ),
        )
        + Op.RETURN(0, 32)
    )

    function_dispatch_cost = function_dispatch.gas_cost(fork)

    # Transaction Loops
    txs = []
    cache_txs = []
    gas_remaining = gas_benchmark_value
    # Start at 1 (ERC20 bloater writes the balance of address to the slot)
    # or start at keccak256("random") for non-existing slots
    slot_offset = (
        1
        if existing_slots
        else 0xA4896A3F93BF4BF58378E579F3CF193BB4AF1022AF7D2089F37D8BAE7157B85F
    )

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

        if cache_strategy == CacheStrategy.CACHE_PREVIOUS_BLOCK:
            with TestPhaseManager.setup():
                # For block-level caching,
                # we need to warm the slot in a separate transaction
                cache_txs.append(
                    Transaction(
                        gas_limit=gas_available,
                        data=calldata,
                        to=attack_contract_address,
                        sender=pre.fund_eoa(),
                        access_list=access_list,
                    )
                )

        with TestPhaseManager.execution():
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

    blocks = build_cache_strategy_blocks(cache_strategy, txs, cache_txs)
    # FIXME: this should not use gas validation as this one should OOG
    # If it does not OOG, the gas calculation is too high, it should be too low
    benchmark_test(pre=pre, blocks=blocks, skip_gas_used_validation=True)


@pytest.mark.parametrize("cache_strategy", list(CacheStrategy))
@pytest.mark.parametrize("token_name", SSTORE_TOKENS)
def test_sstore_erc20_approve(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    token_name: str,
    cache_strategy: CacheStrategy,
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

    call_approve = Op.MSTORE(64, Op.MLOAD(32)) + Op.POP(
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

    if cache_strategy == CacheStrategy.CACHE_TX:
        # Call allowance(ADDRESS, spender) to warm the allowance
        # storage slot that approve will later write to.
        # Memory: save spender→[64], put ADDRESS→[32],
        # set allowance selector, call, then restore.
        cache_warmup = (
            Op.MSTORE(64, Op.MLOAD(32))
            + Op.MSTORE(32, Op.ADDRESS)
            + Op.MSTORE(0, ALLOWANCE_SELECTOR)
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
            + Op.MSTORE(0, APPROVE_SELECTOR)
            + Op.MSTORE(32, Op.MLOAD(64))
        )
    else:
        cache_warmup = Bytecode()

    loop = While(
        body=cache_warmup
        + call_approve
        + Op.MSTORE(32, Op.ADD(Op.MLOAD(32), 1)),
        condition=DECREMENT_COUNTER_CONDITION,
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

    # This dispatch is something close to the minimal amount
    # of code to run for a contract only implementing approve
    # It will therefore greatly underestimate the gas of any ERC20
    # contract because all of them have much more overhead in practice
    # (also function selector at the entry point of the contract)
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
        + Op.MSTORE(
            32,
            Op.SHA3(
                0,
                64,
                # gas accounting
                data_size=64,
                old_memory_size=0,
                new_memory_size=64,
            ),
        )
        + Op.MSTORE(0, Op.CALLDATALOAD(4))
        + Op.SHA3(
            0,
            64,
            # gas accounting
            data_size=64,
        )
        + (
            Op.DUP1
            + Op.SLOAD.with_metadata(key_warm=False)
            + Op.POP
            + Op.SSTORE.with_metadata(key_warm=True)
            if cache_strategy == CacheStrategy.CACHE_TX
            else Op.SSTORE.with_metadata(key_warm=False)
        )
        # Return true
        + Op.MSTORE(0, 1)
        + Op.RETURN(0, 32)
    )

    function_dispatch_cost = function_dispatch.gas_cost(fork)

    if cache_strategy == CacheStrategy.CACHE_TX:
        # Add allowance dispatch cost for the warmup call.
        # allowance(owner, spender) computes the same double-
        # keccak slot as approve but does SLOAD + RETURN.
        function_dispatch_allowance = (
            Op.PUSH4(ALLOWANCE_SELECTOR)
            + Op.EQ
            + Op.JUMPI
            + Op.JUMPDEST
            + Op.CALLDATALOAD(4)
            + Op.CALLDATALOAD(36)
            + Op.MSTORE(0, Op.CALLDATALOAD(4))
            + Op.MSTORE(32, 1)
            + Op.MSTORE(
                32,
                Op.SHA3(
                    0,
                    64,
                    # gas accounting
                    data_size=64,
                    old_memory_size=0,
                    new_memory_size=64,
                ),
            )
            + Op.MSTORE(0, Op.CALLDATALOAD(36))
            + Op.SHA3(
                0,
                64,
                # gas accounting
                data_size=64,
            )
            + Op.SLOAD
            + Op.PUSH0
            + Op.MSTORE
            + Op.RETURN(0, 32)
        )
        function_dispatch_cost += function_dispatch_allowance.gas_cost(fork)

    # Transaction Loops
    txs = []
    cache_txs = []
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

        if cache_strategy == CacheStrategy.CACHE_PREVIOUS_BLOCK:
            with TestPhaseManager.setup():
                cache_txs.append(
                    Transaction(
                        gas_limit=gas_available,
                        data=calldata,
                        to=attack_contract_address,
                        sender=pre.fund_eoa(),
                        access_list=access_list,
                    )
                )

        with TestPhaseManager.execution():
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

    blocks = build_cache_strategy_blocks(cache_strategy, txs, cache_txs)
    # TODO: this test can currently not estimate the gas used
    # It will also overestimate the num_calls it can make to an unknown
    # ERC20 contract and will therefore OOG
    # (this actually passes the gas check as it consumes all gas and
    # thus also the expected gas)
    # TODO: find out how to tackle this. We do not want to OOG
    # because the state root is part of the calculation
    # NOTE: this is not crucial for gas repricing tests
    # as the mint variant is used there.
    benchmark_test(
        pre=pre, blocks=blocks, skip_gas_used_validation=True
    )  # FIXME: temp skips


def build_call_memory_setup(
    selector: int,
    *args: Bytecode | int,
) -> Bytecode:
    """
    Build ABI-encoded memory layout for a contract call.

    MEM[0]  = selector (4 bytes, right-aligned in 32-byte word)
    MEM[32] = args[0]
    MEM[64] = args[1]  ...
    """
    bytecode = Op.MSTORE(
        0,
        selector,
        old_memory_size=0,
        new_memory_size=32,
    )
    for i, arg in enumerate(args):
        offset = 32 * (i + 1)
        bytecode += Op.MSTORE(
            offset,
            arg,
            old_memory_size=offset,
            new_memory_size=offset + 32,
        )
    return bytecode


def build_external_call(
    address: Address,
    num_args: int,
    *,
    address_warm: bool = True,
) -> Bytecode:
    """
    Build POP(CALL(...)) using standard ABI memory layout at offset 0.

    args_offset = 28 (selector at byte 28 of the 32-byte word)
    args_size   = 4 + 32 * num_args
    """
    return Op.POP(
        Op.CALL(
            address=address,
            value=0,
            args_offset=32 - 4,
            args_size=4 + 32 * num_args,
            ret_offset=0,
            ret_size=0,
            address_warm=address_warm,
        )
    )


@pytest.mark.parametrize("token_name", SSTORE_MINT_TOKENS)
@pytest.mark.parametrize("existing_slots", [False, True])
@pytest.mark.parametrize("cache_strategy", list(CacheStrategy))
@pytest.mark.parametrize("no_change", [False, True])
def test_sstore_erc20_mint(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    token_name: str,
    existing_slots: bool,
    cache_strategy: CacheStrategy,
    no_change: bool,
) -> None:
    """
    Benchmark SSTORE using ERC20 mint on bloatnet.
    This targets very specific code and is meant to be
    temporary for the gas repricings effort, to be replaced
    by a robust benchmark which does not depend on specific
    conditions like in this benchmark.
    This contract calls mint() on an ERC20 contract
    which supports the mint() function. It is intended
    to be used with ERC20 contracts bloated via bloatStorage.
    The mint will increase the total supply and the target account.
    """
    # The gas threshold is the minimum amount necessary
    # of gas to re-enter the While loop.
    # This must be high enough to ensure the tx
    # does not go out-of-gas.
    # This can be improved to an actual value by calculating
    # the gas used of the second call to the unknown ERC20 contract
    # and then adding the gas used for the code after the loop
    # (this can be calculated) as extra.
    gas_threshold = 100_000

    # Storage key to read and write address pointer to
    slot_offset = 0

    # Start at 1 for existing balance slots,
    # or at keccak256("random") for non-existing slots
    start_slot = (
        1
        if existing_slots
        else 0xA4896A3F93BF4BF58378E579F3CF193BB4AF1022AF7D2089F37D8BAE7157B85F
    )

    # Stub Account
    erc20_address = pre.deploy_contract(
        code=Bytecode(),
        stub=f"test_sstore_erc20_mint_{token_name}",
    )

    mint_amount = 0 if no_change else 1

    # MEM[0] = function selector
    # MEM[32] = target address
    # MEM[64] = mint amount
    mint_mem_setup = build_call_memory_setup(
        MINT_SELECTOR, Op.SLOAD(slot_offset), mint_amount
    )
    mint_erc20_call = build_external_call(erc20_address, 2)

    # MEM[0] = function selector
    # MEM[32] = target address
    balance_mem_setup = build_call_memory_setup(
        BALANCEOF_SELECTOR, Op.SLOAD(slot_offset)
    )
    balance_erc20_call = build_external_call(erc20_address, 1)

    attack_code = mint_erc20_call
    if cache_strategy == CacheStrategy.CACHE_TX:
        # Warm up storage slot via balanceOf
        attack_code = (
            Op.MSTORE(0, BALANCEOF_SELECTOR)
            + balance_erc20_call
            + Op.MSTORE(0, MINT_SELECTOR)
            + mint_erc20_call
        )

    loop_code = While(
        body=attack_code + Op.MSTORE(32, Op.ADD(Op.MLOAD(32), 1)),
        condition=Op.GT(Op.GAS, gas_threshold),
    )

    cleanup = Op.SSTORE(slot_offset, Op.MLOAD(32))

    # Contract Deployment
    attack_code = mint_mem_setup + loop_code + cleanup
    attack_contract_address = pre.deploy_contract(
        code=attack_code,
        storage={slot_offset: start_slot},
    )

    prewarm_contract_address = attack_contract_address
    if cache_strategy == CacheStrategy.CACHE_PREVIOUS_BLOCK:
        # TODO: calls balanceOf in previous block because
        # mint will change the balance of the account
        # This will SLOAD it in previous block and should
        # put this into cache.
        # Alternatively could also call mint(addr,0)
        # on that. Not sure which is better.
        # Call mint(addr, 0) because a nonzero value would
        # edit the value, and would also create a slot
        # if it was non-existent before. In attack block
        # in non-existent test it would then suddenly
        # be existent which is not the target scenario there.
        warmup_setup = balance_mem_setup

        warmup_attack_loop = While(
            body=balance_erc20_call + Op.MSTORE(32, Op.ADD(Op.MLOAD(32), 1)),
            condition=Op.GT(Op.GAS, gas_threshold),
        )

        warmup_block = warmup_setup + warmup_attack_loop + cleanup

        prewarm_contract_address = pre.deploy_contract(
            code=warmup_block,
            storage={slot_offset: start_slot},
        )

    # Transaction Loops
    gas_limits = []
    gas_remaining = gas_benchmark_value
    intrinsic_gas_cost = fork.transaction_intrinsic_cost_calculator()()
    while gas_remaining >= intrinsic_gas_cost + gas_threshold:
        gas_limit = min(gas_remaining, tx_gas_limit)
        gas_limits.append(gas_limit)
        gas_remaining -= gas_limit

    cache_txs: List[Transaction] = []
    if cache_strategy == CacheStrategy.CACHE_PREVIOUS_BLOCK:
        with TestPhaseManager.setup():
            cache_txs = [
                Transaction(
                    gas_limit=g,
                    to=prewarm_contract_address,
                    sender=pre.fund_eoa(),
                )
                for g in gas_limits
            ]

    with TestPhaseManager.execution():
        txs = [
            Transaction(
                gas_limit=g, to=attack_contract_address, sender=pre.fund_eoa()
            )
            for g in gas_limits
        ]

    blocks = build_cache_strategy_blocks(cache_strategy, txs, cache_txs)

    benchmark_test(
        pre=pre,
        blocks=blocks,
        # NOTE: this specifically targets bloatnet code so the
        # gas calculation could technically be done by inlining
        # the bytecode. This test is temporary and will be removed
        # after (or during) gas repricing effort is done. See
        # https://github.com/ethereum/execution-specs/issues/2411
        skip_gas_used_validation=True,
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
    - oscillation: X→0→X→0, alternates clean (2900) and dirty (100)
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
        )
    )

    # Setup phase: initialize all slots to initial_value
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
            )
        )

    blocks.append(Block(txs=exec_txs))

    benchmark_test(
        pre=pre,
        blocks=blocks,
        skip_gas_used_validation=True,
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


def account_access_params() -> list:
    """Generate (opcode, value_sent, account_mode) triples."""
    params = []

    for mode in AccountMode:
        for op in [Op.CALL, Op.CALLCODE]:
            params.append(pytest.param(op, 0, mode))
            params.append(pytest.param(op, 1, mode))

        for op in [Op.BALANCE, Op.STATICCALL, Op.DELEGATECALL]:
            params.append(pytest.param(op, 0, mode))

    for op in [Op.EXTCODECOPY, Op.EXTCODESIZE, Op.EXTCODEHASH]:
        for mode in [
            AccountMode.EXISTING_CONTRACT,
            AccountMode.NON_EXISTING_ACCOUNT,
        ]:
            params.append(pytest.param(op, 0, mode))

    return params


class AccountMode(Enum):
    """Target Account Mode."""

    EXISTING_CONTRACT = auto()
    EXISTING_EOA = auto()
    NON_EXISTING_ACCOUNT = auto()


@pytest.mark.repricing
@pytest.mark.parametrize("cache_strategy", list(CacheStrategy))
@pytest.mark.parametrize(
    "opcode,value_sent,account_mode", account_access_params()
)
def test_account_access(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Op,
    value_sent: int,
    gas_benchmark_value: int,
    fixed_opcode_count: int | None,
    account_mode: AccountMode,
    cache_strategy: CacheStrategy,
) -> None:
    """Benchmark account access with caching strategies."""
    address_retriever: Bytecode
    if account_mode == AccountMode.EXISTING_CONTRACT:
        # Use ENS registry as target
        target_address = Address(0x6090A6E47849629B7245DFA1CA21D94CD15878EF)
        address_retriever = CreatePreimageLayout(
            sender_address=target_address,
            nonce=1,
        )
        increment_op = address_retriever.increment_nonce_op()
    elif account_mode == AccountMode.EXISTING_EOA:
        # Spamoor EOA creator (https://github.com/CPerezz/spamoor/pull/12)
        # created these accounts on bloatnet with these values (are also the
        # defaults of SequentialAddressLayout)
        address_retriever = SequentialAddressLayout(
            starting_address=0x1000, increment=1
        )
        increment_op = address_retriever.increment_address_op()
    else:
        address_retriever = SequentialAddressLayout(
            starting_address=keccak256(b"random"), increment=1
        )
        increment_op = address_retriever.increment_address_op()

    setup_code: Bytecode = address_retriever

    cache_op = (
        Op.POP(
            Op.BALANCE(
                address=address_retriever.address_op(),
                # Gas accounting
                address_warm=False,
            )
        )
        if cache_strategy == CacheStrategy.CACHE_TX
        else Bytecode()
    )

    access_warm = cache_strategy == CacheStrategy.CACHE_TX

    if opcode == Op.EXTCODECOPY:
        attack_call = opcode(
            address=address_retriever.address_op(),
            size=1024,
            # Gas accounting
            address_warm=access_warm,
        )
    elif opcode in (Op.CALL, Op.CALLCODE):
        attack_call = Op.POP(
            opcode(
                address=address_retriever.address_op(),
                gas=1,
                value=value_sent,
                # Gas accounting
                address_warm=access_warm,
            )
        )
    elif opcode in (Op.STATICCALL, Op.DELEGATECALL):
        attack_call = Op.POP(
            opcode(
                address=address_retriever.address_op(),
                gas=1,
                args_size=1024,
                # Gas accounting
                address_warm=access_warm,
            )
        )
    else:
        # BALANCE, EXTCODESIZE, EXTCODEHASH
        attack_call = Op.POP(
            opcode(
                address=address_retriever.address_op(),
                # Gas accounting
                address_warm=access_warm,
            )
        )

    loop_code = While(
        body=cache_op + attack_call + increment_op,
    )

    attack_code = IteratingBytecode(
        setup=setup_code,
        iterating=loop_code,
        # Since the target contract is guaranteed to have a STOP as the first
        # instruction, we can use a STOP as the iterating subcall code.
        iterating_subcall=Op.STOP,
    )

    # Calldata generator for each transaction of the iterating bytecode.
    def calldata(iteration_count: int, start_iteration: int) -> bytes:
        del iteration_count
        return Hash(start_iteration)

    attack_address = pre.deploy_contract(code=attack_code, balance=10**21)

    post: dict = {}
    cache_txs = []

    with TestPhaseManager.execution():
        attack_sender = pre.fund_eoa()
        if fixed_opcode_count is not None:
            attack_txs = list(
                attack_code.transactions_by_total_iteration_count(
                    fork=fork,
                    total_iterations=int(fixed_opcode_count * 1000),
                    sender=attack_sender,
                    to=attack_address,
                    calldata=calldata,
                )
            )
        else:
            attack_txs = list(
                attack_code.transactions_by_gas_limit(
                    fork=fork,
                    gas_limit=gas_benchmark_value,
                    sender=attack_sender,
                    to=attack_address,
                    calldata=calldata,
                )
            )
        total_gas_cost = sum(tx.gas_cost for tx in attack_txs)

    if cache_strategy == CacheStrategy.CACHE_PREVIOUS_BLOCK:
        with TestPhaseManager.setup():
            cache_sender = pre.fund_eoa()
            for tx in attack_txs:
                cache_txs.append(
                    Transaction(
                        gas_limit=tx.gas_limit,
                        data=tx.data,
                        to=attack_address,
                        sender=cache_sender,
                    )
                )

    blocks = (
        [Block(txs=attack_txs)]
        if cache_strategy != CacheStrategy.CACHE_PREVIOUS_BLOCK
        else [Block(txs=cache_txs), Block(txs=attack_txs)]
    )

    benchmark_test(
        pre=pre,
        post=post,
        blocks=blocks,
        target_opcode=opcode,
        expected_benchmark_gas_used=total_gas_cost,
    )
