"""
abstract: BloatNet worst-case attack benchmark for maximum SSTORE stress (Execute Mode Version).

This test implements a worst-case scenario for Ethereum block processing that exploits
the computational complexity of Patricia Merkle Trie operations. It uses CREATE2 to deploy
contracts at pre-mined addresses with shared prefixes, maximizing trie traversal depth.

Key features:
- Deploys 15,000 contracts via CREATE2 to addresses with configurable prefix sharing depth
- Each contract has deep storage slots with configurable trie depth
- Executes optimized attack bytecode that performs multiple SSTORE operations
- Respects EIP-170 (24KB contract size) and Fusaka (16M gas per tx) limits
- Verifies that deep storage slots are correctly modified

Test parameters:
- storage_depth: Depth of storage slots in the contract (e.g., 10)
- account_depth: Depth of account address prefix sharing (e.g., 5)
- Fixed 15,000 contracts deployed/attacked
- Gas per attack call: 50,000 (sufficient for cold SSTORE operations)
- Compilation requires: solc --metadata-hash none (for reproducible bytecode)
"""

import json
import pytest
from pathlib import Path
from subprocess import run, PIPE
from eth_utils import keccak
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytecode,
    Fork,
    Op,
    Transaction,
    Address,
)

# Attack function selector for WorstCaseERC20.attack(uint256)
ATTACK_SELECTOR = 0x64dd891a  # attack(uint256) - verified with: cast sig "attack(uint256)"

# Maximum gas per transaction (Fusaka EIP limit)
MAX_GAS_PER_TX = 16_000_000

NUM_CONTRACTS = 1000  # Number of pre-deployed contracts to attack (or less if fewer are deployed)

# Nick's deterministic deployer address (must be pre-deployed in execute mode)
NICK_DEPLOYER = Address("0x4e59b44847b379578588920ca78fbf26c0b4956c")


def load_create2_data(storage_depth, account_depth):
    """
    Load the pre-mined CREATE2 addresses for given depth parameters.

    Args:
        storage_depth: Depth of storage slots in the contract (e.g., 10)
        account_depth: Depth of account address prefix sharing (e.g., 5)

    Returns dict with:
        - init_code_hash: Expected hash for reproducible compilation
        - contracts: List of dicts with 'salt' and 'auxiliary_accounts'
    """
    json_filename = f"s{storage_depth}_acc{account_depth}.json"
    json_path = Path(__file__).parent / json_filename

    if not json_path.exists():
        raise FileNotFoundError(f"Pre-mined data not found: {json_filename}")

    with open(json_path, 'r') as f:
        return json.load(f)


def compile_attack_orchestrator():
    """
    Compile the AttackOrchestrator.sol contract.

    Returns:
        bytes: Deployment bytecode for the orchestrator contract
    """
    sol_path = Path(__file__).parent / "AttackOrchestrator.sol"

    if not sol_path.exists():
        raise FileNotFoundError(f"AttackOrchestrator.sol not found at {sol_path}")

    # Compile with optimization and no metadata for reproducibility
    result = run(
        [
            "solc",
            "--bin",
            "--optimize",
            "--optimize-runs", "200",
            "--metadata-hash", "none",  # Exclude metadata for reproducibility
            str(sol_path),
        ],
        stdout=PIPE,
        stderr=PIPE,
        text=True,
    )

    if result.returncode != 0:
        raise Exception(f"Failed to compile AttackOrchestrator: {result.stderr}")

    # Parse the output to get the deployment bytecode
    lines = result.stdout.split('\n')
    bytecode_hex = None

    in_binary_section = False
    for line in lines:
        if "Binary:" in line:
            in_binary_section = True
        elif in_binary_section and line.strip() and not line.startswith("="):
            bytecode_hex = line.strip()
            break

    if not bytecode_hex:
        raise Exception(f"Could not extract bytecode from solc output:\n{result.stdout}")

    # Remove 0x prefix if present
    if bytecode_hex.startswith("0x"):
        bytecode_hex = bytecode_hex[2:]

    return bytes.fromhex(bytecode_hex)



