"""
abstract: BloatNet single-opcode benchmark cases for state-related operations.

   These tests focus on individual EVM opcodes (SLOAD, SSTORE) to measure
   their performance when accessing many storage slots across pre-deployed
   contracts. Unlike multi-opcode tests, these isolate single operations
   to benchmark specific state-handling bottlenecks.
"""

import pytest
from execution_testing import (
    AccessList,
    Account,
    Alloc,
    BenchmarkTestFiller,
    Block,
    BlockchainTestFiller,
    Bytecode,
    Fork,
    Hash,
    Op,
    Storage,
    Transaction,
    While,
)
from execution_testing.cli.pytest_commands.plugins.execute.pre_alloc import (
    AddressStubs,
)

REFERENCE_SPEC_GIT_PATH = "DUMMY/bloatnet.md"
REFERENCE_SPEC_VERSION = "1.0"

# ERC20 function selectors
BALANCEOF_SELECTOR = 0x70A08231  # balanceOf(address)
APPROVE_SELECTOR = 0x095EA7B3  # approve(address,uint256)
ALLOWANCE_SELECTOR = 0xDD62ED3E  # allowance(address,address)


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
@pytest.mark.parametrize("num_contracts", [1, 5, 10, 20, 100])
def test_sload_empty_erc20_balanceof(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    address_stubs: AddressStubs | None,
    num_contracts: int,
    request: pytest.FixtureRequest,
) -> None:
    """
    BloatNet SLOAD benchmark using ERC20 balanceOf queries on random
    addresses.

    This test:
    1. Filters stubs matching test name prefix
       (e.g., test_sload_empty_erc20_balanceof_*)
    2. Uses first N contracts based on num_contracts parameter
    3. Splits gas budget evenly across the selected contracts
    4. Queries balanceOf() incrementally starting by 0 and increasing by 1
       (thus forcing SLOADs to non-existing addresses)
    """
    # Extract test function name for stub filtering
    # Remove parametrization suffix
    test_name = request.node.name.split("[")[0]

    # Filter stubs that match the test name prefix
    matching_stubs = []
    if address_stubs is not None:
        matching_stubs = [
            stub_name
            for stub_name in address_stubs.root.keys()
            if stub_name.startswith(test_name)
        ]

    # Validate we have enough stubs
    if len(matching_stubs) < num_contracts:
        pytest.fail(
            f"Not enough matching stubs for test '{test_name}'. "
            f"Required: {num_contracts}, Found: {len(matching_stubs)}. "
            f"Matching stubs: {matching_stubs}"
        )

    # Select first N stubs
    selected_stubs = matching_stubs[:num_contracts]
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

    # Calculate gas budget per contract
    available_gas = gas_benchmark_value - intrinsic_gas
    gas_per_contract = available_gas // num_contracts

    # For each contract: first call is COLD (2600), subsequent are WARM (100)
    # Solve for calls_per_contract:
    # gas_per_contract = cold_call + (calls-1) * warm_call
    # Simplifies to: gas = cold_warm_diff + calls * warm_call_cost
    warm_call_cost = (
        loop_overhead + gas_costs.G_WARM_ACCOUNT_ACCESS + erc20_internal_gas
    )
    cold_warm_diff = (
        gas_costs.G_COLD_ACCOUNT_ACCESS - gas_costs.G_WARM_ACCOUNT_ACCESS
    )

    calls_per_contract = int(
        (gas_per_contract - cold_warm_diff) // warm_call_cost
    )

    # Deploy selected ERC20 contracts using stubs
    # In execute mode: stubs point to already-deployed contracts on chain
    # In fill mode: empty bytecode is deployed as placeholder
    erc20_addresses = []
    for stub_name in selected_stubs:
        addr = pre.deploy_contract(
            # Required parameter, ignored for stubs in execute mode
            code=Bytecode(),
            stub=stub_name,
        )
        erc20_addresses.append(addr)

    # Log test requirements
    print(
        f"Total gas budget: {gas_benchmark_value / 1_000_000:.1f}M gas. "
        f"~{gas_per_contract / 1_000_000:.1f}M gas per contract, "
        f"{calls_per_contract} balanceOf calls per contract."
    )

    # Build attack code that loops through each contract
    attack_code: Bytecode = (
        Op.JUMPDEST  # Entry point
        # Store selector once for all contracts
        + Op.MSTORE(offset=0, value=BALANCEOF_SELECTOR)
    )

    for erc20_address in erc20_addresses:
        # For each contract, initialize counter and loop
        attack_code += (
            # Initialize counter in memory[32] = number of calls
            Op.MSTORE(offset=32, value=calls_per_contract)
            # Loop for this specific contract
            + While(
                # Continue while counter > 0
                condition=Op.MLOAD(32) + Op.ISZERO + Op.ISZERO,
                body=(
                    # Call balanceOf(address) on ERC20 contract
                    # args_offset=28 reads: selector from MEM[28:32] + address
                    # from MEM[32:64]
                    Op.CALL(
                        address=erc20_address,
                        value=0,
                        args_offset=28,
                        args_size=36,
                        ret_offset=0,
                        ret_size=0,
                    )
                    + Op.POP  # Discard CALL success status
                    # Decrement counter: counter - 1
                    + Op.MSTORE(offset=32, value=Op.SUB(Op.MLOAD(32), 1))
                ),
            )
        )

    # Deploy attack contract
    attack_address = pre.deploy_contract(code=attack_code)

    # Run the attack
    attack_tx = Transaction(
        to=attack_address,
        gas_limit=gas_benchmark_value,
        sender=pre.fund_eoa(),
    )

    # Post-state
    post = {
        attack_address: Account(storage={}),
    }

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[attack_tx])],
        post=post,
    )


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize("num_contracts", [1, 5, 10, 20, 100])
def test_sstore_erc20_approve(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    address_stubs: AddressStubs | None,
    num_contracts: int,
    request: pytest.FixtureRequest,
) -> None:
    """
    BloatNet SSTORE benchmark using ERC20 approve to write to storage.

    This test:
    1. Filters stubs matching test name prefix
       (e.g., test_sstore_erc20_approve_*)
    2. Uses first N contracts based on num_contracts parameter
    3. Splits gas budget evenly across the selected contracts
    4. Calls approve(spender, amount) incrementally (counter as spender)
    5. Forces SSTOREs to allowance mapping storage slots
    """
    # Extract test function name for stub filtering
    # Remove parametrization suffix
    test_name = request.node.name.split("[")[0]

    # Filter stubs that match the test name prefix
    matching_stubs = []
    if address_stubs is not None:
        matching_stubs = [
            stub_name
            for stub_name in address_stubs.root.keys()
            if stub_name.startswith(test_name)
        ]

    # Validate we have enough stubs
    if len(matching_stubs) < num_contracts:
        pytest.fail(
            f"Not enough matching stubs for test '{test_name}'. "
            f"Required: {num_contracts}, Found: {len(matching_stubs)}. "
            f"Matching stubs: {matching_stubs}"
        )

    # Select first N stubs
    selected_stubs = matching_stubs[:num_contracts]
    gas_costs = fork.gas_costs()

    # Calculate gas costs
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(calldata=b"")

    # Per-contract fixed overhead (setup + teardown)
    memory_expansion_cost = 15  # Memory expansion to 160 bytes (5 words)
    overhead_per_contract = (
        gas_costs.G_VERY_LOW  # MSTORE to initialize counter (3)
        + memory_expansion_cost  # Memory expansion (15)
        + gas_costs.G_JUMPDEST  # JUMPDEST at loop start (1)
        + gas_costs.G_LOW  # MLOAD for While condition check (5)
        + gas_costs.G_BASE  # ISZERO (2)
        + gas_costs.G_BASE  # ISZERO (2)
        + gas_costs.G_MID  # JUMPI (8)
        + gas_costs.G_BASE  # POP to clean up counter at end (2)
    )  # = 38

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

    # Calculate total gas needed
    total_overhead = intrinsic_gas + (overhead_per_contract * num_contracts)
    available_gas_for_iterations = gas_benchmark_value - total_overhead

    # For each contract: first call is COLD (2600), subsequent are WARM (100)
    # Solve for calls per contract accounting for cold/warm transition
    warm_call_cost = (
        loop_overhead + gas_costs.G_WARM_ACCOUNT_ACCESS + erc20_internal_gas
    )
    cold_warm_diff = (
        gas_costs.G_COLD_ACCOUNT_ACCESS - gas_costs.G_WARM_ACCOUNT_ACCESS
    )

    # Per contract: gas_available = cold_warm_diff + calls * warm_call_cost
    gas_per_contract = available_gas_for_iterations // num_contracts
    calls_per_contract = int(
        (gas_per_contract - cold_warm_diff) // warm_call_cost
    )

    # Deploy selected ERC20 contracts using stubs
    erc20_addresses = []
    for stub_name in selected_stubs:
        addr = pre.deploy_contract(
            code=Bytecode(),
            stub=stub_name,
        )
        erc20_addresses.append(addr)

    # Log test requirements
    print(
        f"Total gas budget: {gas_benchmark_value / 1_000_000:.1f}M gas. "
        f"Intrinsic: {intrinsic_gas}, "
        f"Overhead per contract: {overhead_per_contract}, "
        f"Warm call cost: {warm_call_cost}. "
        f"{calls_per_contract} approve calls per contract "
        f"({num_contracts} contracts)."
    )

    # Build attack code that loops through each contract
    attack_code: Bytecode = (
        Op.JUMPDEST  # Entry point
        # Store selector once for all contracts
        + Op.MSTORE(offset=0, value=APPROVE_SELECTOR)
    )

    for erc20_address in erc20_addresses:
        # For each contract, initialize counter and loop
        attack_code += (
            # Initialize counter in memory[32] = number of calls
            Op.MSTORE(offset=32, value=calls_per_contract)
            # Loop for this specific contract
            + While(
                # Continue while counter > 0
                condition=Op.MLOAD(32) + Op.ISZERO + Op.ISZERO,
                body=(
                    # Store spender at memory[64] (counter as spender/amount)
                    Op.MSTORE(offset=64, value=Op.MLOAD(32))
                    # Call approve(spender, amount) on ERC20 contract
                    # args_offset=28 reads: selector from MEM[28:32] +
                    # spender from MEM[32:64] + amount from MEM[64:96]
                    # Note: counter at MEM[32:64] is reused as spender,
                    # and value at MEM[64:96] serves as the amount
                    + Op.CALL(
                        address=erc20_address,
                        value=0,
                        args_offset=28,
                        args_size=68,
                        ret_offset=0,
                        ret_size=0,
                    )
                    + Op.POP  # Discard CALL success status
                    # Decrement counter
                    + Op.MSTORE(offset=32, value=Op.SUB(Op.MLOAD(32), 1))
                ),
            )
        )

    # Deploy attack contract
    attack_address = pre.deploy_contract(code=attack_code)

    # Run the attack
    attack_tx = Transaction(
        to=attack_address,
        gas_limit=gas_benchmark_value,
        sender=pre.fund_eoa(),
    )

    # Post-state
    post = {
        attack_address: Account(storage={}),
    }

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[attack_tx])],
        post=post,
    )


