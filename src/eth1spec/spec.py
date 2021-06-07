"""
Ethereum Specification
----------------------
"""

from dataclasses import dataclass
from typing import List, Tuple

from . import crypto, evm, rlp, trie
from .eth_types import (
    TX_BASE_COST,
    TX_DATA_COST_PER_NON_ZERO,
    TX_DATA_COST_PER_ZERO,
    Account,
    Address,
    Block,
    Bytes32,
    Hash32,
    Header,
    Log,
    Receipt,
    Root,
    State,
    Transaction,
    Uint,
)

BLOCK_REWARD = 5 * 10 ** 18
EMPTY_ACCOUNT = Account(
    nonce=Uint(0),
    balance=Uint(0),
    code=bytearray(),
    storage={},
)


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
    #  assert verify_header(block.header)
    gas_used, receipt_root, state = apply_body(
        chain.state,
        block.header.coinbase,
        block.header.number,
        block.header.gas_limit,
        block.header.time,
        block.header.difficulty,
        block.transactions,
        block.ommers,
    )
    #  raise NotImplementedError()  # TODO


def verify_header(header: Header) -> bool:
    """
    Verifies a block header.

    Parameters
    ----------
    header : `eth1spec.eth_types.Header`
        Header to check for correctness.

    Returns
    -------
    verified : `bool`
        True if the header is correct, False otherwise.
    """
    raise NotImplementedError()  # TODO


def apply_body(
    state: State,
    coinbase: Address,
    block_number: Uint,
    block_gas_limit: Uint,
    block_time: Uint,
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
    block_number : `eth1spec.number.Uint`
        Position of the block within the chain.
    block_gas_limit : `eth1spec.number.Uint`
        Initial amount of gas available for execution in this block.
    block_time : `eth1spec.number.Uint`
        Time the block was produced, measured in seconds since the epoch.
    block_difficulty : `eth1spec.number.Uint`
        Difficulty of the block.
    transactions : `List[eth1spec.eth_types.Transaction]`
        Transactions included in the block.
    ommers : `List[eth1spec.eth_types.Header]`
        Headers of ancestor blocks which are not direct parents (formerly
        uncles.)

    Returns
    -------
    gas_available : `eth1spec.number.Uint`
        Remaining gas after all transactions have been executed.
    root : `eth1spec.eth_types.Root`
        State root after all transactions have been executed.
    state : `eth1spec.eth_types.State`
        State after all transactions have been executed.
    """
    gas_available = block_gas_limit
    receipts = []

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
                post_state=Root(
                    bytes.fromhex(
                        "00000000000000000000000000000000000000000000000000000"
                        "00000000000000000000000000000000000000000000000000000"
                        "0000000000000000000000"
                    )
                ),
                cumulative_gas_used=(block_gas_limit - gas_available),
                bloom=Bytes32(
                    bytes.fromhex(
                        "00000000000000000000000000000000000000000000000000000"
                        "00000000000000000000000000000000000000000000000000000"
                        "0000000000000000000000"
                    )
                ),
                logs=logs,
            )
        )

        gas_available -= gas_used

    if coinbase not in state:
        state[coinbase] = EMPTY_ACCOUNT

    state[coinbase].balance += BLOCK_REWARD

    receipts_map = {
        Uint(k).to_big_endian(): v for (k, v) in enumerate(receipts)
    }
    receipts_y = trie.y(receipts_map)
    return (gas_available), trie.TRIE(receipts_y), state


def process_transaction(
    env: evm.Environment, tx: Transaction
) -> Tuple[Uint, List[Log]]:
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
    gas_left : `eth1spec.number.Uint`
        Remaining gas after execution.
    logs : `List[eth1spec.eth_types.Log]`
        Logs generated during execution.
    """
    assert verify_transaction(tx)

    sender_address = env.origin
    sender = env.state[sender_address]

    assert sender.nonce == tx.nonce
    sender.nonce += 1

    cost = tx.gas * tx.gas_price
    assert cost <= sender.balance
    sender.balance -= cost

    if tx.to is None:
        raise NotImplementedError()  # TODO

    return evm.process_call(
        sender_address, tx.to, tx.data, tx.value, tx.gas, Uint(0), env
    )


def verify_transaction(tx: Transaction) -> bool:
    """
    Verifies a transaction.

    Parameters
    ----------
    tx : `eth1spec.eth_types.Transaction`
        Transaction to verify.

    Returns
    -------
    verified : `bool`
        True if the transaction can be executed, or False otherwise.
    """
    data_cost = 0

    for byte in tx.data:
        if byte == 0:
            data_cost += TX_DATA_COST_PER_ZERO
        else:
            data_cost += TX_DATA_COST_PER_NON_ZERO

    return TX_BASE_COST + data_cost <= tx.gas


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
