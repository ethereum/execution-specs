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
from typing import List, Tuple

from . import crypto, evm, rlp, trie
from .base_types import U256, Uint
from .eth_types import (
    EMPTY_ACCOUNT,
    TX_BASE_COST,
    TX_DATA_COST_PER_NON_ZERO,
    TX_DATA_COST_PER_ZERO,
    Address,
    Block,
    Hash32,
    Header,
    Log,
    Receipt,
    Root,
    State,
    Transaction,
)
from .evm.interpreter import process_call

BLOCK_REWARD = 5 * 10 ** 18
GAS_LIMIT_ADJUSTMENT_FACTOR = 1024
GAS_LIMIT_MINIMUM = 125000


@dataclass
class BlockChain:
    """
    History and current state of the block chain.
    """

    blocks: List[Block]
    state: State


def state_transition(chain: BlockChain, block: Block) -> None:
    """
    Attempts to apply a block to an existing block chain.

    Parameters
    ----------
    chain : `eth1spec.eth_types.BlockChain`
        History and current state.
    block : `eth1spec.eth_types.Block`
        Block to apply to `chain`.
    """
    parent_header = get_block_header_by_hash(block.header.parent_hash, chain)
    assert verify_header(block.header, parent_header)
    gas_used, receipt_root, state = apply_body(
        chain.state,
        block.header.coinbase,
        block.header.number,
        block.header.gas_limit,
        block.header.timestamp,
        block.header.difficulty,
        block.transactions,
        block.ommers,
    )

    assert gas_used == block.header.gas_used
    assert receipt_root == block.header.receipt_root
    assert trie.root(trie.map_keys(state)) == block.header.state_root


def verify_header(header: Header, parent_header: Header) -> bool:
    """
    Verifies a block header.

    Parameters
    ----------
    header : `eth1spec.eth_types.Header`
        Header to check for correctness.
    parent_header: `eth1spec.eth_types.Header`
        Parent Header of the header to check for correctness

    Returns
    -------
    verified : `bool`
        True if the header is correct, False otherwise.
    """
    # TODO: get rid of the comment below once
    #  validate_proof_of_work is implemented
    # assert validate_proof_of_work(header)
    assert header.difficulty == calculate_block_difficulty(
        header, parent_header
    )
    assert validate_gas_limit(header.gas_limit, parent_header.gas_limit)
    assert header.timestamp > parent_header.timestamp
    assert header.number == parent_header.number + 1
    assert len(header.extra_data) <= 32
    return True


def apply_body(
    state: State,
    coinbase: Address,
    block_number: Uint,
    block_gas_limit: Uint,
    block_time: U256,
    block_difficulty: Uint,
    transactions: List[Transaction],
    ommers: List[Header],
) -> Tuple[Uint, Root, State]:
    """
    Executes a block.

    Parameters
    ----------
    state : `eth1spec.eth_types.State`
        Current account state.
    coinbase : `eth1spec.eth_types.Address`
        Address of account which receives block reward and transaction fees.
    block_number : `eth1spec.base_types.Uint`
        Position of the block within the chain.
    block_gas_limit : `eth1spec.base_types.Uint`
        Initial amount of gas available for execution in this block.
    block_time : `eth1spec.base_types.U256`
        Time the block was produced, measured in seconds since the epoch.
    block_difficulty : `eth1spec.base_types.Uint`
        Difficulty of the block.
    transactions : `List[eth1spec.eth_types.Transaction]`
        Transactions included in the block.
    ommers : `List[eth1spec.eth_types.Header]`
        Headers of ancestor blocks which are not direct parents (formerly
        uncles.)

    Returns
    -------
    gas_available : `eth1spec.base_types.Uint`
        Remaining gas after all transactions have been executed.
    root : `eth1spec.eth_types.Root`
        State root after all transactions have been executed.
    state : `eth1spec.eth_types.State`
        State after all transactions have been executed.
    """
    gas_available = block_gas_limit
    receipts = []

    if coinbase not in state:
        state[coinbase] = EMPTY_ACCOUNT

    for tx in transactions:
        assert tx.gas <= gas_available
        sender_address = recover_sender(tx)

        env = evm.Environment(
            caller=sender_address,
            origin=sender_address,
            block_hashes=[],
            coinbase=coinbase,
            number=block_number,
            gas_limit=block_gas_limit,
            gas_price=tx.gas_price,
            time=block_time,
            difficulty=block_difficulty,
            state=state,
        )

        gas_used, logs = process_transaction(env, tx)
        gas_available -= gas_used

        receipts.append(
            Receipt(
                post_state=Root(trie.root(trie.map_keys(state))),
                cumulative_gas_used=(block_gas_limit - gas_available),
                bloom=b"\x00" * 256,
                logs=[],
            )
        )

    state[coinbase].balance += BLOCK_REWARD

    gas_remaining = block_gas_limit - gas_available

    receipts_map = {
        bytes(rlp.encode(Uint(k))): v for (k, v) in enumerate(receipts)
    }
    receipt_root = trie.root(trie.map_keys(receipts_map, secured=False))

    return (gas_remaining, receipt_root, state)


