"""
Execution engine data structures and aliases.
"""

from dataclasses import dataclass
from typing import Annotated, Tuple, final

from ethereum_types.bytes import Bytes, Bytes8, Bytes32
from ethereum_types.frozen import slotted_freezable
from ethereum_types.numeric import U64, U256, Uint

from ethereum.crypto.hash import Hash32
from ethereum.state import Address, Root
from ethereum.utils.ssz import (
    ProgressiveSszContainer,
    SszContainer,
    byte_list,
    progressive_byte_list,
    progressive_list,
    uint,
)

from ..blocks import Withdrawal
from ..fork import BlockChain
from ..fork_types import Bloom, VersionedHash
from .requests import ExecutionRequests

# In this module, the execution engine is the chain/state container used by
# the fork's transition functions.
ExecutionEngine = BlockChain
PayloadId = Bytes8
_ZERO_HASH32 = Hash32(b"\x00" * 32)
MAX_EXTRA_DATA_BYTES = 32


@final
@slotted_freezable
@dataclass
class ExecutionPayload(ProgressiveSszContainer):
    """
    Represent a new block to be processed by the execution layer.

    The consensus layer constructs this from a beacon block body and
    passes it to the execution engine for validation.

    Note: execution_request_hash is not a direct field in ExecutionPayload
    but it is indirectly committed to via `block_hash` since `request_hash`
    is in the EL-block header.
    """

    parent_hash: Hash32
    fee_recipient: Address
    state_root: Root
    receipts_root: Root
    logs_bloom: Bloom
    prev_randao: Bytes32
    block_number: Annotated[Uint, uint(64)]
    gas_limit: Annotated[Uint, uint(64)]
    gas_used: Annotated[Uint, uint(64)]
    timestamp: Annotated[U256, uint(64)]
    extra_data: Annotated[Bytes, byte_list(MAX_EXTRA_DATA_BYTES)]
    base_fee_per_gas: Annotated[Uint, uint(256)]
    block_hash: Hash32
    transactions: Annotated[
        Tuple[Annotated[Bytes, progressive_byte_list()], ...],
        progressive_list(),
    ]
    withdrawals: Annotated[Tuple[Withdrawal, ...], progressive_list()]
    blob_gas_used: U64
    excess_blob_gas: U64
    block_access_list: Annotated[Bytes, progressive_byte_list()]
    slot_number: U64


@final
@slotted_freezable
@dataclass
class NewPayloadRequest(SszContainer):
    """
    Contains an execution payload along with versioned hashes, the
    parent beacon block root, and execution requests for the
    ``verify_and_notify_new_payload`` entry point.

    This corresponds to the consensus-layer `NewPayloadRequest`
    container used for Engine API calls.

    [Bellatrix `NewPayloadRequest`]:
    https://ethereum.github.io/consensus-specs/specs/bellatrix/beacon-chain/#newpayloadrequest
    [Electra modified `NewPayloadRequest`]:
    https://ethereum.github.io/consensus-specs/specs/electra/beacon-chain/#modified-newpayloadrequest
    """

    execution_payload: ExecutionPayload
    versioned_hashes: Annotated[Tuple[VersionedHash, ...], progressive_list()]
    parent_beacon_block_root: Root
    execution_requests: ExecutionRequests


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
    Response returned by ``get_payload`` for a prepared payload build.
    """

    execution_payload: ExecutionPayload
    block_value: U256
    blobs_bundle: BlobsBundle
    execution_requests: ExecutionRequests
