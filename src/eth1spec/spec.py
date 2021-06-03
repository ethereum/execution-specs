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
    nonce=0,
    balance=0,
    code=bytearray(),
    storage={},
)


@dataclass
class BlockChain:
    blocks: List[Block]
    state: State


def state_transition(chain: BlockChain, block: Block) -> None:
    assert verify_header(block.header)
    state, receipt_root, gas_used = apply_body(
        chain.state,
        block.header.coinbase,
        block.header.gas_limit,
        block.transactions,
        block.ommers,
    )
    if header == block.header:
        chain.blocks.append(block)
        chain.state = state
    else:
        print("invalid block")


def verify_header(header: Header) -> bool:
    pass


def apply_body(
    state: State,
    coinbase: Address,
    gas_limit: Uint,
    transactions: List[Transaction],
    ommers: List[Header],
) -> Tuple[Uint, Root, State]:
    gas_available = gas_limit
    receipts = []

    for tx in transactions:
        assert tx.gas_limit <= gas_available
        ctx = evm.Environment(
            block_hashes=[],
            coinbase=block.coinbase,
            number=block.number,
            gas_limit=block.gas_limit,
            gas_price=tx.gas_price,
            time=block.time,
            difficulty=block.difficulty,
            state=chain.state,
        )

        logs, gas_used = process_transaction(chain, block, tx)
        gas_available -= gas_used

        receipts.append(
            Receipt(
                post_state=bytes.from_hex(
                    "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
                ),
                cumulative_gas_used=(block.gas_limit - gas_available),
                bloom=bytes.from_hex(
                    "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
                ),
                logs=logs,
            )
        )

        gas_available -= gas_used

    if coinbase not in state:
        state[coinbase] = EMPTY_ACCOUNT

    state[coinbase].balance += BLOCK_REWARD

    return (gas_available), trie.TRIE(trie.y(receipts)), state


def process_transaction(
    ctx: evm.Environment, tx: Transaction
) -> Tuple[List[Log], Uint]:
    assert verify_transaction(tx)

    sender_address = recover_sender(tx)
    sender = ctx.state[sender_address]

    assert sender.nonce == tx.nonce
    sender.nonce += 1

    cost = tx.gas_limit * tx.gas_price
    assert cost <= sender.balance
    sender.balance -= cost

    ctx.caller = sender
    return evm.proccess_call(sender, target, tx.data, tx.value, tx.gas, 0, ctx)


def verify_transaction(tx: Transaction) -> bool:
    data_cost = 0

    for byte in tx.data:
        if byte == 0:
            data_cost += TX_DATA_COST_PER_ZERO
        else:
            data_cost += TX_DATA_COST_PER_NON_ZERO

    return TX_BASE_COST + data_cost <= tx.gas_limit


def recover_sender(tx) -> Address:
    v, r, s = tx.v, tx.r, tx.s

    #  if v > 28:
    #      v = v - (chainid*2+8)

    assert v == 27 or v == 28
    r_int = int.from_bytes(r, "big")
    s_int = int.from_bytes(s, "big")

    assert 0 < r_int and r_int < secp256k1n
    # assert 0<s_int and s_int<(secp256k1n//2+1)     # TODO: this causes error starting in block 46169 (or 46170?), so just commented

    return crypto.secp256k1recover(r, s, v - 27, sig_hash_tx(tx))[12:]


def sig_hash_tx(tx: Transaction) -> Hash32:
    return crypto.keccak256(
        rlp.encode(
            tx.nonce, tx.gas_price, tx.gas_limit, tx.to, tx.value, tx.data
        )
    )
