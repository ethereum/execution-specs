"""
Stateless validation interfaces.
"""

from dataclasses import dataclass
from enum import IntEnum
from typing import List, Sequence, Tuple, final

from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes
from ethereum_types.frozen import slotted_freezable
from ethereum_types.numeric import U16, U64

from ethereum.crypto.hash import Hash32, keccak256
from ethereum.forks.bpo5.blocks import Header as PreviousForkHeader
from ethereum.state import Root

from .blocks import Header
from .execution_engine.new_payload import execute_new_payload_request
from .execution_engine.requests import ExecutionRequests
from .execution_engine.types import NewPayloadRequest
from .fork import ChainContext
from .fork_types import VersionedHash
from .witness_state import WitnessState, build_code_db, build_node_db


@final
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

    headers: Tuple[Bytes, ...]
    """
    RLP-encoded block headers used for pre-state and ``BLOCKHASH`` correctness
    proofs. This may trend toward empty EIP-7709.
    """


@final
@slotted_freezable
@dataclass
class ExecutionPayloadHeader:
    """
    Execution payload header for stateless input scaffolding.

    TODO: Replace with the fork-specific execution payload header container.
    """


@final
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


class ProtocolFork(IntEnum):
    """
    Stable execution-layer fork identifiers used by stateless schemas.
    """

    Frontier = 0x01
    Homestead = 0x02
    DAOFork = 0x03
    TangerineWhistle = 0x04
    SpuriousDragon = 0x05
    Byzantium = 0x06
    StPetersburg = 0x07
    Istanbul = 0x08
    MuirGlacier = 0x09
    Berlin = 0x0A
    London = 0x0B
    ArrowGlacier = 0x0C
    GrayGlacier = 0x0D
    Paris = 0x0E
    Shanghai = 0x0F
    Cancun = 0x10
    Prague = 0x11
    Osaka = 0x12
    BPO1 = 0x13
    BPO2 = 0x14
    Amsterdam = 0x15


@final
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

    chain_id: U64
    """
    Chain identifier used during payload validation and execution.
    """

    public_keys: Tuple[Bytes, ...]
    """
    65-byte uncompressed transaction public keys, in payload order.
    """


@final
@slotted_freezable
@dataclass
class StatelessValidationResult:
    """
    Result returned by stateless validation.

    Note: We use return values to denote "public inputs".

    If ``successful_validation`` is ``False``, the remaining fields are
    only meaningful when the input bytes were decoded successfully. If
    decoding failed before a ``StatelessInput`` existed,
    ``run_stateless_guest`` returns a failed result with sentinel defaults.

    """

    new_payload_request_root: Hash32
    """
    SSZ root of the decoded ``NewPayloadRequest``. This is zero when
    ``run_stateless_guest`` cannot decode the input bytes.
    """

    successful_validation: bool
    """
    Whether the decoded stateless input validated successfully. ``False``
    means validation failed or the guest input bytes could not be decoded.
    """

    chain_id: U64
    """
    Chain identifier decoded from the input. This is zero when
    ``run_stateless_guest`` cannot decode the input bytes.
    """

    schema_id: U16
    """
    Exact input schema decoded and executed by the guest. This uses the
    invalid-input sentinel when ``run_stateless_guest`` cannot decode the
    input bytes.
    """


def compute_new_payload_request_root(
    stateless_input: StatelessInput,
) -> Hash32:
    """
    Compute the request root for a stateless input via SSZ hash tree root.
    """
    from .stateless_ssz import _new_payload_request_to_ssz

    ssz_npr = _new_payload_request_to_ssz(stateless_input.new_payload_request)
    return Hash32(ssz_npr.hash_tree_root())


def _decode_header(header_bytes: Bytes) -> Header | PreviousForkHeader:
    """
    Decode an RLP-encoded header, trying the current fork first and
    falling back to the previous fork for transition-period headers.
    """
    try:
        return rlp.decode_to(Header, header_bytes)
    except rlp.DecodingError:
        return rlp.decode_to(PreviousForkHeader, header_bytes)


def validate_headers(
    encoded_headers: Tuple[Bytes, ...],
) -> Tuple[List[Header | PreviousForkHeader], List[Hash32]]:
    """
    Validate that a sequence of encoded headers forms a contiguous chain.

    Each header's ``parent_hash`` must match the hash of the preceding
    header. Return the decoded headers and block hashes. Headers may
    come from different forks during fork transitions.
    """
    assert len(encoded_headers) <= 256, "Too many headers in witness"
    headers = [
        _decode_header(header_bytes) for header_bytes in encoded_headers
    ]
    block_hashes: List[Hash32] = [
        keccak256(header_bytes) for header_bytes in encoded_headers
    ]
    for i in range(1, len(headers)):
        if headers[i].parent_hash != block_hashes[i - 1]:
            raise Exception("Witness headers are not contiguous")
    return headers, block_hashes


def verify_stateless_new_payload(
    stateless_input: StatelessInput,
) -> StatelessValidationResult:
    """
    Statelessly validate the execution payload.
    """
    from .stateless_ssz import STATELESS_INPUT_SCHEMA_ID

    new_payload_request_root = compute_new_payload_request_root(
        stateless_input
    )
    witness = stateless_input.witness

    try:
        # EEST has one implementation per fork, so it does not need to check
        # the execution payload timestamp against the current fork activation
        # information. A real implementation MUST do these checks!

        # Validate the headers are contiguous and compute their
        # blockhashes.
        decoded_headers, block_hashes = validate_headers(witness.headers)
        parent_header = decoded_headers[-1]

        chain_context = ChainContext(
            chain_id=stateless_input.chain_id,
            block_hashes=block_hashes,
            parent_header=parent_header,
        )

        pre_state = WitnessState(
            _node_db=build_node_db(witness.state),
            _state_root=parent_header.state_root,
            _code_db=build_code_db(witness.codes),
        )

        execute_new_payload_request(
            stateless_input.new_payload_request,
            pre_state,
            chain_context,
            transaction_public_keys=stateless_input.public_keys,
        )
        successful_validation = True
    except Exception:
        successful_validation = False

    return StatelessValidationResult(
        new_payload_request_root=new_payload_request_root,
        successful_validation=successful_validation,
        chain_id=stateless_input.chain_id,
        schema_id=U16(STATELESS_INPUT_SCHEMA_ID),
    )