def sstore_helper_contract(sloads_before_sstore: bool) -> Bytecode:
    """
    Storage contract for benchmark slot access.

    # Calldata Layout:
    # - CALLDATA[0..31]: Number of slots to access
    # - CALLDATA[32..63]: Starting slot index
    # - CALLDATA[64..95]: Value to write
    """
    setup = Bytecode()
    loop = Bytecode()
    cleanup = Bytecode()

    start_marker = 10
    end_marker = 30 + (2 if sloads_before_sstore else 0)

    setup += (
        Op.CALLDATALOAD(0)  # num_slots
        + Op.CALLDATALOAD(32)  # start_slot
        + Op.CALLDATALOAD(64)  # value
    )

    setup += Op.PUSH0  # Counter
    setup += Op.JUMPDEST
    # [counter, value, start_slot, num_slots]

    # Loop Condition: Counter < Num Slots
    loop += Op.DUP4
    loop += Op.DUP2
    loop += Op.LT
    loop += Op.ISZERO
    loop += Op.PUSH1(end_marker)
    loop += Op.JUMPI
    # [counter, value, start_slot, num_slots]

    # Loop Body: Store Value at Start Slot + Counter
    loop += Op.DUP1
    loop += Op.DUP4
    loop += Op.ADD
    loop += Op.DUP3
    # [value, start_slot+counter, counter, value, start_slot, num_slots]

    if sloads_before_sstore:
        loop += Op.DUP2
        loop += Op.SLOAD
        loop += Op.POP
        loop += Op.SSTORE
    else:
        loop += Op.SWAP1
        loop += Op.SSTORE  # STORAGE[start_slot + counter] = value
    # [counter, value, start_slot, num_slots]

    # Loop Post: Increment Counter
    loop += Op.PUSH1(1)
    loop += Op.ADD
    loop += Op.PUSH1(start_marker)
    loop += Op.JUMP
    # [counter + 1, value, start_slot, num_slots]

    # Cleanup: Stop
    cleanup += Op.JUMPDEST
    cleanup += Op.STOP

    assert len(setup) - 1 == start_marker
    assert len(setup) + len(loop) == end_marker
    return setup + loop + cleanup


