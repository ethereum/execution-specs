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

from ethereum.base_types import Bytes0, Bytes32
from ethereum.crypto.elliptic_curve import SECP256K1N, secp256k1_recover
from ethereum.crypto.hash import Hash32, keccak256
from ethereum.exceptions import InvalidBlock
from ethereum.utils.ensure import ensure

from .. import rlp
from ..base_types import U64, U256, Bytes, Uint
from . import vm
from .bloom import logs_bloom
from .fork_types import (
    TX_ACCESS_LIST_ADDRESS_COST,
    TX_ACCESS_LIST_STORAGE_KEY_COST,
    TX_BASE_COST,
    TX_CREATE_COST,
    TX_DATA_COST_PER_NON_ZERO,
    TX_DATA_COST_PER_ZERO,
    AccessListTransaction,
    Address,
    Block,
    Bloom,
    FeeMarketTransaction,
    Header,
    LegacyTransaction,
    Log,
    Receipt,
    Root,
    Transaction,
    Withdrawal,
    decode_transaction,
    encode_transaction,
)
from .state import (
    State,
    account_exists_and_is_empty,
    destroy_account,
    get_account,
    increment_nonce,
    process_withdrawal,
    set_account_balance,
    state_root,
)
from .trie import Trie, root, trie_set
from .utils.message import prepare_message
from .vm.gas import init_code_cost
from .vm.interpreter import MAX_CODE_SIZE, process_message_call

