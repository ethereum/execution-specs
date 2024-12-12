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

from ethereum.base_types import Bytes0
from ethereum.crypto import InvalidSignature
from ethereum.crypto.elliptic_curve import SECP256K1N, secp256k1_recover
from ethereum.crypto.hash import Hash32, keccak256
from ethereum.exceptions import InvalidBlock

from .. import rlp
from ..base_types import U64, U256, Bytes, Uint
from . import vm
from .blocks import Block, Header, Log, Receipt, Withdrawal
from .bloom import logs_bloom
from .fork_types import Address, Bloom, Root, VersionedHash
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
    TX_ACCESS_LIST_ADDRESS_COST,
    TX_ACCESS_LIST_STORAGE_KEY_COST,
    TX_BASE_COST,
    TX_CREATE_COST,
    TX_DATA_COST_PER_NON_ZERO,
    TX_DATA_COST_PER_ZERO,
    AccessListTransaction,
    BlobTransaction,
    FeeMarketTransaction,
    LegacyTransaction,
    Transaction,
    decode_transaction,
    encode_transaction,
)
from .trie import Trie, root, trie_set
from .utils.hexadecimal import hex_to_address
from .utils.message import prepare_message
from .vm import Message
from .vm.gas import (
    calculate_blob_gas_price,
    calculate_data_fee,
    calculate_excess_blob_gas,
    calculate_total_blob_gas,
    init_code_cost,
)
from .vm.interpreter import (
    MAX_CODE_SIZE,
    MessageCallOutput,
    process_message_call,
)

BASE_FEE_MAX_CHANGE_DENOMINATOR = 8
ELASTICITY_MULTIPLIER = 2
GAS_LIMIT_ADJUSTMENT_FACTOR = 1024
GAS_LIMIT_MINIMUM = 5000
EMPTY_OMMER_HASH = keccak256(rlp.encode([]))
SYSTEM_ADDRESS = hex_to_address("0xfffffffffffffffffffffffffffffffffffffffe")
BEACON_ROOTS_ADDRESS = hex_to_address(
    "0x000F3df6D732807Ef1319fB7B8bB8522d0Beac02"
)
SYSTEM_TRANSACTION_GAS = Uint(30000000)
MAX_BLOB_GAS_PER_BLOCK = 786432
VERSIONED_HASH_VERSION_KZG = b"\x01"


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
    validate_header(chain, block.header)
    if block.ommers != ():
        raise InvalidBlock

    env = vm.Environment(
        chain_id=chain.chain_id,
        state=chain.state,
        block_gas_limit=block.header.gas_limit,
        block_hashes=get_last_256_block_hashes(chain),
        coinbase=block.header.coinbase,
        number=block.header.number,
        base_fee_per_gas=block.header.base_fee_per_gas,
        gas_limit=block.header.gas_limit,
        time=block.header.timestamp,
        prev_randao=block.header.prev_randao,
        excess_blob_gas=block.header.excess_blob_gas,
        parent_beacon_block_root=block.header.parent_beacon_block_root,
    )

    apply_body_output = apply_body(
        env,
        block.transactions,
        block.withdrawals,
    )
    if apply_body_output.block_gas_used != block.header.gas_used:
        raise InvalidBlock
    if apply_body_output.transactions_root != block.header.transactions_root:
        raise InvalidBlock
    if apply_body_output.state_root != block.header.state_root:
        raise InvalidBlock
    if apply_body_output.receipt_root != block.header.receipt_root:
        raise InvalidBlock
    if apply_body_output.block_logs_bloom != block.header.bloom:
        raise InvalidBlock
    if apply_body_output.withdrawals_root != block.header.withdrawals_root:
        raise InvalidBlock
    if apply_body_output.blob_gas_used != block.header.blob_gas_used:
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