def process_transaction(
    env: evm.Environment, tx: Transaction
) -> Tuple[U256, List[Log]]:
    """
    Execute a transaction against the provided environment.

    Parameters
    ----------
    env : `eth1spec.evm.Environment`
        Environment for the Ethereum Virtual Machine.
    tx : `eth1spec.eth_types.Transaction`
        Transaction to execute.

    Returns
    -------
    gas_left : `eth1spec.base_types.U256`
        Remaining gas after execution.
    logs : `List[eth1spec.eth_types.Log]`
        Logs generated during execution.
    """
    assert validate_transaction(tx)

    sender_address = env.origin
    sender = env.state[sender_address]

    assert sender.nonce == tx.nonce
    sender.nonce += 1

    cost = tx.gas * tx.gas_price
    assert cost <= sender.balance
    sender.balance -= cost

    gas = tx.gas - calculate_intrinsic_cost(tx)

    if tx.to is None:
        raise NotImplementedError()  # TODO

    gas_left, logs = process_call(
        sender_address, tx.to, tx.data, tx.value, gas, Uint(0), env
    )

    sender.balance += gas_left * tx.gas_price
    gas_used = tx.gas - gas_left
    env.state[env.coinbase].balance += gas_used * tx.gas_price

    return (gas_used, logs)


def validate_transaction(tx: Transaction) -> bool:
    """
    Verifies a transaction.

    Parameters
    ----------
    tx : `eth1spec.eth_types.Transaction`
        Transaction to validate.

    Returns
    -------
    verified : `bool`
        True if the transaction can be executed, or False otherwise.
    """
    return calculate_intrinsic_cost(tx) <= tx.gas


def calculate_intrinsic_cost(tx: Transaction) -> Uint:
    """
    Calculates the intrinsic cost of the transaction that is charged before
    execution is instantiated.

    Parameters
    ----------
    tx : `eth1spec.eth_types.Transaction`
        Transaction to compute the intrinsic cost of.

    Returns
    -------
    verified : `eth1spec.base_types.Uint`
        The intrinsic cost of the transaction.
    """
    data_cost = 0

    for byte in tx.data:
        if byte == 0:
            data_cost += TX_DATA_COST_PER_ZERO
        else:
            data_cost += TX_DATA_COST_PER_NON_ZERO

    return Uint(TX_BASE_COST + data_cost)


def recover_sender(tx: Transaction) -> Address:
    """
    Extracts the sender address from a transaction.

    Parameters
    ----------
    tx : `eth1spec.eth_types.Transaction`
        Transaction of interest.

    Returns
    -------
    sender : `eth1spec.eth_types.Address`
        The address of the account that signed the transaction.
    """
    v, r, s = tx.v, tx.r, tx.s

    #  if v > 28:
    #      v = v - (chain_id*2+8)

    secp256k1n = (
        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
    )

    assert v == 27 or v == 28
    assert 0 < r and r < secp256k1n

    # TODO: this causes error starting in block 46169 (or 46170?)
    # assert 0<s_int and s_int<(secp256k1n//2+1)

    public_key = crypto.secp256k1_recover(r, s, v - 27, signing_hash(tx))
    return Address(crypto.keccak256(public_key)[12:32])