@pytest.mark.parametrize("slot_count", [50, 100])
@pytest.mark.parametrize("use_access_list", [True, False])
@pytest.mark.parametrize("sloads_before_sstore", [True, False])
@pytest.mark.parametrize("num_contracts", [1, 5, 10])
@pytest.mark.parametrize(
    "initial_value,write_value",
    [
        pytest.param(0, 0, id="zero_to_zero"),
        pytest.param(0, 0xDEADBEEF, id="zero_to_nonzero"),
        pytest.param(0xDEADBEEF, 0, id="nonzero_to_zero"),
        pytest.param(0xDEADBEEF, 0xBEEFBEEF, id="nonzero_to_diff"),
        pytest.param(0xDEADBEEF, 0xBEEFBEEF, id="nonzero_to_same"),
    ],
)
def test_sstore_variants(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
    gas_benchmark_values: int,
    slot_count: int,
    use_access_list: bool,
    sloads_before_sstore: bool,
    num_contracts: int,
    initial_value: int,
    write_value: int,
) -> None:
    """
    Benchmark SSTORE instruction with various configurations.

    Variants:
    - use_access_list: Warm storage slots via access list
    - sloads_before_sstore: Number of SLOADs per slot before SSTORE
    - num_contracts: Number of contract instances (cold storage writes)
    - initial_value/write_value: Storage transitions
      (zero_to_zero, zero_to_nonzero, nonzero_to_zero, nonzero_to_nonzero)
    """
    base_contract = sstore_helper_contract(sloads_before_sstore)
    padded_contract = base_contract

    slots_per_contract = slot_count // num_contracts

    txs: list[Transaction] = []
    post = {}

    base_gas_per_contract = min(
        tx_gas_limit, gas_benchmark_values // num_contracts
    )
    gas_remainder = tx_gas_limit % num_contracts

    for contract_idx in range(num_contracts):
        initial_storage = Storage()

        start_slot = contract_idx * slots_per_contract
        for i in range(slots_per_contract):
            initial_storage[start_slot + i] = initial_value

        contract_addr = pre.deploy_contract(
            code=padded_contract,
            storage=initial_storage,
        )

        calldata = (
            slots_per_contract.to_bytes(32, "big")
            + start_slot.to_bytes(32, "big")
            + write_value.to_bytes(32, "big")
        )

        access_list = None
        if use_access_list:
            storage_keys = [
                Hash(start_slot + i) for i in range(slots_per_contract)
            ]
            access_list = [
                AccessList(
                    address=contract_addr,
                    storage_keys=storage_keys,
                )
            ]

        contract_gas_limit = base_gas_per_contract
        if contract_idx == len(txs) - 1:
            contract_gas_limit += gas_remainder

        tx = Transaction(
            to=contract_addr,
            data=calldata,
            gas_limit=contract_gas_limit,
            sender=pre.fund_eoa(),
            access_list=access_list,
        )
        txs.append(tx)

        expected_storage = Storage()
        for i in range(slots_per_contract):
            expected_storage[start_slot + i] = write_value

        post[contract_addr] = Account(
            code=padded_contract,
            storage=expected_storage,
        )

    benchmark_test(
        blocks=[Block(txs=txs)],
        post=post,
        skip_gas_used_validation=True,
    )


