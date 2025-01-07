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
from typing import List, Optional, Set, Tuple

from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes, Bytes32
from ethereum_types.numeric import U64, U256, Uint

from ethereum.crypto.hash import Hash32, keccak256
from ethereum.ethash import dataset_size, generate_cache, hashimoto_light
from ethereum.exceptions import InvalidBlock, InvalidSenderError

from . import vm
from .blocks import Block, Header, Log, Receipt
from .bloom import logs_bloom
from .fork_types import Address, Bloom, Root
from .state import (
    State,
    create_ether,
    destroy_account,
    get_account,
    increment_nonce,
    set_account_balance,
    state_root,
)
from .transactions import (
    Transaction,
    calculate_intrinsic_cost,
    recover_sender,
    validate_transaction,
)
from .trie import Trie, root, trie_set
from .utils.message import prepare_message
from .vm.interpreter import process_message_call

BLOCK_REWARD = U256(5 * 10**18)
GAS_LIMIT_ADJUSTMENT_FACTOR = Uint(1024)
GAS_LIMIT_MINIMUM = Uint(5000)
MINIMUM_DIFFICULTY = Uint(131072)
MAX_OMMER_DEPTH = Uint(6)


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
    validate_ommers(block.ommers, block.header, chain)
    apply_body_output = apply_body(
        chain.state,
        get_last_256_block_hashes(chain),
        block.header.coinbase,
        block.header.number,
        block.header.gas_limit,
        block.header.timestamp,
        block.header.difficulty,
        block.transactions,
        block.ommers,
    )
    if apply_body_output.block_gas_used != block.header.gas_used:
        raise InvalidBlock(
            f"{apply_body_output.block_gas_used} != {block.header.gas_used}"
        )
    if apply_body_output.transactions_root != block.header.transactions_root:
        raise InvalidBlock
    if apply_body_output.state_root != block.header.state_root:
        raise InvalidBlock
    if apply_body_output.receipt_root != block.header.receipt_root:
        raise InvalidBlock
    if apply_body_output.block_logs_bloom != block.header.bloom:
        raise InvalidBlock

    chain.blocks.append(block)
    if len(chain.blocks) > 255:
        # Real clients have to store more blocks to deal with reorgs, but the
        # protocol only requires the last 255
        chain.blocks = chain.blocks[-255:]


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
    if header.timestamp <= parent_header.timestamp:
        raise InvalidBlock
    if header.number != parent_header.number + Uint(1):
        raise InvalidBlock
    if not check_gas_limit(header.gas_limit, parent_header.gas_limit):
        raise InvalidBlock
    if len(header.extra_data) > 32:
        raise InvalidBlock

    block_difficulty = calculate_block_difficulty(
        header.number,
        header.timestamp,
        parent_header.timestamp,
        parent_header.difficulty,
    )
    if header.difficulty != block_difficulty:
        raise InvalidBlock

    block_parent_hash = keccak256(rlp.encode(parent_header))
    if header.parent_hash != block_parent_hash:
        raise InvalidBlock

    validate_proof_of_work(header)


def generate_header_hash_for_pow(header: Header) -> Hash32:
    """
    Generate rlp hash of the header which is to be used for Proof-of-Work
    verification.

    In other words, the PoW artefacts `mix_digest` and `nonce` are ignored
    while calculating this hash.

    A particular PoW is valid for a single hash, that hash is computed by
    this function. The `nonce` and `mix_digest` are omitted from this hash
    because they are being changed by miners in their search for a sufficient
    proof-of-work.

    Parameters
    ----------
    header :
        The header object for which the hash is to be generated.

    Returns
    -------
    hash : `Hash32`
        The PoW valid rlp hash of the passed in header.
    """
    header_data_without_pow_artefacts = (
        header.parent_hash,
        header.ommers_hash,
        header.coinbase,
        header.state_root,
        header.transactions_root,
        header.receipt_root,
        header.bloom,
        header.difficulty,
        header.number,
        header.gas_limit,
        header.gas_used,
        header.timestamp,
        header.extra_data,
    )

    return keccak256(rlp.encode(header_data_without_pow_artefacts))


