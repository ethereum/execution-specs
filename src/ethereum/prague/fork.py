"""
Ethereum Specification
^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Entry point for the Ethereum specification.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple, Union

from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes, Bytes32
from ethereum_types.numeric import U64, U256, Uint

from ethereum.crypto.elliptic_curve import secp256k1_recover
from ethereum.crypto.hash import Hash32, keccak256
from ethereum.exceptions import EthereumException, InvalidBlock

from . import vm
from .blocks import Block, Header, Log, Receipt, Withdrawal, encode_receipt
from .bloom import logs_bloom
from .fork_types import Address, Authorization, Bloom, Root, VersionedHash
from .requests import (
    CONSOLIDATION_REQUEST_TYPE,
    DEPOSIT_REQUEST_TYPE,
    WITHDRAWAL_REQUEST_TYPE,
    compute_requests_hash,
    parse_deposit_requests_from_receipt,
)
from .state import (
    State,
    TransientStorage,
    account_exists_and_is_empty,
    destroy_account,
    destroy_touched_empty_accounts,
    get_account,
    increment_nonce,
    process_withdrawal,
    set_account_balance,
    state_root,
)
from .transactions import (
    AccessListTransaction,
    BlobTransaction,
    FeeMarketTransaction,
    LegacyTransaction,
    SetCodeTransaction,
    Transaction,
    calculate_inclusion_gas_cost,
    calculate_intrinsic_gas_cost,
    decode_transaction,
    encode_transaction,
    recover_sender,
    validate_transaction,
)
from .trie import Trie, root, trie_set
from .utils.hexadecimal import hex_to_address
from .utils.message import prepare_message
from .vm import Message
from .vm.eoa_delegation import is_valid_delegation
from .vm.gas import (
    calculate_blob_gas_price,
    calculate_data_fee,
    calculate_excess_blob_gas,
    calculate_total_blob_gas,
)
from .vm.interpreter import MessageCallOutput, process_message_call

BASE_FEE_MAX_CHANGE_DENOMINATOR = Uint(8)
ELASTICITY_MULTIPLIER = Uint(2)
GAS_LIMIT_ADJUSTMENT_FACTOR = Uint(1024)
GAS_LIMIT_MINIMUM = Uint(5000)
EMPTY_OMMER_HASH = keccak256(rlp.encode([]))
SYSTEM_ADDRESS = hex_to_address("0xfffffffffffffffffffffffffffffffffffffffe")
BEACON_ROOTS_ADDRESS = hex_to_address(
    "0x000F3df6D732807Ef1319fB7B8bB8522d0Beac02"
)
SYSTEM_TRANSACTION_GAS = Uint(30000000)
MAX_BLOB_GAS_PER_BLOCK = Uint(1179648)
VERSIONED_HASH_VERSION_KZG = b"\x01"

WITHDRAWAL_REQUEST_PREDEPLOY_ADDRESS = hex_to_address(
    "0x0c15F14308530b7CDB8460094BbB9cC28b9AaaAA"
)
CONSOLIDATION_REQUEST_PREDEPLOY_ADDRESS = hex_to_address(
    "0x00431F263cE400f4455c2dCf564e53007Ca4bbBb"
)
HISTORY_STORAGE_ADDRESS = hex_to_address(
    "0x0F792be4B0c0cb4DAE440Ef133E90C0eCD48CCCC"
)
HISTORY_SERVE_WINDOW = 8192


@dataclass
class BlockChain:
    """
    History and current state of the block chain.
    """

    blocks: List[Block]
    state: State
    chain_id: U64
    last_block_gas_used: Uint
    last_receipt_root: Root
    last_block_logs_bloom: Bloom
    last_requests_hash: Bytes
    


def apply_fork(old: BlockChain) -> BlockChain:
    """
    Transforms the state from the previous hard fork (`old`) into the block
    chain object for this hard fork and returns it.

    When forks need to implement an irregular state transition, this function
    is used to handle the irregularity. See the :ref:`DAO Fork <dao-fork>` for
    an example.

    Parameters
    ----------
    old :
        Previous block chain object.

    Returns
    -------
    new : `BlockChain`
        Upgraded block chain object for this hard fork.
    """
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
    sender_addresses = validate_block(chain, block)

    apply_body_output = apply_body(
        chain.state,
        get_last_256_block_hashes(chain),
        block.header.coinbase,
        block.header.number,
        block.header.base_fee_per_gas,
        block.header.gas_limit,
        block.header.timestamp,
        block.header.prev_randao,
        block.transactions,
        chain.chain_id,
        block.withdrawals,
        block.header.parent_beacon_block_root,
        calculate_excess_blob_gas(chain.blocks[-1].header),
        sender_addresses,
    )
    
    chain.last_block_gas_used = apply_body_output.block_gas_used
    chain.last_block_logs_bloom = apply_body_output.block_logs_bloom
    chain.last_receipt_root = apply_body_output.receipt_root
    chain.last_requests_hash = apply_body_output.requests_hash
    chain.blocks.append(block)
    if len(chain.blocks) > 255:
        # Real clients have to store more blocks to deal with reorgs, but the
        # protocol only requires the last 255
        chain.blocks = chain.blocks[-255:]


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


def validate_header(header: Header, parent_header: Header) -> None:
    """
    Verifies a block header.

    In order to consider a block's header valid, the logic for the
    quantities in the header should match the logic for the block itself.
    For example the header timestamp should be greater than the block's parent
    timestamp because the block was created *after* the parent block.
    Additionally, the block's number should be directly following the parent
    block's number since it is the next block in the sequence.

    Parameters
    ----------
    header :
        Header to check for correctness.
    parent_header :
        Parent Header of the header to check for correctness
    """
    expected_base_fee_per_gas = calculate_base_fee_per_gas(
        header.gas_limit,
        parent_header.gas_limit,
        header.parent_gas_used,
        parent_header.base_fee_per_gas,
    )
    excess_blob_gas = calculate_excess_blob_gas(parent_header)

    if expected_base_fee_per_gas != header.base_fee_per_gas:
        raise InvalidBlock
    if excess_blob_gas != header.excess_blob_gas:
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
    state: State,
    tx: Transaction,
    sender_address: Address,
    gas_available: Uint,
    base_fee_per_gas: Uint,
) -> Tuple[bool, Tuple[VersionedHash, ...]]:
    """
    Check if the transaction is includable in the block.

    Parameters
    ----------
    state :
        Current state.
    tx :
        The transaction.
    gas_available :
        The gas remaining in the block.
    base_fee_per_gas :
        The block base fee.

    Returns
    -------
    is_transaction_skipped:
        Whether the tx should be skipped rather than executed.
    effective_gas_price :
        The price to charge for gas when the transaction is executed.
    blob_versioned_hashes :
        The blob versioned hashes of the transaction.

    """

    if isinstance(tx, (FeeMarketTransaction, BlobTransaction, SetCodeTransaction)):
        priority_fee_per_gas = min(
            tx.max_priority_fee_per_gas,
            tx.max_fee_per_gas - base_fee_per_gas,
        )
        effective_gas_price = priority_fee_per_gas + base_fee_per_gas
        max_gas_fee = tx.gas * tx.max_fee_per_gas
    else:
        effective_gas_price = tx.gas_price
        max_gas_fee = tx.gas * tx.gas_price

    if isinstance(tx, BlobTransaction):
        max_gas_fee += calculate_total_blob_gas(tx) * Uint(
            tx.max_fee_per_blob_gas
        )
        blob_versioned_hashes = tx.blob_versioned_hashes
    else:
        blob_versioned_hashes = ()

    sender_account = get_account(state, sender_address)
    is_sender_eoa = (
        sender_account.code == bytearray() 
        or is_valid_delegation(sender_account.code)
    )
    is_transaction_skipped = (
        tx.gas > gas_available
        or Uint(sender_account.balance) < max_gas_fee + Uint(tx.value)
        or sender_account.nonce != tx.nonce
        or not is_sender_eoa
    )

    return is_transaction_skipped, effective_gas_price, blob_versioned_hashes


def make_receipt(
    tx: Transaction,
    error: Optional[EthereumException],
    cumulative_gas_used: Uint,
    logs: Tuple[Log, ...],
) -> Union[Bytes, Receipt]:
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
        executed.
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


def check_transaction_static(
    tx: Transaction,
    chain_id: U64,
    base_fee_per_gas: U64,
    excess_blob_gas: U64,
) -> Address:

    if not validate_transaction(tx):
        raise InvalidBlock

    if isinstance(tx, (FeeMarketTransaction, BlobTransaction, SetCodeTransaction)):
        if tx.max_fee_per_gas < tx.max_priority_fee_per_gas:
            raise InvalidBlock
        if tx.max_fee_per_gas < base_fee_per_gas:
            raise InvalidBlock
    else:
        if tx.gas_price < base_fee_per_gas:
            raise InvalidBlock

    if isinstance(tx, BlobTransaction):
        if not isinstance(tx.to, Address):
            raise InvalidBlock
        if len(tx.blob_versioned_hashes) == 0:
            raise InvalidBlock
        for blob_versioned_hash in tx.blob_versioned_hashes:
            if blob_versioned_hash[0:1] != VERSIONED_HASH_VERSION_KZG:
                raise InvalidBlock
        blob_gas_price = calculate_blob_gas_price(excess_blob_gas)
        if Uint(tx.max_fee_per_blob_gas) < blob_gas_price:
            raise InvalidBlock
        
    if isinstance(tx, SetCodeTransaction):
        if not any(tx.authorizations):
            raise InvalidBlock       
            
    return recover_sender(chain_id, tx)

def validate_block(
    chain: BlockChain,
    block: Block,
) -> List[Address]:
    total_inclusion_gas = Uint(0)
    total_blob_gas_used = Uint(0)
    transactions_trie: Trie[
        Bytes, Optional[Union[Bytes, LegacyTransaction]]
    ] = Trie(secured=False, default=None)
    withdrawals_trie: Trie[Bytes, Optional[Union[Bytes, Withdrawal]]] = Trie(
        secured=False, default=None
    )

    parent_header = chain.blocks[-1].header
    validate_header(block.header, parent_header)

    # validate deferred execution outputs from the parent
    if block.header.parent_gas_used != chain.last_block_gas_used:
        raise InvalidBlock
    if block.header.parent_receipt_root != chain.last_receipt_root:
        raise InvalidBlock
    if block.header.parent_bloom != chain.last_block_logs_bloom:
        raise InvalidBlock
    if block.header.parent_requests_hash != chain.last_requests_hash:
        raise InvalidBlock
    if block.header.pre_state_root != state_root(chain.state):
        raise InvalidBlock

    if block.ommers != ():
        raise InvalidBlock

    # Validate coinbase's signature over the header
    coinbase = block.header.coinbase
    header_signer = recover_header_signer(
        chain.chain_id,
        block.header,
    )
    if coinbase != header_signer:
        raise InvalidBlock
    
    sender_addresses = []
    for i, tx in enumerate(map(decode_transaction, block.transactions)):
        sender_address = check_transaction_static(
            tx,
            chain.chain_id,
            block.header.base_fee_per_gas,
            block.header.excess_blob_gas,
        )
        sender_addresses.append(sender_address)
        _, inclusion_gas = calculate_inclusion_gas_cost(tx)
        blob_gas_used = calculate_total_blob_gas(tx)
        
        total_inclusion_gas += inclusion_gas
        total_blob_gas_used += blob_gas_used

        trie_set(
            transactions_trie, rlp.encode(Uint(i)), encode_transaction(tx)
        )

    if total_inclusion_gas > block.header.gas_limit:
        raise InvalidBlock
    if total_blob_gas_used > MAX_BLOB_GAS_PER_BLOCK:
        raise InvalidBlock

    blob_gas_price = calculate_blob_gas_price(block.header.excess_blob_gas)
    inclusion_cost = (
        total_inclusion_gas * block.header.base_fee_per_gas
        + total_blob_gas_used * blob_gas_price
    )
    
    coinbase_account = get_account(chain.state, coinbase)
    if Uint(coinbase_account.balance) < inclusion_cost:
        raise InvalidBlock

    for i, wd in enumerate(block.withdrawals):
        trie_set(withdrawals_trie, rlp.encode(Uint(i)), rlp.encode(wd))

    if block.header.transactions_root != root(transactions_trie):
        raise InvalidBlock
    if block.header.withdrawals_root != root(withdrawals_trie):
        raise InvalidBlock
    if block.header.blob_gas_used != blob_gas_used:
        raise InvalidBlock
    
    return sender_addresses
    

@dataclass
class ApplyBodyOutput:
    """
    Output from applying the block body to the present state.

    Contains the following:

    block_gas_used : `ethereum.base_types.Uint`
        Gas used for executing all transactions.
    receipt_root : `ethereum.fork_types.Root`
        Trie root of all the receipts in the block.
    block_logs_bloom : `Bloom`
        Logs bloom of all the logs included in all the transactions of the
        block.
    state_root : `ethereum.fork_types.Root`
        State root after all transactions have been executed.
    requests_hash : `Bytes`
        Hash of all the requests in the block.
    """

    block_gas_used: Uint
    receipt_root: Root
    block_logs_bloom: Bloom
    state_root: Root
    requests_hash: Bytes


def process_system_transaction(
    target_address: Address,
    data: Bytes,
    block_hashes: List[Hash32],
    coinbase: Address,
    block_number: Uint,
    base_fee_per_gas: Uint,
    block_gas_limit: Uint,
    block_time: U256,
    prev_randao: Bytes32,
    state: State,
    chain_id: U64,
    excess_blob_gas: U64,
) -> MessageCallOutput:
    """
    Process a system transaction.

    Parameters
    ----------
    target_address :
        Address of the contract to call.
    data :
        Data to pass to the contract.
    block_hashes :
        List of hashes of the previous 256 blocks.
    coinbase :
        Address of the block's coinbase.
    block_number :
        Block number.
    base_fee_per_gas :
        Base fee per gas.
    block_gas_limit :
        Gas limit of the block.
    block_time :
        Time the block was produced.
    prev_randao :
        Previous randao value.
    state :
        Current state.
    chain_id :
        ID of the chain.
    excess_blob_gas :
        Excess blob gas.

    Returns
    -------
    system_tx_output : `MessageCallOutput`
        Output of processing the system transaction.
    """
    system_contract_code = get_account(state, target_address).code

    system_tx_message = Message(
        caller=SYSTEM_ADDRESS,
        target=target_address,
        gas=SYSTEM_TRANSACTION_GAS,
        value=U256(0),
        data=data,
        code=system_contract_code,
        depth=Uint(0),
        current_target=target_address,
        code_address=target_address,
        should_transfer_value=False,
        is_static=False,
        accessed_addresses=set(),
        accessed_storage_keys=set(),
        parent_evm=None,
        authorizations=(),
    )

    system_tx_env = vm.Environment(
        caller=SYSTEM_ADDRESS,
        block_hashes=block_hashes,
        origin=SYSTEM_ADDRESS,
        coinbase=coinbase,
        number=block_number,
        gas_limit=block_gas_limit,
        base_fee_per_gas=base_fee_per_gas,
        gas_price=base_fee_per_gas,
        time=block_time,
        prev_randao=prev_randao,
        state=state,
        chain_id=chain_id,
        traces=[],
        excess_blob_gas=excess_blob_gas,
        blob_versioned_hashes=(),
        transient_storage=TransientStorage(),
    )

    system_tx_output = process_message_call(system_tx_message, system_tx_env)

    # TODO: Empty accounts in post-merge forks are impossible
    # see Ethereum Improvement Proposal 7523.
    # This line is only included to support invalid tests in the test suite
    # and will have to be removed in the future.
    # See https://github.com/ethereum/execution-specs/issues/955
    destroy_touched_empty_accounts(
        system_tx_env.state, system_tx_output.touched_accounts
    )

    return system_tx_output


def apply_body(
    state: State,
    block_hashes: List[Hash32],
    coinbase: Address,
    block_number: Uint,
    base_fee_per_gas: Uint,
    block_gas_limit: Uint,
    block_time: U256,
    prev_randao: Bytes32,
    transactions: Tuple[Union[LegacyTransaction, Bytes], ...],
    chain_id: U64,
    withdrawals: Tuple[Withdrawal, ...],
    parent_beacon_block_root: Root,
    excess_blob_gas: U64,
    sender_addresses: List[Address],
) -> ApplyBodyOutput:
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
    state :
        Current account state.
    block_hashes :
        List of hashes of the previous 256 blocks in the order of
        increasing block number.
    coinbase :
        Address of account which receives block reward and transaction fees.
    block_number :
        Position of the block within the chain.
    base_fee_per_gas :
        Base fee per gas of within the block.
    block_gas_limit :
        Initial amount of gas available for execution in this block.
    block_time :
        Time the block was produced, measured in seconds since the epoch.
    prev_randao :
        The previous randao from the beacon chain.
    transactions :
        Transactions included in the block.
    ommers :
        Headers of ancestor blocks which are not direct parents (formerly
        uncles.)
    chain_id :
        ID of the executing chain.
    withdrawals :
        Withdrawals to be processed in the current block.
    parent_beacon_block_root :
        The root of the beacon block from the parent block.
    excess_blob_gas :
        Excess blob gas calculated from the previous block.

    Returns
    -------
    apply_body_output : `ApplyBodyOutput`
        Output of applying the block body to the state.
    """
    receipts_trie: Trie[Bytes, Optional[Union[Bytes, Receipt]]] = Trie(
        secured=False, default=None
    )
    block_logs: Tuple[Log, ...] = ()
    deposit_requests: Bytes = b""

    blob_gas_price = calculate_blob_gas_price(excess_blob_gas)
    decoded_transactions = map(decode_transaction, transactions)
    total_inclusion_gas = sum(calculate_inclusion_gas_cost(tx)[1] for tx in decoded_transactions)
    total_blob_gas_used = sum(calculate_total_blob_gas(tx) for tx in decoded_transactions)
    inclusion_cost = (
        total_inclusion_gas * base_fee_per_gas
        + total_blob_gas_used * blob_gas_price
    )
    coinbase_account = get_account(state, coinbase)
    coinbase_balance_after_inclusion_cost = (
        Uint(coinbase_account.balance) - inclusion_cost
    )
    # Charge coinbase for inclusion costs
    set_account_balance(
        env.state,
        env.coinbase,
        U256(coinbase_balance_after_inclusion_cost),
    )
    gas_available = block_gas_limit - total_inclusion_gas

    process_system_transaction(
        BEACON_ROOTS_ADDRESS,
        parent_beacon_block_root,
        block_hashes,
        coinbase,
        block_number,
        base_fee_per_gas,
        block_gas_limit,
        block_time,
        prev_randao,
        state,
        chain_id,
        excess_blob_gas,
    ) 

    process_system_transaction(
        HISTORY_STORAGE_ADDRESS,
        block_hashes[-1],  # The parent hash
        block_hashes,
        coinbase,
        block_number,
        base_fee_per_gas,
        block_gas_limit,
        block_time,
        prev_randao,
        state,
        chain_id,
        excess_blob_gas,
    )

    for i, tx in enumerate(decoded_transactions):
        sender_address = sender_addresses[i]
        inclusion_gas = calculate_inclusion_gas_cost(tx)
        gas_available += inclusion_gas
        (
            is_transaction_skipped,
            effective_gas_price,
            blob_versioned_hashes,
        ) = check_transaction(
            state,
            tx,
            sender_address,
            gas_available,
        )
        
        if is_transaction_skipped:
            gas_available -= inclusion_gas
        else:
            env = vm.Environment(
                caller=sender_address,
                origin=sender_address,
                block_hashes=block_hashes,
                coinbase=coinbase,
                number=block_number,
                gas_limit=block_gas_limit,
                base_fee_per_gas=base_fee_per_gas,
                gas_price=effective_gas_price,
                time=block_time,
                prev_randao=prev_randao,
                state=state,
                chain_id=chain_id,
                traces=[],
                excess_blob_gas=excess_blob_gas,
                blob_versioned_hashes=blob_versioned_hashes,
                transient_storage=TransientStorage(),
            )

            gas_used, logs, error = process_transaction(env, tx)
            gas_available -= gas_used

            receipt = make_receipt(
                tx, error, (block_gas_limit - gas_available), logs
            )

            trie_set(
                receipts_trie,
                rlp.encode(Uint(i)),
                receipt,
            )

            block_logs += logs
            deposit_requests += parse_deposit_requests_from_receipt(receipt)

    for i, wd in enumerate(withdrawals):
        process_withdrawal(state, wd)

        if account_exists_and_is_empty(state, wd.address):
            destroy_account(state, wd.address)

    requests_from_execution = process_general_purpose_requests(
        deposit_requests,
        state,
        block_hashes,
        coinbase,
        block_number,
        base_fee_per_gas,
        block_gas_limit,
        block_time,
        prev_randao,
        chain_id,
        excess_blob_gas,
    )

    block_gas_used = block_gas_limit - gas_available
    receipt_root = root(receipts_trie)
    block_logs_bloom = logs_bloom(block_logs)
    state_root = state_root(state)
    requests_hash = compute_requests_hash(requests_from_execution)

    return ApplyBodyOutput(
        block_gas_used,
        receipt_root,
        block_logs_bloom,
        state_root,
        requests_hash,
    )


