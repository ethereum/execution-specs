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
from ethereum_types.bytes import Bytes
from ethereum_types.numeric import U64, U256, Uint

from ethereum.crypto.hash import Hash32, keccak256
from ethereum.exceptions import (
    EthereumException,
    InvalidBlock,
    InvalidSenderError,
)
from ethereum.shanghai import fork as previous_fork

from . import vm
from .blocks import (
    AnyBlock,
    AnyHeader,
    Block,
    Header,
    Log,
    Receipt,
    Withdrawal,
    encode_receipt,
    header_base_fee_per_gas,
)
from .bloom import logs_bloom
from .fork_types import Account, Address, VersionedHash
from .state import (
    State,
    TransientStorage,
    account_exists_and_is_empty,
    destroy_account,
    destroy_touched_empty_accounts,
    get_account,
    increment_nonce,
    modify_state,
    set_account_balance,
    state_root,
)
from .transactions import (
    AccessListTransaction,
    BlobTransaction,
    FeeMarketTransaction,
    LegacyTransaction,
    Transaction,
    decode_transaction,
    encode_transaction,
    get_transaction_hash,
    recover_sender,
    validate_transaction,
)
from .trie import root, trie_set
from .utils.hexadecimal import hex_to_address
from .utils.message import prepare_message
from .vm import Message
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
INITIAL_BASE_FEE = Uint(1000000000)
EMPTY_OMMER_HASH = keccak256(rlp.encode([]))
SYSTEM_ADDRESS = hex_to_address("0xfffffffffffffffffffffffffffffffffffffffe")
BEACON_ROOTS_ADDRESS = hex_to_address(
    "0x000F3df6D732807Ef1319fB7B8bB8522d0Beac02"
)
SYSTEM_TRANSACTION_GAS = Uint(30000000)
MAX_BLOB_GAS_PER_BLOCK = Uint(786432)
VERSIONED_HASH_VERSION_KZG = b"\x01"


@dataclass
class BlockChain:
    """
    History and current state of the block chain.
    """

    blocks: List[AnyBlock]
    state: State
    chain_id: U64


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
    parent = parent_header(chain, block.header)
    validate_header(parent, block.header)
    if block.ommers != ():
        raise InvalidBlock

    block_env = vm.BlockEnvironment(
        chain_id=chain.chain_id,
        state=chain.state,
        block_gas_limit=block.header.gas_limit,
        block_hashes=get_last_256_block_hashes(chain),
        coinbase=block.header.coinbase,
        number=block.header.number,
        base_fee_per_gas=block.header.base_fee_per_gas,
        time=block.header.timestamp,
        prev_randao=block.header.prev_randao,
        excess_blob_gas=block.header.excess_blob_gas,
        parent_beacon_block_root=block.header.parent_beacon_block_root,
    )

    block_output = apply_body(
        block_env=block_env,
        transactions=block.transactions,
        withdrawals=block.withdrawals,
    )
    block_state_root = state_root(block_env.state)
    transactions_root = root(block_output.transactions_trie)
    receipt_root = root(block_output.receipts_trie)
    block_logs_bloom = logs_bloom(block_output.block_logs)
    withdrawals_root = root(block_output.withdrawals_trie)

    if block_output.block_gas_used != block.header.gas_used:
        raise InvalidBlock(
            f"{block_output.block_gas_used} != {block.header.gas_used}"
        )
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


def parent_header(chain: BlockChain, header: AnyHeader) -> AnyHeader:
    """
    Gets the parent of a block, given that block's `header` and `chain`.
    """
    if header.number < Uint(1):
        raise InvalidBlock

    parent_number = header.number - Uint(1)
    first_number = chain.blocks[0].header.number
    last_number = chain.blocks[-1].header.number

    if parent_number < first_number or parent_number > last_number:
        raise InvalidBlock

    return chain.blocks[parent_number - first_number].header


