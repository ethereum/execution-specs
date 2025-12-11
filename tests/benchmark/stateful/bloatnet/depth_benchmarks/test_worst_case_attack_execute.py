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

NUM_CONTRACTS = 15000  # Full test with 15,000 contracts

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


def compile_worst_case_contract(storage_depth):
    """
    Compile WorstCaseERC20 contract with given storage depth.

    Args:
        storage_depth: Depth of storage slots in the contract (e.g., 10)

    CRITICAL: Must use --metadata-hash none to exclude IPFS metadata
    that would otherwise make bytecode non-reproducible across environments.

    Returns:
        bytes: Init code (deployment bytecode including constructor)
    """
    sol_filename = f"depth_{storage_depth}.sol"
    sol_path = Path(__file__).parent / sol_filename

    if not sol_path.exists():
        raise FileNotFoundError(f"Contract source not found: {sol_filename}")

    # Compile with exact flags for reproducibility
    result = run(
        [
            "solc",
            "--bin",  # Get deployment bytecode (constructor + runtime)
            "--optimize",
            "--optimize-runs", "200",
            "--metadata-hash", "none",  # CRITICAL: Exclude metadata for reproducible bytecode
            str(sol_path),
        ],
        stdout=PIPE,
        stderr=PIPE,
        text=True,
    )

    if result.returncode != 0:
        raise Exception(f"Failed to compile Solidity contract: {result.stderr}")

    # Parse the output to get the deployment bytecode (includes constructor)
    lines = result.stdout.split('\n')
    bytecode_hex = None

    # Look for the bytecode section
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

    # Return raw bytes - we'll wrap it in Bytecode later with proper params
    return bytes.fromhex(bytecode_hex)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize("storage_depth,account_depth", [(9, 3)])  # Add more tuples as files become available
