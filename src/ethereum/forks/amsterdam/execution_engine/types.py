"""
Execution engine data structures and aliases.
"""

from dataclasses import dataclass
from typing import Dict, Tuple, final

from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes, Bytes8, Bytes32
from ethereum_types.frozen import slotted_freezable
from ethereum_types.numeric import U64, U256, Uint

from ethereum.crypto.hash import Hash32, keccak256
from ethereum.state import Address, Root
from ethereum.state_mpt import State, copy_state

from ..blocks import Block, Withdrawal
from ..fork import BlockChain
from ..fork_types import Bloom, VersionedHash


@final
@dataclass
class ExecutionEngine:
    """
    Execution-layer state that the engine methods operate on.

    Beyond the canonical [`BlockChain`], the engine remembers every
    block that passed [`verify_and_notify_new_payload`] together with
    the genesis anchor, so that [`notify_forkchoice_updated`] can move
    the head to any validated block by re-executing its ancestry.

    [`BlockChain`]: ref:ethereum.forks.amsterdam.fork.BlockChain
    [`verify_and_notify_new_payload`]:
        ref:ethereum.forks.amsterdam.execution_engine.new_payload.verify_and_notify_new_payload
    [`notify_forkchoice_updated`]:
        ref:ethereum.forks.amsterdam.execution_engine.forkchoice_update.notify_forkchoice_updated
    """  # noqa: E501

    chain: BlockChain
    """Canonical chain: the ancestry of the current head."""

    validated_blocks: Dict[Hash32, Block]
    """Every block that passed payload validation, by block hash."""

    genesis_block: Block
    """Anchor block that every canonical chain starts from."""

    genesis_state: State
    """State at genesis, the starting point for head rebuilds."""


def create_execution_engine(chain: BlockChain) -> ExecutionEngine:
    """
    Wrap a single-block genesis `chain` into an [`ExecutionEngine`].

    [`ExecutionEngine`]:
        ref:ethereum.forks.amsterdam.execution_engine.types.ExecutionEngine
    """
    genesis_block = chain.blocks[0]
    return ExecutionEngine(
        chain=chain,
        validated_blocks={
            keccak256(rlp.encode(genesis_block.header)): genesis_block
        },
        genesis_block=genesis_block,
        genesis_state=copy_state(chain.state),
    )


PayloadId = Bytes8
"""
Identifier of a payload build process, returned by
[`notify_forkchoice_updated`] and consumed by [`get_payload`].

[`notify_forkchoice_updated`]:
    ref:ethereum.forks.amsterdam.execution_engine.forkchoice_update.notify_forkchoice_updated
[`get_payload`]:
    ref:ethereum.forks.amsterdam.execution_engine.get_payload.get_payload
"""  # noqa: E501


@final
@slotted_freezable
@dataclass
class ExecutionPayload:
    """
    Represent a new block to be processed by the execution layer.

    The consensus layer constructs this from a beacon block body and
    passes it to the execution engine for validation. Mirrors the
    [`ExecutionPayloadV4`] structure of the Engine API.

    The execution requests are not a direct field in the payload but are
    indirectly committed to via `block_hash`, since `requests_hash` is
    part of the execution-layer block header.

    [`ExecutionPayloadV4`]: https://github.com/ethereum/execution-apis/blob/main/src/engine/amsterdam.md
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
    block_access_list: Bytes
    slot_number: U64


@final
@slotted_freezable
@dataclass
class NewPayloadRequest:
    """
    Contain an execution payload along with versioned hashes, the parent
    beacon block root, and execution requests for the
    [`verify_and_notify_new_payload`] entry point.

    Corresponds to the consensus-layer [`NewPayloadRequest`] container
    and carries the parameters of the Engine API `engine_newPayloadV5`
    method. The execution requests are carried in their opaque wire
    form; [`decode_execution_requests`] parses them when typed access
    is needed.

    [`decode_execution_requests`]:
        ref:ethereum.forks.amsterdam.execution_engine.requests.decode_execution_requests

    [`verify_and_notify_new_payload`]:
        ref:ethereum.forks.amsterdam.execution_engine.new_payload.verify_and_notify_new_payload
    [`NewPayloadRequest`]: https://ethereum.github.io/consensus-specs/specs/electra/beacon-chain/#modified-newpayloadrequest
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
        ref:ethereum.forks.amsterdam.execution_engine.get_payload.get_payload
    """

    execution_payload: ExecutionPayload
    block_value: U256
    blobs_bundle: BlobsBundle
    execution_requests: Tuple[Bytes, ...]
    should_override_builder: bool
