"""
Host-side assembly of stateless input from block execution data.
"""

from typing import List

from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes
from ethereum_types.numeric import U64

from ethereum.crypto.hash import Hash32, keccak256

from .block_access_lists import BlockAccessList
from .blocks import Block
from .execution_engine.requests import ExecutionRequests
from .execution_engine.types import ExecutionPayload, NewPayloadRequest
from .fork_types import VersionedHash
from .stateless import (
    BlobSchedule,
    ChainConfig,
    ExecutionWitness,
    ForkActivation,
    ForkConfig,
    ProtocolFork,
    StatelessInput,
    StatelessValidationResult,
)
from .stateless_ssz import (
    STATELESS_INPUT_SCHEMA_ID_BYTES,
    SszStatelessValidationResult,
    ssz_to_validation_result,
    stateless_input_to_ssz,
)
from .transactions import (
    BlobTransaction,
    LegacyTransaction,
    Transaction,
    decode_transaction,
    recover_transaction_public_key,
)
from .vm.gas import (
    BLOB_BASE_FEE_UPDATE_FRACTION,
    BLOB_SCHEDULE_MAX,
    BLOB_SCHEDULE_TARGET,
)


def serialize_stateless_input(
    stateless_input: StatelessInput,
) -> Bytes:
    """Serialize a StatelessInput to schema-prefixed SSZ bytes."""
    ssz_obj = stateless_input_to_ssz(stateless_input)
    return Bytes(
        STATELESS_INPUT_SCHEMA_ID_BYTES + bytes(ssz_obj.encode_bytes())
    )


def deserialize_stateless_output(data: Bytes) -> StatelessValidationResult:
    """Deserialize a StatelessValidationResult from SSZ bytes."""
    ssz_obj = SszStatelessValidationResult.decode_bytes(data)
    return ssz_to_validation_result(ssz_obj)


def build_chain_config(chain_id: U64) -> ChainConfig:
    """
    Build the chain configuration supported by this host.

    For now the Amsterdam stateless host only describes the Amsterdam fork.
    """
    return ChainConfig(
        chain_id=chain_id,
        active_fork=ForkConfig(
            fork=ProtocolFork.Amsterdam,
            activation=ForkActivation(
                block_number=None,
                timestamp=U64(0),
            ),
            blob_schedule=BlobSchedule(
                target=BLOB_SCHEDULE_TARGET,
                max=BLOB_SCHEDULE_MAX,
                base_fee_update_fraction=U64(BLOB_BASE_FEE_UPDATE_FRACTION),
            ),
        ),
    )


def build_stateless_input(
    block: Block,
    *,
    execution_witness: ExecutionWitness,
    execution_requests: ExecutionRequests,
    block_access_list: BlockAccessList,
    chain_id: U64,
) -> StatelessInput:
    """
    Build a StatelessInput from a completed block.

    Extract the header, transactions, and withdrawals from the block,
    compute the block hash, collect versioned hashes, and package
    everything into a StatelessInput ready for stateless guest execution.
    """
    header = block.header
    block_hash = Hash32(keccak256(rlp.encode(header)))

    # Encode transactions to bytes, recover public keys, and collect
    # versioned hashes.
    tx_bytes_list: List[Bytes] = []
    public_keys: List[Bytes] = []
    versioned_hashes: List[VersionedHash] = []
    for tx in block.transactions:
        tx_obj: Transaction
        if isinstance(tx, LegacyTransaction):
            tx_bytes_list.append(Bytes(rlp.encode(tx)))
            tx_obj = tx
        else:
            tx_bytes_list.append(Bytes(tx))
            # A typed tx may be malformed (pre-execution-rejected by
            # t8n but still committed to by the block's transactions
            # trie).
            try:
                tx_obj = decode_transaction(tx)
            except Exception:
                continue
        public_keys.append(recover_transaction_public_key(chain_id, tx_obj))
        if isinstance(tx_obj, BlobTransaction):
            versioned_hashes.extend(tx_obj.blob_versioned_hashes)

    # Block access list as RLP bytes.
    bal_bytes = Bytes(rlp.encode(block_access_list))

    payload = ExecutionPayload(
        parent_hash=header.parent_hash,
        fee_recipient=header.coinbase,
        state_root=header.state_root,
        receipts_root=header.receipt_root,
        logs_bloom=header.bloom,
        prev_randao=header.prev_randao,
        block_number=header.number,
        gas_limit=header.gas_limit,
        gas_used=header.gas_used,
        timestamp=header.timestamp,
        extra_data=header.extra_data,
        base_fee_per_gas=header.base_fee_per_gas,
        block_hash=block_hash,
        transactions=tuple(tx_bytes_list),
        withdrawals=block.withdrawals,
        blob_gas_used=header.blob_gas_used,
        excess_blob_gas=header.excess_blob_gas,
        block_access_list=bal_bytes,
    )

    new_payload = NewPayloadRequest(
        execution_payload=payload,
        versioned_hashes=tuple(versioned_hashes),
        parent_beacon_block_root=header.parent_beacon_block_root,
        execution_requests=execution_requests,
    )

    return StatelessInput(
        new_payload_request=new_payload,
        witness=execution_witness,
        chain_config=build_chain_config(chain_id),
        public_keys=tuple(public_keys),
    )
