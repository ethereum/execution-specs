"""
Common conversion methods.
"""
from re import sub
from typing import Any, List, Optional, SupportsBytes, TypeAlias

BytesConvertible: TypeAlias = str | bytes | SupportsBytes | List[int]
FixedSizeBytesConvertible: TypeAlias = str | bytes | SupportsBytes | List[int] | int
NumberConvertible: TypeAlias = str | bytes | SupportsBytes | int


def int_or_none(input: Any, default: Optional[int] = None) -> int | None:
    """
    Converts a value to int or returns a default (None).
    """
    if input is None:
        return default
    if type(input) == int:
        return input
    return int(input, 0)


def str_or_none(input: Any, default: Optional[str] = None) -> str | None:
    """
    Converts a value to string or returns a default (None).
    """
    if input is None:
        return default
    if type(input) == str:
        return input
    return str(input)


def to_bytes(input: BytesConvertible) -> bytes:
    """
    Converts multiple types into bytes.
    """
    if input is None:
        raise Exception("Cannot convert `None` input to bytes")

    if isinstance(input, SupportsBytes) or isinstance(input, bytes) or isinstance(input, list):
        return bytes(input)

    if isinstance(input, str):
        # We can have a hex representation of bytes with spaces for
        # readability
        input = sub(r"\s+", "", input)
        if input.startswith("0x"):
            input = input[2:]
        if len(input) % 2 == 1:
            input = "0" + input
        return bytes.fromhex(input)

    raise Exception("invalid type for `bytes`")


def to_fixed_size_bytes(input: FixedSizeBytesConvertible, size: int) -> bytes:
    """
    Converts multiple types into fixed-size bytes.
    """
    if isinstance(input, int):
        return int.to_bytes(input, length=size, byteorder="big")
    input = to_bytes(input)
    if len(input) > size:
        raise Exception(f"input is too large for fixed size bytes: {len(input)} > {size}")
    return bytes(input).rjust(size, b"\x00")


def to_hex(input: BytesConvertible) -> str:
    """
    Converts multiple types into a bytes hex string.
    """
    return "0x" + to_bytes(input).hex()


def to_number(input: NumberConvertible) -> int:
    """
    Converts multiple types into a number.
    """
    if isinstance(input, int):
        return input
    if isinstance(input, str):
        return int(input, 0)
    if isinstance(input, bytes) or isinstance(input, SupportsBytes):
        return int.from_bytes(input, byteorder="big")
    raise Exception("invalid type for `number`")


def to_fixed_size_hex(input: FixedSizeBytesConvertible, size: int) -> str:
    """
    Converts multiple types into a bytes hex string.
    """
    return "0x" + to_fixed_size_bytes(input, size).hex()
