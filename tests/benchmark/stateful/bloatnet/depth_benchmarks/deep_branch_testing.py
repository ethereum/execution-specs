"""
abstract: BloatNet worst-case attack benchmark for maximum SSTORE stress (Execute Mode Version).

This test implements a worst-case scenario for Ethereum block processing that exploits
the computational complexity of Patricia Merkle Trie operations. It uses CREATE2 to deploy
contracts at pre-mined addresses with shared prefixes, maximizing trie traversal depth.

Key features:
- Attacks pre-deployed contracts via CREATE2 addresses derived from init_code_hash + Nick's deployer
- Each contract has deep storage slots with configurable trie depth
- Executes optimized attack bytecode that performs multiple SSTORE operations
- Respects Fusaka tx gas limit (16M gas) and fills blocks as much as possible
- Verifies attack success via a separate verification transaction at block end

Test parameters:
- storage_depth: Depth of storage slots in the contract (e.g., 9)
- account_depth: Depth of account address prefix sharing (e.g., 5)
- NUM_CONTRACTS: Dynamically computed based on gas_benchmark_value
- Gas per attack call: ~8,050 gas (2,750 overhead + 5,300 forwarded)
"""

import json
import pytest
import re
from pathlib import Path
from subprocess import run, PIPE
from eth_utils import keccak
import rlp
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Fork,
    Transaction,
    Address,
)

# Attack function selector for WorstCaseERC20.attack(uint256)
ATTACK_SELECTOR = 0x64dd891a  # attack(uint256) - verified with: cast sig "attack(uint256)"

# Maximum gas per transaction (Fusaka EIP limit)
MAX_GAS_PER_TX = 16_000_000

# Nick's deterministic deployer address (must be pre-deployed in execute mode)
NICK_DEPLOYER = Address("0x4e59b44847b379578588920ca78fbf26c0b4956c")

# Gas costs for attack calculations
# Measured empirically: 1 attack = 29,340 gas, 1990 attacks = 16,025,257 gas
# Per-attack gas = (16,025,257 - 29,340) / 1989 ≈ 8,042
# TX overhead = 29,340 - 8,042 ≈ 21,298
TX_BASE_GAS = 21_000
TX_CALLDATA_GAS = 1_600  # 4-byte selector + 3 uint256s
TX_OVERHEAD = TX_BASE_GAS + TX_CALLDATA_GAS  # ~22,600 total

# Per-iteration gas cost in AttackOrchestrator (measured empirically)
# Breakdown: ~2,742 overhead (cold account 2600 + call base 100 + loop ops ~42) + 5,300 forwarded
GAS_PER_ATTACK = 8_050  # Use 8,050 to have margin over measured 8,042

# Maximum attacks per transaction at 16M gas limit
# MAX_ATTACKS_PER_TX = floor((16,000,000 - 22,600) / 8,050) = 1,985
MAX_ATTACKS_PER_TX = 1980  # Use 1,980 for safety margin


def load_create2_data(storage_depth: int, account_depth: int) -> dict:
    """
    Load the pre-mined CREATE2 data for given depth parameters.

    Args:
        storage_depth: Depth of storage slots in the contract (e.g., 9)
        account_depth: Depth of account address prefix sharing (e.g., 5)

    Returns dict with:
        - init_code_hash: Expected hash for reproducible compilation
        - deployer: Nick's deployer address
        - contracts: List of dicts with 'salt' and 'auxiliary_accounts'
    """
    json_filename = f"s{storage_depth}_acc{account_depth}.json"
    json_path = Path(__file__).parent / json_filename

    if not json_path.exists():
        raise FileNotFoundError(f"Pre-mined data not found: {json_filename}")

    with open(json_path, 'r') as f:
        return json.load(f)