def validate_header(header: AnyHeader, parent_header: AnyHeader) -> None:
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
    if not isinstance(header, Header):
        assert not isinstance(parent_header, Header)
        return previous_fork.validate_header(header, parent_header)

    excess_blob_gas = calculate_excess_blob_gas(parent_header)
    if header.excess_blob_gas != excess_blob_gas:
        raise InvalidBlock

    if header.gas_used > header.gas_limit:
        raise InvalidBlock

    expected_base_fee_per_gas = INITIAL_BASE_FEE
    parent_base_fee_per_gas = header_base_fee_per_gas(parent_header)
    if parent_base_fee_per_gas is not None:
        # For every block except the first, calculate the base fee per gas
        # based on the parent block.
        expected_base_fee_per_gas = calculate_base_fee_per_gas(
            header.gas_limit,
            parent_header.gas_limit,
            parent_header.gas_used,
            parent_base_fee_per_gas,
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
) -> Tuple[Address, Uint, Tuple[VersionedHash, ...], Uint]:
    """
    Check if the transaction is includable in the block.

    Parameters
    ----------
    block_env :
        The block scoped environment.
    block_output :
        The block output for the current block.
    tx :
        The transaction.

    Returns
    -------
    sender_address :
        The sender of the transaction.
    effective_gas_price :
        The price to charge for gas when the transaction is executed.
    blob_versioned_hashes :
        The blob versioned hashes of the transaction.
    tx_blob_gas_used:
        The blob gas used by the transaction.

    Raises
    ------
    InvalidBlock :
        If the transaction is not includable.
    """
    gas_available = block_env.block_gas_limit - block_output.block_gas_used
    blob_gas_available = MAX_BLOB_GAS_PER_BLOCK - block_output.blob_gas_used

    if tx.gas > gas_available:
        raise InvalidBlock

    tx_blob_gas_used = calculate_total_blob_gas(tx)
    if tx_blob_gas_used > blob_gas_available:
        raise InvalidBlock

    sender_address = recover_sender(block_env.chain_id, tx)
    sender_account = get_account(block_env.state, sender_address)

    if isinstance(tx, (FeeMarketTransaction, BlobTransaction)):
        if tx.max_fee_per_gas < tx.max_priority_fee_per_gas:
            raise InvalidBlock
        if tx.max_fee_per_gas < block_env.base_fee_per_gas:
            raise InvalidBlock

        priority_fee_per_gas = min(
            tx.max_priority_fee_per_gas,
            tx.max_fee_per_gas - block_env.base_fee_per_gas,
        )
        effective_gas_price = priority_fee_per_gas + block_env.base_fee_per_gas
        max_gas_fee = tx.gas * tx.max_fee_per_gas
    else:
        if tx.gas_price < block_env.base_fee_per_gas:
            raise InvalidBlock
        effective_gas_price = tx.gas_price
        max_gas_fee = tx.gas * tx.gas_price

    if isinstance(tx, BlobTransaction):
        if not isinstance(tx.to, Address):
            raise InvalidBlock
        if len(tx.blob_versioned_hashes) == 0:
            raise InvalidBlock
        for blob_versioned_hash in tx.blob_versioned_hashes:
            if blob_versioned_hash[0:1] != VERSIONED_HASH_VERSION_KZG:
                raise InvalidBlock

        blob_gas_price = calculate_blob_gas_price(block_env.excess_blob_gas)
        if Uint(tx.max_fee_per_blob_gas) < blob_gas_price:
            raise InvalidBlock

        max_gas_fee += calculate_total_blob_gas(tx) * Uint(
            tx.max_fee_per_blob_gas
        )
        blob_versioned_hashes = tx.blob_versioned_hashes
    else:
        blob_versioned_hashes = ()
    if sender_account.nonce != tx.nonce:
        raise InvalidBlock
    if Uint(sender_account.balance) < max_gas_fee + Uint(tx.value):
        raise InvalidBlock
    if sender_account.code:
        raise InvalidSenderError("not EOA")

    return (
        sender_address,
        effective_gas_price,
        blob_versioned_hashes,
        tx_blob_gas_used,
    )


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


def process_system_transaction(
    block_env: vm.BlockEnvironment,
    target_address: Address,
    data: Bytes,
) -> MessageCallOutput:
    """
    Process a system transaction.

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
    system_tx_output : `MessageCallOutput`
        Output of processing the system transaction.
    """
    system_contract_code = get_account(block_env.state, target_address).code

    tx_env = vm.TransactionEnvironment(
        origin=SYSTEM_ADDRESS,
        gas_price=block_env.base_fee_per_gas,
        gas=SYSTEM_TRANSACTION_GAS,
        access_list_addresses=set(),
        access_list_storage_keys=set(),
        transient_storage=TransientStorage(),
        blob_versioned_hashes=(),
        index_in_block=None,
        tx_hash=None,
        traces=[],
    )

    system_tx_message = Message(
        block_env=block_env,
        tx_env=tx_env,
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
    )

    system_tx_output = process_message_call(system_tx_message)

    # TODO: Empty accounts in post-merge forks are impossible
    # see Ethereum Improvement Proposal 7523.
    # This line is only included to support invalid tests in the test suite
    # and will have to be removed in the future.
    # See https://github.com/ethereum/execution-specs/issues/955
    destroy_touched_empty_accounts(
        block_env.state, system_tx_output.touched_accounts
    )

    return system_tx_output