def signing_hash(tx: Transaction) -> Hash32:
    """
    Compute the hash of a transaction used in the signature.

    Parameters
    ----------
    tx : `eth1spec.eth_types.Transaction`
        Transaction of interest.

    Returns
    -------
    hash : `eth1spec.eth_types.Hash32`
        Hash of the transaction.
    """
    return crypto.keccak256(
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


def compute_header_hash(header: Header) -> Hash32:
    """
    Computes the hash of a block header.

    Parameters
    ----------
    header : `eth1spec.eth_types.Header`
        Header of interest.

    Returns
    -------
    hash : `eth1spec.eth_types.Hash32`
        Hash of the header.
    """
    return crypto.keccak256(
        rlp.encode(
            (
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
                header.mix_digest,
                header.nonce,
            )
        )
    )


def get_block_header_by_hash(hash: Hash32, chain: BlockChain) -> Header:
    """
    Fetches the block header with the corresponding hash.

    Parameters
    ----------
    hash : `eth1spec.eth_types.Hash32`
        Hash of the header of interest.

    chain : `eth1spec.eth_types.BlockChain`
        History and current state.

    Returns
    -------
    Header : `eth1spec.eth_types.Header`
        Block header found by its hash.
    """
    for block in chain.blocks:
        if compute_header_hash(block.header) == hash:
            return block.header
    else:
        raise ValueError(f"Could not find header with hash={hash.hex()}")


def validate_proof_of_work(header: Header) -> bool:
    """
    Validates the Proof of Work constraints

    Parameters
    ----------
    header : `eth1spec.eth_types.Uint`
        header of interest

    Returns
    -------
    valid : `bool`
        True if Proof of Work constraints are satisfied, False otherwise
    """
    # TODO: Implement this method once proof of work
    #  algorithm is implemented
    #  https://github.com/quilt/eth1.0-specs/issues/43
    raise NotImplementedError


def validate_gas_limit(gas_limit: Uint, parent_gas_limit: Uint) -> bool:
    """
    Validates the gas limit for a block

    Parameters
    ----------
    gas_limit : `eth1spec.eth_types.Uint`
        Gas limit to validate.

    parent_gas_limit : `eth1spec.eth_types.Uint`
        Gas limit of the parent block.

    Returns
    -------
    valid : `bool`
        True if gas limit constraints are satisfied, False otherwise
    """
    max_adjustment_delta = parent_gas_limit // GAS_LIMIT_ADJUSTMENT_FACTOR
    if gas_limit >= parent_gas_limit + max_adjustment_delta:
        return False
    if gas_limit <= parent_gas_limit - max_adjustment_delta:
        return False
    if gas_limit < GAS_LIMIT_MINIMUM:
        return False

    return True


def calculate_block_difficulty(header: Header, parent_header: Header) -> Uint:
    """
    Computes difficulty of a block using its header and parent header
    Parameters
    ----------
    header: `eth1spec.eth_types.Header`
        header of interest
    parent_header: `eth1spec.eth_types.Header`
        parent header of header of interest
    Returns
    ------
    difficulty: Uint
        Computed difficulty for a block.
    """
    if header.number == 0:
        return Uint(131072)
    elif header.timestamp < parent_header.timestamp + 13:
        return parent_header.difficulty + parent_header.difficulty // Uint(
            2048
        )
    else:  # header.timestamp >= parent_header.timestamp + 13
        return max(
            Uint(131072),
            parent_header.difficulty
            - (parent_header.difficulty // Uint(2048)),
        )


def print_state(state: State) -> None:
    """
    Pretty prints the state.

    Parameters
    ----------
    state : `eth1spec.eth_types.State`
        Ethereum state.
    """
    nice = {}
    for (address, account) in state.items():
        nice[address.hex()] = {
            "nonce": account.nonce,
            "balance": account.balance,
            "code": account.code.hex(),
            "storage": {},
        }

        for (k, v) in account.storage.items():
            nice[address.hex()]["storage"][k.hex()] = v.hex()  # type: ignore

    print(nice)
