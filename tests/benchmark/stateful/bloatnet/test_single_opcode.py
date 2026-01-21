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
