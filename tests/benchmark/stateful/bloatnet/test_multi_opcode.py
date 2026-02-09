"""
abstract: BloatNet bench cases extracted from https://hackmd.io/9icZeLN7R0Sk5mIjKlZAHQ.

   The idea of all these tests is to stress client implementations to find out
   where the limits of processing are focusing specifically on state-related
   operations.
"""

import json
import math
from pathlib import Path

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

    # Deploy factory using stub contract - NO HARDCODED VALUES
    # The stub "bloatnet_factory" must be provided via --address-stubs flag
    # The factory at that address MUST have:
    # - Slot 0: Number of deployed contracts
    # - Slot 1: Init code hash for CREATE2 address calculation
    factory_address = pre.deploy_contract(
        code=Bytecode(),  # Required parameter, but will be ignored for stubs
        stub="bloatnet_factory",
    )

    # Calculate number of transactions needed (EIP-7825 compliance)
    num_txs = max(1, math.ceil(gas_benchmark_value / tx_gas_limit))

    # Calculate how many contracts to access based on available gas
    total_available_gas = (
        gas_benchmark_value - (intrinsic_gas * num_txs) - 1000
    )
    total_contracts = int(total_available_gas // cost_per_contract)
    contracts_per_tx = total_contracts // num_txs

    # Log test requirements - deployed count read from factory storage
    print(
        f"Test needs {total_contracts} contracts for "
        f"{gas_benchmark_value / 1_000_000:.1f}M gas "
        f"across {num_txs} transaction(s). "
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

    # Build transactions
    txs = []
    post = {}
    contracts_remaining = total_contracts
    salt_offset = 0

    for i in range(num_txs):
        # Last tx gets remaining contracts
        tx_contracts = (
            contracts_per_tx if i < num_txs - 1 else contracts_remaining
        )
        contracts_remaining -= tx_contracts

        # Build attack contract that reads config from factory
        attack_code = (
            # Call getConfig() on factory to get config
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
            + Op.MLOAD(128)  # Load init_code_hash
            # Setup memory for CREATE2 address generation
            # Memory layout at 0: 0xFF + factory_addr(20) + salt(32) + hash(32)
            + Op.MSTORE(
                0, factory_address
            )  # Store factory address at memory position 0
            + Op.MSTORE8(11, 0xFF)  # Store 0xFF prefix at byte 11
            + Op.MSTORE(32, salt_offset)  # Store starting salt at position 32
            # Stack now has: [init_code_hash]
            + Op.PUSH1(64)  # Push memory position
            + Op.MSTORE  # Store init_code_hash at memory[64]
            # Push our iteration count onto stack
            + Op.PUSH4(tx_contracts)
            # Main attack loop - iterate through contracts for this tx
            + While(
                body=(
                    # Generate CREATE2 addr: keccak256(0xFF+factory+salt+hash)
                    Op.SHA3(11, 85)  # CREATE2 addr from memory[11:96]
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

        # Update salt offset for next transaction
        salt_offset += tx_contracts

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=txs)],
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

    # Deploy factory using stub contract - NO HARDCODED VALUES
    # The stub "bloatnet_factory" must be provided via --address-stubs flag
    # The factory at that address MUST have:
    # - Slot 0: Number of deployed contracts
    # - Slot 1: Init code hash for CREATE2 address calculation
    factory_address = pre.deploy_contract(
        code=Bytecode(),  # Required parameter, but will be ignored for stubs
        stub="bloatnet_factory",
    )

    # Calculate number of transactions needed (EIP-7825 compliance)
    num_txs = max(1, math.ceil(gas_benchmark_value / tx_gas_limit))

    # Calculate how many contracts to access
    total_available_gas = (
        gas_benchmark_value - (intrinsic_gas * num_txs) - 1000
    )
    total_contracts = int(total_available_gas // cost_per_contract)
    contracts_per_tx = total_contracts // num_txs

    # Log test requirements - deployed count read from factory storage
    print(
        f"Test needs {total_contracts} contracts for "
        f"{gas_benchmark_value / 1_000_000:.1f}M gas "
        f"across {num_txs} transaction(s). "
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

    # Build transactions
    txs = []
    post = {}
    contracts_remaining = total_contracts
    salt_offset = 0

    for i in range(num_txs):
        # Last tx gets remaining contracts
        tx_contracts = (
            contracts_per_tx if i < num_txs - 1 else contracts_remaining
        )
        contracts_remaining -= tx_contracts

        # Build attack contract that reads config from factory
        attack_code = (
            # Call getConfig() on factory to get config
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
            # Memory[128:160] = init_code_hash
            + Op.MLOAD(128)  # Load init_code_hash
            # Setup memory for CREATE2 address generation
            # Memory layout at 0: 0xFF + factory_addr(20) + salt(32) + hash(32)
            + Op.MSTORE(
                0, factory_address
            )  # Store factory address at memory position 0
            + Op.MSTORE8(11, 0xFF)  # Store 0xFF prefix at byte 11
            + Op.MSTORE(32, salt_offset)  # Store starting salt at position 32
            # Stack now has: [init_code_hash]
            + Op.PUSH1(64)  # Push memory position
            + Op.MSTORE  # Store init_code_hash at memory[64]
            # Push our iteration count onto stack
            + Op.PUSH4(tx_contracts)
            # Main attack loop - iterate through contracts for this tx
            + While(
                body=(
                    # Generate CREATE2 address
                    Op.SHA3(11, 85)  # CREATE2 addr from memory[11:96]
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

        # Update salt offset for next transaction
        salt_offset += tx_contracts

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=txs)],
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

    # Deploy factory using stub contract
    factory_address = pre.deploy_contract(
        code=Bytecode(),
        stub="bloatnet_factory",
    )

    # Calculate number of transactions needed (EIP-7825 compliance)
    num_txs = max(1, math.ceil(gas_benchmark_value / tx_gas_limit))

    # Calculate how many contracts to access based on available gas
    total_available_gas = (
        gas_benchmark_value - (intrinsic_gas * num_txs) - 1000
    )
    total_contracts = int(total_available_gas // cost_per_contract)
    contracts_per_tx = total_contracts // num_txs

    # Log test requirements
    print(
        f"Test needs {total_contracts} contracts for "
        f"{gas_benchmark_value / 1_000_000:.1f}M gas "
        f"across {num_txs} transaction(s). "
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

    # Build transactions
    txs = []
    post = {}
    contracts_remaining = total_contracts
    salt_offset = 0

    for i in range(num_txs):
        # Last tx gets remaining contracts
        tx_contracts = (
            contracts_per_tx if i < num_txs - 1 else contracts_remaining
        )
        contracts_remaining -= tx_contracts

        # Build attack contract that reads config from factory
        attack_code = (
            # Call getConfig() on factory to get config
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
            + Op.MLOAD(128)  # Load init_code_hash
            # Setup memory for CREATE2 address generation
            + Op.MSTORE(0, factory_address)
            + Op.MSTORE8(11, 0xFF)
            + Op.MSTORE(32, salt_offset)  # Starting salt for this tx
            + Op.PUSH1(64)
            + Op.MSTORE  # Store init_code_hash
            # Push our iteration count onto stack
            + Op.PUSH4(tx_contracts)
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

        # Update salt offset for next transaction
        salt_offset += tx_contracts

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=txs)],
        post=post,
    )


# ERC20 function selectors
BALANCEOF_SELECTOR = 0x70A08231  # balanceOf(address)
APPROVE_SELECTOR = 0x095EA7B3  # approve(address,uint256)

# Load token names from stubs.json for test parametrization
_STUBS_FILE = Path(__file__).parent / "stubs.json"
with open(_STUBS_FILE) as f:
    _STUBS = json.load(f)

# Extract unique token names for mixed sload/sstore tests
MIXED_TOKENS = [
    k.replace("test_mixed_sload_sstore_", "")
    for k in _STUBS.keys()
    if k.startswith("test_mixed_sload_sstore_")
]


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize("token_name", MIXED_TOKENS)
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
    token_name: str,
    sload_percent: int,
    sstore_percent: int,
) -> None:
    """
    BloatNet mixed SLOAD/SSTORE benchmark with configurable operation ratios.

    This test:
    1. Uses a single ERC20 contract specified by token_name parameter
    2. Allocates full gas budget to that contract
    3. Divides gas into SLOAD and SSTORE portions by percentage
    4. Executes balanceOf (SLOAD) and approve (SSTORE) calls per the ratio
    5. Stresses clients with combined read/write operations on large contracts
    """
    stub_name = f"test_mixed_sload_sstore_{token_name}"
    gas_costs = fork.gas_costs()

    # Calculate gas costs
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(calldata=b"")

    # Fixed overhead for SLOAD loop
    sload_loop_overhead = (
        # Attack contract loop overhead
        gas_costs.G_VERY_LOW * 2  # MLOAD counter (3*2)
        + gas_costs.G_VERY_LOW * 2  # MSTORE selector (3*2)
        + gas_costs.G_VERY_LOW * 3  # MLOAD + MSTORE address (3*3)
        + gas_costs.G_BASE  # POP (2)
        + gas_costs.G_BASE * 3  # SUB + MLOAD + MSTORE counter decrement
        + gas_costs.G_BASE * 2  # ISZERO * 2 for loop condition (2*2)
        + gas_costs.G_MID  # JUMPI (8)
    )

    # ERC20 balanceOf internal gas
    sload_erc20_internal = (
        gas_costs.G_VERY_LOW  # PUSH4 selector (3)
        + gas_costs.G_BASE  # EQ selector match (2)
        + gas_costs.G_MID  # JUMPI to function (8)
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
        + gas_costs.G_LOW  # MLOAD counter (5)
        + gas_costs.G_VERY_LOW  # MSTORE spender at memory[64] (3)
        + gas_costs.G_BASE  # POP call result (2)
        # Counter decrement
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

    # ERC20 approve internal gas
    # Cold SSTORE: 22100 = 20000 base + 2100 cold access
    sstore_erc20_internal = (
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
    )

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

    # First SSTORE call is COLD (2600), rest are WARM (100)
    sstore_warm_cost = (
        sstore_loop_overhead
        + gas_costs.G_WARM_ACCOUNT_ACCESS
        + sstore_erc20_internal
    )

    # Deploy ERC20 contract using stub
    erc20_address = pre.deploy_contract(
        code=Bytecode(),
        stub=stub_name,
    )

    # Calculate number of transactions needed (EIP-7825 compliance)
    num_txs = max(1, math.ceil(gas_benchmark_value / tx_gas_limit))

    # Calculate total available gas and split by percentage
    total_available_gas = gas_benchmark_value - (intrinsic_gas * num_txs)
    sload_gas = (total_available_gas * sload_percent) // 100
    sstore_gas = (total_available_gas * sstore_percent) // 100

    # Calculate total calls for each operation type
    total_sload_calls = int((sload_gas - cold_warm_diff) // sload_warm_cost)
    total_sstore_calls = int((sstore_gas - cold_warm_diff) // sstore_warm_cost)

    # Distribute calls across transactions
    sload_calls_per_tx = total_sload_calls // num_txs
    sstore_calls_per_tx = total_sstore_calls // num_txs

    # Log test requirements
    print(
        f"Token: {token_name}, "
        f"Total gas budget: {gas_benchmark_value / 1_000_000:.1f}M gas "
        f"({sload_percent}% SLOAD, {sstore_percent}% SSTORE). "
        f"{total_sload_calls} balanceOf, {total_sstore_calls} approve "
        f"across {num_txs} tx(s)."
    )

    # Build transactions
    txs = []
    post = {}
    sload_remaining = total_sload_calls
    sstore_remaining = total_sstore_calls

    for i in range(num_txs):
        # Last tx gets remaining calls
        tx_sload_calls = (
            sload_calls_per_tx if i < num_txs - 1 else sload_remaining
        )
        tx_sstore_calls = (
            sstore_calls_per_tx if i < num_txs - 1 else sstore_remaining
        )
        sload_remaining -= tx_sload_calls
        sstore_remaining -= tx_sstore_calls

        # Build attack code for this transaction
        attack_code: Bytecode = (
            Op.JUMPDEST  # Entry point
            + Op.MSTORE(offset=0, value=BALANCEOF_SELECTOR)
            # SLOAD operations (balanceOf)
            + Op.MSTORE(offset=32, value=tx_sload_calls)
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
            # SSTORE operations (approve)
            + Op.MSTORE(offset=0, value=APPROVE_SELECTOR)
            + Op.MSTORE(offset=32, value=tx_sstore_calls)
            + While(
                condition=Op.MLOAD(32) + Op.ISZERO + Op.ISZERO,
                body=(
                    Op.MSTORE(offset=64, value=Op.MLOAD(32))
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
