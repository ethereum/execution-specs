"""
Stateless guest interfaces.
"""

from ethereum_types.bytes import Bytes

from .stateless import (
    StatelessInput,
    StatelessValidationResult,
    verify_stateless_new_payload,
)
from .stateless_ssz import (
    SszStatelessInput,
    ssz_to_stateless_input,
    validation_result_to_ssz,
)


def serialize_stateless_output(
    output: StatelessValidationResult,
) -> Bytes:
    """Serialize a StatelessValidationResult to SSZ bytes."""
    ssz_obj = validation_result_to_ssz(output)
    return Bytes(ssz_obj.encode_bytes())


def deserialize_stateless_input(data: Bytes) -> StatelessInput:
    """Deserialize a StatelessInput from SSZ bytes."""
    ssz_obj = SszStatelessInput.decode_bytes(data)
    return ssz_to_stateless_input(ssz_obj)


def run_stateless_guest(input_bytes: Bytes) -> Bytes:
    """
    Run the stateless guest with serialized input, return serialized output.
    """
    stateless_input = deserialize_stateless_input(input_bytes)
    stateless_output = verify_stateless_new_payload(stateless_input)

    output_bytes = serialize_stateless_output(stateless_output)
    return output_bytes
