"""
Stateless validation interfaces.
"""

from dataclasses import dataclass
from typing import List, Tuple, final

from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes
from ethereum_types.frozen import slotted_freezable
from ethereum_types.numeric import U16, U64

from ethereum.crypto.hash import Hash32, keccak256
from ethereum.forks.bpo5.blocks import Header as PreviousHeader
from ethereum.state_witness import WitnessState, build_code_db, build_node_db
from ethereum.stateless.types import (
    MAX_WITNESS_HEADERS,
    STATELESS_INPUT_SCHEMA_ID_SIZE,
    ExecutionWitness,
    ProtocolFork,
    StatelessValidationResult,
    stateless_input_schema_id,
)
from ethereum.utils.ssz import SszContainer

from .blocks import Header
from .execution_engine.new_payload import execute_new_payload_request
from .execution_engine.types import NewPayloadRequest
from .fork import ChainContext

STATELESS_INPUT_SCHEMA_FORK_INDEX = ProtocolFork.Amsterdam
STATELESS_INPUT_SCHEMA_REVISION = 0x01
STATELESS_INPUT_SCHEMA_ID = stateless_input_schema_id(
    STATELESS_INPUT_SCHEMA_FORK_INDEX, STATELESS_INPUT_SCHEMA_REVISION
)
STATELESS_INPUT_SCHEMA_ID_BYTES = STATELESS_INPUT_SCHEMA_ID.to_bytes(
    STATELESS_INPUT_SCHEMA_ID_SIZE,
    "big",
)


@final
@slotted_freezable
@dataclass
class StatelessInput(SszContainer):
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


def compute_new_payload_request_root(
    stateless_input: StatelessInput,
) -> Hash32:
    """
    Compute the request root for a stateless input via SSZ hash tree root.
    """
    return Hash32(stateless_input.new_payload_request.hash_tree_root())


def _decode_header(header_bytes: Bytes) -> Header | PreviousHeader:
    """
    Decode an RLP-encoded header, trying the current fork first and
    falling back to the previous fork for transition-period headers.
    """
    try:
        return rlp.decode_to(Header, header_bytes)
    except rlp.DecodingError:
        return rlp.decode_to(PreviousHeader, header_bytes)


def validate_headers(
    encoded_headers: Tuple[Bytes, ...],
) -> Tuple[List[Header | PreviousHeader], List[Hash32]]:
    """
    Validate that a sequence of encoded headers forms a contiguous chain.

    Each header's ``parent_hash`` must match the hash of the preceding
    header. Return the decoded headers and block hashes. Headers may
    come from different forks during fork transitions.
    """
    assert len(encoded_headers) <= MAX_WITNESS_HEADERS, (
        "Too many headers in witness"
    )
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
