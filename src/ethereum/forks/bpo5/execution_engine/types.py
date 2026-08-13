"""
Structures of the [Engine API], as of the BPO5 fork.

Each structure version is additive over its predecessor, mirroring the
execution-apis documents: a client serving BPO5 understands every
structure listed here.

[Engine API]: https://github.com/ethereum/execution-apis/blob/main/src/engine/osaka.md
"""  # noqa: E501

import enum
from dataclasses import dataclass
from typing import Dict, Optional, Tuple, final

from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes, Bytes8, Bytes32
from ethereum_types.frozen import slotted_freezable
from ethereum_types.numeric import U64, U256, Uint

from ethereum.crypto.hash import Hash32, keccak256
from ethereum.state import Address, Root
from ethereum.state_mpt import State, copy_state

from ..blocks import Block, Withdrawal
from ..fork import BlockChain
from ..fork_types import Bloom

PayloadId = Bytes8
"""
Identifier of a payload build process; returned by the
`engine_forkchoiceUpdated` family when payload attributes are given.
"""


class PayloadStatus(enum.Enum):
    """
    Validation outcome of a payload, per the Engine API.

    `ACCEPTED` is reserved for payloads taken on side chains without
    validation; this specification validates every payload and never
    returns it.
    """

    VALID = "VALID"
    INVALID = "INVALID"
    SYNCING = "SYNCING"
    ACCEPTED = "ACCEPTED"


@final
@slotted_freezable
@dataclass
class PayloadStatusV1:
    """
    Status object returned by the `engine_newPayload` and
    `engine_forkchoiceUpdated` families.
    """

    status: PayloadStatus
    latest_valid_hash: Optional[Hash32]
    validation_error: Optional[str]


@final
@slotted_freezable
@dataclass
class ForkchoiceStateV1:
    """
    Fork-choice state communicated by the consensus layer: the head to
    adopt and the safe and finalized ancestors.
    """

    head_block_hash: Hash32
    safe_block_hash: Hash32
    finalized_block_hash: Hash32


@final
@slotted_freezable
@dataclass
class ForkchoiceUpdatedResponse:
    """
    Response of the `engine_forkchoiceUpdated` family: the status of
    the head selection and, when a build was started, its identifier.
    """

    payload_status: PayloadStatusV1
    payload_id: Optional[PayloadId]


@final
@dataclass
class ExecutionEngine:
    """
    Execution-layer state that the engine methods operate on.

    Beyond the canonical [`BlockChain`], the engine remembers every
    block that passed payload validation together with the state it
    produced, so payloads can extend any validated branch and a
    forkchoice update can adopt any validated block as head.

    [`BlockChain`]: ref:ethereum.forks.bpo5.fork.BlockChain
    """

    chain: BlockChain
    """Canonical chain: the ancestry of the current head."""

    validated_blocks: Dict[Hash32, Block]
    """Every block that passed payload validation, by block hash."""

    states: Dict[Hash32, State]
    """The state after each validated block, by block hash."""

    genesis_block: Block
    """Anchor block that every canonical chain starts from."""


def create_execution_engine(chain: BlockChain) -> ExecutionEngine:
    """
    Wrap a single-block genesis `chain` into an [`ExecutionEngine`].

    [`ExecutionEngine`]:
        ref:ethereum.forks.bpo5.execution_engine.types.ExecutionEngine
    """
    genesis_block = chain.blocks[0]
    genesis_hash = keccak256(rlp.encode(genesis_block.header))
    return ExecutionEngine(
        chain=chain,
        validated_blocks={genesis_hash: genesis_block},
        states={genesis_hash: copy_state(chain.state)},
        genesis_block=genesis_block,
    )


@final
@slotted_freezable
@dataclass
class ExecutionPayloadV1:
    """
    Payload of the `engine_newPayload` family of methods.
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


@final
@slotted_freezable
@dataclass
class ExecutionPayloadV2:
    """
    Payload of the `engine_newPayload` family of methods.

    Adds `withdrawals` to [`ExecutionPayloadV1`].

    [`ExecutionPayloadV1`]:
        ref:ethereum.forks.bpo5.execution_engine.types.ExecutionPayloadV1
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


@final
@slotted_freezable
@dataclass
class ExecutionPayloadV3:
    """
    Payload of the `engine_newPayload` family of methods.

    Adds `blob_gas_used` and `excess_blob_gas` to
    [`ExecutionPayloadV2`].

    [`ExecutionPayloadV2`]:
        ref:ethereum.forks.bpo5.execution_engine.types.ExecutionPayloadV2
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


@final
@slotted_freezable
@dataclass
class PayloadAttributesV1:
    """
    Build parameters carried by `engine_forkchoiceUpdatedV1`
    when the consensus layer requests a new block.
    """

    timestamp: U256
    prev_randao: Bytes32
    suggested_fee_recipient: Address


@final
@slotted_freezable
@dataclass
class PayloadAttributesV2:
    """
    Build parameters carried by `engine_forkchoiceUpdatedV2`
    when the consensus layer requests a new block.
    """

    timestamp: U256
    prev_randao: Bytes32
    suggested_fee_recipient: Address
    withdrawals: Tuple[Withdrawal, ...]


@final
@slotted_freezable
@dataclass
class PayloadAttributesV3:
    """
    Build parameters carried by `engine_forkchoiceUpdatedV3`
    when the consensus layer requests a new block.
    """

    timestamp: U256
    prev_randao: Bytes32
    suggested_fee_recipient: Address
    withdrawals: Tuple[Withdrawal, ...]
    parent_beacon_block_root: Root


@final
@slotted_freezable
@dataclass
class BlobsBundleV1:
    """
    Blob data of a built payload; `proofs` carries blob proofs.
    """

    commitments: Tuple[Bytes, ...]
    proofs: Tuple[Bytes, ...]
    blobs: Tuple[Bytes, ...]


@final
@slotted_freezable
@dataclass
class BlobsBundleV2:
    """
    Blob data of a built payload; `proofs` carries cell proofs for
    the extended blobs (EIP-7594).
    """

    commitments: Tuple[Bytes, ...]
    proofs: Tuple[Bytes, ...]
    blobs: Tuple[Bytes, ...]


@final
@slotted_freezable
@dataclass
class GetPayloadResponseV2:
    """
    Response of `engine_getPayloadV2`.
    """

    execution_payload: ExecutionPayloadV2
    block_value: U256


@final
@slotted_freezable
@dataclass
class GetPayloadResponseV3:
    """
    Response of `engine_getPayloadV3`.
    """

    execution_payload: ExecutionPayloadV3
    block_value: U256
    blobs_bundle: BlobsBundleV1
    should_override_builder: bool


@final
@slotted_freezable
@dataclass
class GetPayloadResponseV4:
    """
    Response of `engine_getPayloadV4`.
    """

    execution_payload: ExecutionPayloadV3
    block_value: U256
    blobs_bundle: BlobsBundleV1
    should_override_builder: bool
    execution_requests: Tuple[Bytes, ...]


@final
@slotted_freezable
@dataclass
class GetPayloadResponseV5:
    """
    Response of `engine_getPayloadV5`.
    """

    execution_payload: ExecutionPayloadV3
    block_value: U256
    blobs_bundle: BlobsBundleV2
    should_override_builder: bool
    execution_requests: Tuple[Bytes, ...]