def compile_solidity_contract(sol_filename: str) -> bytes:
    """
    Compile a Solidity contract and return deployment bytecode.

    Args:
        sol_filename: Name of the .sol file in the same directory

    Returns:
        bytes: Deployment bytecode for the contract
    """
    sol_path = Path(__file__).parent / sol_filename

    if not sol_path.exists():
        raise FileNotFoundError(f"{sol_filename} not found at {sol_path}")

    # Compile with optimization and no metadata for reproducibility
    result = run(
        [
            "solc",
            "--bin",
            "--optimize",
            "--optimize-runs", "200",
            "--metadata-hash", "none",
            str(sol_path),
        ],
        stdout=PIPE,
        stderr=PIPE,
        text=True,
    )

    if result.returncode != 0:
        raise Exception(f"Failed to compile {sol_filename}: {result.stderr}")

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

    if bytecode_hex.startswith("0x"):
        bytecode_hex = bytecode_hex[2:]

    return bytes.fromhex(bytecode_hex)


def get_deep_slot_from_sol(storage_depth: int) -> int:
    """
    Extract the deepest storage slot from the contract source.

    Args:
        storage_depth: Storage depth to find the corresponding .sol file

    Returns:
        int: The deepest storage slot value
    """
    sol_filename = f"depth_{storage_depth}.sol"
    sol_path = Path(__file__).parent / sol_filename

    with open(sol_path, 'r') as f:
        content = f.read()
        # Find all sstore operations in the constructor
        sstore_pattern = r'sstore\((0x[0-9a-fA-F]+),\s*1\)'
        sstores = re.findall(sstore_pattern, content)
        if sstores:
            # The last sstore is the deepest slot
            return int(sstores[-1], 16)
        else:
            raise Exception(f"Could not find sstore operations in {sol_filename}")


def calculate_create2_address(deployer_addr: Address, salt: int, init_code_hash: bytes) -> Address:
    """
    Calculate CREATE2 address for a given salt and init code hash.

    Args:
        deployer_addr: The deployer contract address (Nick's factory)
        salt: The salt value (monotonically increasing integer)
        init_code_hash: The keccak256 hash of the init code

    Returns:
        Address: The CREATE2 address
    """
    deployer_bytes = bytes.fromhex(str(deployer_addr)[2:])
    salt_bytes = salt.to_bytes(32, 'big')

    # CREATE2 preimage: 0xff ++ deployer ++ salt ++ keccak256(init_code)
    preimage = b'\xff' + deployer_bytes + salt_bytes + init_code_hash
    address_bytes = keccak(preimage)[12:]
    return Address("0x" + address_bytes.hex())