def test_worst_depth_stateroot_recomp(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    storage_depth: int,
    account_depth: int,
) -> None:
    """
    BloatNet worst-case SSTORE attack benchmark with configurable depths.

    Executes a worst-case attack pattern that maximizes trie traversal overhead:
    1. Deploys 15,000 contracts via CREATE2 to addresses with configurable prefix sharing
    2. Each contract contains storage slots at configurable trie depths
    3. Generates optimized attack bytecode that calls attack() on multiple contracts
    4. Respects gas limits: 16M per tx (Fusaka), 24KB contract size (EIP-170)
    5. Verifies storage modifications using exact value tracking

    Key optimizations:
    - Function selector stored once and reused (saves 34 bytes per call)
    - Batches attacks into multiple contracts when hitting size limits
    - Uses 50,000 gas per CALL (sufficient for cold SSTORE operations)

    Args:
        storage_depth: Depth of storage slots in the contract (e.g., 10)
        account_depth: Depth of account address prefix sharing (e.g., 5)
    """
    # Load pre-mined CREATE2 data for the given depth parameters
    try:
        create2_data = load_create2_data(storage_depth, account_depth)
    except FileNotFoundError as e:
        pytest.skip(f"Skipping test: {e}")

    init_code_hash_expected = create2_data["init_code_hash"]
    contracts = create2_data["contracts"][:NUM_CONTRACTS]

    # Create an EOA with a known private key for the deployer
    deployer_eoa = pre.fund_eoa(amount=10000 * 10**18)  # 10,000 ETH
    deployer_address = deployer_eoa  # Use this address for transactions


    # Get gas costs
    gas_costs = fork.gas_costs()

    # Display test configuration
    print(f"\nSetting up worst-case attack benchmark (Execute Mode):")
    print(f"  Contracts to deploy: {NUM_CONTRACTS}")
    print(f"  Storage depth: {storage_depth}")
    print(f"  Account depth: {account_depth}")
    print(f"  Total auxiliary accounts: {NUM_CONTRACTS * account_depth}")

    # Phase 0: Deploy orchestrator FIRST with nonce 0 to have deterministic address
    print(f"\nPhase 0: Deploy attack orchestrator first")

    # Compile the AttackOrchestrator contract
    print(f"  Compiling AttackOrchestrator.sol...")
    orchestrator_bytecode = compile_attack_orchestrator()

    # Phase 1: Create funding transactions for auxiliary accounts
    # We need to use transactions, not pre-allocation, for execute mode
    funding_txs = []
    for i, contract_data in enumerate(contracts):
        auxiliary_accounts = contract_data.get("auxiliary_accounts", [])
        for aux_account in auxiliary_accounts:
            aux_address = Address(aux_account)
            # Create funding transaction with 1 wei to ensure the account exists in the trie
            funding_tx = Transaction(
                to=aux_address,
                value=1,  # 1 wei to create the account in the trie
                gas_limit=21_000,
                sender=deployer_address,
                max_fee_per_gas=10_000_000_000,  # 10 gwei
                max_priority_fee_per_gas=1_000_000_000,  # 1 gwei
            )
            funding_txs.append(funding_tx)

    # Compile contract for the specified storage depth
    print(f"  Compiling depth_{storage_depth}.sol...")
    try:
        init_code_bytes = compile_worst_case_contract(storage_depth)
    except FileNotFoundError as e:
        pytest.skip(f"Skipping test: {e}")
    # Wrap in Bytecode with proper stack parameters
    init_code = Bytecode(init_code_bytes, popped_stack_items=0, pushed_stack_items=0)

    # Calculate gas for deployment
    # CREATE2 gas: 32000 base + 6 * init_code_size + execution
    init_code_size = len(init_code)
    # Constructor performs storage_depth SSTOREs to deep slots
    # Each SSTORE to a new slot costs ~22100 gas (cold storage)
    constructor_gas = storage_depth * 22100  # Dynamic based on storage depth
    deployment_gas_per_contract = (
        32000  # CREATE2 base cost
        + 6 * init_code_size  # Init code cost (6 gas per byte for CREATE2)
        + 200 * init_code_size  # Code deposit cost (200 gas per byte)
        + constructor_gas  # Constructor execution (storage_depth SSTOREs to deep slots)
    )

    # Calculate how many contracts we can deploy per transaction
    max_contracts_per_tx = MAX_GAS_PER_TX // deployment_gas_per_contract

    print(f"  Init code size: {init_code_size} bytes")
    print(f"  Deployment gas per contract: ~{deployment_gas_per_contract:,}")
    print(f"  Max deployments per tx: {max_contracts_per_tx}")


    from ethereum.crypto.hash import keccak256

    # Calculate actual CREATE2 addresses using Nick's deployer
    actual_contracts = []
    deployment_txs = []  # Track deployment transactions

    print(f"  Deploying {NUM_CONTRACTS} contracts via Nick's method...")
    print(f"  Nick's deployer: {NICK_DEPLOYER}")

    for i, contract_data in enumerate(contracts):
        salt = contract_data["salt"]

        # Convert salt to 32 bytes
        salt_bytes = salt.to_bytes(32, 'big') if isinstance(salt, int) else bytes.fromhex(salt[2:] if salt.startswith("0x") else salt)

        # Nick's method: calldata = salt (32 bytes) + init_code
        calldata = salt_bytes + bytes(init_code)

        # Calculate CREATE2 address: keccak256(0xff ++ nick_deployer ++ salt ++ keccak256(init_code))
        create2_input = (
            bytes.fromhex("ff") +
            bytes(NICK_DEPLOYER) +
            salt_bytes +
            keccak256(bytes(init_code))
        )
        contract_addr = keccak256(create2_input)[-20:]  # Last 20 bytes

        # In execute mode, we can't use pre.deploy_contract with address parameter
        # Contract will be deployed via CREATE2 transactions to Nick's deployer
        contract_address = Address("0x" + contract_addr.hex())

        # Create deployment transaction to Nick's deployer
        deploy_tx = Transaction(
            to=NICK_DEPLOYER,
            data=calldata,
            gas_limit=deployment_gas_per_contract + 50000,  # Add buffer for CREATE2 operation
            sender=deployer_address,
            max_fee_per_gas=10_000_000_000,  # 10 gwei
            max_priority_fee_per_gas=1_000_000_000,  # 1 gwei
        )
        deployment_txs.append(deploy_tx)

        # Track the actual contract address
        actual_contracts.append({
            "contract_address": "0x" + contract_addr.hex(),
            "salt": salt,
            "auxiliary_accounts": contract_data.get("auxiliary_accounts", [])
        })


    # Update contracts list with actual addresses
    contracts = actual_contracts

    print(f"\nActual CREATE2 addresses (first 10):")
    for i, c in enumerate(contracts[:10]):
        print(f"  {i}: {c['contract_address']}")


    # Phase 2: Deploy and use attack orchestrator
    # The orchestrator derives CREATE2 addresses and calls attack() on each
    print(f"\nPhase 2: Attack orchestrator deployment and execution")
    orchestrator_bytecode = compile_attack_orchestrator()

    # TODO: Come back to this and compute the exact value.
    GAS_PER_ATTACK = 50_100

    # TODO: Get back to this after we have the GAS_PER_ATTACK computed
    # Account for transaction overhead (~21,200) and function dispatch (~100)
    MAX_ATTACKS_PER_TX = 318  # (16,000,000 - 21,200) / 50,100

    attack_txs = []
    last_written_values = {}
    attack_value = 42  # Fixed value to write to all contracts

    # ABI encode constructor parameters for Nick's deployer
    deployer_bytes = bytes(NICK_DEPLOYER)
    # Use the actual init code hash (computed from our compiled bytecode)
    hash_bytes = keccak256(bytes(init_code))

    print(f"  Computed init code hash: 0x{hash_bytes.hex()}")
    print(f"  Expected init code hash: {init_code_hash_expected}")

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
    from eth_utils import keccak
    # Nonce = 0 since orchestrator is deployed first
    nonce_for_orchestrator = 0
    deployer_bytes = bytes.fromhex(str(deployer_address)[2:])
    orchestrator_address_bytes = keccak(rlp.encode([deployer_bytes, nonce_for_orchestrator]))[12:]
    orchestrator_address = Address("0x" + orchestrator_address_bytes.hex())

    print(f"  Orchestrator will be deployed at: {orchestrator_address}")


    # Create orchestrator attack transactions
    # Since orchestrator is pre-deployed, we always create attack transactions
    for batch_start in range(0, NUM_CONTRACTS, MAX_ATTACKS_PER_TX):
        batch_end = min(batch_start + MAX_ATTACKS_PER_TX, NUM_CONTRACTS)

        # Track values for verification
        for i in range(batch_start, batch_end):
            contract_address = Address(contracts[i]["contract_address"])
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
    all_txs = [orchestrator_deploy_tx] + funding_txs + deployment_txs + attack_txs

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
    print(f"\nPost-state verification (first 3 contracts):")
    for i, contract_data in enumerate(contracts):
        contract_address = Address(contract_data["contract_address"])
        if i < 3:
            print(f"  Checking contract {i}: {contract_address}")

        if contract_address in last_written_values:
            # Contract was attacked - verify the last written value
            expected_value = last_written_values[contract_address]
            if i < 3:
                print(f"    Expected storage[{hex(DEEP_SLOT)}] = {expected_value}")
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