BASE_FEE_MAX_CHANGE_DENOMINATOR = 8
ELASTICITY_MULTIPLIER = 2
GAS_LIMIT_ADJUSTMENT_FACTOR = 1024
GAS_LIMIT_MINIMUM = 5000
EMPTY_OMMER_HASH = keccak256(rlp.encode([]))


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
    parent_header = chain.blocks[-1].header
    validate_header(block.header, parent_header)
    ensure(block.ommers == (), InvalidBlock)
    (
        gas_used,
        transactions_root,
        receipt_root,
        block_logs_bloom,
        state,
        withdrawals_root,
    ) = apply_body(
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
    )
    ensure(gas_used == block.header.gas_used, InvalidBlock)
    ensure(transactions_root == block.header.transactions_root, InvalidBlock)
    ensure(state_root(state) == block.header.state_root, InvalidBlock)
    ensure(receipt_root == block.header.receipt_root, InvalidBlock)
    ensure(block_logs_bloom == block.header.bloom, InvalidBlock)
    ensure(withdrawals_root == block.header.withdrawals_root, InvalidBlock)

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

    ensure(
        check_gas_limit(block_gas_limit, parent_gas_limit),
        InvalidBlock,
    )

    if parent_gas_used == parent_gas_target:
        expected_base_fee_per_gas = parent_base_fee_per_gas
    elif parent_gas_used > parent_gas_target:
        gas_used_delta = parent_gas_used - parent_gas_target

        parent_fee_gas_delta = parent_base_fee_per_gas * gas_used_delta
        target_fee_gas_delta = parent_fee_gas_delta // parent_gas_target

        base_fee_per_gas_delta = max(
            target_fee_gas_delta // BASE_FEE_MAX_CHANGE_DENOMINATOR,
            1,
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
    Additionally, the block's number should be directly folowing the parent
    block's number since it is the next block in the sequence.

    Parameters
    ----------
    header :
        Header to check for correctness.
    parent_header :
        Parent Header of the header to check for correctness
    """
    ensure(header.gas_used <= header.gas_limit, InvalidBlock)

    expected_base_fee_per_gas = calculate_base_fee_per_gas(
        header.gas_limit,
        parent_header.gas_limit,
        parent_header.gas_used,
        parent_header.base_fee_per_gas,
    )

    ensure(expected_base_fee_per_gas == header.base_fee_per_gas, InvalidBlock)

    ensure(header.timestamp > parent_header.timestamp, InvalidBlock)
    ensure(header.number == parent_header.number + 1, InvalidBlock)
    ensure(len(header.extra_data) <= 32, InvalidBlock)

    ensure(header.difficulty == 0, InvalidBlock)
    ensure(header.nonce == b"\x00\x00\x00\x00\x00\x00\x00\x00", InvalidBlock)
    ensure(header.ommers_hash == EMPTY_OMMER_HASH, InvalidBlock)

    block_parent_hash = keccak256(rlp.encode(parent_header))
    ensure(header.parent_hash == block_parent_hash, InvalidBlock)


def check_transaction(
    tx: Transaction,
    base_fee_per_gas: Uint,
    gas_available: Uint,
    chain_id: U64,
) -> Tuple[Address, Uint]:
    """
    Check if the transaction is includable in the block.

    Parameters
    ----------
    tx :
        The transaction.
    base_fee_per_gas :
        The block base fee.
    gas_available :
        The gas remaining in the block.
    chain_id :
        The ID of the current chain.

    Returns
    -------
    sender_address :
        The sender of the transaction.
    effective_gas_price :
        The price to charge for gas when the transaction is executed.

    Raises
    ------
    InvalidBlock :
        If the transaction is not includable.
    """
    ensure(tx.gas <= gas_available, InvalidBlock)
    sender_address = recover_sender(chain_id, tx)

    if isinstance(tx, FeeMarketTransaction):
        ensure(tx.max_fee_per_gas >= tx.max_priority_fee_per_gas, InvalidBlock)
        ensure(tx.max_fee_per_gas >= base_fee_per_gas, InvalidBlock)

        priority_fee_per_gas = min(
            tx.max_priority_fee_per_gas,
            tx.max_fee_per_gas - base_fee_per_gas,
        )
        effective_gas_price = priority_fee_per_gas + base_fee_per_gas
    else:
        ensure(tx.gas_price >= base_fee_per_gas, InvalidBlock)
        effective_gas_price = tx.gas_price

    return sender_address, effective_gas_price


def make_receipt(
    tx: Transaction,
    has_erred: bool,
    cumulative_gas_used: Uint,
    logs: Tuple[Log, ...],
) -> Union[Bytes, Receipt]:
    """
    Make the receipt for a transaction that was executed.

    Parameters
    ----------
    tx :
        The executed transaction.
    has_erred :
        Whether the top level frame of the transaction exited with an error.
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
        succeeded=not has_erred,
        cumulative_gas_used=cumulative_gas_used,
        bloom=logs_bloom(logs),
        logs=logs,
    )

    if isinstance(tx, AccessListTransaction):
        return b"\x01" + rlp.encode(receipt)
    if isinstance(tx, FeeMarketTransaction):
        return b"\x02" + rlp.encode(receipt)
    else:
        return receipt


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
) -> Tuple[Uint, Root, Root, Bloom, State, Root]:
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

    Returns
    -------
    gas_available : `ethereum.base_types.Uint`
        Remaining gas after all transactions have been executed.
    transactions_root : `ethereum.fork_types.Root`
        Trie root of all the transactions in the block.
    receipt_root : `ethereum.fork_types.Root`
        Trie root of all the receipts in the block.
    block_logs_bloom : `Bloom`
        Logs bloom of all the logs included in all the transactions of the
        block.
    state : `ethereum.fork_types.State`
        State after all transactions have been executed.
    """
    gas_available = block_gas_limit
    transactions_trie: Trie[
        Bytes, Optional[Union[Bytes, LegacyTransaction]]
    ] = Trie(secured=False, default=None)
    receipts_trie: Trie[Bytes, Optional[Union[Bytes, Receipt]]] = Trie(
        secured=False, default=None
    )
    withdrawals_trie: Trie[Bytes, Optional[Union[Bytes, Withdrawal]]] = Trie(
        secured=False, default=None
    )
    block_logs: Tuple[Log, ...] = ()

    for i, tx in enumerate(map(decode_transaction, transactions)):
        trie_set(
            transactions_trie, rlp.encode(Uint(i)), encode_transaction(tx)
        )

        sender_address, effective_gas_price = check_transaction(
            tx, base_fee_per_gas, gas_available, chain_id
        )

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
        )

        gas_used, logs, has_erred = process_transaction(env, tx)
        gas_available -= gas_used

        receipt = make_receipt(
            tx, has_erred, (block_gas_limit - gas_available), logs
        )

        trie_set(
            receipts_trie,
            rlp.encode(Uint(i)),
            receipt,
        )

        block_logs += logs

    block_gas_used = block_gas_limit - gas_available

    block_logs_bloom = logs_bloom(block_logs)

    for i, wd in enumerate(withdrawals):
        trie_set(withdrawals_trie, rlp.encode(Uint(i)), rlp.encode(wd))

        process_withdrawal(state, wd)

        if account_exists_and_is_empty(state, wd.address):
            destroy_account(state, wd.address)

    return (
        block_gas_used,
        root(transactions_trie),
        root(receipts_trie),
        block_logs_bloom,
        state,
        root(withdrawals_trie),
    )


def process_transaction(
    env: vm.Environment, tx: Transaction
) -> Tuple[Uint, Tuple[Log, ...], bool]:
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
    logs : `Tuple[ethereum.fork_types.Log, ...]`
        Logs generated during execution.
    """
    ensure(validate_transaction(tx), InvalidBlock)

    sender = env.origin
    sender_account = get_account(env.state, sender)

    if isinstance(tx, FeeMarketTransaction):
        gas_fee = tx.gas * tx.max_fee_per_gas
    else:
        gas_fee = tx.gas * tx.gas_price

    ensure(sender_account.nonce == tx.nonce, InvalidBlock)
    ensure(sender_account.balance >= gas_fee + tx.value, InvalidBlock)
    ensure(sender_account.code == bytearray(), InvalidBlock)

    effective_gas_fee = tx.gas * env.gas_price

    gas = tx.gas - calculate_intrinsic_cost(tx)
    increment_nonce(env.state, sender)

    sender_balance_after_gas_fee = sender_account.balance - effective_gas_fee
    set_account_balance(env.state, sender, sender_balance_after_gas_fee)

    preaccessed_addresses = set()
    preaccessed_storage_keys = set()
    preaccessed_addresses.add(env.coinbase)
    if isinstance(tx, (AccessListTransaction, FeeMarketTransaction)):
        for (address, keys) in tx.access_list:
            preaccessed_addresses.add(address)
            for key in keys:
                preaccessed_storage_keys.add((address, key))

    message = prepare_message(
        sender,
        tx.to,
        tx.value,
        tx.data,
        gas,
        env,
        preaccessed_addresses=frozenset(preaccessed_addresses),
        preaccessed_storage_keys=frozenset(preaccessed_storage_keys),
    )

    output = process_message_call(message, env)

    gas_used = tx.gas - output.gas_left
    gas_refund = min(gas_used // 5, output.refund_counter)
    gas_refund_amount = (output.gas_left + gas_refund) * env.gas_price

    # For non-1559 transactions env.gas_price == tx.gas_price
    priority_fee_per_gas = env.gas_price - env.base_fee_per_gas
    transaction_fee = (
        tx.gas - output.gas_left - gas_refund
    ) * priority_fee_per_gas

    total_gas_used = gas_used - gas_refund

    # refund gas
    sender_balance_after_refund = (
        get_account(env.state, sender).balance + gas_refund_amount
    )
    set_account_balance(env.state, sender, sender_balance_after_refund)

    # transfer miner fees
    coinbase_balance_after_mining_fee = (
        get_account(env.state, env.coinbase).balance + transaction_fee
    )
    if coinbase_balance_after_mining_fee != 0:
        set_account_balance(
            env.state, env.coinbase, coinbase_balance_after_mining_fee
        )
    elif account_exists_and_is_empty(env.state, env.coinbase):
        destroy_account(env.state, env.coinbase)

    for address in output.accounts_to_delete:
        destroy_account(env.state, address)

    for address in output.touched_accounts:
        if account_exists_and_is_empty(env.state, address):
            destroy_account(env.state, address)

    return total_gas_used, output.logs, output.has_erred


def validate_transaction(tx: Transaction) -> bool:
    """
    Verifies a transaction.

    The gas in a transaction gets used to pay for the intrinsic cost of
    operations, therefore if there is insufficient gas then it would not
    be possible to execute a transaction and it will be declared invalid.

    Additionally, the nonce of a transaction must not equal or exceed the
    limit defined in `EIP-2681 <https://eips.ethereum.org/EIPS/eip-2681>`_.
    In practice, defining the limit as ``2**64-1`` has no impact because
    sending ``2**64-1`` transactions is improbable. It's not strictly
    impossible though, ``2**64-1`` transactions is the entire capacity of the
    Ethereum blockchain at 2022 gas limits for a little over 22 years.

    Parameters
    ----------
    tx :
        Transaction to validate.

    Returns
    -------
    verified : `bool`
        True if the transaction can be executed, or False otherwise.
    """
    if calculate_intrinsic_cost(tx) > tx.gas:
        return False
    if tx.nonce >= 2**64 - 1:
        return False
    if tx.to == Bytes0(b"") and len(tx.data) > 2 * MAX_CODE_SIZE:
        return False

    return True


def calculate_intrinsic_cost(tx: Transaction) -> Uint:
    """
    Calculates the gas that is charged before execution is started.

    The intrinsic cost of the transaction is charged before execution has
    begun. Functions/operations in the EVM cost money to execute so this
    intrinsic cost is for the operations that need to be paid for as part of
    the transaction. Data transfer, for example, is part of this intrinsic
    cost. It costs ether to send data over the wire and that ether is
    accounted for in the intrinsic cost calculated in this function. This
    intrinsic cost must be calculated and paid for before execution in order
    for all operations to be implemented.

    Parameters
    ----------
    tx :
        Transaction to compute the intrinsic cost of.

    Returns
    -------
    verified : `ethereum.base_types.Uint`
        The intrinsic cost of the transaction.
    """
    data_cost = 0

    for byte in tx.data:
        if byte == 0:
            data_cost += TX_DATA_COST_PER_ZERO
        else:
            data_cost += TX_DATA_COST_PER_NON_ZERO

    if tx.to == Bytes0(b""):
        create_cost = TX_CREATE_COST + int(init_code_cost(Uint(len(tx.data))))
    else:
        create_cost = 0

    access_list_cost = 0
    if isinstance(tx, (AccessListTransaction, FeeMarketTransaction)):
        for (_address, keys) in tx.access_list:
            access_list_cost += TX_ACCESS_LIST_ADDRESS_COST
            access_list_cost += len(keys) * TX_ACCESS_LIST_STORAGE_KEY_COST

    return Uint(TX_BASE_COST + data_cost + create_cost + access_list_cost)


def recover_sender(chain_id: U64, tx: Transaction) -> Address:
    """
    Extracts the sender address from a transaction.

    The v, r, and s values are the three parts that make up the signature
    of a transaction. In order to recover the sender of a transaction the two
    components needed are the signature (``v``, ``r``, and ``s``) and the
    signing hash of the transaction. The sender's public key can be obtained
    with these two values and therefore the sender address can be retrieved.

    Parameters
    ----------
    tx :
        Transaction of interest.
    chain_id :
        ID of the executing chain.

    Returns
    -------
    sender : `ethereum.fork_types.Address`
        The address of the account that signed the transaction.
    """
    v, r, s = tx.v, tx.r, tx.s

    ensure(0 < r and r < SECP256K1N, InvalidBlock)
    ensure(0 < s and s <= SECP256K1N // 2, InvalidBlock)

    if isinstance(tx, LegacyTransaction):
        if v == 27 or v == 28:
            public_key = secp256k1_recover(
                r, s, v - 27, signing_hash_pre155(tx)
            )
        else:
            ensure(
                v == 35 + chain_id * 2 or v == 36 + chain_id * 2, InvalidBlock
            )
            public_key = secp256k1_recover(
                r, s, v - 35 - chain_id * 2, signing_hash_155(tx, chain_id)
            )
    elif isinstance(tx, AccessListTransaction):
        public_key = secp256k1_recover(r, s, v, signing_hash_2930(tx))
    elif isinstance(tx, FeeMarketTransaction):
        public_key = secp256k1_recover(r, s, v, signing_hash_1559(tx))

    return Address(keccak256(public_key)[12:32])


def signing_hash_pre155(tx: LegacyTransaction) -> Hash32:
    """
    Compute the hash of a transaction used in a legacy (pre EIP 155) signature.

    Parameters
    ----------
    tx :
        Transaction of interest.

    Returns
    -------
    hash : `ethereum.crypto.hash.Hash32`
        Hash of the transaction.
    """
    return keccak256(
        rlp.encode(
            (
                tx.nonce,
                tx.gas_price,
                tx.gas,
                tx.to,
                tx.value,
                tx.data,
            )
        )
    )


def signing_hash_155(tx: LegacyTransaction, chain_id: U64) -> Hash32:
    """
    Compute the hash of a transaction used in a EIP 155 signature.

    Parameters
    ----------
    tx :
        Transaction of interest.
    chain_id :
        The id of the current chain.

    Returns
    -------
    hash : `ethereum.crypto.hash.Hash32`
        Hash of the transaction.
    """
    return keccak256(
        rlp.encode(
            (
                tx.nonce,
                tx.gas_price,
                tx.gas,
                tx.to,
                tx.value,
                tx.data,
                chain_id,
                Uint(0),
                Uint(0),
            )
        )
    )


def signing_hash_2930(tx: AccessListTransaction) -> Hash32:
    """
    Compute the hash of a transaction used in a EIP 2930 signature.

    Parameters
    ----------
    tx :
        Transaction of interest.

    Returns
    -------
    hash : `ethereum.crypto.hash.Hash32`
        Hash of the transaction.
    """
    return keccak256(
        b"\x01"
        + rlp.encode(
            (
                tx.chain_id,
                tx.nonce,
                tx.gas_price,
                tx.gas,
                tx.to,
                tx.value,
                tx.data,
                tx.access_list,
            )
        )
    )


def signing_hash_1559(tx: FeeMarketTransaction) -> Hash32:
    """
    Compute the hash of a transaction used in a EIP 1559 signature.

    Parameters
    ----------
    tx :
        Transaction of interest.

    Returns
    -------
    hash : `ethereum.crypto.hash.Hash32`
        Hash of the transaction.
    """
    return keccak256(
        b"\x02"
        + rlp.encode(
            (
                tx.chain_id,
                tx.nonce,
                tx.max_priority_fee_per_gas,
                tx.max_fee_per_gas,
                tx.gas,
                tx.to,
                tx.value,
                tx.data,
                tx.access_list,
            )
        )
    )


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