def apply_body(
    block_env: vm.BlockEnvironment,
    transactions: Tuple[Union[LegacyTransaction, Bytes], ...],
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

    process_system_transaction(
        block_env=block_env,
        target_address=BEACON_ROOTS_ADDRESS,
        data=block_env.parent_beacon_block_root,
    )

    for i, tx in enumerate(map(decode_transaction, transactions)):
        process_transaction(block_env, block_output, tx, Uint(i))

    process_withdrawals(block_env, block_output, withdrawals)

    return block_output


def process_transaction(
    block_env: vm.BlockEnvironment,
    block_output: vm.BlockOutput,
    tx: Transaction,
    index: Uint,
) -> None:
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
    block_env :
        Environment for the Ethereum Virtual Machine.
    block_output :
        The block output for the current block.
    tx :
        Transaction to execute.
    index:
        Index of the transaction in the block.
    """
    trie_set(
        block_output.transactions_trie,
        rlp.encode(index),
        encode_transaction(tx),
    )

    intrinsic_gas = validate_transaction(tx)

    (
        sender,
        effective_gas_price,
        blob_versioned_hashes,
        tx_blob_gas_used,
    ) = check_transaction(
        block_env=block_env,
        block_output=block_output,
        tx=tx,
    )

    sender_account = get_account(block_env.state, sender)

    if isinstance(tx, BlobTransaction):
        blob_gas_fee = calculate_data_fee(block_env.excess_blob_gas, tx)
    else:
        blob_gas_fee = Uint(0)

    effective_gas_fee = tx.gas * effective_gas_price

    gas = tx.gas - intrinsic_gas
    increment_nonce(block_env.state, sender)

    sender_balance_after_gas_fee = (
        Uint(sender_account.balance) - effective_gas_fee - blob_gas_fee
    )
    set_account_balance(
        block_env.state, sender, U256(sender_balance_after_gas_fee)
    )

    access_list_addresses = set()
    access_list_storage_keys = set()
    access_list_addresses.add(block_env.coinbase)
    if isinstance(
        tx, (AccessListTransaction, FeeMarketTransaction, BlobTransaction)
    ):
        for address, keys in tx.access_list:
            access_list_addresses.add(address)
            for key in keys:
                access_list_storage_keys.add((address, key))

    tx_env = vm.TransactionEnvironment(
        origin=sender,
        gas_price=effective_gas_price,
        gas=gas,
        access_list_addresses=access_list_addresses,
        access_list_storage_keys=access_list_storage_keys,
        transient_storage=TransientStorage(),
        blob_versioned_hashes=blob_versioned_hashes,
        index_in_block=index,
        tx_hash=get_transaction_hash(encode_transaction(tx)),
        traces=[],
    )

    message = prepare_message(block_env, tx_env, tx)

    tx_output = process_message_call(message)

    gas_used = tx.gas - tx_output.gas_left
    gas_refund = min(gas_used // Uint(5), Uint(tx_output.refund_counter))
    tx_gas_used = gas_used - gas_refund
    tx_output.gas_left = tx.gas - tx_gas_used
    gas_refund_amount = tx_output.gas_left * effective_gas_price

    # For non-1559 transactions effective_gas_price == tx.gas_price
    priority_fee_per_gas = effective_gas_price - block_env.base_fee_per_gas
    transaction_fee = tx_gas_used * priority_fee_per_gas

    # refund gas
    sender_balance_after_refund = get_account(
        block_env.state, sender
    ).balance + U256(gas_refund_amount)
    set_account_balance(block_env.state, sender, sender_balance_after_refund)

    # transfer miner fees
    coinbase_balance_after_mining_fee = get_account(
        block_env.state, block_env.coinbase
    ).balance + U256(transaction_fee)
    if coinbase_balance_after_mining_fee != 0:
        set_account_balance(
            block_env.state,
            block_env.coinbase,
            coinbase_balance_after_mining_fee,
        )
    elif account_exists_and_is_empty(block_env.state, block_env.coinbase):
        destroy_account(block_env.state, block_env.coinbase)

    for address in tx_output.accounts_to_delete:
        destroy_account(block_env.state, address)

    destroy_touched_empty_accounts(block_env.state, tx_output.touched_accounts)

    block_output.block_gas_used += tx_gas_used
    block_output.blob_gas_used += tx_blob_gas_used

    receipt = make_receipt(
        tx, tx_output.error, block_output.block_gas_used, tx_output.logs
    )

    trie_set(
        block_output.receipts_trie,
        rlp.encode(Uint(index)),
        receipt,
    )

    block_output.block_logs += tx_output.logs


def process_withdrawals(
    block_env: vm.BlockEnvironment,
    block_output: vm.BlockOutput,
    withdrawals: Tuple[Withdrawal, ...],
) -> None:
    """
    Increase the balance of the withdrawing account.
    """

    def increase_recipient_balance(recipient: Account) -> None:
        recipient.balance += wd.amount * U256(10**9)

    for i, wd in enumerate(withdrawals):
        trie_set(
            block_output.withdrawals_trie,
            rlp.encode(Uint(i)),
            rlp.encode(wd),
        )

        modify_state(block_env.state, wd.address, increase_recipient_balance)

        if account_exists_and_is_empty(block_env.state, wd.address):
            destroy_account(block_env.state, wd.address)


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
