"""
Conversion helpers between Engine API structures and blocks.
"""

from typing import Optional, Tuple

from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes, Bytes8
from ethereum_types.numeric import Uint

from ethereum.crypto.hash import Hash32, keccak256
from ethereum.merkle_patricia_trie import Trie, root, trie_set
from ethereum.state import Root
from ethereum.state_mpt import copy_state

from ..blocks import Block, Header
from ..fork import EMPTY_OMMER_HASH, BlockChain
from ..requests import compute_requests_hash
from ..transactions import LegacyTransaction
from .types import ExecutionEngine, ExecutionPayloadV3


def _payload_header(
    execution_payload: ExecutionPayloadV3,
    parent_beacon_block_root: Root,
    execution_requests: Tuple[Bytes, ...],
) -> Header:
    """
    Build the execution header implied by a payload.
    """
    transactions_trie: Trie[Bytes, Optional[Bytes]] = Trie(
        secured=False, default=None
    )
    for i, encoded_tx in enumerate(execution_payload.transactions):
        trie_set(
            transactions_trie,
            rlp.encode(Uint(i)),
            encoded_tx,
        )
    transactions_root = root(transactions_trie)

    withdrawals_trie: Trie[Bytes, Optional[Bytes]] = Trie(
        secured=False, default=None
    )
    for i, withdrawal in enumerate(execution_payload.withdrawals):
        trie_set(
            withdrawals_trie,
            rlp.encode(Uint(i)),
            rlp.encode(withdrawal),
        )
    withdrawals_root = root(withdrawals_trie)

    # The wire-form requests are hashed as opaque items; their contents
    # play no part in the block hash.
    requests_hash = Hash32(compute_requests_hash(list(execution_requests)))

    return Header(
        parent_hash=execution_payload.parent_hash,
        ommers_hash=EMPTY_OMMER_HASH,
        coinbase=execution_payload.fee_recipient,
        state_root=execution_payload.state_root,
        transactions_root=transactions_root,
        receipt_root=execution_payload.receipts_root,
        bloom=execution_payload.logs_bloom,
        difficulty=Uint(0),
        number=execution_payload.block_number,
        gas_limit=execution_payload.gas_limit,
        gas_used=execution_payload.gas_used,
        timestamp=execution_payload.timestamp,
        extra_data=execution_payload.extra_data,
        prev_randao=execution_payload.prev_randao,
        nonce=Bytes8(b"\x00\x00\x00\x00\x00\x00\x00\x00"),
        base_fee_per_gas=execution_payload.base_fee_per_gas,
        withdrawals_root=withdrawals_root,
        blob_gas_used=execution_payload.blob_gas_used,
        excess_blob_gas=execution_payload.excess_blob_gas,
        parent_beacon_block_root=parent_beacon_block_root,
        requests_hash=requests_hash,
    )


def _payload_transaction_to_block_transaction(
    encoded_transaction: Bytes,
) -> LegacyTransaction | Bytes:
    """Return the canonical block representation of a payload transaction."""
    if not encoded_transaction or encoded_transaction[0] < 0xC0:
        return encoded_transaction

    return rlp.decode_to(LegacyTransaction, encoded_transaction)


def _payload_block(
    execution_payload: ExecutionPayloadV3,
    parent_beacon_block_root: Root,
    execution_requests: Tuple[Bytes, ...],
) -> Block:
    """
    Convert an execution payload into an execution-layer block.
    """
    header = _payload_header(
        execution_payload,
        parent_beacon_block_root,
        execution_requests,
    )

    return Block(
        header=header,
        transactions=tuple(
            _payload_transaction_to_block_transaction(encoded_transaction)
            for encoded_transaction in execution_payload.transactions
        ),
        ommers=(),
        withdrawals=execution_payload.withdrawals,
    )


def chain_of(engine: ExecutionEngine, block_hash: Hash32) -> BlockChain:
    """
    Build the chain whose head is the validated block `block_hash`.

    The chain is the block's ancestry paired with a copy of the state
    the block produced; nothing is re-executed.
    """
    branch = []
    cursor = block_hash
    genesis_hash = keccak256(rlp.encode(engine.genesis_block.header))
    while cursor != genesis_hash:
        block = engine.validated_blocks[cursor]
        branch.append(block)
        cursor = block.header.parent_hash
    branch.append(engine.genesis_block)
    branch.reverse()

    return BlockChain(
        blocks=branch[-255:],
        state=copy_state(engine.states[block_hash]),
        chain_id=engine.chain.chain_id,
    )
