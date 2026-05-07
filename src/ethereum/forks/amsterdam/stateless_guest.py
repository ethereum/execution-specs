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
    STATELESS_INPUT_SCHEMA_ID,
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
    """Deserialize a StatelessInput from schema-prefixed SSZ bytes."""
    if len(data) == 0:
        raise ValueError("Stateless input is missing schema id")
    schema_id = data[0]
    if schema_id != STATELESS_INPUT_SCHEMA_ID:
        raise ValueError(
            f"Unsupported stateless input schema id: 0x{schema_id:02x}"
        )
    ssz_obj = SszStatelessInput.decode_bytes(data[1:])
    return ssz_to_stateless_input(ssz_obj)


def run_stateless_guest(input_bytes: Bytes) -> Bytes:
    """
    Run the stateless guest with serialized input, return serialized output.
    """
    stateless_input = deserialize_stateless_input(input_bytes)
    stateless_output = verify_stateless_new_payload(stateless_input)

    output_bytes = serialize_stateless_output(stateless_output)
    return output_bytes
