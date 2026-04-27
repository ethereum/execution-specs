"""
Execution engine data structures and aliases.
"""

from dataclasses import dataclass
from typing import Tuple

from ethereum_types.bytes import Bytes, Bytes8, Bytes32
from ethereum_types.frozen import slotted_freezable
from ethereum_types.numeric import U64, U256, Uint

from ethereum.crypto.hash import Hash32
from ethereum.state import Address, Root

from ..blocks import Withdrawal
from ..fork import BlockChain
from ..fork_types import Bloom, VersionedHash
from .requests import ExecutionRequests

# In this module, the execution engine is the chain/state container used by
# the fork's transition functions.
ExecutionEngine = BlockChain
PayloadId = Bytes8
_ZERO_HASH32 = Hash32(b"\x00" * 32)


@slotted_freezable
@dataclass
class ExecutionPayload:
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
    block_access_list: Bytes


@slotted_freezable
@dataclass
class NewPayloadRequest:
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
    versioned_hashes: Tuple[VersionedHash, ...]
    parent_beacon_block_root: Root
    execution_requests: ExecutionRequests


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


@slotted_freezable
@dataclass
class BlobsBundle:
    """
    Bundle of blobs data associated with a built payload.
    """

    commitments: Tuple[Bytes, ...]
    proofs: Tuple[Bytes, ...]
    blobs: Tuple[Bytes, ...]


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
