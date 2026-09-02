"""
Stateless guest interfaces.
"""

from ethereum_types.bytes import Bytes
from ethereum_types.numeric import U16, U64

from ethereum.crypto.hash import Hash32

from .stateless import (
    STATELESS_INPUT_SCHEMA_ID,
    STATELESS_INPUT_SCHEMA_ID_SIZE,
    StatelessInput,
    StatelessValidationResult,
    verify_stateless_new_payload,
)


def serialize_stateless_output(
    output: StatelessValidationResult,
) -> Bytes:
    """Serialize a StatelessValidationResult to SSZ bytes."""
    return Bytes(output.encode_bytes())


def deserialize_stateless_input(data: Bytes) -> StatelessInput:
    """Deserialize a StatelessInput from schema-prefixed SSZ bytes."""
    if len(data) < STATELESS_INPUT_SCHEMA_ID_SIZE:
        raise ValueError("Stateless input is missing schema id")
    schema_id = int.from_bytes(
        data[:STATELESS_INPUT_SCHEMA_ID_SIZE],
        "big",
    )
    if schema_id != STATELESS_INPUT_SCHEMA_ID:
        raise ValueError(
            f"Unsupported stateless input schema id: 0x{schema_id:04x}"
        )
    return StatelessInput.decode_bytes(data[STATELESS_INPUT_SCHEMA_ID_SIZE:])


def _default_failed_stateless_output() -> StatelessValidationResult:
    """
    Return the sentinel result used when stateless input cannot be decoded.
    """
    return StatelessValidationResult(
        new_payload_request_root=Hash32(b"\0" * 32),
        successful_validation=False,
        chain_id=U64(0),
        schema_id=U16(0),
    )


def run_stateless_guest(input_bytes: Bytes) -> Bytes:
    """
    Run the stateless guest with serialized input, return serialized output.
    """
    try:
        stateless_input = deserialize_stateless_input(input_bytes)
    except Exception:
        stateless_output = _default_failed_stateless_output()
    else:
        stateless_output = verify_stateless_new_payload(stateless_input)

    output_bytes = serialize_stateless_output(stateless_output)
    return output_bytes
