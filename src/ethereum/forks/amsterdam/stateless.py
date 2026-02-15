"""
Stateless validation interfaces.
"""

from dataclasses import dataclass
from typing import Sequence, Tuple

from ethereum_types.bytes import Bytes
from ethereum_types.frozen import slotted_freezable
from ethereum_types.numeric import U64

from ethereum.crypto.hash import Hash32

from .blocks import Block
from .execution_engine import NewPayloadRequest
from .fork_types import Root, VersionedHash

# Amsterdam currently carries execution requests as raw bytes in order.
ExecutionRequests = Tuple[Bytes, ...]


@slotted_freezable
@dataclass
class ExecutionPayloadHeader:
    """
    Execution payload header for stateless input scaffolding.

    TODO: Replace with the fork-specific execution payload header container.
    """


@slotted_freezable
@dataclass
class NewPayloadRequestHeader:
    """
    Header-only form of ``NewPayloadRequest`` for stateless flows.

    We expect ``hash_tree_root(execution_payload_header)`` equals
    ``hash_tree_root(execution_payload)``.
    """

    execution_payload_header: ExecutionPayloadHeader
    versioned_hashes: Sequence[VersionedHash]
    parent_beacon_block_root: Root
    execution_requests: ExecutionRequests


@slotted_freezable
@dataclass
class ExecutionWitness:
    """
    Execution witness data for stateless validation.
    """

    state: Tuple[Bytes, ...]
    """
    Hashed trie-node preimages needed during execution and state-root
    recomputation.
    """

    codes: Tuple[Bytes, ...]
    """
    Contract-code preimages (created or accessed) needed during execution.
    """

    keys: Tuple[Bytes, ...]
    """
    Hashed account/storage-key preimages (unhashed addresses and storage
    slots) needed during execution.
    """

    headers: Tuple[Bytes, ...]
    """
    RLP-encoded block headers used for pre-state and ``BLOCKHASH`` correctness
    proofs. This may trend toward empty with EIP-2935 and EIP-7709.
    """


@slotted_freezable
@dataclass
class ChainConfig:
    """
    Chain configuration needed for stateless validation.

    TODO: Since we do not want the client to hold all possible chains,
    we may want to add more to the chain config, like a genesis file.
    """

    chain_id: U64


@slotted_freezable
@dataclass
class StatelessInput:
    """
    Input to stateless validation.
    """

    new_payload_request: NewPayloadRequest
    """
    Consensus-layer payload request to validate statelessly. See
    ``execution_engine.NewPayloadRequest`` for structure and links to
    consensus-specs.
    """

    witness: ExecutionWitness
    """
    Execution witness material required to re-execute the core
    state transition function statelessly.
    """

    chain_config: ChainConfig
    """
    Chain configuration values needed during stateless validation.
    """

    public_keys: Tuple[Bytes, ...]
    """
    Recovered transaction public keys, in transaction order.
    """


@slotted_freezable
@dataclass
class StatelessValidationResult:
    """
    Result returned by stateless validation.
    """

    new_payload_request_root: Hash32
    successful_validation: bool


def compute_new_payload_request_root(
    stateless_input: StatelessInput,
) -> Hash32:
    """
    Compute the request root for a stateless input.

    TODO: Replace this with ``new_payload_request.tree_hash_root``.

    # For readability, we can convert to NewPayloadRequestHeader and
    # then the payload request root.
    """
    raise NotImplementedError


def new_payload_request_to_block(
    new_payload_request: NewPayloadRequest,
) -> Block:
    """
    Convert a NewPayloadRequest into a block.
    """
    raise NotImplementedError


def verify_stateless_new_payload(
    stateless_input: StatelessInput,
) -> StatelessValidationResult:
    """
    Statelessly validate the execution payload.
    """
    # TODO: We can fill this in properly once the pre-state PR
    # TODO: and state change PRs are completed.
    # TODO: We would effectively call `verify_and_notify_new_payload`

    return StatelessValidationResult(
        new_payload_request_root=compute_new_payload_request_root(
            stateless_input
        ),
        successful_validation=True,
    )