@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize("storage_depth,account_depth", [
    (9, 3), 
    (9, 4), 
    (9, 5), 
    (9, 6),
    (10, 3), 
    (10, 4), 
    (10, 5), 
    (10, 6)])  
def test_worst_depth_stateroot_recomp(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    storage_depth: int,
    account_depth: int,
) -> None:
    """
    BloatNet worst-case SSTORE attack benchmark with pre-deployed contracts.

    This test assumes contracts have been pre-deployed using deploy_worst_case_contracts.py:
    1. Uses pre-deployed contracts at CREATE2 addresses
    2. Deploys AttackOrchestrator that derives addresses and calls attack()
    3. Respects gas limits: 16M per tx (Fusaka)
    4. Verifies storage modifications in post-state

    Args:
        storage_depth: Depth of storage slots in the contract (e.g., 9)
        account_depth: Depth of account address prefix sharing (e.g., 3)
    """
    print(f"\nTesting with pre-deployed contracts:")
    print(f"  Storage depth: {storage_depth}")
    print(f"  Account depth: {account_depth}")
    print(f"  Number of contracts: {NUM_CONTRACTS}")

    # Load the CREATE2 data to get the init code hash
    create2_data = load_create2_data(storage_depth, account_depth)
    init_code_hash_hex = create2_data.get("init_code_hash")
    if not init_code_hash_hex:
        raise ValueError(f"No init_code_hash found in s{storage_depth}_acc{account_depth}.json")

    # Remove 0x prefix if present and convert to bytes
    if init_code_hash_hex.startswith("0x"):
        init_code_hash_hex = init_code_hash_hex[2:]
    hash_bytes = bytes.fromhex(init_code_hash_hex)

    # Create an EOA with a known private key for the deployer
    deployer_eoa = pre.fund_eoa(amount=10000 * 10**18)  # 10,000 ETH
    deployer_address = deployer_eoa  # Use this address for transactions

    # Compile the AttackOrchestrator contract
    print(f"  Compiling AttackOrchestrator.sol...")
    orchestrator_bytecode = compile_attack_orchestrator()

    # Gas per attack with optimized forwarding (3,650 gas to target)
    GAS_PER_ATTACK = 6_364  # 2,714 overhead + 3,650 forwarded

    # Gas cost breakdown for MAX_ATTACKS_PER_TX calculation:
    #
    # Transaction overhead (22,900 gas total):
    #   - Base transaction cost: 21,000 gas
    #   - Calldata (4-byte selector + 3 uint256s): 1,600 gas
    #   - Function dispatch overhead: ~100 gas
    #   - Initial SLOAD for immutables (2 reads): 200 gas
    #
    # Per-iteration gas cost in AttackOrchestrator (52,714 gas total):
    #   Loop overhead (24 gas):
    #     - lt(i, endIndex): 3 gas
    #     - add(i, 1): 3 gas
    #     - JUMPI: 10 gas
    #     - JUMP: 8 gas
    #   CREATE2 address derivation (75 gas):
    #     - mstore8 for 0xff: 3 gas
    #     - shl + mstore for deployer: 6 gas
    #     - mstore for salt: 6 gas
    #     - mstore for codeHash: 6 gas
    #     - keccak256(85 bytes): 48 gas
    #     - and operation: 3 gas
    #   Call preparation (9 gas):
    #     - Two mstore operations: 6 gas
    #     - add operation: 3 gas
    #   CALL opcode overhead (2,606 gas):
    #     - Cold address access: 2,600 gas
    #     - Memory expansion: 6 gas
    #
    # Total overhead per iteration: 24 + 75 + 9 + 2,606 = 2,714 gas
    #
    # IMPORTANT: AttackOrchestrator.sol line 72 hardcodes 50,000 gas forwarded to each target.
    # This is NOT a cost - it's the gas LIMIT we give to the target's attack() function.
    # The actual gas consumed by the target depends on the SSTORE operation complexity.
    #
    # With optimized 3,650 gas forwarding per call:
    # Total per iteration = 2,714 (overhead) + 3,650 (forwarded) = 6,364 gas
    # MAX_ATTACKS_PER_TX = (16,000,000 - 22,900) / 6,364 = 2,510
    #
    # This is a massive improvement from 303 attacks with the old 50k forwarding
    MAX_ATTACKS_PER_TX = 2510  # Maximum attacks with optimized 3,650 gas forwarding

    attack_txs = []
    last_written_values = {}
    attack_value = 42  # Fixed value to write to all contracts

    # ABI encode constructor parameters for Nick's deployer
    deployer_bytes = bytes(NICK_DEPLOYER)

    print(f"  Using init code hash from JSON: 0x{hash_bytes.hex()}")

    # Constructor arguments are ABI-encoded: address (32 bytes) + bytes32 (32 bytes)
    constructor_args = deployer_bytes.rjust(32, b'\x00') + hash_bytes

    # Combine bytecode with constructor arguments
    orchestrator_init_code = orchestrator_bytecode + constructor_args

    # In execute mode, deploy orchestrator via transaction
    # We can't use pre.deploy_contract with address parameter
    orchestrator_deploy_tx = Transaction(
        to=None,  # Contract creation transaction
        data=orchestrator_init_code,
        gas_limit=2_000_000,  # Sufficient for orchestrator deployment
        sender=deployer_address,
        max_fee_per_gas=10_000_000_000,  # 10 gwei
        max_priority_fee_per_gas=1_000_000_000,  # 1 gwei
    )

    # Calculate the orchestrator address based on nonce 0 (deployed FIRST)
    import rlp
    # Nonce = 0 since orchestrator is deployed first
    nonce_for_orchestrator = 0
    deployer_bytes = bytes.fromhex(str(deployer_address)[2:])
    orchestrator_address_bytes = keccak(rlp.encode([deployer_bytes, nonce_for_orchestrator]))[12:]
    orchestrator_address = Address("0x" + orchestrator_address_bytes.hex())

    print(f"  Orchestrator will be deployed at: {orchestrator_address}")

    # Function to calculate CREATE2 addresses
    def calculate_create2_address(deployer_addr, salt, init_code_hash):
        """Calculate CREATE2 address for a given salt and init code hash"""
        deployer_bytes = bytes.fromhex(str(deployer_addr)[2:])
        salt_bytes = salt.to_bytes(32, 'big')

        # CREATE2 preimage: 0xff ++ deployer ++ salt ++ keccak256(init_code)
        preimage = b'\xff' + deployer_bytes + salt_bytes + init_code_hash
        address_bytes = keccak(preimage)[12:]
        return Address("0x" + address_bytes.hex())

    # Create orchestrator attack transactions
    # Since orchestrator is pre-deployed, we always create attack transactions
    for batch_start in range(0, NUM_CONTRACTS, MAX_ATTACKS_PER_TX):
        batch_end = min(batch_start + MAX_ATTACKS_PER_TX, NUM_CONTRACTS)

        # Track values for verification
        for i in range(batch_start, batch_end):
            # Derive CREATE2 address for this contract
            contract_address = calculate_create2_address(NICK_DEPLOYER, i, hash_bytes)
            last_written_values[contract_address] = attack_value

        # Create calldata: attack(value, startIndex, endIndex)
        # Selector for orchestrator's attack(uint256,uint256,uint256) is 0x407f85f8
        calldata = (
            bytes.fromhex("407f85f8")  # orchestrator's attack(uint256,uint256,uint256) selector
            + attack_value.to_bytes(32, 'big')
            + batch_start.to_bytes(32, 'big')
            + batch_end.to_bytes(32, 'big')
        )

        attack_tx = Transaction(
            to=orchestrator_address,
            gas_limit=min(MAX_GAS_PER_TX, (batch_end - batch_start) * GAS_PER_ATTACK + 21_200),
            sender=deployer_address,
            data=calldata,
            max_fee_per_gas=10_000_000_000,  # 10 gwei
            max_priority_fee_per_gas=1_000_000_000,  # 1 gwei
        )
        attack_txs.append(attack_tx)

    # Create blocks with all transactions in proper order
    # IMPORTANT: Deploy orchestrator FIRST (nonce 0) to have deterministic address
    # Respect gas_benchmark_value to split transactions across multiple blocks
    blocks = []

    # Gas limits:
    # - MAX_GAS_PER_TX: 16M gas per transaction max (Fusaka limit)
    # - gas_benchmark_value: max gas per block (already in gas units, e.g. 60000000 for 60M)
    max_block_gas = gas_benchmark_value

    # Combine all transactions in order
    all_txs = [orchestrator_deploy_tx] + attack_txs

    if all_txs:
        # First, verify no transaction exceeds the 16M gas limit
        for i, tx in enumerate(all_txs):
            tx_gas = tx.gas_limit if tx.gas_limit else 21000
            if tx_gas > MAX_GAS_PER_TX:
                raise ValueError(
                    f"Transaction {i} exceeds MAX_GAS_PER_TX ({MAX_GAS_PER_TX:,}): "
                    f"gas_limit={tx_gas:,}"
                )

        current_block_txs = []
        current_block_gas = 0
        block_count = 0

        for tx in all_txs:
            tx_gas = tx.gas_limit if tx.gas_limit else 21000  # Default gas for simple transfers

            # Check if adding this transaction would exceed the block gas limit
            if current_block_gas + tx_gas > max_block_gas and current_block_txs:
                # Create a block with the current transactions
                blocks.append(Block(txs=current_block_txs))
                block_count += 1
                print(f"  Block {block_count}: {len(current_block_txs)} txs, gas used: {current_block_gas:,}")

                # Start a new block with this transaction
                current_block_txs = [tx]
                current_block_gas = tx_gas
            else:
                # Add transaction to current block
                current_block_txs.append(tx)
                current_block_gas += tx_gas

        # Add the last block if there are remaining transactions
        if current_block_txs:
            blocks.append(Block(txs=current_block_txs))
            block_count += 1
            print(f"  Block {block_count}: {len(current_block_txs)} txs, gas used: {current_block_gas:,}")

    print(f"Total blocks created: {len(blocks)}")



    # Post-state verification: Ensure storage was modified correctly
    # We track exact values written during attacks and verify them in post-state
    post = {}

    # Extract the deepest storage slot from the contract source
    # The deepest slot is the last sstore in the constructor
    # TODO: This is garbage. But we have no other way to actually get this info.
    # We can't make RPC requests from within the test.
    sol_filename = f"depth_{storage_depth}.sol"
    sol_path = Path(__file__).parent / sol_filename

    with open(sol_path, 'r') as f:
        content = f.read()
        # Find all sstore operations in the constructor
        import re
        sstore_pattern = r'sstore\((0x[0-9a-fA-F]+),\s*1\)'
        sstores = re.findall(sstore_pattern, content)
        if sstores:
            # The last sstore is the deepest slot
            DEEP_SLOT = int(sstores[-1], 16)
        else:
            raise Exception(f"Could not find sstore operations in {sol_filename}")

    print(f"\nDeep storage slot for depth {storage_depth}: {hex(DEEP_SLOT)}")
    print(f"Expected: Changed from initial value of 1 to {attack_value} after attack")

    # Verify that each attacked contract's deep storage slot contains the expected value
    print(f"\nPost-state verification:")
    print(f"  Verifying {len(last_written_values)} contracts were attacked")
    print(f"  Sample verification (first 3 contracts):")

    for i, (contract_address, expected_value) in enumerate(last_written_values.items()):
        if i < 3:
            print(f"    Contract {i} ({contract_address}): storage[{hex(DEEP_SLOT)}] = {expected_value}")

        # Verify the attack worked - storage should be modified
        post[contract_address] = Account(
            # Contract should exist with code
            storage={
                DEEP_SLOT: expected_value,  # Exact value from last attack
            }
        )

    blockchain_test(
        pre=pre,
        blocks=blocks,
        post=post,
    )