def validate_proof_of_work(header: Header) -> None:
    """
    Validates the Proof of Work constraints.

    In order to verify that a miner's proof-of-work is valid for a block, a
    ``mix-digest`` and ``result`` are calculated using the ``hashimoto_light``
    hash function. The mix digest is a hash of the header and the nonce that
    is passed through and it confirms whether or not proof-of-work was done
    on the correct block. The result is the actual hash value of the block.

    Parameters
    ----------
    header :
        Header of interest.
    """
    header_hash = generate_header_hash_for_pow(header)
    # TODO: Memoize this somewhere and read from that data instead of
    # calculating cache for every block validation.
    cache = generate_cache(header.number)
    mix_digest, result = hashimoto_light(
        header_hash, header.nonce, cache, dataset_size(header.number)
    )
    if mix_digest != header.mix_digest:
        raise InvalidBlock

    limit = Uint(U256.MAX_VALUE) + Uint(1)
    if Uint.from_be_bytes(result) > (limit // header.difficulty):
        raise InvalidBlock


def check_transaction(
    tx: Transaction,
    gas_available: Uint,
) -> Address:
    """
    Check if the transaction is includable in the block.

    Parameters
    ----------
    tx :
        The transaction.
    gas_available :
        The gas remaining in the block.

    Returns
    -------
    sender_address :
        The sender of the transaction.

    Raises
    ------
    InvalidBlock :
        If the transaction is not includable.
    """
    if tx.gas > gas_available:
        raise InvalidBlock
    sender_address = recover_sender(tx)

    return sender_address


def make_receipt(
    tx: Transaction,
    post_state: Bytes32,
    cumulative_gas_used: Uint,
    logs: Tuple[Log, ...],
) -> Receipt:
    """
    Make the receipt for a transaction that was executed.

    Parameters
    ----------
    tx :
        The executed transaction.
    post_state :
        The state root immediately after this transaction.
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
        post_state=post_state,
        cumulative_gas_used=cumulative_gas_used,
        bloom=logs_bloom(logs),
        logs=logs,
    )

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
    """

    block_gas_used: Uint
    transactions_root: Root
    receipt_root: Root
    block_logs_bloom: Bloom
    state_root: Root


def apply_body(
    state: State,
    block_hashes: List[Hash32],
    coinbase: Address,
    block_number: Uint,
    block_gas_limit: Uint,
    block_time: U256,
    block_difficulty: Uint,
    transactions: Tuple[Transaction, ...],
    ommers: Tuple[Header, ...],
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
    block_gas_limit :
        Initial amount of gas available for execution in this block.
    block_time :
        Time the block was produced, measured in seconds since the epoch.
    block_difficulty :
        Difficulty of the block.
    transactions :
        Transactions included in the block.
    ommers :
        Headers of ancestor blocks which are not direct parents (formerly
        uncles.)

    Returns
    -------
    apply_body_output : `ApplyBodyOutput`
        Output of applying the block body to the state.
    """
    gas_available = block_gas_limit
    transactions_trie: Trie[Bytes, Optional[Transaction]] = Trie(
        secured=False, default=None
    )
    receipts_trie: Trie[Bytes, Optional[Receipt]] = Trie(
        secured=False, default=None
    )
    block_logs: Tuple[Log, ...] = ()

    for i, tx in enumerate(transactions):
        trie_set(transactions_trie, rlp.encode(Uint(i)), tx)

        sender_address = check_transaction(tx, gas_available)

        env = vm.Environment(
            caller=sender_address,
            origin=sender_address,
            block_hashes=block_hashes,
            coinbase=coinbase,
            number=block_number,
            gas_limit=block_gas_limit,
            gas_price=tx.gas_price,
            time=block_time,
            difficulty=block_difficulty,
            state=state,
            traces=[],
        )

        gas_used, logs = process_transaction(env, tx)
        gas_available -= gas_used

        receipt = make_receipt(
            tx, state_root(state), (block_gas_limit - gas_available), logs
        )

        trie_set(
            receipts_trie,
            rlp.encode(Uint(i)),
            receipt,
        )

        block_logs += logs

    pay_rewards(state, block_number, coinbase, ommers)

    block_gas_used = block_gas_limit - gas_available

    block_logs_bloom = logs_bloom(block_logs)

    return ApplyBodyOutput(
        block_gas_used,
        root(transactions_trie),
        root(receipts_trie),
        block_logs_bloom,
        state_root(state),
    )


def validate_ommers(
    ommers: Tuple[Header, ...], block_header: Header, chain: BlockChain
) -> None:
    """
    Validates the ommers mentioned in the block.

    An ommer block is a block that wasn't canonically added to the
    blockchain because it wasn't validated as fast as the canonical block
    but was mined at the same time.

    To be considered valid, the ommers must adhere to the rules defined in
    the Ethereum protocol. The maximum amount of ommers is 2 per block and
    there cannot be duplicate ommers in a block. Many of the other ommer
    constraints are listed in the in-line comments of this function.

    Parameters
    ----------
    ommers :
        List of ommers mentioned in the current block.
    block_header:
        The header of current block.
    chain :
        History and current state.
    """
    block_hash = keccak256(rlp.encode(block_header))
    if keccak256(rlp.encode(ommers)) != block_header.ommers_hash:
        raise InvalidBlock

    if len(ommers) == 0:
        # Nothing to validate
        return

    # Check that each ommer satisfies the constraints of a header
    for ommer in ommers:
        if Uint(1) > ommer.number or ommer.number >= block_header.number:
            raise InvalidBlock
        ommer_parent_header = chain.blocks[
            -(block_header.number - ommer.number) - 1
        ].header
        validate_header(ommer, ommer_parent_header)
    if len(ommers) > 2:
        raise InvalidBlock

    ommers_hashes = [keccak256(rlp.encode(ommer)) for ommer in ommers]
    if len(ommers_hashes) != len(set(ommers_hashes)):
        raise InvalidBlock

    recent_canonical_blocks = chain.blocks[-(MAX_OMMER_DEPTH + Uint(1)) :]
    recent_canonical_block_hashes = {
        keccak256(rlp.encode(block.header))
        for block in recent_canonical_blocks
    }
    recent_ommers_hashes: Set[Hash32] = set()
    for block in recent_canonical_blocks:
        recent_ommers_hashes = recent_ommers_hashes.union(
            {keccak256(rlp.encode(ommer)) for ommer in block.ommers}
        )

    for ommer_index, ommer in enumerate(ommers):
        ommer_hash = ommers_hashes[ommer_index]
        if ommer_hash == block_hash:
            raise InvalidBlock
        if ommer_hash in recent_canonical_block_hashes:
            raise InvalidBlock
        if ommer_hash in recent_ommers_hashes:
            raise InvalidBlock

        # Ommer age with respect to the current block. For example, an age of
        # 1 indicates that the ommer is a sibling of previous block.
        ommer_age = block_header.number - ommer.number
        if Uint(1) > ommer_age or ommer_age > MAX_OMMER_DEPTH:
            raise InvalidBlock
        if ommer.parent_hash not in recent_canonical_block_hashes:
            raise InvalidBlock
        if ommer.parent_hash == block_header.parent_hash:
            raise InvalidBlock


def pay_rewards(
    state: State,
    block_number: Uint,
    coinbase: Address,
    ommers: Tuple[Header, ...],
) -> None:
    """
    Pay rewards to the block miner as well as the ommers miners.

    The miner of the canonical block is rewarded with the predetermined
    block reward, ``BLOCK_REWARD``, plus a variable award based off of the
    number of ommer blocks that were mined around the same time, and included
    in the canonical block's header. An ommer block is a block that wasn't
    added to the canonical blockchain because it wasn't validated as fast as
    the accepted block but was mined at the same time. Although not all blocks
    that are mined are added to the canonical chain, miners are still paid a
    reward for their efforts. This reward is called an ommer reward and is
    calculated based on the number associated with the ommer block that they
    mined.

    Parameters
    ----------
    state :
        Current account state.
    block_number :
        Position of the block within the chain.
    coinbase :
        Address of account which receives block reward and transaction fees.
    ommers :
        List of ommers mentioned in the current block.
    """
    ommer_count = U256(len(ommers))
    miner_reward = BLOCK_REWARD + (ommer_count * (BLOCK_REWARD // U256(32)))
    create_ether(state, coinbase, miner_reward)

    for ommer in ommers:
        # Ommer age with respect to the current block.
        ommer_age = U256(block_number - ommer.number)
        ommer_miner_reward = ((U256(8) - ommer_age) * BLOCK_REWARD) // U256(8)
        create_ether(state, ommer.coinbase, ommer_miner_reward)


def process_transaction(
    env: vm.Environment, tx: Transaction
) -> Tuple[Uint, Tuple[Log, ...]]:
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
    if not validate_transaction(tx):
        raise InvalidBlock

    sender = env.origin
    sender_account = get_account(env.state, sender)
    gas_fee = tx.gas * tx.gas_price
    if sender_account.nonce != tx.nonce:
        raise InvalidBlock
    if Uint(sender_account.balance) < gas_fee + Uint(tx.value):
        raise InvalidBlock
    if sender_account.code != bytearray():
        raise InvalidSenderError("not EOA")

    gas = tx.gas - calculate_intrinsic_cost(tx)
    increment_nonce(env.state, sender)
    sender_balance_after_gas_fee = Uint(sender_account.balance) - gas_fee
    set_account_balance(env.state, sender, U256(sender_balance_after_gas_fee))

    message = prepare_message(
        sender,
        tx.to,
        tx.value,
        tx.data,
        gas,
        env,
    )

    output = process_message_call(message, env)

    gas_used = tx.gas - output.gas_left
    gas_refund = min(gas_used // Uint(2), Uint(output.refund_counter))
    gas_refund_amount = (output.gas_left + gas_refund) * tx.gas_price
    transaction_fee = (tx.gas - output.gas_left - gas_refund) * tx.gas_price
    total_gas_used = gas_used - gas_refund

    # refund gas
    sender_balance_after_refund = get_account(
        env.state, sender
    ).balance + U256(gas_refund_amount)
    set_account_balance(env.state, sender, sender_balance_after_refund)

    # transfer miner fees
    coinbase_balance_after_mining_fee = get_account(
        env.state, env.coinbase
    ).balance + U256(transaction_fee)
    set_account_balance(
        env.state, env.coinbase, coinbase_balance_after_mining_fee
    )

    for address in output.accounts_to_delete:
        destroy_account(env.state, address)

    return total_gas_used, output.logs


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


def calculate_block_difficulty(
    block_number: Uint,
    block_timestamp: U256,
    parent_timestamp: U256,
    parent_difficulty: Uint,
) -> Uint:
    """
    Computes difficulty of a block using its header and parent header.

    The difficulty is determined by the time the block was created after its
    parent. The ``offset`` is calculated using the parent block's difficulty,
    ``parent_difficulty``, and the timestamp between blocks. This offset is
    then added to the parent difficulty and is stored as the ``difficulty``
    variable. If the time between the block and its parent is too short, the
    offset will result in a positive number thus making the sum of
    ``parent_difficulty`` and ``offset`` to be a greater value in order to
    avoid mass forking. But, if the time is long enough, then the offset
    results in a negative value making the block less difficult than
    its parent.

    The base standard for a block's difficulty is the predefined value
    set for the genesis block since it has no parent. So, a block
    can't be less difficult than the genesis block, therefore each block's
    difficulty is set to the maximum value between the calculated
    difficulty and the ``GENESIS_DIFFICULTY``.

    Parameters
    ----------
    block_number :
        Block number of the block.
    block_timestamp :
        Timestamp of the block.
    parent_timestamp :
        Timestamp of the parent block.
    parent_difficulty :
        difficulty of the parent block.

    Returns
    -------
    difficulty : `ethereum.base_types.Uint`
        Computed difficulty for a block.
    """
    offset = (
        int(parent_difficulty)
        // 2048
        * max(1 - int(block_timestamp - parent_timestamp) // 10, -99)
    )
    difficulty = int(parent_difficulty) + offset
    # Historical Note: The difficulty bomb was not present in Ethereum at the
    # start of Frontier, but was added shortly after launch. However since the
    # bomb has no effect prior to block 200000 we pretend it existed from
    # genesis.
    # See https://github.com/ethereum/go-ethereum/pull/1588
    num_bomb_periods = (int(block_number) // 100000) - 2
    if num_bomb_periods >= 0:
        difficulty += 2**num_bomb_periods

    # Some clients raise the difficulty to `MINIMUM_DIFFICULTY` prior to adding
    # the bomb. This bug does not matter because the difficulty is always much
    # greater than `MINIMUM_DIFFICULTY` on Mainnet.
    return Uint(max(difficulty, int(MINIMUM_DIFFICULTY)))