def validate_header(chain: BlockChain, header: Header) -> None:
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
    chain :
        History and current state.
    header :
        Header to check for correctness.
    """
    parent_header = chain.blocks[-1].header
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
    if header.number != parent_header.number + 1:
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
    env: vm.Environment,
    tx: Transaction,
    gas_available: Uint,
) -> Tuple[Address, Uint, Tuple[VersionedHash, ...]]:
    """
    Check if the transaction is includable in the block.

    Parameters
    ----------
    env :
        The execution environment.
    tx :
        The transaction.
    gas_available :
        The gas remaining in the block.

    Returns
    -------
    sender_address :
        The sender of the transaction.
    effective_gas_price :
        The price to charge for gas when the transaction is executed.
    blob_versioned_hashes :
        The blob versioned hashes of the transaction.

    Raises
    ------
    InvalidBlock :
        If the transaction is not includable.
    """
    if calculate_intrinsic_cost(tx) > tx.gas:
        raise InvalidBlock
    if tx.nonce >= 2**64 - 1:
        raise InvalidBlock
    if tx.to == Bytes0(b"") and len(tx.data) > 2 * MAX_CODE_SIZE:
        raise InvalidBlock

    if tx.gas > gas_available:
        raise InvalidBlock

    sender_address = recover_sender(env.chain_id, tx)

    sender_account = get_account(env.state, sender_address)

    base_fee_per_gas = env.base_fee_per_gas
    if isinstance(tx, (FeeMarketTransaction, BlobTransaction)):
        if tx.max_fee_per_gas < tx.max_priority_fee_per_gas:
            raise InvalidBlock
        if tx.max_fee_per_gas < base_fee_per_gas:
            raise InvalidBlock

        priority_fee_per_gas = min(
            tx.max_priority_fee_per_gas,
            tx.max_fee_per_gas - base_fee_per_gas,
        )
        effective_gas_price = priority_fee_per_gas + base_fee_per_gas
        max_gas_fee = tx.gas * tx.max_fee_per_gas
    else:
        if tx.gas_price < base_fee_per_gas:
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

        if tx.max_fee_per_blob_gas < calculate_blob_gas_price(
            env.excess_blob_gas
        ):
            raise InvalidBlock

        max_gas_fee += calculate_total_blob_gas(tx) * tx.max_fee_per_blob_gas
        blob_versioned_hashes = tx.blob_versioned_hashes
    else:
        blob_versioned_hashes = ()
    if sender_account.nonce != tx.nonce:
        raise InvalidBlock
    if sender_account.balance < max_gas_fee + tx.value:
        raise InvalidBlock
    if sender_account.code != bytearray():
        raise InvalidBlock

    return sender_address, effective_gas_price, blob_versioned_hashes


def make_receipt(
    tx: Transaction,
    error: Optional[Exception],
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

    if isinstance(tx, AccessListTransaction):
        return b"\x01" + rlp.encode(receipt)
    elif isinstance(tx, FeeMarketTransaction):
        return b"\x02" + rlp.encode(receipt)
    elif isinstance(tx, BlobTransaction):
        return b"\x03" + rlp.encode(receipt)
    else:
        return receipt


@dataclass
class ApplyBodyOutput:
    """
    Output from applying the block body to the present state.

    Contains the following:

    block_gas_used : `ethereum.base_types.Uint`
        Gas used for executing all transactions.
    transactions_root : `ethereum.fork_types.Root`
        Trie root of all the transactions in the block.
    receipt_root : `ethereum.fork_types.Root`
        Trie root of all the receipts in the block.
    block_logs_bloom : `Bloom`
        Logs bloom of all the logs included in all the transactions of the
        block.
    state_root : `ethereum.fork_types.Root`
        State root after all transactions have been executed.
    withdrawals_root : `ethereum.fork_types.Root`
        Trie root of all the withdrawals in the block.
    blob_gas_used : `ethereum.base_types.Uint`
        Total blob gas used in the block.
    """

    block_gas_used: Uint
    transactions_root: Root
    receipt_root: Root
    block_logs_bloom: Bloom
    state_root: Root
    withdrawals_root: Root
    blob_gas_used: Uint


def process_system_transaction(
    env: vm.Environment,
    target_address: Address,
    data: Bytes,
) -> MessageCallOutput:
    """
    Process a system transaction.

    Parameters
    ----------
    env :
        The execution environment.
    target_address :
        Address of the contract to call.
    data :
        Data to pass to the contract.

    Returns
    -------
    system_tx_output : `MessageCallOutput`
        Output of processing the system transaction.
    """
    system_contract_code = get_account(env.state, target_address).code

    system_tx_message = Message(
        origin=SYSTEM_ADDRESS,
        caller=SYSTEM_ADDRESS,
        gas_price=env.base_fee_per_gas,
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
        transient_storage=TransientStorage(),
        blob_versioned_hashes=(),
        parent_evm=None,
        traces=[],
    )

    system_tx_output = process_message_call(system_tx_message, env)

    destroy_touched_empty_accounts(
        env.state, system_tx_output.touched_accounts
    )

    return system_tx_output


def apply_body(
    env: vm.Environment,
    transactions: Tuple[Union[LegacyTransaction, Bytes], ...],
    withdrawals: Tuple[Withdrawal, ...],
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
    env :
        The execution environment.
    transactions :
        Transactions included in the block.
    withdrawals :
        Withdrawals to be processed in the current block.

    Returns
    -------
    apply_body_output : `ApplyBodyOutput`
        Output of applying the block body to the state.
    """
    blob_gas_used = Uint(0)
    gas_available = env.block_gas_limit
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

    process_system_transaction(
        env=env,
        target_address=BEACON_ROOTS_ADDRESS,
        data=env.parent_beacon_block_root,
    )

    for i, tx in enumerate(map(decode_transaction, transactions)):
        trie_set(
            transactions_trie, rlp.encode(Uint(i)), encode_transaction(tx)
        )

        gas_used, logs, error = process_transaction(env, tx, gas_available)
        gas_available -= gas_used

        receipt = make_receipt(
            tx, error, (env.block_gas_limit - gas_available), logs
        )

        trie_set(
            receipts_trie,
            rlp.encode(Uint(i)),
            receipt,
        )

        block_logs += logs
        blob_gas_used += calculate_total_blob_gas(tx)
    if blob_gas_used > MAX_BLOB_GAS_PER_BLOCK:
        raise InvalidBlock
    block_gas_used = env.block_gas_limit - gas_available

    block_logs_bloom = logs_bloom(block_logs)

    for i, wd in enumerate(withdrawals):
        trie_set(withdrawals_trie, rlp.encode(Uint(i)), rlp.encode(wd))

        process_withdrawal(env.state, wd)

        if account_exists_and_is_empty(env.state, wd.address):
            destroy_account(env.state, wd.address)

    return ApplyBodyOutput(
        block_gas_used,
        root(transactions_trie),
        root(receipts_trie),
        block_logs_bloom,
        state_root(env.state),
        root(withdrawals_trie),
        blob_gas_used,
    )


