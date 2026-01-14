"""
abstract: BloatNet bench cases extracted from https://hackmd.io/9icZeLN7R0Sk5mIjKlZAHQ.

   The idea of all these tests is to stress client implementations to find out
   where the limits of processing are focusing specifically on state-related
   operations.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytecode,
    Fork,
    Op,
    Transaction,
    While,
)
from execution_testing.cli.pytest_commands.plugins.execute.pre_alloc import (
    AddressStubs,
)

REFERENCE_SPEC_GIT_PATH = "DUMMY/bloatnet.md"
REFERENCE_SPEC_VERSION = "1.0"


# BLOATNET ARCHITECTURE:
#
#   [Initcode Contract]        [Factory Contract]              [24KB Contracts]
#         (9.5KB)                    (116B)                     (N x 24KB each)
#           │                          │                              │
#           │  EXTCODECOPY             │   CREATE2(salt++)            │
#           └──────────────►           ├──────────────────►     Contract_0
#                                      ├──────────────────►     Contract_1
#                                      ├──────────────────►     Contract_2
#                                      └──────────────────►     Contract_N
#
#   [Attack Contract] ──STATICCALL──► [Factory.getConfig()]
#           │                              returns: (N, hash)
#           └─► Loop(i=0 to N):
#                 1. Generate CREATE2 addr: keccak256(0xFF|factory|i|hash)[12:]
#                 2. BALANCE(addr)    → 2600 gas (cold access)
#                 3. EXTCODESIZE(addr) → 100 gas (warm access)
#
# HOW IT WORKS:
#   1. Factory uses EXTCODECOPY to load initcode, avoiding PC-relative jumps
#   2. Each CREATE2 deployment produces unique 24KB bytecode (via ADDRESS)
#   3. All contracts share same initcode hash for deterministic addresses
#   4. Attack rapidly accesses all contracts, stressing client's state handling


@pytest.mark.parametrize(
    "balance_first",
    [True, False],
    ids=["balance_extcodesize", "extcodesize_balance"],
)
@pytest.mark.valid_from("Prague")
def test_bloatnet_balance_extcodesize(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    balance_first: bool,
) -> None:
    """
    BloatNet test using BALANCE + EXTCODESIZE with "on-the-fly" CREATE2
    address generation.

    This test:
    1. Assumes contracts are already deployed via the factory (salt 0 to N-1)
    2. Generates CREATE2 addresses dynamically during execution
    3. Calls BALANCE and EXTCODESIZE (order controlled by balance_first param)
    4. Maximizes cache eviction by accessing many contracts
    """
    gas_costs = fork.gas_costs()

    # Calculate gas costs
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(calldata=b"")

    # Setup overhead (before loop): STATICCALL + result handling + memory setup
    setup_overhead = (
        gas_costs.G_COLD_ACCOUNT_ACCESS  # STATICCALL to factory (2600)
        + gas_costs.G_VERY_LOW  # ISZERO (3)
        + gas_costs.G_VERY_LOW  # PUSH2 (3)
        + gas_costs.G_HIGH  # JUMPI (10)
        + gas_costs.G_VERY_LOW * 2  # MLOAD × 2 for factory results (3 * 2)
        + gas_costs.G_VERY_LOW * 3  # MSTORE × 3 for memory setup (3 * 3)
        + gas_costs.G_VERY_LOW  # MSTORE8 for 0xFF prefix (3)
        + gas_costs.G_VERY_LOW  # PUSH1 for memory position (3)
    )

    # Cleanup overhead (after loop)
    cleanup_overhead = gas_costs.G_BASE  # POP counter (2)

    # While loop condition overhead per iteration
    loop_condition_overhead = (
        gas_costs.G_VERY_LOW  # DUP1 (3)
        + gas_costs.G_VERY_LOW  # PUSH1 (3)
        + gas_costs.G_VERY_LOW  # SWAP1 (3)
        + gas_costs.G_VERY_LOW  # SUB (3)
        + gas_costs.G_VERY_LOW  # DUP1 (3)
        + gas_costs.G_VERY_LOW  # ISZERO (3)
        + gas_costs.G_VERY_LOW  # ISZERO (3)
        + gas_costs.G_HIGH  # JUMPI (10)
    )

    # Cost per contract access with CREATE2 address generation
    cost_per_contract = (
        gas_costs.G_KECCAK_256  # SHA3 static cost for address generation (30)
        + gas_costs.G_KECCAK_256_WORD * 3  # SHA3 dynamic (85 bytes = 3 words)
        + gas_costs.G_COLD_ACCOUNT_ACCESS  # Cold access (2600)
        + gas_costs.G_BASE  # POP first result (2)
        + gas_costs.G_WARM_ACCOUNT_ACCESS  # Warm access (100)
        + gas_costs.G_BASE  # POP second result (2)
        + gas_costs.G_VERY_LOW  # DUP1 before first op (3)
        + gas_costs.G_VERY_LOW  # MLOAD for salt (3)
        + gas_costs.G_VERY_LOW  # ADD for increment (3)
        + gas_costs.G_VERY_LOW  # MSTORE salt back (3)
        + loop_condition_overhead  # While loop condition
    )

    # Calculate how many transactions we need to fill the block
    num_txs = max(1, gas_benchmark_value // tx_gas_limit)

    # Calculate how many contracts to access per transaction
    total_overhead = setup_overhead + cleanup_overhead
    available_gas_per_tx = tx_gas_limit - intrinsic_gas - total_overhead
    contracts_per_tx = int(available_gas_per_tx // cost_per_contract)

    # Deploy factory using stub contract - NO HARDCODED VALUES
    # The stub "bloatnet_factory" must be provided via --address-stubs flag
    # The factory at that address MUST have:
    # - Slot 0: Number of deployed contracts
    # - Slot 1: Init code hash for CREATE2 address calculation
    factory_address = pre.deploy_contract(
        code=Bytecode(),  # Required parameter, but will be ignored for stubs
        stub="bloatnet_factory",
    )

    # Log test requirements - deployed count read from factory storage
    print(
        f"Tx gas limit: {tx_gas_limit / 1_000_000:.1f}M gas. "
        f"Number of txs: {num_txs}. "
        f"Contracts per tx: {contracts_per_tx}. "
        f"Factory storage will be checked during execution."
    )

    # Define operations that differ based on parameter
    balance_op = Op.POP(Op.BALANCE)
    extcodesize_op = Op.POP(Op.EXTCODESIZE)
    benchmark_ops = (
        (balance_op + extcodesize_op)
        if balance_first
        else (extcodesize_op + balance_op)
    )

    # Build attack contract that reads config from factory and performs attack
    attack_code = (
        # Call getConfig() on factory to get num_deployed and init_code_hash
        Op.STATICCALL(
            gas=Op.GAS,
            address=factory_address,
            args_offset=0,
            args_size=0,
            ret_offset=96,
            ret_size=64,
        )
        # Check if call succeeded
        + Op.ISZERO
        + Op.PUSH2(0x1000)  # Jump to error handler if failed (far jump)
        + Op.JUMPI
        # Load results from memory
        # Memory[96:128] = num_deployed_contracts
        # Memory[128:160] = init_code_hash
        + Op.MLOAD(96)  # Load num_deployed_contracts
        + Op.MLOAD(128)  # Load init_code_hash
        # Setup memory for CREATE2 address generation
        # Memory layout at 0: 0xFF + factory_addr(20) + salt(32) + hash(32)
        + Op.MSTORE(
            0, factory_address
        )  # Store factory address at memory position 0
        + Op.MSTORE8(11, 0xFF)  # Store 0xFF prefix at position (32 - 20 - 1)
        + Op.MSTORE(32, 0)  # Store salt at position 32
        # Stack now has: [num_contracts, init_code_hash]
        + Op.PUSH1(64)  # Push memory position
        + Op.MSTORE  # Store init_code_hash at memory[64]
        # Stack now has: [num_contracts]
        # Main attack loop - iterate through all deployed contracts
        + While(
            body=(
                # Generate CREATE2 addr: keccak256(0xFF+factory+salt+hash)
                Op.SHA3(11, 85)  # Generate CREATE2 address from memory[11:96]
                # The address is now on the stack
                + Op.DUP1  # Duplicate for second operation
                + benchmark_ops  # Execute operations in specified order
                # Increment salt for next iteration
                + Op.MSTORE(
                    32, Op.ADD(Op.MLOAD(32), 1)
                )  # Increment and store salt
            ),
            # Continue while we haven't reached the limit
            condition=Op.DUP1
            + Op.PUSH1(1)
            + Op.SWAP1
            + Op.SUB
            + Op.DUP1
            + Op.ISZERO
            + Op.ISZERO,
        )
        + Op.POP  # Clean up counter
    )

    # Deploy attack contract
    attack_address = pre.deploy_contract(code=attack_code)

    # Create multiple attack transactions to fill the block
    sender = pre.fund_eoa()
    attack_txs = [
        Transaction(
            to=attack_address,
            gas_limit=tx_gas_limit,
            sender=sender,
        )
        for _ in range(num_txs)
    ]

    # Post-state: just verify attack contract exists
    post = {
        attack_address: Account(storage={}),
    }

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=attack_txs)],
        post=post,
    )


@pytest.mark.parametrize(
    "balance_first",
    [True, False],
    ids=["balance_extcodecopy", "extcodecopy_balance"],
)
@pytest.mark.valid_from("Prague")
def test_bloatnet_balance_extcodecopy(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    balance_first: bool,
) -> None:
    """
    BloatNet test using BALANCE + EXTCODECOPY with on-the-fly CREATE2
    address generation.

    This test forces actual bytecode reads from disk by:
    1. Assumes contracts are already deployed via the factory
    2. Generating CREATE2 addresses dynamically during execution
    3. Using BALANCE and EXTCODECOPY (order controlled by balance_first param)
    4. Reading 1 byte from the END of the bytecode to force full contract load
    """
    gas_costs = fork.gas_costs()
    max_contract_size = fork.max_code_size()

    # Calculate costs
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(calldata=b"")

    # Setup overhead (before loop): STATICCALL + result handling + memory setup
    setup_overhead = (
        gas_costs.G_COLD_ACCOUNT_ACCESS  # STATICCALL to factory (2600)
        + gas_costs.G_VERY_LOW  # ISZERO (3)
        + gas_costs.G_VERY_LOW  # PUSH2 (3)
        + gas_costs.G_HIGH  # JUMPI (10)
        + gas_costs.G_VERY_LOW * 2  # MLOAD × 2 for factory results (3 * 2)
        + gas_costs.G_VERY_LOW * 3  # MSTORE × 3 for memory setup (3 * 3)
        + gas_costs.G_VERY_LOW  # MSTORE8 for 0xFF prefix (3)
        + gas_costs.G_VERY_LOW  # PUSH1 for memory position (3)
    )

    # Cleanup overhead (after loop)
    cleanup_overhead = gas_costs.G_BASE  # POP counter (2)

    # While loop condition overhead per iteration
    loop_condition_overhead = (
        gas_costs.G_VERY_LOW  # DUP1 (3)
        + gas_costs.G_VERY_LOW  # PUSH1 (3)
        + gas_costs.G_VERY_LOW  # SWAP1 (3)
        + gas_costs.G_VERY_LOW  # SUB (3)
        + gas_costs.G_VERY_LOW  # DUP1 (3)
        + gas_costs.G_VERY_LOW  # ISZERO (3)
        + gas_costs.G_VERY_LOW  # ISZERO (3)
        + gas_costs.G_HIGH  # JUMPI (10)
    )

    # Cost per contract with EXTCODECOPY and CREATE2 address generation
    cost_per_contract = (
        gas_costs.G_KECCAK_256  # SHA3 static cost for address generation (30)
        + gas_costs.G_KECCAK_256_WORD * 3  # SHA3 dynamic (85 bytes = 3 words)
        + gas_costs.G_COLD_ACCOUNT_ACCESS  # Cold access (2600)
        + gas_costs.G_BASE  # POP first result (2)
        + gas_costs.G_WARM_ACCOUNT_ACCESS  # Warm access base (100)
        + gas_costs.G_COPY * 1  # Copy cost for 1 byte (3)
        + gas_costs.G_VERY_LOW * 2  # DUP1 + DUP4 for address (6)
        + gas_costs.G_VERY_LOW * 2  # MLOAD for salt twice (6)
        + gas_costs.G_VERY_LOW * 2  # ADD operations (6)
        + gas_costs.G_VERY_LOW  # MSTORE salt back (3)
        + gas_costs.G_BASE  # POP after second op (2)
        + loop_condition_overhead  # While loop condition
    )

    # Calculate how many transactions we need to fill the block
    num_txs = max(1, gas_benchmark_value // tx_gas_limit)

    # Calculate how many contracts to access per transaction
    total_overhead = setup_overhead + cleanup_overhead
    available_gas_per_tx = tx_gas_limit - intrinsic_gas - total_overhead
    contracts_per_tx = int(available_gas_per_tx // cost_per_contract)

    # Deploy factory using stub contract - NO HARDCODED VALUES
    # The stub "bloatnet_factory" must be provided via --address-stubs flag
    # The factory at that address MUST have:
    # - Slot 0: Number of deployed contracts
    # - Slot 1: Init code hash for CREATE2 address calculation
    factory_address = pre.deploy_contract(
        code=Bytecode(),  # Required parameter, but will be ignored for stubs
        stub="bloatnet_factory",
    )

    # Log test requirements - deployed count read from factory storage
    print(
        f"Tx gas limit: {tx_gas_limit / 1_000_000:.1f}M gas. "
        f"Number of txs: {num_txs}. "
        f"Contracts per tx: {contracts_per_tx}. "
        f"Factory storage will be checked during execution."
    )

    # Define operations that differ based on parameter
    balance_op = Op.POP(Op.BALANCE)
    extcodecopy_op = (
        Op.PUSH1(1)  # size (1 byte)
        + Op.PUSH2(max_contract_size - 1)  # code offset (last byte)
        + Op.ADD(Op.MLOAD(32), 96)  # unique memory offset
        + Op.DUP4  # address (duplicated earlier)
        + Op.EXTCODECOPY
        + Op.POP  # clean up address
    )
    benchmark_ops = (
        (balance_op + extcodecopy_op)
        if balance_first
        else (extcodecopy_op + balance_op)
    )

    # Build attack contract that reads config from factory and performs attack
    attack_code = (
        # Call getConfig() on factory to get num_deployed and init_code_hash
        Op.STATICCALL(
            gas=Op.GAS,
            address=factory_address,
            args_offset=0,
            args_size=0,
            ret_offset=96,
            ret_size=64,
        )
        # Check if call succeeded
        + Op.ISZERO
        + Op.PUSH2(0x1000)  # Jump to error handler if failed (far jump)
        + Op.JUMPI
        # Load results from memory
        # Memory[96:128] = num_deployed_contracts
        # Memory[128:160] = init_code_hash
        + Op.MLOAD(96)  # Load num_deployed_contracts
        + Op.MLOAD(128)  # Load init_code_hash
        # Setup memory for CREATE2 address generation
        # Memory layout at 0: 0xFF + factory_addr(20) + salt(32) + hash(32)
        + Op.MSTORE(
            0, factory_address
        )  # Store factory address at memory position 0
        + Op.MSTORE8(11, 0xFF)  # Store 0xFF prefix at position (32 - 20 - 1)
        + Op.MSTORE(32, 0)  # Store salt at position 32
        # Stack now has: [num_contracts, init_code_hash]
        + Op.PUSH1(64)  # Push memory position
        + Op.MSTORE  # Store init_code_hash at memory[64]
        # Stack now has: [num_contracts]
        # Main attack loop - iterate through all deployed contracts
        + While(
            body=(
                # Generate CREATE2 address
                Op.SHA3(11, 85)  # Generate CREATE2 address from memory[11:96]
                # The address is now on the stack
                + Op.DUP1  # Duplicate for later operations
                + benchmark_ops  # Execute operations in specified order
                # Increment salt for next iteration
                + Op.MSTORE(
                    32, Op.ADD(Op.MLOAD(32), 1)
                )  # Increment and store salt
            ),
            # Continue while counter > 0
            condition=Op.DUP1
            + Op.PUSH1(1)
            + Op.SWAP1
            + Op.SUB
            + Op.DUP1
            + Op.ISZERO
            + Op.ISZERO,
        )
        + Op.POP  # Clean up counter
    )

    # Deploy attack contract
    attack_address = pre.deploy_contract(code=attack_code)

    # Create multiple attack transactions to fill the block
    sender = pre.fund_eoa()
    attack_txs = [
        Transaction(
            to=attack_address,
            gas_limit=tx_gas_limit,
            sender=sender,
        )
        for _ in range(num_txs)
    ]

    # Post-state
    post = {
        attack_address: Account(storage={}),
    }

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=attack_txs)],
        post=post,
    )


@pytest.mark.parametrize(
    "balance_first",
    [True, False],
    ids=["balance_extcodehash", "extcodehash_balance"],
)
@pytest.mark.valid_from("Prague")
def test_bloatnet_balance_extcodehash(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    balance_first: bool,
) -> None:
    """
    BloatNet test using BALANCE + EXTCODEHASH with on-the-fly CREATE2
    address generation.

    This test:
    1. Assumes contracts are already deployed via the factory
    2. Generates CREATE2 addresses dynamically during execution
    3. Calls BALANCE and EXTCODEHASH (order controlled by balance_first param)
    4. Forces client to compute code hash for 24KB bytecode
    """
    gas_costs = fork.gas_costs()

    # Calculate gas costs
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(calldata=b"")

    # Setup overhead (before loop): STATICCALL + result handling + memory setup
    setup_overhead = (
        gas_costs.G_COLD_ACCOUNT_ACCESS  # STATICCALL to factory (2600)
        + gas_costs.G_VERY_LOW  # ISZERO (3)
        + gas_costs.G_VERY_LOW  # PUSH2 (3)
        + gas_costs.G_HIGH  # JUMPI (10)
        + gas_costs.G_VERY_LOW * 2  # MLOAD × 2 for factory results (3 * 2)
        + gas_costs.G_VERY_LOW * 3  # MSTORE × 3 for memory setup (3 * 3)
        + gas_costs.G_VERY_LOW  # MSTORE8 for 0xFF prefix (3)
        + gas_costs.G_VERY_LOW  # PUSH1 for memory position (3)
    )

    # Cleanup overhead (after loop)
    cleanup_overhead = gas_costs.G_BASE  # POP counter (2)

    # While loop condition overhead per iteration
    loop_condition_overhead = (
        gas_costs.G_VERY_LOW  # DUP1 (3)
        + gas_costs.G_VERY_LOW  # PUSH1 (3)
        + gas_costs.G_VERY_LOW  # SWAP1 (3)
        + gas_costs.G_VERY_LOW  # SUB (3)
        + gas_costs.G_VERY_LOW  # DUP1 (3)
        + gas_costs.G_VERY_LOW  # ISZERO (3)
        + gas_costs.G_VERY_LOW  # ISZERO (3)
        + gas_costs.G_HIGH  # JUMPI (10)
    )

    # Cost per contract access with CREATE2 address generation
    cost_per_contract = (
        gas_costs.G_KECCAK_256  # SHA3 static cost for address generation (30)
        + gas_costs.G_KECCAK_256_WORD * 3  # SHA3 dynamic (85 bytes = 3 words)
        + gas_costs.G_COLD_ACCOUNT_ACCESS  # Cold access (2600)
        + gas_costs.G_BASE  # POP first result (2)
        + gas_costs.G_WARM_ACCOUNT_ACCESS  # Warm access (100)
        + gas_costs.G_BASE  # POP second result (2)
        + gas_costs.G_VERY_LOW  # DUP1 before first op (3)
        + gas_costs.G_VERY_LOW  # MLOAD for salt (3)
        + gas_costs.G_VERY_LOW  # ADD for increment (3)
        + gas_costs.G_VERY_LOW  # MSTORE salt back (3)
        + loop_condition_overhead  # While loop condition
    )

    # Calculate how many transactions we need to fill the block
    num_txs = max(1, gas_benchmark_value // tx_gas_limit)

    # Calculate how many contracts to access per transaction
    total_overhead = setup_overhead + cleanup_overhead
    available_gas_per_tx = tx_gas_limit - intrinsic_gas - total_overhead
    contracts_per_tx = int(available_gas_per_tx // cost_per_contract)

    # Deploy factory using stub contract
    factory_address = pre.deploy_contract(
        code=Bytecode(),
        stub="bloatnet_factory",
    )

    # Log test requirements
    print(
        f"Tx gas limit: {tx_gas_limit / 1_000_000:.1f}M gas. "
        f"Number of txs: {num_txs}. "
        f"Contracts per tx: {contracts_per_tx}. "
        f"Factory storage will be checked during execution."
    )

    # Define operations that differ based on parameter
    balance_op = Op.POP(Op.BALANCE)
    extcodehash_op = Op.POP(Op.EXTCODEHASH)
    benchmark_ops = (
        (balance_op + extcodehash_op)
        if balance_first
        else (extcodehash_op + balance_op)
    )

    # Build attack contract that reads config from factory and performs attack
    attack_code = (
        # Call getConfig() on factory to get num_deployed and init_code_hash
        Op.STATICCALL(
            gas=Op.GAS,
            address=factory_address,
            args_offset=0,
            args_size=0,
            ret_offset=96,
            ret_size=64,
        )
        # Check if call succeeded
        + Op.ISZERO
        + Op.PUSH2(0x1000)  # Jump to error handler if failed
        + Op.JUMPI
        # Load results from memory
        + Op.MLOAD(96)  # Load num_deployed_contracts
        + Op.MLOAD(128)  # Load init_code_hash
        # Setup memory for CREATE2 address generation
        + Op.MSTORE(0, factory_address)
        + Op.MSTORE8(11, 0xFF)
        + Op.MSTORE(32, 0)  # Initial salt
        + Op.PUSH1(64)
        + Op.MSTORE  # Store init_code_hash
        # Main attack loop
        + While(
            body=(
                # Generate CREATE2 address
                Op.SHA3(11, 85)
                + Op.DUP1  # Duplicate for second operation
                + benchmark_ops  # Execute operations in specified order
                # Increment salt
                + Op.MSTORE(32, Op.ADD(Op.MLOAD(32), 1))
            ),
            condition=Op.DUP1
            + Op.PUSH1(1)
            + Op.SWAP1
            + Op.SUB
            + Op.DUP1
            + Op.ISZERO
            + Op.ISZERO,
        )
        + Op.POP  # Clean up counter
    )

    # Deploy attack contract
    attack_address = pre.deploy_contract(code=attack_code)

    # Create multiple attack transactions to fill the block
    sender = pre.fund_eoa()
    attack_txs = [
        Transaction(
            to=attack_address,
            gas_limit=tx_gas_limit,
            sender=sender,
        )
        for _ in range(num_txs)
    ]

    # Post-state
    post = {
        attack_address: Account(storage={}),
    }

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=attack_txs)],
        post=post,
    )


# ERC20 function selectors
BALANCEOF_SELECTOR = 0x70A08231  # balanceOf(address)
APPROVE_SELECTOR = 0x095EA7B3  # approve(address,uint256)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize("num_contracts", [1, 5, 10, 20, 100])
@pytest.mark.parametrize(
    "sload_percent,sstore_percent",
    [
        pytest.param(10, 90, id="10-90"),
        pytest.param(30, 70, id="30-70"),
        pytest.param(50, 50, id="50-50"),
        pytest.param(70, 30, id="70-30"),
        pytest.param(90, 10, id="90-10"),
    ],
)
def test_mixed_sload_sstore(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    address_stubs: AddressStubs | None,
    num_contracts: int,
    sload_percent: int,
    sstore_percent: int,
    request: pytest.FixtureRequest,
) -> None:
    """
    BloatNet mixed SLOAD/SSTORE benchmark with configurable operation ratios.

    This test:
    1. Filters stubs matching test name prefix
       (e.g., test_mixed_sload_sstore_*)
    2. Uses first N contracts based on num_contracts parameter
    3. Divides gas budget evenly across all selected contracts
    4. For each contract, divides gas into SLOAD and SSTORE portions by
       percentage
    5. Executes balanceOf (SLOAD) and approve (SSTORE) calls per the ratio
    6. Stresses clients with combined read/write operations on large
       contracts
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

    # Per-contract fixed overhead (setup + teardown for each contract's loops)
    # Each contract has two loops: SLOAD (balanceOf) and SSTORE (approve)
    overhead_per_contract = (
        # SLOAD loop setup/teardown
        gas_costs.G_VERY_LOW  # MSTORE to initialize counter (3)
        + gas_costs.G_JUMPDEST  # JUMPDEST at loop start (1)
        + gas_costs.G_VERY_LOW  # MLOAD for While condition (3)
        + gas_costs.G_VERY_LOW  # ISZERO (3)
        + gas_costs.G_VERY_LOW  # ISZERO (3)
        + gas_costs.G_HIGH  # JUMPI (10)
        # SSTORE loop setup/teardown
        + gas_costs.G_VERY_LOW  # MSTORE selector (3)
        + gas_costs.G_VERY_LOW  # MSTORE to initialize counter (3)
        + gas_costs.G_JUMPDEST  # JUMPDEST at loop start (1)
        + gas_costs.G_VERY_LOW  # MLOAD for While condition (3)
        + gas_costs.G_VERY_LOW  # ISZERO (3)
        + gas_costs.G_VERY_LOW  # ISZERO (3)
        + gas_costs.G_HIGH  # JUMPI (10)
    )

    # Fixed overhead for SLOAD loop
    sload_loop_overhead = (
        # Attack contract loop overhead
        gas_costs.G_VERY_LOW * 2  # MLOAD counter (3*2)
        + gas_costs.G_VERY_LOW * 2  # MSTORE selector (3*2)
        + gas_costs.G_VERY_LOW * 3  # MLOAD + MSTORE address (3*3)
        + gas_costs.G_BASE  # POP (2)
        + gas_costs.G_VERY_LOW * 3  # SUB + MLOAD + MSTORE decrement (3*3)
        + gas_costs.G_VERY_LOW * 2  # ISZERO * 2 for loop condition (3*2)
        + gas_costs.G_HIGH  # JUMPI (10)
    )

    # ERC20 balanceOf internal gas
    sload_erc20_internal = (
        gas_costs.G_VERY_LOW  # PUSH4 selector (3)
        + gas_costs.G_BASE  # EQ selector match (2)
        + gas_costs.G_HIGH  # JUMPI to function (10)
        + gas_costs.G_JUMPDEST  # JUMPDEST at function start (1)
        + gas_costs.G_VERY_LOW * 2  # CALLDATALOAD arg (3*2)
        + gas_costs.G_KECCAK_256  # keccak256 static (30)
        + gas_costs.G_KECCAK_256_WORD * 2  # keccak256 dynamic 64 bytes
        + gas_costs.G_COLD_SLOAD  # Cold SLOAD - always cold
        + gas_costs.G_VERY_LOW * 3  # MSTORE result + RETURN setup (3*3)
    )

    # Fixed overhead for SSTORE loop
    sstore_loop_overhead = (
        # Attack contract loop body operations
        gas_costs.G_VERY_LOW  # MSTORE selector at memory[32] (3)
        + gas_costs.G_VERY_LOW  # MLOAD counter (3)
        + gas_costs.G_VERY_LOW  # MSTORE spender at memory[64] (3)
        + gas_costs.G_BASE  # POP call result (2)
        # Counter decrement
        + gas_costs.G_VERY_LOW  # MLOAD counter (3)
        + gas_costs.G_VERY_LOW  # PUSH1 1 (3)
        + gas_costs.G_VERY_LOW  # SUB (3)
        + gas_costs.G_VERY_LOW  # MSTORE counter back (3)
        # While loop condition check
        + gas_costs.G_VERY_LOW  # MLOAD counter (3)
        + gas_costs.G_VERY_LOW  # ISZERO (3)
        + gas_costs.G_VERY_LOW  # ISZERO (3)
        + gas_costs.G_HIGH  # JUMPI back to loop start (10)
    )

    # ERC20 approve internal gas
    # Cold SSTORE: 22100 = 20000 base + 2100 cold access
    sstore_erc20_internal = (
        gas_costs.G_VERY_LOW  # PUSH4 selector (3)
        + gas_costs.G_BASE  # EQ selector match (2)
        + gas_costs.G_HIGH  # JUMPI to function (10)
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
    )

    # Calculate how many transactions we need to fill the block
    num_txs = max(1, gas_benchmark_value // tx_gas_limit)

    # Calculate gas budget per contract per transaction
    total_overhead_per_tx = intrinsic_gas + (
        overhead_per_contract * num_contracts
    )
    available_gas_per_tx = tx_gas_limit - total_overhead_per_tx
    gas_per_contract_per_tx = available_gas_per_tx // num_contracts

    # For each contract, split gas by percentage
    sload_gas_per_contract = (gas_per_contract_per_tx * sload_percent) // 100
    sstore_gas_per_contract = (gas_per_contract_per_tx * sstore_percent) // 100

    # Account for cold/warm transitions in CALL costs
    # First SLOAD call is COLD (2600), rest are WARM (100)
    sload_warm_cost = (
        sload_loop_overhead
        + gas_costs.G_WARM_ACCOUNT_ACCESS
        + sload_erc20_internal
    )
    cold_warm_diff = (
        gas_costs.G_COLD_ACCOUNT_ACCESS - gas_costs.G_WARM_ACCOUNT_ACCESS
    )
    sload_calls_per_contract = int(
        (sload_gas_per_contract - cold_warm_diff) // sload_warm_cost
    )

    # First SSTORE call is COLD (2600), rest are WARM (100)
    sstore_warm_cost = (
        sstore_loop_overhead
        + gas_costs.G_WARM_ACCOUNT_ACCESS
        + sstore_erc20_internal
    )
    sstore_calls_per_contract = int(
        (sstore_gas_per_contract - cold_warm_diff) // sstore_warm_cost
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
        f"Tx gas limit: {tx_gas_limit / 1_000_000:.1f}M gas. "
        f"Number of txs: {num_txs}. "
        f"~{gas_per_contract_per_tx / 1_000_000:.2f}M gas per contract per tx "
        f"({sload_percent}% SLOAD, {sstore_percent}% SSTORE). "
        f"Per contract per tx: {sload_calls_per_contract} balanceOf calls, "
        f"{sstore_calls_per_contract} approve calls."
    )

    # Build attack code that loops through each contract
    attack_code: Bytecode = (
        Op.JUMPDEST  # Entry point
        # Store selector once for all contracts
        + Op.MSTORE(offset=0, value=BALANCEOF_SELECTOR)
    )

    for erc20_address in erc20_addresses:
        # For each contract, execute SLOAD operations (balanceOf)
        attack_code += (
            # Initialize counter in memory[32] = number of balanceOf calls
            Op.MSTORE(offset=32, value=sload_calls_per_contract)
            # Loop for balanceOf calls
            + While(
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
                    # Decrement counter
                    + Op.MSTORE(offset=32, value=Op.SUB(Op.MLOAD(32), 1))
                ),
            )
        )

        # For each contract, execute SSTORE operations (approve)
        # Reuse the same memory layout as balanceOf
        attack_code += (
            # Store approve selector at memory[0] (reusing same slot)
            Op.MSTORE(offset=0, value=APPROVE_SELECTOR)
            # Initialize counter in memory[32] = number of approve calls
            # (reusing same slot)
            + Op.MSTORE(offset=32, value=sstore_calls_per_contract)
            # Loop for approve calls
            + While(
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

    # Create multiple attack transactions to fill the block
    sender = pre.fund_eoa()
    attack_txs = [
        Transaction(
            to=attack_address,
            gas_limit=tx_gas_limit,
            sender=sender,
        )
        for _ in range(num_txs)
    ]

    # Post-state
    post = {
        attack_address: Account(storage={}),
    }

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=attack_txs)],
        post=post,
    )
