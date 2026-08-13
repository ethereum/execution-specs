"""
Execution engine data structures and aliases.
"""

from dataclasses import dataclass
from typing import Tuple, final

from ethereum_types.bytes import Bytes, Bytes8, Bytes32
from ethereum_types.frozen import slotted_freezable
from ethereum_types.numeric import U64, U256, Uint

from ethereum.crypto.hash import Hash32
from ethereum.state import Address, Root

from ..blocks import Withdrawal
from ..fork import BlockChain
from ..fork_types import Bloom, VersionedHash

ExecutionEngine = BlockChain
"""
Chain and state container that the execution engine methods operate on.
"""

PayloadId = Bytes8
"""
Identifier of a payload build process, returned by
[`notify_forkchoice_updated`] and consumed by [`get_payload`].

[`notify_forkchoice_updated`]:
    ref:ethereum.forks.osaka.execution_engine.forkchoice_update.notify_forkchoice_updated
[`get_payload`]:
    ref:ethereum.forks.osaka.execution_engine.get_payload.get_payload
"""  # noqa: E501


@final
@slotted_freezable
@dataclass
class ExecutionPayload:
    """
    Represent a new block to be processed by the execution layer.

    The consensus layer constructs this from a beacon block body and
    passes it to the execution engine for validation. Mirrors the
    [`ExecutionPayloadV3`] structure of the Engine API.

    [`ExecutionPayloadV3`]: https://github.com/ethereum/execution-apis/blob/main/src/engine/osaka.md
    """  # noqa: E501

    parent_hash: Hash32
    fee_recipient: Address
    state_root: Root
    receipts_root: Root
    logs_bloom: Bloom
    prev_randao: Bytes32
    block_number: Uint
    gas_limit: Uint
    gas_used: Uint
    timestamp: U256
    extra_data: Bytes
    base_fee_per_gas: Uint
    block_hash: Hash32
    transactions: Tuple[Bytes, ...]
    withdrawals: Tuple[Withdrawal, ...]
    blob_gas_used: U64
    excess_blob_gas: U64


@final
@slotted_freezable
@dataclass
class NewPayloadRequest:
    """
    Contain the parameters of the Engine API `engine_newPayloadV4`
    method for the [`verify_and_notify_new_payload`] entry point. The
    execution requests are carried in their opaque wire form and
    committed to via the header's requests hash.

    [`verify_and_notify_new_payload`]:
        ref:ethereum.forks.osaka.execution_engine.new_payload.verify_and_notify_new_payload
    """  # noqa: E501

    execution_payload: ExecutionPayload
    versioned_hashes: Tuple[VersionedHash, ...]
    parent_beacon_block_root: Root
    execution_requests: Tuple[Bytes, ...]


@final
@slotted_freezable
@dataclass
class PayloadAttributes:
    """
    Carry the parameters that the consensus layer supplies when it
    requests the execution layer to build a new block.
    """

    timestamp: U256
    prev_randao: Bytes32
    suggested_fee_recipient: Address
    withdrawals: Tuple[Withdrawal, ...]
    parent_beacon_block_root: Root


@final
@slotted_freezable
@dataclass
class BlobsBundle:
    """
    Bundle of blobs data associated with a built payload.
    """

    commitments: Tuple[Bytes, ...]
    proofs: Tuple[Bytes, ...]
    blobs: Tuple[Bytes, ...]


@final
@slotted_freezable
@dataclass
class GetPayloadResponse:
    """
    Response returned by [`get_payload`] for a prepared payload build.

    [`get_payload`]:
        ref:ethereum.forks.osaka.execution_engine.get_payload.get_payload
    """

    execution_payload: ExecutionPayload
    block_value: U256
    blobs_bundle: BlobsBundle
    execution_requests: Tuple[Bytes, ...]
