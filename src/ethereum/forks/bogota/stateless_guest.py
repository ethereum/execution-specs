"""
Stateless guest interfaces.
"""

from ethereum_types.bytes import Bytes

from ethereum.stateless.types import (
    FAILED_STATELESS_OUTPUT,
    STATELESS_INPUT_SCHEMA_ID_SIZE,
    serialize_stateless_output,
)

from .stateless import (
    STATELESS_INPUT_SCHEMA_ID,
    StatelessInput,
    verify_stateless_new_payload,
)


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


def run_stateless_guest(input_bytes: Bytes) -> Bytes:
    """
    Run the stateless guest with serialized input, return serialized output.
    """
    try:
        stateless_input = deserialize_stateless_input(input_bytes)
        stateless_output = verify_stateless_new_payload(stateless_input)
    except Exception:
        stateless_output = FAILED_STATELESS_OUTPUT

    output_bytes = serialize_stateless_output(stateless_output)
    return output_bytes
