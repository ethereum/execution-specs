"""
Types shared by the stateless validation of every fork.
"""

from dataclasses import dataclass
from enum import IntEnum
from typing import Annotated, Tuple, final

from ethereum_types.bytes import Bytes
from ethereum_types.frozen import slotted_freezable
from ethereum_types.numeric import U16, U64

from ethereum.crypto.hash import Hash32
from ethereum.utils.ssz import (
    ProgressiveSszContainer,
    SszContainer,
    byte_list,
    progressive_list,
    ssz_list,
)

MAX_WITNESS_HEADERS = 256
MAX_BYTES_PER_CODE = 2**16
MAX_BYTES_PER_HEADER = 2**10
MAX_BYTES_PER_WITNESS_NODE = 2**10


@final
@slotted_freezable
@dataclass
class ExecutionWitness(SszContainer):
    """
    Execution witness data for stateless validation.
    """

    state: Annotated[
        Tuple[Annotated[Bytes, byte_list(MAX_BYTES_PER_WITNESS_NODE)], ...],
        progressive_list(),
    ]
    """
    Hashed trie-node preimages needed during execution and state-root
    recomputation.
    """

    codes: Annotated[
        Tuple[Annotated[Bytes, byte_list(MAX_BYTES_PER_CODE)], ...],
        progressive_list(),
    ]
    """
    Contract-code preimages (created or accessed) needed during execution.
    """

    headers: Annotated[
        Tuple[Annotated[Bytes, byte_list(MAX_BYTES_PER_HEADER)], ...],
        ssz_list(MAX_WITNESS_HEADERS),
    ]
    """
    RLP-encoded block headers used for pre-state and ``BLOCKHASH`` correctness
    proofs. This may trend toward empty EIP-7709.
    """


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


STATELESS_INPUT_SCHEMA_ID_SIZE = 2
"""
Size in bytes of the schema id that prefixes a serialized stateless input.
"""


def stateless_input_schema_id(fork: ProtocolFork, revision: int) -> int:
    """
    Build the schema id of a fork's stateless input.

    The high byte is the fork's [`ProtocolFork`] and the low byte is the
    revision of its input schema, so each fork can change its input without
    reusing an id.

    [`ProtocolFork`]: ref:ethereum.stateless.types.ProtocolFork
    """
    return (fork << 8) | revision


@final
@slotted_freezable
@dataclass
class StatelessValidationResult(ProgressiveSszContainer):
    """
    Result returned by stateless validation.

    Note: We use return values to denote "public inputs". This mirrors the
    consensus-layer `PublicInput` container.

    If ``schema_id`` is zero, the guest could not decode the input or
    produce a validation result, and the remaining fields have sentinel
    defaults. Otherwise, the fields identify the decoded input, including
    when execution validation fails.

    """

    new_payload_request_root: Hash32
    """
    SSZ root of the decoded ``NewPayloadRequest``. This is zero in the
    sentinel result.
    """

    successful_validation: bool
    """
    Whether the decoded stateless input validated successfully. ``False``
    means validation failed or the guest could not produce a result.
    """

    chain_id: U64
    """
    Chain identifier decoded from the input. This is zero in the sentinel
    result.
    """

    schema_id: U16
    """
    Exact input schema decoded and executed by the guest. This uses the
    zero sentinel when the guest cannot decode the input or produce a
    validation result.
    """


FAILED_STATELESS_OUTPUT = StatelessValidationResult(
    new_payload_request_root=Hash32(b"\0" * 32),
    successful_validation=False,
    chain_id=U64(0),
    schema_id=U16(0),
)
"""
Sentinel the guest returns when it cannot produce a validation result.
"""


def serialize_stateless_output(
    output: StatelessValidationResult,
) -> Bytes:
    """Serialize a StatelessValidationResult to SSZ bytes."""
    return Bytes(output.encode_bytes())


def deserialize_stateless_output(data: Bytes) -> StatelessValidationResult:
    """Deserialize a StatelessValidationResult from SSZ bytes."""
    return StatelessValidationResult.decode_bytes(data)