def calculate_num_contracts(gas_benchmark_value: int) -> int:
    """
    Dynamically calculate the number of contracts to attack based on gas budget.

    The total gas budget needs to cover:
    - Orchestrator deployment transaction (~2M gas)
    - Verifier deployment transaction (~500k gas)
    - Attack transactions (up to 16M gas each, ~2510 attacks per tx)
    - Verification transaction (~100k gas)

    Args:
        gas_benchmark_value: Total gas budget for the block(s)

    Returns:
        int: Number of contracts that can be attacked
    """
    # Reserve gas for orchestrator deployment, verifier deployment, and verification
    orchestrator_deploy_gas = 2_000_000
    verifier_deploy_gas = 500_000
    verification_gas = 100_000
    reserved_gas = orchestrator_deploy_gas + verifier_deploy_gas + verification_gas

    available_gas = gas_benchmark_value - reserved_gas
    if available_gas <= 0:
        return 1

    # Calculate how many attacks fit in the available gas
    # Each 16M tx can fit MAX_ATTACKS_PER_TX attacks
    num_full_txs = available_gas // MAX_GAS_PER_TX
    total_attacks = num_full_txs * MAX_ATTACKS_PER_TX

    # Add partial transaction attacks if there's remaining gas
    remaining_gas = available_gas - (num_full_txs * MAX_GAS_PER_TX)
    if remaining_gas > TX_OVERHEAD:
        additional_attacks = (remaining_gas - TX_OVERHEAD) // GAS_PER_ATTACK
        total_attacks += additional_attacks

    return max(1, total_attacks)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize("storage_depth,account_depth", [
    (9, 5),
])
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

    This test:
    1. Derives CREATE2 addresses from init_code_hash + Nick's deployer + monotonic salts
    2. Deploys AttackOrchestrator that calls attack() on each target
    3. Fills blocks with 16M gas transactions attacking pre-deployed contracts
    4. Adds a verification transaction at the end to confirm attack success

    Args:
        storage_depth: Depth of storage slots in the contract (e.g., 9)
        account_depth: Depth of account address prefix sharing (e.g., 5)
    """
    # Dynamically calculate number of contracts based on gas budget
    num_contracts = calculate_num_contracts(gas_benchmark_value)

    print(f"\nTesting with pre-deployed contracts:")
    print(f"  Storage depth: {storage_depth}")
    print(f"  Account depth: {account_depth}")
    print(f"  Gas benchmark value: {gas_benchmark_value:,}")
    print(f"  Calculated NUM_CONTRACTS: {num_contracts}")

    # Load the CREATE2 data to get the init code hash
    create2_data = load_create2_data(storage_depth, account_depth)
    init_code_hash_hex = create2_data.get("init_code_hash")
    if not init_code_hash_hex:
        raise ValueError(f"No init_code_hash found in s{storage_depth}_acc{account_depth}.json")

    # Remove 0x prefix if present and convert to bytes
    if init_code_hash_hex.startswith("0x"):
        init_code_hash_hex = init_code_hash_hex[2:]
    init_code_hash = bytes.fromhex(init_code_hash_hex)

    # Verify we have enough contracts in the JSON
    available_contracts = len(create2_data.get("contracts", []))
    if num_contracts > available_contracts:
        print(f"  WARNING: Requested {num_contracts} contracts but only {available_contracts} available")
        num_contracts = available_contracts

    print(f"  Final NUM_CONTRACTS: {num_contracts}")

    # Create an EOA with funds for the deployer
    deployer_eoa = pre.fund_eoa(amount=10000 * 10**18)  # 10,000 ETH

    # Compile the AttackOrchestrator contract
    print(f"  Compiling AttackOrchestrator.sol...")
    orchestrator_bytecode = compile_solidity_contract("AttackOrchestrator.sol")

    # Compile the Verifier contract
    print(f"  Compiling Verifier.sol...")
    verifier_bytecode = compile_solidity_contract("Verifier.sol")

    # Get the deep storage slot for verification
    deep_slot = get_deep_slot_from_sol(storage_depth)
    print(f"  Deep storage slot: {hex(deep_slot)}")

    # ABI encode constructor parameters for AttackOrchestrator
    # Constructor: constructor(address _deployer, bytes32 _initCodeHash)
    nick_deployer_bytes = bytes(NICK_DEPLOYER)
    constructor_args = nick_deployer_bytes.rjust(32, b'\x00') + init_code_hash
    orchestrator_init_code = orchestrator_bytecode + constructor_args

    print(f"  Using init code hash from JSON: 0x{init_code_hash.hex()}")

    # Calculate orchestrator address (nonce 0)
    deployer_addr_bytes = bytes.fromhex(str(deployer_eoa)[2:])
    orchestrator_address_bytes = keccak(rlp.encode([deployer_addr_bytes, 0]))[12:]
    orchestrator_address = Address("0x" + orchestrator_address_bytes.hex())
    print(f"  Orchestrator will be deployed at: {orchestrator_address}")

    # Calculate verifier address (nonce 1)
    verifier_address_bytes = keccak(rlp.encode([deployer_addr_bytes, 1]))[12:]
    verifier_address = Address("0x" + verifier_address_bytes.hex())
    print(f"  Verifier will be deployed at: {verifier_address}")

    # Create deployment transactions
    orchestrator_deploy_tx = Transaction(
        to=None,
        data=orchestrator_init_code,
        gas_limit=2_000_000,
        sender=deployer_eoa,
        max_fee_per_gas=10_000_000_000,
        max_priority_fee_per_gas=1_000_000_000,
    )

    verifier_deploy_tx = Transaction(
        to=None,
        data=verifier_bytecode,
        gas_limit=500_000,
        sender=deployer_eoa,
        max_fee_per_gas=10_000_000_000,
        max_priority_fee_per_gas=1_000_000_000,
    )

    # Build attack transactions
    attack_txs = []
    attack_value = 42  # Fixed value to write to all contracts

    for batch_start in range(0, num_contracts, MAX_ATTACKS_PER_TX):
        batch_end = min(batch_start + MAX_ATTACKS_PER_TX, num_contracts)
        batch_size = batch_end - batch_start

        # Create calldata: attack(value, startIndex, endIndex)
        # Selector for orchestrator's attack(uint256,uint256,uint256) is 0x407f85f8
        calldata = (
            bytes.fromhex("407f85f8")  # attack(uint256,uint256,uint256) selector
            + attack_value.to_bytes(32, 'big')
            + batch_start.to_bytes(32, 'big')
            + batch_end.to_bytes(32, 'big')
        )

        # Calculate gas for this batch - aim for close to 16M
        batch_gas = min(MAX_GAS_PER_TX, batch_size * GAS_PER_ATTACK + TX_OVERHEAD)

        attack_tx = Transaction(
            to=orchestrator_address,
            gas_limit=batch_gas,
            sender=deployer_eoa,
            data=calldata,
            max_fee_per_gas=10_000_000_000,
            max_priority_fee_per_gas=1_000_000_000,
        )
        attack_txs.append(attack_tx)

    print(f"  Created {len(attack_txs)} attack transactions")

    # Calculate the last attacked contract address for verification
    last_contract_salt = num_contracts - 1
    last_contract_address = calculate_create2_address(NICK_DEPLOYER, last_contract_salt, init_code_hash)
    print(f"  Last attacked contract (salt={last_contract_salt}): {last_contract_address}")

    # Create verification transaction
    # Verifier.verify(address target, uint256 expectedValue)
    # Selector: bytes4(keccak256("verify(address,uint256)")) = 0x6be45db7
    verify_calldata = (
        bytes.fromhex("6be45db7")  # verify(address,uint256) selector
        + bytes.fromhex(str(last_contract_address)[2:]).rjust(32, b'\x00')
        + attack_value.to_bytes(32, 'big')
    )

    verification_tx = Transaction(
        to=verifier_address,
        gas_limit=100_000,
        sender=deployer_eoa,
        data=verify_calldata,
        max_fee_per_gas=10_000_000_000,
        max_priority_fee_per_gas=1_000_000_000,
    )

    # Build blocks - pack transactions to maximize block gas usage
    # Order: orchestrator deploy, verifier deploy, attack txs, verification tx
    all_txs = [orchestrator_deploy_tx, verifier_deploy_tx] + attack_txs + [verification_tx]

    blocks = []
    current_block_txs = []
    current_block_gas = 0
    max_block_gas = gas_benchmark_value

    for tx in all_txs:
        tx_gas = tx.gas_limit if tx.gas_limit else 21000

        # Ensure no single tx exceeds 16M gas limit
        if tx_gas > MAX_GAS_PER_TX:
            raise ValueError(f"Transaction exceeds MAX_GAS_PER_TX ({MAX_GAS_PER_TX:,}): gas_limit={tx_gas:,}")

        # Check if adding this tx would exceed block gas limit
        if current_block_gas + tx_gas > max_block_gas and current_block_txs:
            blocks.append(Block(txs=current_block_txs))
            print(f"  Block {len(blocks)}: {len(current_block_txs)} txs, gas: {current_block_gas:,}")
            current_block_txs = [tx]
            current_block_gas = tx_gas
        else:
            current_block_txs.append(tx)
            current_block_gas += tx_gas

    # Add the last block
    if current_block_txs:
        blocks.append(Block(txs=current_block_txs))
        print(f"  Block {len(blocks)}: {len(current_block_txs)} txs, gas: {current_block_gas:,}")

    print(f"  Total blocks: {len(blocks)}")

    # Post-state verification - minimal check on the last attacked contract
    post = {
        # Verify the last attacked contract's deep slot was updated
        last_contract_address: Account(
            storage={
                deep_slot: attack_value,
            }
        ),
    }

    blockchain_test(
        pre=pre,
        blocks=blocks,
        post=post,
    )
