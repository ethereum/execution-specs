"""
Stateless guest interfaces.
"""

from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes

from .stateless import (
    StatelessInput,
    StatelessValidationResult,
    verify_stateless_new_payload,
)


def serialize_stateless_output(output: StatelessValidationResult) -> Bytes:
    """
    Serialize a ``StatelessValidationResult`` to RLP-encoded bytes.

    TODO: change to ssz, rlp was easier to get working with codebase.
    """
    return Bytes(rlp.encode(output))


def deserialize_stateless_input(data: Bytes) -> StatelessInput:
    """
    Deserialize a ``StatelessInput`` from RLP-encoded bytes.

    TODO: change to ssz, rlp was easier to get working with codebase.
    """
    return rlp.decode_to(StatelessInput, data)


def run_stateless_guest(input_bytes: Bytes) -> Bytes:
    """
    Run the stateless guest with serialized input, return serialized output.
    """
    stateless_input = deserialize_stateless_input(input_bytes)
    stateless_output = verify_stateless_new_payload(stateless_input)

    output_bytes = serialize_stateless_output(stateless_output)
    return output_bytes