def sload_helper_contract() -> Bytecode:
    """
    Storage contract for benchmark slot access.

    # Calldata Layout:
    # - CALLDATA[0..31]: incrementer
    # - CALLDATA[32..63]: Number of slots to access
    """
    setup = Bytecode()
    loop = Bytecode()
    cleanup = Bytecode()

    start_marker = 4
    end_marker = 26

    setup += Op.PUSH0  # counter
    setup += Op.CALLDATALOAD(32)  # num_slots
    setup += Op.JUMPDEST
    # [num_slots, counter]

    # Loop Condition: Counter < Num Slots
    loop += Op.DUP1
    loop += Op.ISZERO
    loop += Op.PUSH1(end_marker)
    loop += Op.JUMPI
    # [num_slots, counter]

    # Loop Body: SLOAD value at counter
    loop += Op.PUSH1(1)
    loop += Op.SWAP1
    loop += Op.SUB
    loop += Op.SWAP1
    # [counter, num_slots-1]

    loop += Op.DUP1
    loop += Op.SLOAD
    loop += Op.POP
    # [counter, num_slots-1]

    loop += Op.CALLDATALOAD(0)
    loop += Op.ADD
    loop += Op.SWAP1
    # [num_slots-1, incrementer+counter]

    loop += Op.PUSH1(start_marker)
    loop += Op.JUMP
    # [num_slots-1, incrementer+counter]

    cleanup += Op.JUMPDEST
    cleanup += Op.STOP

    assert len(setup) - 1 == start_marker
    assert len(setup) + len(loop) == end_marker
    return setup + loop + cleanup


