"""
abstract: BloatNet worst-case attack benchmark for maximum SSTORE stress.

This test implements a worst-case scenario for Ethereum block processing
that exploits the computational complexity of Patricia Merkle Trie
operations. It uses CREATE2 to deploy contracts at pre-mined addresses
with shared prefixes, maximizing trie traversal depth.

Key features:
- Attacks pre-deployed contracts via CREATE2 address derivation
- Each contract has deep storage slots with configurable trie depth
- Executes optimized attack bytecode with multiple SSTORE operations
- Respects Fusaka tx gas limit (16M gas) and fills blocks fully
- Verifies attack success via a verification transaction at block end

Test parameters:
- storage_depth: Depth of storage slots (e.g., 10, 11)
- account_depth: Account address prefix sharing depth (e.g., 6, 7)
- NUM_CONTRACTS: Dynamically computed based on gas_benchmark_value
- Gas per attack call: ~8,050 gas (~2,742 overhead + 5,300 forwarded)

Contract sources:
- AttackOrchestrator.sol and Verifier.sol:
  https://gist.github.com/CPerezz/8686da933fa5c045fbdf7c31e20e6c71
- Pre-mined assets (depth_*.sol, s*_acc*.json):
  https://github.com/CPerezz/worst_case_miner/tree/master/mined_assets
"""

import json
import re
import urllib.error
import urllib.request
import warnings
from pathlib import Path
from typing import Any

import pytest
import rlp  # type: ignore[import-untyped]
from eth_utils import keccak
from execution_testing import (
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Fork,
    Transaction,
)

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
# Breakdown: ~2,742 overhead (cold 2600 + call 100 + loop ~42) + 5,300 fwd
GAS_PER_ATTACK = 8_050  # 8,050 for margin over measured 8,042

# Maximum attacks per transaction at 16M gas limit
# MAX_ATTACKS_PER_TX = floor((16,000,000 - 22,600) / 8,050) = 1,985
MAX_ATTACKS_PER_TX = 1980  # Use 1,980 for safety margin

# GitHub raw URL base for downloading mined assets
MINED_ASSETS_URL = (
    "https://raw.githubusercontent.com/CPerezz/"
    "worst_case_miner/master/mined_assets"
)

# Gas limits for deployment and verification transactions
ORCHESTRATOR_DEPLOY_GAS = 2_000_000
VERIFIER_DEPLOY_GAS = 500_000
VERIFICATION_GAS = 100_000

# Transaction fee parameters (in wei)
MAX_FEE_PER_GAS = 10_000_000_000  # 10 gwei
MAX_PRIORITY_FEE_PER_GAS = 1_000_000_000  # 1 gwei

# Initial balance for the deployer EOA
DEPLOYER_INITIAL_BALANCE = 10_000 * 10**18  # 10,000 ETH

# Arbitrary value written to storage slots during attack
DEFAULT_ATTACK_VALUE = 42

# AttackOrchestrator deployment bytecode (without constructor args)
# Compiled with: solc --bin --optimize --optimize-runs 200 --metadata-hash none
# Source: https://gist.github.com/CPerezz/8686da933fa5c045fbdf7c31e20e6c71
ATTACK_ORCHESTRATOR_BYTECODE = bytes.fromhex(
    "60c060405234801561000f575f5ffd5b5060405161025138038061025183398101604081905261002e91"
    "610044565b6001600160a01b0390911660805260a05261007b565b5f5f60408385031215610055575f5f"
    "fd5b82516001600160a01b038116811461006b575f5ffd5b6020939093015192949293505050565b6080"
    "5160a0516101ab6100a65f395f81816059015260f001525f81816093015260cf01526101ab5ff3fe6080"
    "60405234801561000f575f5ffd5b506004361061003f575f3560e01c8063407f85f814610041578063db"
    "4c545e14610054578063efdee94f1461008e575b005b61003f61004f366004610175565b6100cd565b61"
    "007b7f00000000000000000000000000000000000000000000000000000000000000008156"
    "5b6040519081526020015b60405180910390f35b6100b57f000000000000000000000000000000000000"
    "0000000000000000000000000000815"
    "65b6040516001600160a01b039091168152602001610085565b7f00000000000000000000000000000000"
    "000000000000000000000000000000007f0000000000000000000000000000000000000000000000000000"
    "0000000000008181855b8581101561016b575f60ff81538360601b6001820152816015820152826035"
    "820152506001600160a01b0360555f2016608063326ec48d60e11b81528960048201525f5f6024835f86"
    "6114b4f1505050600101610113565b5050505050505050565b5f5f5f60608486031215610187575f5ffd"
    "5b50508135936020830135935060409092013591905056fea164736f6c634300081e000a"
)