def process_general_purpose_requests(
    deposit_requests: Bytes,
    state: State,
    block_hashes: List[Hash32],
    coinbase: Address,
    block_number: Uint,
    base_fee_per_gas: Uint,
    block_gas_limit: Uint,
    block_time: U256,
    prev_randao: Bytes32,
    chain_id: U64,
    excess_blob_gas: U64,
) -> List[Bytes]:
    """
    Process all the requests in the block.

    Parameters
    ----------
    deposit_requests :
        The deposit requests.
    state :
        Current state.
    block_hashes :
        List of hashes of the previous 256 blocks.
    coinbase :
        Address of the block's coinbase.
    block_number :
        Block number.
    base_fee_per_gas :
        Base fee per gas.
    block_gas_limit :
        Initial amount of gas available for execution in this block.
    block_time :
        Time the block was produced.
    prev_randao :
        The previous randao from the beacon chain.
    chain_id :
        ID of the executing chain.
    excess_blob_gas :
        Excess blob gas.

    Returns
    -------
    requests_from_execution : `List[Bytes]`
        The requests from the execution
    """
    # Requests are to be in ascending order of request type
    requests_from_execution: List[Bytes] = []
    if len(deposit_requests) > 0:
        requests_from_execution.append(DEPOSIT_REQUEST_TYPE + deposit_requests)

    system_withdrawal_tx_output = process_system_transaction(
        WITHDRAWAL_REQUEST_PREDEPLOY_ADDRESS,
        b"",
        block_hashes,
        coinbase,
        block_number,
        base_fee_per_gas,
        block_gas_limit,
        block_time,
        prev_randao,
        state,
        chain_id,
        excess_blob_gas,
    )

    if len(system_withdrawal_tx_output.return_data) > 0:
        requests_from_execution.append(
            WITHDRAWAL_REQUEST_TYPE + system_withdrawal_tx_output.return_data
        )

    system_consolidation_tx_output = process_system_transaction(
        CONSOLIDATION_REQUEST_PREDEPLOY_ADDRESS,
        b"",
        block_hashes,
        coinbase,
        block_number,
        base_fee_per_gas,
        block_gas_limit,
        block_time,
        prev_randao,
        state,
        chain_id,
        excess_blob_gas,
    )

    if len(system_consolidation_tx_output.return_data) > 0:
        requests_from_execution.append(
            CONSOLIDATION_REQUEST_TYPE
            + system_consolidation_tx_output.return_data
        )

    return requests_from_execution


