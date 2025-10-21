"""
Converter module for transforming fuzzer DTOs to EEST domain models.

This module performs explicit transformation from fuzzer's
JSON-RPC format (captured in DTOs) to EEST's internal domain
models (Transaction, Account, etc.).

Key Responsibilities:
1. Field mapping (gas → gas_limit, from → sender, etc.)
2. Creating EOA objects from private keys
3. Building proper EEST domain models with all required context
4. Preventing TestAddress pollution by setting sender
   BEFORE model_post_init
"""

from typing import Dict

from ethereum_test_base_types import Address, Hash, HexNumber
from ethereum_test_forks import Fork
from ethereum_test_specs import BlockchainTest
from ethereum_test_tools import Account, AuthorizationTuple, Block, Transaction
from ethereum_test_types import Alloc, Environment
from ethereum_test_types.account_types import EOA

from .models import (
    FuzzerAccountInput,
    FuzzerAuthorizationInput,
    FuzzerOutput,
    FuzzerTransactionInput,
)


def fuzzer_account_to_eest_account(
    fuzzer_account: FuzzerAccountInput,
) -> Account:
    """
    Convert fuzzer account DTO to EEST Account domain model.

    Args:
        fuzzer_account: Raw account data from fuzzer

    Returns:
        EEST Account ready for pre-state

    """
    return Account(
        balance=fuzzer_account.balance,
        nonce=fuzzer_account.nonce,
        code=fuzzer_account.code,
        storage=fuzzer_account.storage,
    )


def fuzzer_authorization_to_eest(
    fuzzer_auth: FuzzerAuthorizationInput,
) -> AuthorizationTuple:
    """
    Convert fuzzer authorization DTO to EEST AuthorizationTuple.

    Args:
        fuzzer_auth: Raw authorization data from fuzzer

    Returns:
        EEST AuthorizationTuple for EIP-7702 transactions

    """
    return AuthorizationTuple(
        chain_id=fuzzer_auth.chain_id,
        address=fuzzer_auth.address,
        nonce=fuzzer_auth.nonce,
        v=fuzzer_auth.v,
        r=fuzzer_auth.r,
        s=fuzzer_auth.s,
    )


def fuzzer_transaction_to_eest_transaction(
    fuzzer_tx: FuzzerTransactionInput,
    sender_eoa: EOA,
) -> Transaction:
    """
    Convert fuzzer transaction DTO to EEST Transaction domain model.

    This function performs explicit field mapping and MUST set sender BEFORE
    calling Transaction constructor to prevent TestAddress injection.

    Key Mappings:
    - fuzzer_tx.gas → transaction.gas_limit (JSON-RPC → EEST naming)
    - fuzzer_tx.from_ → sender_eoa (Address → EOA with private key)
    - fuzzer_tx.data → transaction.data (same field, explicit for clarity)

    Args:
        fuzzer_tx: Raw transaction data from fuzzer
        sender_eoa: EOA object created from private key (prevents TestAddress)

    Returns:
        EEST Transaction ready for block generation

    """
    # Build authorization list if present
    auth_list = None
    if fuzzer_tx.authorization_list:
        auth_list = [
            fuzzer_authorization_to_eest(auth)
            for auth in fuzzer_tx.authorization_list
        ]

    # Create Transaction with sender set BEFORE model_post_init runs
    # This prevents Transaction.model_post_init from injecting TestAddress
    return Transaction(
        sender=sender_eoa,  # ✓ Set explicitly to prevent TestAddress
        to=fuzzer_tx.to,
        gas_limit=fuzzer_tx.gas,  # ✓ Explicit mapping: gas → gas_limit
        gas_price=fuzzer_tx.gas_price,
        max_fee_per_gas=fuzzer_tx.max_fee_per_gas,
        max_priority_fee_per_gas=fuzzer_tx.max_priority_fee_per_gas,
        nonce=fuzzer_tx.nonce,
        data=fuzzer_tx.data,
        value=fuzzer_tx.value,
        access_list=fuzzer_tx.access_list,
        blob_versioned_hashes=fuzzer_tx.blob_versioned_hashes,
        max_fee_per_blob_gas=fuzzer_tx.max_fee_per_blob_gas,
        authorization_list=auth_list,
    )


def create_sender_eoa_map(
    accounts: Dict[Address, FuzzerAccountInput],
) -> Dict[Address, EOA]:
    """
    Create map of addresses to EOA objects from accounts with private keys.

    Args:
        accounts: Dictionary of address to fuzzer account data

    Returns:
        Dictionary mapping addresses to EOA objects for transaction signing

    Raises:
        AssertionError: If private key doesn't match the account address

    """
    senders: Dict[Address, EOA] = {}

    for addr, account in accounts.items():
        if account.private_key is None:
            continue

        # Create EOA from private key
        sender = EOA(key=account.private_key)

        # Verify private key matches address (safety check)
        assert Address(sender) == addr, (
            f"Private key for account {addr} does not match derived address {sender}"
        )

        senders[addr] = sender

    return senders