@pytest.mark.parametrize("num_slots", [1, 10, 50, 100, 200])
@pytest.mark.parametrize("warm_slots", [False, True])
@pytest.mark.parametrize("storage_keys_set", [False, True])
@pytest.mark.parametrize("incrementer", [0, 1])
def test_storage_sload_benchmark(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    warm_slots: bool,
    storage_keys_set: bool,
    num_slots: int,
    incrementer: int,
    tx_gas_limit: int,
) -> None:
    """
    Benchmark SSTORE instruction with various configurations.

    Variants:
    - use_access_list: Warm storage slots via access list
    - sloads_before_sstore: Number of SLOADs per slot before SSTORE
    - num_contracts: Number of contract instances (cold storage writes)
    - initial_value/write_value: Storage transitions
      (zero_to_zero, zero_to_nonzero, nonzero_to_zero, nonzero_to_nonzero)
    """
    slots: set[int] = set()
    if storage_keys_set:
        slots = {i * incrementer for i in range(num_slots)}
    initial_storage = Storage.model_validate(dict.fromkeys(slots, 1))

    storage_contract = pre.deploy_contract(
        code=sload_helper_contract(),
        storage=initial_storage,
    )

    calldata = incrementer.to_bytes(32, "big") + num_slots.to_bytes(32, "big")

    access_lists: list[AccessList] = []

    if warm_slots:
        access_lists = [
            AccessList(
                address=storage_contract,
                storage_keys=list(slots),
            ),
        ]

    tx = Transaction(
        to=storage_contract,
        gas_limit=tx_gas_limit,
        access_list=access_lists,
        data=calldata,
        sender=pre.fund_eoa(),
    )

    benchmark_test(
        pre=pre,
        blocks=[Block(txs=[tx])],
        skip_gas_used_validation=True,
    )
