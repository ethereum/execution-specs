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
def write_input_bytes(data: Bytes) -> None:
    """
    Write bytes as input for the guest to read, prefixed with a 4-byte
    big-endian length.
    """
    _get_buffer().write(len(data).to_bytes(4, "big"))
    _get_buffer().write(data)


# TODO: This method is for the host
def rewind_input() -> None:
    """
    Seek the input buffer back to the start so the guest can read it.

    Call this after all ``write_input_bytes`` calls and before ``entrypoint``.
    """
    _get_buffer().seek(0)


# This is a method for the guest
def read_input_bytes() -> Bytes:
    """
    Read the input written by ``write_input``.

    Reads the 4-byte big-endian length prefix, then returns that many bytes.
    """
    length = int.from_bytes(_get_buffer().read(4), "big")
    return Bytes(_get_buffer().read(length))


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


# TODO: We could just have this be a method that takes in bytes and
# returns bytes
def entrypoint() -> Bytes:
    """
    Guest program entry point.
    """
    input_data = read_input_bytes()
    stateless_input = deserialize_stateless_input(input_data)

    stateless_output = verify_stateless_new_payload(stateless_input)

    output_data = serialize_stateless_output(stateless_output)
    return output_data