def process_transaction(
    env: vm.Environment, tx: Transaction
) -> Tuple[Uint, Tuple[Log, ...], Optional[EthereumException]]:
    """
    Execute a transaction against the provided environment.

    This function processes the actions needed to execute a transaction.
    It decrements the sender's account after calculating the gas fee and
    refunds them the proper amount after execution. Calling contracts,
    deploying code, and incrementing nonces are all examples of actions that
    happen within this function or from a call made within this function.

    Accounts that are marked for deletion are processed and destroyed after
    execution.

    Parameters
    ----------
    env :
        Environment for the Ethereum Virtual Machine.
    tx :
        Transaction to execute.

    Returns
    -------
    gas_left : `ethereum.base_types.U256`
        Remaining gas after execution.
    logs : `Tuple[ethereum.blocks.Log, ...]`
        Logs generated during execution.
    """
    intrinsic_gas, calldata_floor_gas_cost = calculate_intrinsic_gas_cost(tx)
    sender = env.origin
    sender_account = get_account(env.state, sender)
    coinbase_account = get_account(env.state, env.coinbase)
    increment_nonce(env.state, sender)

    max_gas_fee = tx.gas * env.gas_price
    blob_gas_fee = calculate_data_fee(env.excess_blob_gas, tx)

    sender_balance_after_gas_fee = (
        sender_account.balance
        - U256(max_gas_fee + blob_gas_fee)
    )
    set_account_balance(env.state, sender, sender_balance_after_gas_fee)

    preaccessed_addresses = set()
    preaccessed_storage_keys = set()
    preaccessed_addresses.add(env.coinbase)
    if isinstance(
        tx,
        (
            AccessListTransaction,
            FeeMarketTransaction,
            BlobTransaction,
            SetCodeTransaction,
        ),
    ):
        for address, keys in tx.access_list:
            preaccessed_addresses.add(address)
            for key in keys:
                preaccessed_storage_keys.add((address, key))

    authorizations: Tuple[Authorization, ...] = ()
    if isinstance(tx, SetCodeTransaction):
        authorizations = tx.authorizations
    gas = tx.gas - intrinsic_gas
    message = prepare_message(
        sender,
        tx.to,
        tx.value,
        tx.data,
        gas,
        env,
        preaccessed_addresses=frozenset(preaccessed_addresses),
        preaccessed_storage_keys=frozenset(preaccessed_storage_keys),
        authorizations=authorizations,
    )

    output = process_message_call(message, env)

    # For EIP-7623 we first calculate the total_gas_used, which includes
    # the execution gas refund.
    total_gas_used = tx.gas - output.gas_left
    gas_refund = min(
        total_gas_used // Uint(5), Uint(output.refund_counter)
    )
    total_gas_used -= gas_refund

    # Transactions with less total_gas_used than the floor pay at the
    # floor cost.
    total_gas_used = max(total_gas_used, calldata_floor_gas_cost)
    gas_refund_amount = (tx.gas - total_gas_used) * env.gas_price

    # For non-1559 transactions env.gas_price == tx.gas_price
    priority_fee_per_gas = env.gas_price - env.base_fee_per_gas
    priority_fee = total_gas_used * priority_fee_per_gas

    # refund gas
    sender_balance_after_refund = (
        sender_account.balance 
        + U256(gas_refund_amount)
    )
    set_account_balance(env.state, sender, sender_balance_after_refund)

    inclusion_cost_refund = (
        calculate_inclusion_gas_cost(tx)[1] * env.base_fee_per_gas
        + blob_gas_fee
    )
    
    # transfer priority fees and refund inclusion cost
    coinbase_balance_after_transaction = (
        coinbase_account.balance 
        + U256(priority_fee)
        + U256(inclusion_cost_refund)
    )
    if coinbase_balance_after_transaction != 0:
        set_account_balance(
            env.state, env.coinbase, coinbase_balance_after_transaction
        )
    elif account_exists_and_is_empty(env.state, env.coinbase):
        destroy_account(env.state, env.coinbase)

    for address in output.accounts_to_delete:
        destroy_account(env.state, address)

    destroy_touched_empty_accounts(env.state, output.touched_accounts)

    return total_gas_used, output.logs, output.error