def blockchain_test_from_fuzzer(
    fuzzer_output: FuzzerOutput,
    fork: Fork,
    num_blocks: int = 1,
    block_strategy: str = "distribute",
    block_time: int = 12,
) -> BlockchainTest:
    """
    Convert fuzzer output to BlockchainTest instance.

    This is the main entry point for fuzzer-to-EEST conversion.
    It orchestrates:
    1. Parsing and validation (already done by FuzzerOutput DTO)
    2. Creating EOA objects from private keys
    3. Converting DTOs to domain models
    4. Building blocks and test structure

    Args:
        fuzzer_output: Parsed and validated fuzzer output (DTO)
        fork: Fork to use for the test
        num_blocks: Number of blocks to generate
        block_strategy: How to distribute transactions across blocks
                       - "distribute": Split evenly maintaining
                         nonce order
                       - "first-block": All transactions in first
                         block
        block_time: Seconds between block timestamps

    Returns:
        BlockchainTest instance ready for fixture generation

    Raises:
        AssertionError: If invariants are violated
                       (sender validation, etc.)

    """
    # Step 1: Convert accounts to EEST Account domain models
    pre_dict: Dict[Address, Account | None] = {}
    for addr, fuzzer_account in fuzzer_output.accounts.items():
        pre_dict[addr] = fuzzer_account_to_eest_account(fuzzer_account)
    pre = Alloc(pre_dict)

    # Step 2: Create EOA map for transaction signing
    sender_eoa_map = create_sender_eoa_map(fuzzer_output.accounts)

    # Step 3: Convert transactions to EEST Transaction domain models
    eest_transactions: list[Transaction] = []
    for fuzzer_tx in fuzzer_output.transactions:
        # Verify sender has private key
        assert fuzzer_tx.from_ in sender_eoa_map, (
            f"Sender {fuzzer_tx.from_} not found in accounts with private keys"
        )

        # Convert with explicit sender (prevents TestAddress injection)
        eest_tx = fuzzer_transaction_to_eest_transaction(
            fuzzer_tx,
            sender_eoa=sender_eoa_map[fuzzer_tx.from_],
        )
        eest_transactions.append(eest_tx)

    # Step 4: Build genesis environment
    env = fuzzer_output.env
    genesis_env = Environment(
        fee_recipient=env.fee_recipient,
        difficulty=0,  # Post-merge
        gas_limit=int(env.gas_limit),
        number=0,
        timestamp=HexNumber(int(env.timestamp) - 12),
        prev_randao=env.prev_randao or Hash(0),
        base_fee_per_gas=env.base_fee_per_gas
        if env.base_fee_per_gas
        else None,
        excess_blob_gas=env.excess_blob_gas if env.excess_blob_gas else None,
        blob_gas_used=env.blob_gas_used if env.blob_gas_used else None,
    ).set_fork_requirements(fork)

    # Step 5: Distribute transactions across blocks
    blocks = _distribute_transactions_to_blocks(
        eest_transactions,
        num_blocks,
        block_strategy,
        block_time,
        env,
        fuzzer_output.parent_beacon_block_root,
    )

    return BlockchainTest(
        pre=pre,
        blocks=blocks,
        post={},  # Post-state verification can be added later
        genesis_environment=genesis_env,
        chain_id=fuzzer_output.chain_id,
    )


def _distribute_transactions_to_blocks(
    transactions: list[Transaction],
    num_blocks: int,
    strategy: str,
    block_time: int,
    base_env: Environment,
    parent_beacon_block_root: Hash | None,
) -> list[Block]:
    """
    Distribute transactions across multiple blocks.

    Args:
        transactions: List of EEST Transaction objects (ready for execution)
        num_blocks: Number of blocks to create
        strategy: Distribution strategy ("distribute" or "first-block")
        block_time: Seconds between blocks
        base_env: Base environment for first block
        parent_beacon_block_root: Beacon root (only for first block)

    Returns:
        List of Block objects

    """
    if strategy == "first-block":
        # All transactions in first block, rest empty
        tx_distribution = [transactions] + [[] for _ in range(num_blocks - 1)]
    elif strategy == "distribute":
        # Split transactions evenly maintaining nonce order
        if not transactions:
            tx_distribution = [[] for _ in range(num_blocks)]
        else:
            result = []
            chunk_size = len(transactions) // num_blocks
            remainder = len(transactions) % num_blocks

            start = 0
            for i in range(num_blocks):
                # Distribute remainder across first blocks
                current_chunk_size = chunk_size + (1 if i < remainder else 0)
                end = start + current_chunk_size
                result.append(transactions[start:end])
                start = end

            tx_distribution = result
    else:
        raise ValueError(f"Unknown block strategy: {strategy}")

    # Create blocks with incrementing timestamps
    base_timestamp = int(base_env.timestamp)
    blocks = []
    for i, block_txs in enumerate(tx_distribution):
        blocks.append(
            Block(
                txs=block_txs,
                timestamp=base_timestamp + (i * block_time),
                fee_recipient=base_env.fee_recipient,
                parent_beacon_block_root=parent_beacon_block_root
                if i == 0
                else None,
            )
        )

    return blocks
