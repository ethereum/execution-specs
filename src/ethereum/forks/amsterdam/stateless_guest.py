"""
Stateless guest interfaces.
"""

# ------- IO ---------

import io
import threading

from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes

from .stateless import (
    StatelessInput,
    StatelessValidationResult,
    verify_stateless_new_payload,
)

_local: threading.local = threading.local()


def _get_buffer() -> io.BytesIO:
    if not hasattr(_local, "buffer"):
        _local.buffer = io.BytesIO()
    return _local.buffer


# TODO: This method is for the host
def write_input(data: Bytes) -> None:
    """
    Write bytes as input for the guest to read.
    """
    _get_buffer().write(data)


# This is a method for the guest
def read_input(n: int) -> Bytes:
    """
    Read ``n`` bytes written by ``write_input``.
    """
    return Bytes(_get_buffer().read(n))


def serialize_stateless_output(output: StatelessValidationResult) -> Bytes:
    """
    Serialize a ``StatelessValidationResult`` to RLP-encoded bytes.
    TODO: change to ssz, rlp was easier to get working with codebase.
    """
    return Bytes(rlp.encode(output))


# TODO: This method is for the host
def serialize_stateless_input(stateless_input: StatelessInput) -> Bytes:
    """
    Serialize a ``StatelessInput`` to RLP-encoded bytes.
    TODO: change to ssz, rlp was easier to get working with codebase.
    """
    return Bytes(rlp.encode(stateless_input))


def deserialize_stateless_input(data: Bytes) -> StatelessInput:
    """
    Deserialize a ``StatelessInput`` from RLP-encoded bytes.
    TODO: change to ssz, rlp was easier to get working with codebase.
    """
    return rlp.decode_to(StatelessInput, data)


def entrypoint() -> Bytes:
    """
    Guest program entry point.
    """
    length = int.from_bytes(read_input(4), "big")
    input_data = read_input(length)
    stateless_input = deserialize_stateless_input(input_data)

    stateless_output = verify_stateless_new_payload(stateless_input)

    output_data = serialize_stateless_output(stateless_output)
    return output_data
