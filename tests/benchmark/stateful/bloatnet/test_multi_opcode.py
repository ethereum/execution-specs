"""
abstract: BloatNet bench cases extracted from https://hackmd.io/9icZeLN7R0Sk5mIjKlZAHQ.

   The idea of all these tests is to stress client implementations to find out
   where the limits of processing are focusing specifically on state-related
   operations.
"""

import pytest
from ethereum_test_forks import Fork
from ethereum_test_tools import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Transaction,
    While,
)
from ethereum_test_vm import Bytecode
from ethereum_test_vm import Opcodes as Op

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

    # Cost per contract access with CREATE2 address generation
    cost_per_contract = (
        gas_costs.G_KECCAK_256  # SHA3 static cost for address generation (30)
        + gas_costs.G_KECCAK_256_WORD
        * 3  # SHA3 dynamic cost (85 bytes = 3 words * 6)
        + gas_costs.G_COLD_ACCOUNT_ACCESS  # Cold access (2600)
        + gas_costs.G_BASE  # POP first result (2)
        + gas_costs.G_WARM_ACCOUNT_ACCESS  # Warm access (100)
        + gas_costs.G_BASE  # POP second result (2)
        + gas_costs.G_BASE  # DUP1 before first op (3)
        + gas_costs.G_VERY_LOW * 4  # PUSH1 operations (4 * 3)
        + gas_costs.G_LOW  # MLOAD for salt (3)
        + gas_costs.G_VERY_LOW  # ADD for increment (3)
        + gas_costs.G_LOW  # MSTORE salt back (3)
        + 10  # While loop overhead
    )

    # Calculate how many contracts to access based on available gas
    available_gas = (
        gas_benchmark_value - intrinsic_gas - 1000
    )  # Reserve for cleanup
    contracts_needed = int(available_gas // cost_per_contract)

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
        f"Test needs {contracts_needed} contracts for "
        f"{gas_benchmark_value / 1_000_000:.1f}M gas. "
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

    # Run the attack
    attack_tx = Transaction(
        to=attack_address,
        gas_limit=gas_benchmark_value,
        sender=pre.fund_eoa(),
    )

    # Post-state: just verify attack contract exists
    post = {
        attack_address: Account(storage={}),
    }

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[attack_tx])],
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

    # Cost per contract with EXTCODECOPY and CREATE2 address generation
    cost_per_contract = (
        gas_costs.G_KECCAK_256  # SHA3 static cost for address generation (30)
        + gas_costs.G_KECCAK_256_WORD
        * 3  # SHA3 dynamic cost (85 bytes = 3 words * 6)
        + gas_costs.G_COLD_ACCOUNT_ACCESS  # Cold access (2600)
        + gas_costs.G_BASE  # POP first result (2)
        + gas_costs.G_WARM_ACCOUNT_ACCESS  # Warm access base (100)
        + gas_costs.G_COPY * 1  # Copy cost for 1 byte (3)
        + gas_costs.G_BASE * 2  # DUP1 before first op, DUP4 for address (6)
        + gas_costs.G_VERY_LOW * 8  # PUSH operations (8 * 3 = 24)
        + gas_costs.G_LOW * 2  # MLOAD for salt twice (6)
        + gas_costs.G_VERY_LOW * 2  # ADD operations (6)
        + gas_costs.G_LOW  # MSTORE salt back (3)
        + gas_costs.G_BASE  # POP after second op (2)
        + 10  # While loop overhead
    )

    # Calculate how many contracts to access
    available_gas = gas_benchmark_value - intrinsic_gas - 1000
    contracts_needed = int(available_gas // cost_per_contract)

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
        f"Test needs {contracts_needed} contracts for "
        f"{gas_benchmark_value / 1_000_000:.1f}M gas. "
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

    # Cost per contract access with CREATE2 address generation
    cost_per_contract = (
        gas_costs.G_KECCAK_256  # SHA3 static cost for address generation (30)
        + gas_costs.G_KECCAK_256_WORD
        * 3  # SHA3 dynamic cost (85 bytes = 3 words * 6)
        + gas_costs.G_COLD_ACCOUNT_ACCESS  # Cold access (2600)
        + gas_costs.G_BASE  # POP first result (2)
        + gas_costs.G_WARM_ACCOUNT_ACCESS  # Warm access (100)
        + gas_costs.G_BASE  # POP second result (2)
        + gas_costs.G_BASE  # DUP1 before first op (3)
        + gas_costs.G_VERY_LOW * 4  # PUSH1 operations (4 * 3)
        + gas_costs.G_LOW  # MLOAD for salt (3)
        + gas_costs.G_VERY_LOW  # ADD for increment (3)
        + gas_costs.G_LOW  # MSTORE salt back (3)
        + 10  # While loop overhead
    )

    # Calculate how many contracts to access based on available gas
    available_gas = (
        gas_benchmark_value - intrinsic_gas - 1000
    )  # Reserve for cleanup
    contracts_needed = int(available_gas // cost_per_contract)

    # Deploy factory using stub contract
    factory_address = pre.deploy_contract(
        code=Bytecode(),
        stub="bloatnet_factory",
    )

    # Log test requirements
    print(
        f"Test needs {contracts_needed} contracts for "
        f"{gas_benchmark_value / 1_000_000:.1f}M gas. "
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