# Verifier deployment bytecode
# Compiled with: solc --bin --optimize --optimize-runs 200 --metadata-hash none
# Source: https://gist.github.com/CPerezz/8686da933fa5c045fbdf7c31e20e6c71
VERIFIER_BYTECODE = bytes.fromhex(
    "6080604052348015600e575f5ffd5b5061018b8061001c5f395ff3fe608060405234801561000f575f5f"
    "fd5b5060043610610029575f3560e01c80636704fe9f1461002d575b5f5ffd5b61004061003b36600461"
    "011c565b610054565b604051901515815260200160405180910390f35b60408051600481526024810182"
    "526020810180516001600160e01b0316633bdadbf360e11b17905290515f91829182916001600160a01b"
    "038716916100999190610151565b5f60405180830381855afa9150503d805f81146100d1576040519150"
    "601f19603f3d011682016040523d82523d5f602084013e6100d6565b606091505b50915091508115806100"
    "ea57508051602014155b156100f9575f92505050610116565b5f8180602001905181019061010e919061"
    "0167565b851493505050505b92915050565b5f5f6040838503121561012d575f5ffd5b82356001600160"
    "a01b0381168114610143575f5ffd5b946020939093013593505050565b5f82518060208501845e5f9201"
    "91825250919050565b5f60208284031215610177575f5ffd5b505191905056fea164736f6c634300081e"
    "000a"
)


def download_mined_asset(filename: str) -> str:
    """
    Download a mined asset file from GitHub if not cached locally.

    Args:
        filename: Name of the file (e.g., "s9_acc5.json" or "depth_9.sol")

    Returns:
        str: Content of the file

    """
    cache_dir = Path(__file__).parent / ".cache"
    cache_dir.mkdir(exist_ok=True)
    cache_path = cache_dir / filename

    if cache_path.exists():
        with open(cache_path, "r") as f:
            return f.read()

    url = f"{MINED_ASSETS_URL}/{filename}"
    print(f"  Downloading {filename} from {url}...")

    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            content = response.read().decode("utf-8")
            # Cache the file locally
            with open(cache_path, "w") as f:
                f.write(content)
            return content
    except urllib.error.URLError as e:
        raise RuntimeError(f"Failed to download {filename}: {e}") from e


def load_create2_data(
    storage_depth: int, account_depth: int
) -> dict[str, Any]:
    """
    Load the pre-mined CREATE2 data for given depth parameters.

    Downloads from GitHub if not available locally.

    Args:
        storage_depth: Depth of storage slots in the contract (e.g., 9)
        account_depth: Depth of account address prefix sharing (e.g., 5)

    Returns dict with:
        - init_code_hash: Expected hash for reproducible compilation
        - deployer: Nick's deployer address
        - contracts: List of dicts with 'salt' and 'auxiliary_accounts'

    """
    json_filename = f"s{storage_depth}_acc{account_depth}.json"
    content = download_mined_asset(json_filename)
    return json.loads(content)


def get_deep_slot_from_sol(storage_depth: int) -> int:
    """
    Extract the deepest storage slot from the contract source.

    Downloads the .sol file from GitHub if not available locally.

    Args:
        storage_depth: Storage depth to find the corresponding .sol file

    Returns:
        int: The deepest storage slot value

    """
    sol_filename = f"depth_{storage_depth}.sol"
    content = download_mined_asset(sol_filename)

    # Find all sstore operations in the constructor
    sstore_pattern = r"sstore\((0x[0-9a-fA-F]+),\s*1\)"
    sstores = re.findall(sstore_pattern, content)
    if sstores:
        # The last sstore is the deepest slot
        return int(sstores[-1], 16)
    else:
        raise RuntimeError(f"No sstore operations in {sol_filename}")


def calculate_create2_address(
    deployer_addr: Address, salt: int, init_code_hash: bytes
) -> Address:
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
    salt_bytes = salt.to_bytes(32, "big")

    # CREATE2 preimage: 0xff ++ deployer ++ salt ++ keccak256(init_code)
    preimage = b"\xff" + deployer_bytes + salt_bytes + init_code_hash
    address_bytes = keccak(preimage)[12:]
    return Address("0x" + address_bytes.hex())