def compute_header_hash(header: Header) -> Hash32:
    """
    Computes the hash of a block header.

    The header hash of a block is the canonical hash that is used to refer
    to a specific block and completely distinguishes a block from another.

    ``keccak256`` is a function that produces a 256 bit hash of any input.
    It also takes in any number of bytes as an input and produces a single
    hash for them. A hash is a completely unique output for a single input.
    So an input corresponds to one unique hash that can be used to identify
    the input exactly.

    Prior to using the ``keccak256`` hash function, the header must be
    encoded using the Recursive-Length Prefix. See :ref:`rlp`.
    RLP encoding the header converts it into a space-efficient format that
    allows for easy transfer of data between nodes. The purpose of RLP is to
    encode arbitrarily nested arrays of binary data, and RLP is the primary
    encoding method used to serialize objects in Ethereum's execution layer.
    The only purpose of RLP is to encode structure; encoding specific data
    types (e.g. strings, floats) is left up to higher-order protocols.

    Parameters
    ----------
    header :
        Header of interest.

    Returns
    -------
    hash : `ethereum.crypto.hash.Hash32`
        Hash of the header.
    """
    return keccak256(rlp.encode(header))


def check_gas_limit(gas_limit: Uint, parent_gas_limit: Uint) -> bool:
    """
    Validates the gas limit for a block.

    The bounds of the gas limit, ``max_adjustment_delta``, is set as the
    quotient of the parent block's gas limit and the
    ``GAS_LIMIT_ADJUSTMENT_FACTOR``. Therefore, if the gas limit that is
    passed through as a parameter is greater than or equal to the *sum* of
    the parent's gas and the adjustment delta then the limit for gas is too
    high and fails this function's check. Similarly, if the limit is less
    than or equal to the *difference* of the parent's gas and the adjustment
    delta *or* the predefined ``GAS_LIMIT_MINIMUM`` then this function's
    check fails because the gas limit doesn't allow for a sufficient or
    reasonable amount of gas to be used on a block.

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
    max_adjustment_delta = parent_gas_limit // GAS_LIMIT_ADJUSTMENT_FACTOR
    if gas_limit >= parent_gas_limit + max_adjustment_delta:
        return False
    if gas_limit <= parent_gas_limit - max_adjustment_delta:
        return False
    if gas_limit < GAS_LIMIT_MINIMUM:
        return False

    return True


def recover_header_signer(
    chain_id: U64,
    header: Header,
) -> Address:
    
    signing_hash = keccak256(
        b"EthereumBlockHeader" 
        + rlp.encode(
            (
                chain_id,
                header.parent_hash,
                header.ommers_hash,
                header.coinbase,
                header.pre_state_root,
                header.transactions_root,
                header.parent_receipt_root,
                header.parent_bloom,
                header.difficulty,
                header.number,
                header.gas_limit,
                header.parent_gas_used,
                header.timestamp,
                header.extra_data,
                header.prev_randao,
                header.nonce,
                header.base_fee_per_gas,
                header.withdrawals_root,
                header.blob_gas_used,
                header.excess_blob_gas,
                header.parent_beacon_block_root,
                header.parent_requests_hash,
            )
        )
    )

    r = header.r
    s = header.s
    y_parity = header.y_parity

    public_key = secp256k1_recover(
            r, s, y_parity, signing_hash
    )

    return Address(keccak256(public_key)[12:32])