def process_transaction(
    env: vm.Environment,
    tx: Transaction,
    gas_available: Uint,
) -> Tuple[Uint, Tuple[Log, ...], Optional[Exception]]:
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
    gas_available :
        Gas available for the transaction in the block.

    Returns
    -------
    gas_left : `ethereum.base_types.U256`
        Remaining gas after execution.
    logs : `Tuple[ethereum.blocks.Log, ...]`
        Logs generated during execution.
    """
    (
        sender_address,
        effective_gas_price,
        blob_versioned_hashes,
    ) = check_transaction(
        env=env,
        tx=tx,
        gas_available=gas_available,
    )
    sender = sender_address
    sender_account = get_account(env.state, sender)

    if isinstance(tx, BlobTransaction):
        blob_gas_fee = calculate_data_fee(env.excess_blob_gas, tx)
    else:
        blob_gas_fee = Uint(0)

    effective_gas_fee = tx.gas * effective_gas_price

    gas = tx.gas - calculate_intrinsic_cost(tx)
    increment_nonce(env.state, sender)

    sender_balance_after_gas_fee = (
        sender_account.balance - effective_gas_fee - blob_gas_fee
    )
    set_account_balance(env.state, sender, sender_balance_after_gas_fee)

    preaccessed_addresses = set()
    preaccessed_storage_keys = set()
    preaccessed_addresses.add(env.coinbase)
    if isinstance(
        tx, (AccessListTransaction, FeeMarketTransaction, BlobTransaction)
    ):
        for address, keys in tx.access_list:
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
        code_address=None,
        should_transfer_value=True,
        is_static=False,
        preaccessed_addresses=frozenset(preaccessed_addresses),
        preaccessed_storage_keys=frozenset(preaccessed_storage_keys),
        gas_price=effective_gas_price,
        blob_versioned_hashes=blob_versioned_hashes,
    )

    output = process_message_call(message, env)

    gas_used = tx.gas - output.gas_left
    gas_refund = min(gas_used // 5, output.refund_counter)
    gas_refund_amount = (output.gas_left + gas_refund) * effective_gas_price

    # For non-1559 transactions env.gas_price == tx.gas_price
    priority_fee_per_gas = effective_gas_price - env.base_fee_per_gas
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

    destroy_touched_empty_accounts(env.state, output.touched_accounts)

    return total_gas_used, output.logs, output.error


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
    if isinstance(
        tx, (AccessListTransaction, FeeMarketTransaction, BlobTransaction)
    ):
        for _address, keys in tx.access_list:
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
    r, s = tx.r, tx.s
    if 0 >= r or r >= SECP256K1N:
        raise InvalidBlock
    if 0 >= s or s > SECP256K1N // 2:
        raise InvalidBlock

    try:
        if isinstance(tx, LegacyTransaction):
            v = tx.v
            if v == 27 or v == 28:
                public_key = secp256k1_recover(
                    r, s, v - 27, signing_hash_pre155(tx)
                )
            else:
                if v != 35 + chain_id * 2 and v != 36 + chain_id * 2:
                    raise InvalidBlock
                public_key = secp256k1_recover(
                    r, s, v - 35 - chain_id * 2, signing_hash_155(tx, chain_id)
                )
        elif isinstance(tx, AccessListTransaction):
            public_key = secp256k1_recover(
                r, s, tx.y_parity, signing_hash_2930(tx)
            )
        elif isinstance(tx, FeeMarketTransaction):
            public_key = secp256k1_recover(
                r, s, tx.y_parity, signing_hash_1559(tx)
            )
        elif isinstance(tx, BlobTransaction):
            public_key = secp256k1_recover(
                r, s, tx.y_parity, signing_hash_4844(tx)
            )
    except InvalidSignature as e:
        raise InvalidBlock from e

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


def signing_hash_4844(tx: BlobTransaction) -> Hash32:
    """
    Compute the hash of a transaction used in a EIP-4844 signature.

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
        b"\x03"
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
                tx.max_fee_per_blob_gas,
                tx.blob_versioned_hashes,
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
