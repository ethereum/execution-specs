"""
Ethereum Specification.

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Entry point for the Ethereum specification.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple, final

from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes, Bytes0
from ethereum_types.frozen import slotted_freezable
from ethereum_types.numeric import U64, U256, Uint, ulen

from ethereum.crypto.hash import Hash32, keccak256
from ethereum.exceptions import (
    EthereumException,
    InsufficientBalanceError,
    InvalidBlock,
    InvalidSenderError,
)
from ethereum.forks.bpo5.blocks import Header as PreviousHeader
from ethereum.merkle_patricia_trie import root, trie_set
from ethereum.state import (
    EMPTY_ACCOUNT,
    EMPTY_CODE_HASH,
    Account,
    Address,
    BlockDiff,
)
from ethereum.state_mpt import (
    State,
    apply_changes_to_state,
    set_account,
    store_code,
)

from . import vm
from .block_access_lists import (
    BlockAccessListBuilder,
    build_block_access_list,
    hash_block_access_list,
    validate_block_access_list_gas_limit,
)
from .blocks import Block, Header, Log, Receipt, Withdrawal, encode_receipt
from .bloom import logs_bloom
from .exceptions import WrongChainIdError
from .fork_types import (
    Authorization,
    BlockAccessIndex,
    ExecutionGas,
    StateGas,
)
from .frame_processing import process_frame_transaction
from .requests import (
    BUILDER_DEPOSIT_REQUEST_TYPE,
    BUILDER_EXIT_REQUEST_TYPE,
    CONSOLIDATION_REQUEST_TYPE,
    DEPOSIT_REQUEST_TYPE,
    WITHDRAWAL_REQUEST_TYPE,
    compute_requests_hash,
    parse_deposit_requests,
)
from .state_tracker import (
    BlockState,
    TransactionState,
    clear_account_preserving_balance,
    create_ether,
    extract_block_diff,
    get_account,
    get_code,
    incorporate_tx_into_block,
    increment_nonce,
    set_account_balance,
)
from .transactions import (
    TX_MAX_GAS_LIMIT,
    BlobTransaction,
    LegacyTransaction,
    SetCodeTransaction,
    Transaction,
    calculate_effective_gas_price,
    calculate_max_gas_fee,
    chain_id,
    check_nonce,
    decode_transaction,
    encode_transaction,
    get_transaction_hash,
    has_access_list,
    recover_sender,
    validate_transaction,
)
from .transactions.frame_transaction import (
    EXPIRY_VERIFIER,
    EXPIRY_VERIFIER_CODE,
    FrameTransaction,
)
from .utils.address import compute_contract_address
from .utils.hexadecimal import hex_to_address
from .vm.eoa_delegation import is_valid_delegation
from .vm.gas import (
    MAX_BLOB_GAS_PER_BLOCK as MAX_BLOB_GAS_PER_BLOCK,
)
from .vm.gas import (
    GasCosts,
    StateGasCosts,
    TransactionGasSettlement,
    allocate_evm_gas,
    calculate_data_fee,
    calculate_excess_blob_gas,
    calculate_total_blob_gas,
    check_block_gas_capacity,
    check_max_fee_per_blob_gas,
    settle_transaction_gas,
)
from .vm.interpreter import TransactionOutput, process_top_level

BASE_FEE_MAX_CHANGE_DENOMINATOR = Uint(8)
ELASTICITY_MULTIPLIER = Uint(2)
EMPTY_OMMER_HASH = keccak256(rlp.encode([]))
SYSTEM_ADDRESS = hex_to_address("0xfffffffffffffffffffffffffffffffffffffffe")
BEACON_ROOTS_ADDRESS = hex_to_address(
    "0x000F3df6D732807Ef1319fB7B8bB8522d0Beac02"
)
SYSTEM_TRANSACTION_GAS = ExecutionGas(Uint(30000000))
SYSTEM_MAX_SSTORES_PER_CALL = Uint(16)
"""
Upper bound on the number of new storage slots a single system call is
expected to write.
"""
GWEI_TO_WEI = U256(10**9)

WITHDRAWAL_REQUEST_PREDEPLOY_ADDRESS = hex_to_address(
    "0x00000961Ef480Eb55e80D19ad83579A64c007002"
)
CONSOLIDATION_REQUEST_PREDEPLOY_ADDRESS = hex_to_address(
    "0x0000BBdDc7CE488642fb579F8B00f3a590007251"
)
BUILDER_DEPOSIT_CONTRACT_ADDRESS = hex_to_address(
    "0x0000BFF46984E3725691FA540A8C7589300D8282"
)
BUILDER_EXIT_CONTRACT_ADDRESS = hex_to_address(
    "0x000064D678505AD48F8CCB093BC65613800E8282"
)
HISTORY_STORAGE_ADDRESS = hex_to_address(
    "0x0000F90827F1C53a10cb7A02335B175320002935"
)
MAX_BLOCK_SIZE = 10_485_760
SAFETY_MARGIN = 2_097_152
MAX_RLP_BLOCK_SIZE = MAX_BLOCK_SIZE - SAFETY_MARGIN


@final
@slotted_freezable
@dataclass
class ChainContext:
    """
    Chain context needed for block execution.
    """

    chain_id: U64
    """Identify the chain for transaction signature recovery."""

    block_hashes: List[Hash32]
    """Recent ancestor hashes (up to 256) for the ``BLOCKHASH`` opcode."""

    parent_header: Header | PreviousHeader
    """Parent header used for header validation and system contracts."""


@final
@dataclass
class BlockChain:
    """
    History and current state of the block chain.
    """

    blocks: List[Block]
    state: State
    chain_id: U64


def apply_fork(old: BlockChain) -> BlockChain:
    """
    Transform the state from the previous hard fork (`old`) into the
    block chain object for this hard fork and return it.

    As required by [EIP-8141], the runtime code of the expiry verifier
    contract ([`EXPIRY_VERIFIER_CODE`][evc]) is installed at
    [`EXPIRY_VERIFIER`][ev] when this fork activates. Only the code is
    installed: the account's other fields are left untouched, so a
    previously nonexistent account keeps a zero nonce and any balance
    the account held before the fork is preserved.

    [EIP-8141]: https://eips.ethereum.org/EIPS/eip-8141
    [ev]: ref:ethereum.forks.amsterdam.transactions.frame_transaction.EXPIRY_VERIFIER
    [evc]: ref:ethereum.forks.amsterdam.transactions.frame_transaction.EXPIRY_VERIFIER_CODE
    """  # noqa: E501
    state = old.state
    existing_account = state.get_account_optional(EXPIRY_VERIFIER)
    if existing_account is None:
        existing_account = EMPTY_ACCOUNT

    code_hash = store_code(state, EXPIRY_VERIFIER_CODE)
    set_account(
        state,
        EXPIRY_VERIFIER,
        Account(
            nonce=existing_account.nonce,
            balance=existing_account.balance,
            code_hash=code_hash,
        ),
    )
    return old


def get_last_256_block_hashes(chain: BlockChain) -> List[Hash32]:
    """
    Obtain the list of hashes of the previous 256 blocks in order of
    increasing block number.

    This function will return less hashes for the first 256 blocks.

    The ``BLOCKHASH`` opcode needs to access the latest hashes on the chain,
    therefore this function retrieves them.

    Parameters
    ----------
    chain :
        History and current state.

    Returns
    -------
    recent_block_hashes : `List[Hash32]`
        Hashes of the recent 256 blocks in order of increasing block number.

    """
    recent_blocks = chain.blocks[-255:]
    # TODO: This function has not been tested rigorously
    if len(recent_blocks) == 0:
        return []

    recent_block_hashes = []

    for block in recent_blocks:
        prev_block_hash = block.header.parent_hash
        recent_block_hashes.append(prev_block_hash)

    # We are computing the hash only for the most recent block and not for
    # the rest of the blocks as they have successors which have the hash of
    # the current block as parent hash.
    most_recent_block_hash = keccak256(rlp.encode(recent_blocks[-1].header))
    recent_block_hashes.append(most_recent_block_hash)

    return recent_block_hashes


def state_transition(chain: BlockChain, block: Block) -> None:
    """
    Attempts to apply a block to an existing block chain.

    All parts of the block's contents need to be verified before being added
    to the chain. Blocks are verified by ensuring that the contents of the
    block make logical sense with the contents of the parent block. The
    information in the block's header must also match the corresponding
    information in the block.

    To implement Ethereum, in theory clients are only required to store the
    most recent 255 blocks of the chain since as far as execution is
    concerned, only those blocks are accessed. Practically, however, clients
    should store more blocks to handle reorgs.

    Parameters
    ----------
    chain :
        History and current state.
    block :
        Block to apply to `chain`.

    """
    chain_context = ChainContext(
        chain_id=chain.chain_id,
        block_hashes=get_last_256_block_hashes(chain),
        parent_header=chain.blocks[-1].header,
    )

    block_diff = execute_block(block, chain.state, chain_context)

    apply_changes_to_state(chain.state, block_diff)
    chain.blocks.append(block)
    if len(chain.blocks) > 255:
        # Real clients have to store more blocks to deal with reorgs, but the
        # protocol only requires the last 255
        chain.blocks = chain.blocks[-255:]


def execute_block(
    block: Block,
    pre_state: State,
    chain_context: ChainContext,
) -> BlockDiff:
    """
    Execute a block and validate the resulting roots against the header.

    This method is idempotent.

    Parameters
    ----------
    block :
        Block to validate and execute.
    pre_state :
        Pre-execution state provider.
    chain_context :
        Chain context that the block may need during execution.

    Returns
    -------
    block_diff : `BlockDiff`
        Account, storage, and code changes produced by block execution.

    """
    if len(rlp.encode(block)) > MAX_RLP_BLOCK_SIZE:
        raise InvalidBlock("Block rlp size exceeds MAX_RLP_BLOCK_SIZE")

    parent_header = chain_context.parent_header
    validate_header(parent_header, block.header)

    if block.ommers != ():
        raise InvalidBlock

    block_state = BlockState(pre_state=pre_state)

    block_env = vm.BlockEnvironment(
        chain_id=chain_context.chain_id,
        state=block_state,
        block_gas_limit=block.header.gas_limit,
        block_hashes=chain_context.block_hashes,
        coinbase=block.header.coinbase,
        number=block.header.number,
        base_fee_per_gas=block.header.base_fee_per_gas,
        time=block.header.timestamp,
        prev_randao=block.header.prev_randao,
        excess_blob_gas=block.header.excess_blob_gas,
        parent_beacon_block_root=block.header.parent_beacon_block_root,
        block_access_list_builder=BlockAccessListBuilder(),
        slot_number=block.header.slot_number,
    )

    block_output = apply_body(
        block_env=block_env,
        transactions=block.transactions,
        withdrawals=block.withdrawals,
    )
    block_diff = extract_block_diff(block_state)
    block_state_root = pre_state.compute_state_root(block_diff)
    transactions_root = root(block_output.transactions_trie)
    receipt_root = root(block_output.receipts_trie)
    block_logs_bloom = logs_bloom(block_output.block_logs)
    withdrawals_root = root(block_output.withdrawals_trie)
    requests_hash = compute_requests_hash(block_output.requests)
    computed_block_access_list_hash = hash_block_access_list(
        block_output.block_access_list
    )

    block_gas_used = max(
        block_output.block_gas_used,
        block_output.block_state_gas_used,
    )
    if block_gas_used != block.header.gas_used:
        raise InvalidBlock(f"{block_gas_used} != {block.header.gas_used}")
    if transactions_root != block.header.transactions_root:
        raise InvalidBlock
    if block_state_root != block.header.state_root:
        raise InvalidBlock
    if receipt_root != block.header.receipt_root:
        raise InvalidBlock
    if block_logs_bloom != block.header.bloom:
        raise InvalidBlock
    if withdrawals_root != block.header.withdrawals_root:
        raise InvalidBlock
    if block_output.blob_gas_used != block.header.blob_gas_used:
        raise InvalidBlock
    if requests_hash != block.header.requests_hash:
        raise InvalidBlock
    if computed_block_access_list_hash != block.header.block_access_list_hash:
        raise InvalidBlock("Invalid block access list hash")

    return block_diff


def calculate_base_fee_per_gas(
    block_gas_limit: Uint,
    parent_gas_limit: Uint,
    parent_gas_used: Uint,
    parent_base_fee_per_gas: Uint,
) -> Uint:
    """
    Calculates the base fee per gas for the block.

    Parameters
    ----------
    block_gas_limit :
        Gas limit of the block for which the base fee is being calculated.
    parent_gas_limit :
        Gas limit of the parent block.
    parent_gas_used :
        Gas used in the parent block.
    parent_base_fee_per_gas :
        Base fee per gas of the parent block.

    Returns
    -------
    base_fee_per_gas : `Uint`
        Base fee per gas for the block.

    """
    parent_gas_target = parent_gas_limit // ELASTICITY_MULTIPLIER
    if not check_gas_limit(block_gas_limit, parent_gas_limit):
        raise InvalidBlock

    if parent_gas_used == parent_gas_target:
        expected_base_fee_per_gas = parent_base_fee_per_gas
    elif parent_gas_used > parent_gas_target:
        gas_used_delta = parent_gas_used - parent_gas_target

        parent_fee_gas_delta = parent_base_fee_per_gas * gas_used_delta
        target_fee_gas_delta = parent_fee_gas_delta // parent_gas_target

        base_fee_per_gas_delta = max(
            target_fee_gas_delta // BASE_FEE_MAX_CHANGE_DENOMINATOR,
            Uint(1),
        )

        expected_base_fee_per_gas = (
            parent_base_fee_per_gas + base_fee_per_gas_delta
        )
    else:
        gas_used_delta = parent_gas_target - parent_gas_used

        parent_fee_gas_delta = parent_base_fee_per_gas * gas_used_delta
        target_fee_gas_delta = parent_fee_gas_delta // parent_gas_target

        base_fee_per_gas_delta = (
            target_fee_gas_delta // BASE_FEE_MAX_CHANGE_DENOMINATOR
        )

        expected_base_fee_per_gas = (
            parent_base_fee_per_gas - base_fee_per_gas_delta
        )

    return Uint(expected_base_fee_per_gas)


def validate_header(
    parent_header: Header | PreviousHeader, header: Header
) -> None:
    """
    Verify a block header against its parent.

    In order to consider a block's header valid, the logic for the
    quantities in the header should match the logic for the block itself.
    For example the header timestamp should be greater than the block's parent
    timestamp because the block was created *after* the parent block.
    Additionally, the block's number should be directly following the parent
    block's number since it is the next block in the sequence.

    Parameters
    ----------
    parent_header :
        Header of the parent block.
    header :
        Header to check for correctness.

    """
    if header.number < Uint(1):
        raise InvalidBlock

    excess_blob_gas = calculate_excess_blob_gas(parent_header)
    if header.excess_blob_gas != excess_blob_gas:
        raise InvalidBlock

    if header.gas_used > header.gas_limit:
        raise InvalidBlock

    expected_base_fee_per_gas = calculate_base_fee_per_gas(
        header.gas_limit,
        parent_header.gas_limit,
        parent_header.gas_used,
        parent_header.base_fee_per_gas,
    )
    if expected_base_fee_per_gas != header.base_fee_per_gas:
        raise InvalidBlock
    if header.timestamp <= parent_header.timestamp:
        raise InvalidBlock
    if header.number != parent_header.number + Uint(1):
        raise InvalidBlock
    if len(header.extra_data) > 32:
        raise InvalidBlock
    if header.difficulty != 0:
        raise InvalidBlock
    if header.nonce != b"\x00\x00\x00\x00\x00\x00\x00\x00":
        raise InvalidBlock
    if header.ommers_hash != EMPTY_OMMER_HASH:
        raise InvalidBlock

    block_parent_hash = keccak256(rlp.encode(parent_header))
    if header.parent_hash != block_parent_hash:
        raise InvalidBlock


def check_transaction(
    block_env: vm.BlockEnvironment,
    block_output: vm.BlockOutput,
    tx: Transaction,
    index: Uint,
) -> vm.TransactionEnvironment:
    """
    Admit a raw transaction and build its execution environment.

    Recover the sender, statically validate the transaction, and check
    that it is includable in the block, in that order, so that a
    transaction invalid in several ways reports the earliest failure.

    Parameters
    ----------
    block_env :
        The block scoped environment.
    block_output :
        The block output for the current block.
    tx :
        The transaction.
    index :
        The index of the current transaction.

    Returns
    -------
    tx_env :
        The environment for executing the transaction.

    Raises
    ------
    InvalidBlock :
        If the transaction is not includable.
    InvalidSignatureError :
        If the transaction's signature is invalid.
    InsufficientTransactionGasError :
        If the transaction does not provide enough gas to cover its
        intrinsic cost.
    GasUsedExceedsLimitError :
        If the gas used by the transaction exceeds the block's gas limit.
    NonceMismatchError :
        If the nonce of the transaction is not equal to the sender's nonce.
    InsufficientBalanceError :
        If the sender's balance is not enough to pay for the transaction.
    InvalidSenderError :
        If the transaction is from an address that does not exist anymore.
    InsufficientMaxFeePerGasError :
        If the maximum fee per gas is insufficient for the transaction.
    InsufficientMaxFeePerBlobGasError :
        If the maximum fee per blob gas is insufficient for the transaction.
    BlobGasLimitExceededError :
        If the blob gas used by the transaction exceeds the block's blob gas
        limit.

    """
    assert not isinstance(tx, FrameTransaction)

    sender = recover_sender(tx)
    intrinsic = validate_transaction(tx, sender)
    tx_state = TransactionState(parent=block_env.state)

    # Under the reservoir model any part of the gas limit can end up
    # in either dimension, so the whole limit is reserved in both; a
    # single transaction's execution gas is capped by EIP-7825.
    check_block_gas_capacity(
        block_env,
        block_output,
        min(TX_MAX_GAS_LIMIT, tx.gas),
        tx.gas,
        calculate_total_blob_gas(tx),
    )

    sender_account = get_account(tx_state, sender)

    effective_gas_price = calculate_effective_gas_price(
        tx, block_env.base_fee_per_gas
    )
    max_gas_fee = calculate_max_gas_fee(tx, tx.gas)

    if isinstance(tx, BlobTransaction):
        check_max_fee_per_blob_gas(
            tx.blob_versioned_hashes,
            tx.max_fee_per_blob_gas,
            block_env.excess_blob_gas,
        )

        max_gas_fee += Uint(calculate_total_blob_gas(tx)) * Uint(
            tx.max_fee_per_blob_gas
        )
        blob_versioned_hashes = tx.blob_versioned_hashes
    else:
        blob_versioned_hashes = ()

    check_nonce(tx, sender_account.nonce)

    if Uint(sender_account.balance) < max_gas_fee + Uint(tx.value):
        raise InsufficientBalanceError("insufficient sender balance")
    sender_code = get_code(tx_state, sender_account.code_hash)
    if sender_account.code_hash != EMPTY_CODE_HASH and not is_valid_delegation(
        sender_code
    ):
        raise InvalidSenderError("not EOA")

    # Split the EVM gas into an execution-gas grant (capped by the
    # remaining execution-gas budget) and a state gas reservoir.
    allocation = allocate_evm_gas(tx.gas, intrinsic)

    access_list_addresses = set()
    access_list_storage_keys = set()
    if has_access_list(tx):
        for access in tx.access_list:
            access_list_addresses.add(access.account)
            for slot in access.slots:
                access_list_storage_keys.add((access.account, slot))

    authorizations: Tuple[Authorization, ...] = ()
    if isinstance(tx, SetCodeTransaction):
        authorizations = tx.authorizations

    if isinstance(tx.to, Bytes0):
        is_create = True
        # A creation's frame runs at the address the contract
        # deploys to.
        recipient = compute_contract_address(sender, sender_account.nonce)
    else:
        is_create = False
        recipient = tx.to

    accounts_with_paid_writes = {sender}
    if is_create or tx.value > U256(0):
        accounts_with_paid_writes.add(recipient)

    return vm.TransactionEnvironment(
        origin=sender,
        gas_limit=tx.gas,
        effective_gas_price=effective_gas_price,
        execution_gas_grant=allocation.execution_gas,
        state_gas_reservoir=allocation.state_gas_reservoir,
        calldata_floor=intrinsic.calldata_floor,
        access_list_addresses=access_list_addresses,
        access_list_storage_keys=access_list_storage_keys,
        accounts_with_paid_writes=accounts_with_paid_writes,
        state=tx_state,
        blob_versioned_hashes=blob_versioned_hashes,
        authorizations=authorizations,
        index_in_block=index,
        tx_hash=get_transaction_hash(encode_transaction(tx)),
        top_level_context=vm.TopLevelContext(
            recipient=recipient,
            is_create=is_create,
            data=tx.data,
            value=tx.value,
        ),
        frame_context=None,
    )


def make_receipt(
    tx: Transaction,
    error: Optional[EthereumException],
    cumulative_gas_used: Uint,
    logs: Tuple[Log, ...],
) -> Bytes | Receipt:
    """
    Make the receipt for a transaction that was executed.

    Parameters
    ----------
    tx :
        The executed transaction.
    error :
        Error in the top level frame of the transaction, if any.
    cumulative_gas_used :
        The total gas used so far in the block after the transaction was
        executed. This is the gas used after refunds.
    logs :
        The logs produced by the transaction.

    Returns
    -------
    receipt :
        The receipt for the transaction.

    """
    receipt = Receipt(
        succeeded=error is None,
        cumulative_gas_used=cumulative_gas_used,
        bloom=logs_bloom(logs),
        logs=logs,
    )

    return encode_receipt(tx, receipt)


def process_checked_system_transaction(
    block_env: vm.BlockEnvironment,
    target_address: Address,
    data: Bytes,
) -> TransactionOutput:
    """
    Process a system transaction and raise an error if the contract does not
    contain code or if the transaction fails.

    Parameters
    ----------
    block_env :
        The block scoped environment.
    target_address :
        Address of the contract to call.
    data :
        Data to pass to the contract.

    Returns
    -------
    system_tx_output : `TransactionOutput`
        The settled output of the system transaction.

    """
    # Pre-check that the system contract has code. We use a throwaway
    # TransactionState here that is *never* propagated back to BlockState
    # (no incorporate_tx_into_block call); the same get_account / get_code
    # lookups are performed and properly tracked by
    # process_unchecked_system_transaction below, which this function
    # always calls. Reading via a TransactionState (rather than directly
    # against pre_state) lets us see system contracts deployed earlier in
    # the same block — see EIP-7002 and EIP-7251 for this edge case.
    untracked_state = TransactionState(parent=block_env.state)
    system_contract_code = get_code(
        untracked_state,
        get_account(untracked_state, target_address).code_hash,
    )

    if len(system_contract_code) == 0:
        raise InvalidBlock(
            f"System contract address {target_address.hex()} does not "
            "contain code"
        )

    system_tx_output = process_unchecked_system_transaction(
        block_env,
        target_address,
        data,
    )

    if system_tx_output.error:
        raise InvalidBlock(
            f"System contract ({target_address.hex()}) call failed: "
            f"{system_tx_output.error}"
        )

    return system_tx_output


def process_unchecked_system_transaction(
    block_env: vm.BlockEnvironment,
    target_address: Address,
    data: Bytes,
) -> TransactionOutput:
    """
    Process a system transaction without checking if the contract contains
    code or if the transaction fails.

    Parameters
    ----------
    block_env :
        The block scoped environment.
    target_address :
        Address of the contract to call.
    data :
        Data to pass to the contract.

    Returns
    -------
    system_tx_output : `TransactionOutput`
        The settled output of the system transaction.

    """
    system_tx_state = TransactionState(parent=block_env.state)

    tx_env = vm.TransactionEnvironment(
        origin=SYSTEM_ADDRESS,
        gas_limit=SYSTEM_TRANSACTION_GAS,
        effective_gas_price=block_env.base_fee_per_gas,
        execution_gas_grant=SYSTEM_TRANSACTION_GAS,
        state_gas_reservoir=StateGas(
            StateGasCosts.STORAGE_SET * SYSTEM_MAX_SSTORES_PER_CALL
        ),
        calldata_floor=Uint(0),
        access_list_addresses=set(),
        access_list_storage_keys=set(),
        # A system transaction charges no gas, so no write is paid for.
        accounts_with_paid_writes=set(),
        state=system_tx_state,
        blob_versioned_hashes=(),
        authorizations=(),
        index_in_block=None,
        tx_hash=None,
        top_level_context=vm.TopLevelContext(
            recipient=target_address,
            is_create=False,
            data=data,
            value=U256(0),
        ),
        frame_context=None,
    )

    system_tx_output = process_top_level(block_env, tx_env)

    incorporate_tx_into_block(
        system_tx_state, block_env.block_access_list_builder
    )

    return system_tx_output


def apply_body(
    block_env: vm.BlockEnvironment,
    transactions: Tuple[LegacyTransaction | Bytes, ...],
    withdrawals: Tuple[Withdrawal, ...],
) -> vm.BlockOutput:
    """
    Executes a block.

    Many of the contents of a block are stored in data structures called
    tries. There is a transactions trie which is similar to a ledger of the
    transactions stored in the current block. There is also a receipts trie
    which stores the results of executing a transaction, like the post state
    and gas used. This function creates and executes the block that is to be
    added to the chain.

    Parameters
    ----------
    block_env :
        The block scoped environment.
    transactions :
        Transactions included in the block.
    withdrawals :
        Withdrawals to be processed in the current block.

    Returns
    -------
    block_output :
        The block output for the current block.

    """
    block_output = vm.BlockOutput()

    process_unchecked_system_transaction(
        block_env=block_env,
        target_address=BEACON_ROOTS_ADDRESS,
        data=block_env.parent_beacon_block_root,
    )

    process_unchecked_system_transaction(
        block_env=block_env,
        target_address=HISTORY_STORAGE_ADDRESS,
        data=block_env.block_hashes[-1],  # The parent hash
    )

    for i, tx in enumerate(map(decode_transaction, transactions)):
        process_transaction(block_env, block_output, tx, Uint(i))

    # EIP-7928: Post-execution operations use index N+1
    block_env.block_access_list_builder.block_access_index = BlockAccessIndex(
        ulen(transactions) + Uint(1)
    )

    process_withdrawals(block_env, block_output, withdrawals)

    process_general_purpose_requests(
        block_env=block_env,
        block_output=block_output,
    )

    block_output.block_access_list = build_block_access_list(
        block_env.block_access_list_builder, block_env.state
    )

    # Validate block access list gas limit constraint (EIP-7928)
    validate_block_access_list_gas_limit(
        block_access_list=block_output.block_access_list,
        block_gas_limit=block_env.block_gas_limit,
    )

    return block_output


def process_general_purpose_requests(
    block_env: vm.BlockEnvironment,
    block_output: vm.BlockOutput,
) -> None:
    """
    Process all the requests in the block.

    Parameters
    ----------
    block_env :
        The execution environment for the Block.
    block_output :
        The block output for the current block.

    """
    # Requests are to be in ascending order of request type
    deposit_requests = parse_deposit_requests(block_output)
    requests_from_execution = block_output.requests
    if len(deposit_requests) > 0:
        requests_from_execution.append(DEPOSIT_REQUEST_TYPE + deposit_requests)

    system_withdrawal_tx_output = process_checked_system_transaction(
        block_env=block_env,
        target_address=WITHDRAWAL_REQUEST_PREDEPLOY_ADDRESS,
        data=b"",
    )

    if len(system_withdrawal_tx_output.return_data) > 0:
        requests_from_execution.append(
            WITHDRAWAL_REQUEST_TYPE + system_withdrawal_tx_output.return_data
        )

    system_consolidation_tx_output = process_checked_system_transaction(
        block_env=block_env,
        target_address=CONSOLIDATION_REQUEST_PREDEPLOY_ADDRESS,
        data=b"",
    )

    if len(system_consolidation_tx_output.return_data) > 0:
        requests_from_execution.append(
            CONSOLIDATION_REQUEST_TYPE
            + system_consolidation_tx_output.return_data
        )

    system_builder_deposit_tx_output = process_checked_system_transaction(
        block_env=block_env,
        target_address=BUILDER_DEPOSIT_CONTRACT_ADDRESS,
        data=b"",
    )

    if len(system_builder_deposit_tx_output.return_data) > 0:
        requests_from_execution.append(
            BUILDER_DEPOSIT_REQUEST_TYPE
            + system_builder_deposit_tx_output.return_data
        )

    system_builder_exit_tx_output = process_checked_system_transaction(
        block_env=block_env,
        target_address=BUILDER_EXIT_CONTRACT_ADDRESS,
        data=b"",
    )

    if len(system_builder_exit_tx_output.return_data) > 0:
        requests_from_execution.append(
            BUILDER_EXIT_REQUEST_TYPE
            + system_builder_exit_tx_output.return_data
        )


def update_sender_state(
    block_env: vm.BlockEnvironment,
    tx_env: vm.TransactionEnvironment,
    tx: Transaction,
) -> None:
    """
    Debit the sender for the transaction's maximum possible gas fee.

    Increment the sender's nonce and deduct the largest fee the
    transaction could incur -- its gas limit priced at the effective gas
    price, plus the blob fee resolved at inclusion -- up front.
    Execution later refunds whatever execution gas was not spent.

    Parameters
    ----------
    block_env :
        The block's execution environment.
    tx_env :
        The transaction's execution environment.
    tx :
        The transaction being charged.

    """
    tx_state = tx_env.state
    sender = tx_env.origin
    sender_account = get_account(tx_state, sender)

    effective_gas_fee = tx_env.gas_limit * tx_env.effective_gas_price
    if isinstance(tx, BlobTransaction):
        blob_gas_fee = calculate_data_fee(block_env.excess_blob_gas, tx)
    else:
        blob_gas_fee = Uint(0)

    increment_nonce(tx_state, sender)

    sender_balance_after_gas_fee = (
        Uint(sender_account.balance) - effective_gas_fee - blob_gas_fee
    )
    set_account_balance(tx_state, sender, U256(sender_balance_after_gas_fee))


def disburse_gas_fees(
    block_env: vm.BlockEnvironment,
    tx_env: vm.TransactionEnvironment,
    settlement: TransactionGasSettlement,
    payer: Address,
) -> None:
    """
    Refund the payer's unspent gas and pay the priority fee.

    Return the gas the transaction did not use to the ``payer`` that
    fronted the maximum fee at inclusion, priced at the effective gas
    price, and credit the coinbase with the priority fee on the gas that
    was used.

    Parameters
    ----------
    block_env :
        The block scoped environment.
    tx_env :
        The transaction's execution environment.
    settlement :
        The settled gas amounts.
    payer :
        The account that fronted the maximum gas fee and receives the
        refund.

    """
    tx_state = tx_env.state
    gas_refund_amount = settlement.gas_left * tx_env.effective_gas_price

    priority_fee_per_gas = (
        tx_env.effective_gas_price - block_env.base_fee_per_gas
    )
    transaction_fee = settlement.gas_used * priority_fee_per_gas

    create_ether(tx_state, payer, U256(gas_refund_amount))
    create_ether(tx_state, block_env.coinbase, U256(transaction_fee))


def process_transaction(
    block_env: vm.BlockEnvironment,
    block_output: vm.BlockOutput,
    tx: Transaction,
    index: Uint,
) -> None:
    """
    Execute a transaction against the provided environment.

    This function processes the actions needed to execute a transaction.
    It decrements the sender's account balance after calculating the gas fee
    and refunds them the proper amount after execution. Calling contracts,
    deploying code, and incrementing nonces are all examples of actions that
    happen within this function or from a call made within this function.

    Accounts that are marked for deletion are processed and destroyed after
    execution.

    Parameters
    ----------
    block_env :
        Environment for the Ethereum Virtual Machine.
    block_output :
        The block output for the current block.
    tx :
        Transaction to execute.
    index:
        Index of the transaction in the block.

    """
    block_env.block_access_list_builder.block_access_index = BlockAccessIndex(
        index + Uint(1)
    )

    trie_set(
        block_output.transactions_trie,
        rlp.encode(index),
        encode_transaction(tx),
    )

    tx_chain_id = chain_id(tx)
    if tx_chain_id is not None and tx_chain_id != block_env.chain_id:
        raise WrongChainIdError(
            expected=block_env.chain_id,
            actual=tx_chain_id,
        )

    if isinstance(tx, FrameTransaction):
        return process_frame_transaction(block_env, block_output, tx, index)

    tx_env = check_transaction(block_env, block_output, tx, index)

    update_sender_state(block_env, tx_env, tx)

    tx_output = process_top_level(block_env, tx_env)

    settlement = settle_transaction_gas(
        tx_env.gas_limit,
        tx_env.calldata_floor,
        tx_output.gas_left,
        tx_output.state_gas_left,
        tx_output.refund_counter,
        tx_output.state_gas_used,
    )

    disburse_gas_fees(block_env, tx_env, settlement, tx_env.origin)

    block_output.block_gas_used += settlement.execution_gas_used
    block_output.block_state_gas_used += settlement.state_gas_used
    block_output.blob_gas_used += calculate_total_blob_gas(tx)

    block_output.cumulative_gas_used += settlement.gas_used
    receipt = make_receipt(
        tx, tx_output.error, block_output.cumulative_gas_used, tx_output.logs
    )

    receipt_key = rlp.encode(Uint(index))
    block_output.receipt_keys += (receipt_key,)

    trie_set(
        block_output.receipts_trie,
        receipt_key,
        receipt,
    )

    block_output.block_logs += tx_output.logs

    for address in tx_output.accounts_to_delete:
        clear_account_preserving_balance(tx_env.state, address)

    incorporate_tx_into_block(
        tx_env.state, block_env.block_access_list_builder
    )


def process_withdrawals(
    block_env: vm.BlockEnvironment,
    block_output: vm.BlockOutput,
    withdrawals: Tuple[Withdrawal, ...],
) -> None:
    """
    Increase the balance of the withdrawing account.
    """
    wd_state = TransactionState(parent=block_env.state)

    for i, wd in enumerate(withdrawals):
        trie_set(
            block_output.withdrawals_trie,
            rlp.encode(Uint(i)),
            rlp.encode(wd),
        )

        create_ether(wd_state, wd.address, U256(wd.amount) * GWEI_TO_WEI)

    incorporate_tx_into_block(wd_state, block_env.block_access_list_builder)


def check_gas_limit(gas_limit: Uint, parent_gas_limit: Uint) -> bool:
    """
    Validates the gas limit for a block.

    The bounds of the gas limit, ``max_adjustment_delta``, is set as the
    quotient of the parent block's gas limit and the
    ``LIMIT_ADJUSTMENT_FACTOR``. Therefore, if the gas limit that is passed
    through as a parameter is greater than or equal to the *sum* of the
    parent's gas and the adjustment delta then the limit for gas is too high
    and fails this function's check. Similarly, if the limit is less than or
    equal to the *difference* of the parent's gas and the adjustment delta *or*
    the predefined ``LIMIT_MINIMUM`` then this function's check fails because
    the gas limit doesn't allow for a sufficient or reasonable amount of gas to
    be used on a block.

    Parameters
    ----------
    gas_limit :
        Gas limit to validate.

    parent_gas_limit :
        Gas limit of the parent block.

    Returns
    -------
    check : `bool`
        True if gas limit constraints are satisfied, False otherwise.

    """
    max_adjustment_delta = parent_gas_limit // GasCosts.LIMIT_ADJUSTMENT_FACTOR
    if gas_limit >= parent_gas_limit + max_adjustment_delta:
        return False
    if gas_limit <= parent_gas_limit - max_adjustment_delta:
        return False
    if gas_limit < GasCosts.LIMIT_MINIMUM:
        return False

    return True