def calculate_num_contracts(gas_benchmark_value: int) -> int:
    """
    Calculate the number of contracts to attack based on gas budget.

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
    # Reserve gas for orchestrator, verifier deployment, and verification
    reserved_gas = (
        ORCHESTRATOR_DEPLOY_GAS + VERIFIER_DEPLOY_GAS + VERIFICATION_GAS
    )

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
@pytest.mark.parametrize(
    "storage_depth,account_depth",
    [
        (10, 6),  # From worst_case_miner/mined_assets
    ],
)
def test_worst_depth_stateroot_recomp(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    _fork: Fork,
    gas_benchmark_value: int,
    storage_depth: int,
    account_depth: int,
) -> None:
    """
    BloatNet worst-case SSTORE attack benchmark with pre-deployed contracts.

    This test:
    1. Derives CREATE2 addresses from init_code_hash + Nick's deployer
    2. Deploys AttackOrchestrator that calls attack() on each target
    3. Fills blocks with 16M gas transactions attacking contracts
    4. Adds a verification transaction at the end to confirm success

    Args:
        blockchain_test: The blockchain test filler
        pre: Pre-state allocation
        _fork: The fork to test on (unused, provided by pytest fixture)
        gas_benchmark_value: Gas budget for benchmark
        storage_depth: Depth of storage slots in the contract
        account_depth: Account address prefix sharing depth

    """
    # Dynamically calculate number of contracts based on gas budget
    num_contracts = calculate_num_contracts(gas_benchmark_value)

    print("\nTesting with pre-deployed contracts:")
    print(f"  Storage depth: {storage_depth}")
    print(f"  Account depth: {account_depth}")
    print(f"  Gas benchmark value: {gas_benchmark_value:,}")
    print(f"  Calculated NUM_CONTRACTS: {num_contracts}")

    # Load the CREATE2 data to get the init code hash
    create2_data = load_create2_data(storage_depth, account_depth)
    init_code_hash_hex = create2_data.get("init_code_hash")
    if not init_code_hash_hex:
        json_name = f"s{storage_depth}_acc{account_depth}.json"
        raise ValueError(f"No init_code_hash found in {json_name}")

    # Remove 0x prefix if present and convert to bytes
    if init_code_hash_hex.startswith("0x"):
        init_code_hash_hex = init_code_hash_hex[2:]
    init_code_hash = bytes.fromhex(init_code_hash_hex)

    # Verify we have enough contracts in the JSON
    available_contracts = len(create2_data.get("contracts", []))
    if available_contracts == 0:
        json_name = f"s{storage_depth}_acc{account_depth}.json"
        raise ValueError(f"No contracts available in {json_name}")
    if num_contracts > available_contracts:
        warnings.warn(
            f"Requested {num_contracts} contracts but only "
            f"{available_contracts} available, using {available_contracts}",
            stacklevel=2,
        )
        num_contracts = available_contracts

    print(f"  Final NUM_CONTRACTS: {num_contracts}")

    # Create an EOA with funds for the deployer
    deployer_eoa = pre.fund_eoa(amount=DEPLOYER_INITIAL_BALANCE)

    # Get the deep storage slot for verification (downloads .sol if needed)
    deep_slot = get_deep_slot_from_sol(storage_depth)
    print(f"  Deep storage slot: {hex(deep_slot)}")

    # ABI encode constructor parameters for AttackOrchestrator
    # Constructor: constructor(address _deployer, bytes32 _initCodeHash)
    nick_deployer_bytes = bytes(NICK_DEPLOYER)
    constructor_args = nick_deployer_bytes.rjust(32, b"\x00") + init_code_hash
    orchestrator_init_code = ATTACK_ORCHESTRATOR_BYTECODE + constructor_args

    print(f"  Using init code hash from JSON: 0x{init_code_hash.hex()}")

    # Calculate orchestrator address (nonce 0)
    deployer_addr_bytes = bytes.fromhex(str(deployer_eoa)[2:])
    orch_addr_bytes = keccak(rlp.encode([deployer_addr_bytes, 0]))[12:]
    orchestrator_address = Address("0x" + orch_addr_bytes.hex())
    print(f"  Orchestrator will be deployed at: {orchestrator_address}")

    # Calculate verifier address (nonce 1)
    verifier_address_bytes = keccak(rlp.encode([deployer_addr_bytes, 1]))[12:]
    verifier_address = Address("0x" + verifier_address_bytes.hex())
    print(f"  Verifier will be deployed at: {verifier_address}")

    # Create deployment transactions
    orchestrator_deploy_tx = Transaction(
        to=None,
        data=orchestrator_init_code,
        gas_limit=ORCHESTRATOR_DEPLOY_GAS,
        sender=deployer_eoa,
        max_fee_per_gas=MAX_FEE_PER_GAS,
        max_priority_fee_per_gas=MAX_PRIORITY_FEE_PER_GAS,
    )

    verifier_deploy_tx = Transaction(
        to=None,
        data=VERIFIER_BYTECODE,
        gas_limit=VERIFIER_DEPLOY_GAS,
        sender=deployer_eoa,
        max_fee_per_gas=MAX_FEE_PER_GAS,
        max_priority_fee_per_gas=MAX_PRIORITY_FEE_PER_GAS,
    )

    # Build attack transactions
    attack_txs: list[Transaction] = []
    attack_value = DEFAULT_ATTACK_VALUE

    for batch_start in range(0, num_contracts, MAX_ATTACKS_PER_TX):
        batch_end = min(batch_start + MAX_ATTACKS_PER_TX, num_contracts)
        batch_size = batch_end - batch_start

        # Create calldata: attack(value, startIndex, endIndex)
        # Selector: 0x407f85f8 = attack(uint256,uint256,uint256)
        calldata = (
            bytes.fromhex("407f85f8")
            + attack_value.to_bytes(32, "big")
            + batch_start.to_bytes(32, "big")
            + batch_end.to_bytes(32, "big")
        )

        # Calculate gas for this batch - aim for close to 16M
        batch_gas = min(
            MAX_GAS_PER_TX, batch_size * GAS_PER_ATTACK + TX_OVERHEAD
        )

        attack_tx = Transaction(
            to=orchestrator_address,
            gas_limit=batch_gas,
            sender=deployer_eoa,
            data=calldata,
            max_fee_per_gas=MAX_FEE_PER_GAS,
            max_priority_fee_per_gas=MAX_PRIORITY_FEE_PER_GAS,
        )
        attack_txs.append(attack_tx)

    print(f"  Created {len(attack_txs)} attack transactions")

    # Calculate the last attacked contract address for verification
    last_contract_salt = num_contracts - 1
    last_contract_address = calculate_create2_address(
        NICK_DEPLOYER, last_contract_salt, init_code_hash
    )
    print(
        f"  Last contract (salt={last_contract_salt}): {last_contract_address}"
    )

    # Create verification transaction
    # Verifier.verify(address target, uint256 expectedValue)
    # Selector: bytes4(keccak256("verify(address,uint256)")) = 0x6be45db7
    verify_calldata = (
        bytes.fromhex("6be45db7")  # verify(address,uint256) selector
        + bytes.fromhex(str(last_contract_address)[2:]).rjust(32, b"\x00")
        + attack_value.to_bytes(32, "big")
    )

    verification_tx = Transaction(
        to=verifier_address,
        gas_limit=VERIFICATION_GAS,
        sender=deployer_eoa,
        data=verify_calldata,
        max_fee_per_gas=MAX_FEE_PER_GAS,
        max_priority_fee_per_gas=MAX_PRIORITY_FEE_PER_GAS,
    )

    # Build blocks - pack transactions to maximize block gas usage
    # Order: orchestrator deploy, verifier deploy, attack txs, verification
    all_txs = (
        [orchestrator_deploy_tx, verifier_deploy_tx]
        + attack_txs
        + [verification_tx]
    )

    blocks: list[Block] = []
    current_block_txs: list[Transaction] = []
    current_block_gas = 0
    max_block_gas = gas_benchmark_value

    for tx in all_txs:
        tx_gas = tx.gas_limit if tx.gas_limit else 21000

        # Ensure no single tx exceeds 16M gas limit
        if tx_gas > MAX_GAS_PER_TX:
            raise ValueError(
                f"Tx exceeds MAX_GAS_PER_TX ({MAX_GAS_PER_TX:,}): {tx_gas:,}"
            )

        # Check if adding this tx would exceed block gas limit
        if current_block_gas + tx_gas > max_block_gas and current_block_txs:
            blocks.append(Block(txs=current_block_txs))
            n_txs = len(current_block_txs)
            print(f"  Block {len(blocks)}: {n_txs} txs, {current_block_gas:,}")
            current_block_txs = [tx]
            current_block_gas = tx_gas
        else:
            current_block_txs.append(tx)
            current_block_gas += tx_gas

    # Add the last block
    if current_block_txs:
        blocks.append(Block(txs=current_block_txs))
        n_txs = len(current_block_txs)
        print(f"  Block {len(blocks)}: {n_txs} txs, {current_block_gas:,}")

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
