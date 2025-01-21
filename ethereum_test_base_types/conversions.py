"""Common conversion methods."""

from re import sub
from typing import Any, List, Optional, SupportsBytes, TypeAlias

BytesConvertible: TypeAlias = str | bytes | SupportsBytes | List[int]
FixedSizeBytesConvertible: TypeAlias = str | bytes | SupportsBytes | List[int] | int
NumberConvertible: TypeAlias = str | bytes | SupportsBytes | int


def int_or_none(input_value: Any, default: Optional[int] = None) -> int | None:
    """Convert a value to int or returns a default (None)."""
    if input_value is None:
        return default
    if isinstance(input_value, int):
        return input_value
    return int(input_value, 0)


def str_or_none(input_value: Any, default: Optional[str] = None) -> str | None:
    """Convert a value to string or returns a default (None)."""
    if input_value is None:
        return default
    if isinstance(input_value, str):
        return input_value
    return str(input_value)


def to_bytes(input_bytes: BytesConvertible) -> bytes:
    """Convert multiple types into bytes."""
    if input_bytes is None:
        raise Exception("Cannot convert `None` input to bytes")

    if (
        isinstance(input_bytes, SupportsBytes)
        or isinstance(input_bytes, bytes)
        or isinstance(input_bytes, list)
    ):
        return bytes(input_bytes)

    if isinstance(input_bytes, str):
        # We can have a hex representation of bytes with spaces for readability
        input_bytes = sub(r"\s+", "", input_bytes)
        if input_bytes.startswith("0x"):
            input_bytes = input_bytes[2:]
        if len(input_bytes) % 2 == 1:
            input_bytes = "0" + input_bytes
        return bytes.fromhex(input_bytes)

    raise Exception("invalid type for `bytes`")


def to_fixed_size_bytes(
    input_bytes: FixedSizeBytesConvertible,
    size: int,
    *,
    left_padding: bool = False,
    right_padding: bool = False,
) -> bytes:
    """
    Convert multiple types into fixed-size bytes.

    :param input_bytes: The input data to convert.
    :param size: The size of the output bytes.
    :param left_padding: Whether to allow left-padding of the input data bytes using zeros. If the
        input data is an integer, padding is always performed.
    :param right_padding: Whether to allow right-padding of the input data bytes using zeros. If
        the input data is an integer, padding is always performed.
    """
    if isinstance(input_bytes, int):
        return int.to_bytes(input_bytes, length=size, byteorder="big", signed=input_bytes < 0)
    input_bytes = to_bytes(input_bytes)
    if len(input_bytes) > size:
        raise Exception(f"input is too large for fixed size bytes: {len(input_bytes)} > {size}")
    if len(input_bytes) < size:
        if left_padding:
            return bytes(input_bytes).rjust(size, b"\x00")
        if right_padding:
            return bytes(input_bytes).ljust(size, b"\x00")
        raise Exception(
            f"input is too small for fixed size bytes: {len(input_bytes)} < {size}\n"
            "Use `left_padding=True` or `right_padding=True` to allow padding."
        )
    return input_bytes


def to_hex(input_bytes: BytesConvertible) -> str:
    """Convert multiple types into a bytes hex string."""
    return "0x" + to_bytes(input_bytes).hex()


def to_number(input_number: NumberConvertible) -> int:
    """Convert multiple types into a number."""
    if isinstance(input_number, int):
        return input_number
    if isinstance(input_number, str):
        return int(input_number, 0)
    if isinstance(input_number, bytes) or isinstance(input_number, SupportsBytes):
        return int.from_bytes(input_number, byteorder="big")
    raise Exception("invalid type for `number`")
