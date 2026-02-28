"""
Host-side assembly of stateless input from block execution data.
"""

from typing import List, Optional, Tuple

from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes, Bytes8
from ethereum_types.numeric import U64, Uint

from ethereum.crypto.hash import Hash32, keccak256
from ethereum.state import Root

from .blocks import Header, Withdrawal
from .execution_engine.types import ExecutionPayload, NewPayloadRequest
from .fork import EMPTY_OMMER_HASH
from .fork_types import Bloom, VersionedHash
from .stateless import ChainConfig, StatelessInput
from .stateless_types import ExecutionWitness
from .transactions import BlobTransaction, decode_transaction
from .trie import trie_get
from .vm import BlockEnvironment, BlockOutput

# Amsterdam currently carries execution requests as raw bytes in order.
# TODO: can we get rid of this?
ExecutionRequests = Tuple[Bytes, ...]


def serialize_stateless_input(stateless_input: StatelessInput) -> Bytes:
    """
    Serialize a ``StatelessInput`` to RLP-encoded bytes.

    TODO: change to ssz, rlp was easier to get working with codebase.
    """
    return Bytes(rlp.encode(stateless_input))


def build_stateless_input(
    block_output: BlockOutput,
    block_env: BlockEnvironment,
    *,
    state_root: Root,
    transactions_root: Root,
    receipt_root: Root,
    bloom: Bloom,
    gas_used: Uint,
    withdrawals_root: Root,
    requests_hash: Hash32,
    block_access_list_hash: Hash32,
    withdrawals: Tuple[Withdrawal, ...],
    block_headers: Tuple[Bytes, ...],
    execution_witness: Optional[ExecutionWitness] = None,
) -> StatelessInput:
    """
    Build a StatelessInput from a completed block's execution data.

    Assemble the block header, compute the block hash, extract
    transaction bytes and versioned hashes, and package everything
    into a StatelessInput ready for stateless guest execution.
    """
    # Parent hash from the block environment.
    bh = block_env.block_hashes
    parent_hash = (
        Hash32(bytes(bh[-1]))
        if bh and bh[-1] is not None
        else Hash32(b"\x00" * 32)
    )

    header = Header(
        parent_hash=parent_hash,
        ommers_hash=EMPTY_OMMER_HASH,
        coinbase=block_env.coinbase,
        state_root=state_root,
        transactions_root=transactions_root,
        receipt_root=receipt_root,
        bloom=bloom,
        difficulty=Uint(0),
        number=block_env.number,
        gas_limit=block_env.block_gas_limit,
        gas_used=gas_used,
        timestamp=block_env.time,
        extra_data=Bytes(b""),
        prev_randao=block_env.prev_randao,
        nonce=Bytes8(b"\x00\x00\x00\x00\x00\x00\x00\x00"),
        base_fee_per_gas=block_env.base_fee_per_gas,
        withdrawals_root=withdrawals_root,
        blob_gas_used=block_output.blob_gas_used,
        excess_blob_gas=block_env.excess_blob_gas,
        parent_beacon_block_root=block_env.parent_beacon_block_root,
        requests_hash=requests_hash,
        block_access_list_hash=block_access_list_hash,
    )
    block_hash = Hash32(keccak256(rlp.encode(header)))

    # Extract transaction bytes and versioned hashes.
    tx_bytes_list = []
    versioned_hashes: List[VersionedHash] = []
    for key in block_output.receipt_keys:
        tx_val = trie_get(block_output.transactions_trie, key)
        if tx_val is None:
            continue
        tx_encoded = (
            tx_val if isinstance(tx_val, bytes) else rlp.encode(tx_val)
        )
        tx_bytes_list.append(Bytes(tx_encoded))
        try:
            tx_obj = decode_transaction(
                tx_encoded if isinstance(tx_val, bytes) else tx_val
            )
            if isinstance(tx_obj, BlobTransaction):
                versioned_hashes.extend(tx_obj.blob_versioned_hashes)
        except Exception:
            pass

    # Block access list as RLP bytes.
    bal = block_output.block_access_list
    bal_bytes = Bytes(rlp.encode(bal)) if bal is not None else Bytes(b"")

    # Execution requests.
    exec_requests: ExecutionRequests = tuple(
        Bytes(bytes(r)) for r in (block_output.requests or [])
    )

    # Prefer headers populated by BLOCKHASH access during execution;
    # fall back to the immediate parent header from the environment.
    ew = execution_witness
    if ew and ew.headers:
        witness_headers = ew.headers
    elif block_headers:
        witness_headers = (Bytes(block_headers[-1]),)
    else:
        witness_headers = ()

    witness = ExecutionWitness(
        state=ew.state if ew else (),
        codes=ew.codes if ew else (),
        headers=witness_headers,
    )

    payload = ExecutionPayload(
        parent_hash=parent_hash,
        fee_recipient=block_env.coinbase,
        state_root=state_root,
        receipts_root=receipt_root,
        logs_bloom=bloom,
        prev_randao=block_env.prev_randao,
        block_number=block_env.number,
        gas_limit=block_env.block_gas_limit,
        gas_used=gas_used,
        timestamp=block_env.time,
        extra_data=Bytes(b""),
        base_fee_per_gas=block_env.base_fee_per_gas,
        block_hash=block_hash,
        transactions=tuple(tx_bytes_list),
        withdrawals=withdrawals,
        blob_gas_used=block_output.blob_gas_used,
        excess_blob_gas=block_env.excess_blob_gas,
        block_access_list=bal_bytes,
    )

    new_payload = NewPayloadRequest(
        execution_payload=payload,
        versioned_hashes=tuple(versioned_hashes),
        parent_beacon_block_root=block_env.parent_beacon_block_root,
        execution_requests=exec_requests,
    )

    return StatelessInput(
        new_payload_request=new_payload,
        witness=witness,
        chain_config=ChainConfig(chain_id=U64(int(block_env.chain_id))),
        public_keys=(),
    )
