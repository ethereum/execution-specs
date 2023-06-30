"""
Common conversion methods.
"""
from typing import Any, Dict, List

from ..code import Code, code_to_hex


def address_to_bytes(input: str | bytes | int | None) -> bytes:
    """
    Converts an address string or int to bytes.
    """
    if input is None:
        return bytes()
    elif type(input) == int:
        return int.to_bytes(input, length=20, byteorder="big")
    elif type(input) == str:
        if input.startswith("0x"):
            input = input[2:]
        if len(input) % 2 != 0:
            input = "0" + input
        b = bytes.fromhex(input)
        if len(b) > 20:
            raise ValueError(f"Address is too long: {input}")
        return b.rjust(20, b"\x00")
    elif isinstance(input, bytes):
        if len(input) > 20:
            raise ValueError(f"Address is too long: {input.hex()}")
        return input.rjust(20, b"\x00")
    raise ValueError(f"Invalid address type: {type(input)}")


def address_or_none(input: str | bytes | int | None, default=None) -> str | None:
    """
    Converts the input into an address hex string.
    """
    if input is None:
        return default

    if type(input) == int:
        input = int.to_bytes(input, length=20, byteorder="big")

    if type(input) == str:
        if input.startswith("0x"):
            input = input[2:]
        if len(input) % 2 != 0:
            input = "0" + input
        input = bytes.fromhex(input)

    assert isinstance(input, bytes), f"Invalid address type: {type(input)}"

    return "0x" + input.rjust(20, b"\x00").hex()


def even_padding(input: Dict, excluded: List[Any | None]) -> Dict:
    """
    Adds even padding to each field in the input (nested) dictionary.
    """
    for key, value in input.items():
        if key not in excluded:
            if isinstance(value, dict):
                even_padding(value, excluded)
            elif isinstance(value, str | None):
                if value != "0x" and value is not None:
                    input[key] = key_value_padding(value)
                else:
                    input[key] = "0x"
    return input


def key_value_padding(value: str) -> str:
    """
    Adds even padding to a dictionary key or value string.
    """
    if value is None:
        return "0x"

    new_value = value.lstrip("0x").lstrip("0")
    new_value = "00" if new_value == "" else new_value
    if len(new_value) % 2 == 1:
        new_value = "0" + new_value
    return "0x" + new_value


def hash_string(input: str | bytes | int | None) -> str:
    """
    Converts the input into a hash string.
    """
    if input is None:
        return "0x" + "00" * 64

    if type(input) == int:
        input = int.to_bytes(input, length=32, byteorder="big")

    if type(input) == str:
        if input.startswith("0x"):
            input = input[2:]
        if len(input) % 2 != 0:
            input = "0" + input
        input = bytes.fromhex(input)

    assert isinstance(input, bytes), f"Invalid hash type: {type(input)}"

    return "0x" + input.rjust(32, b"\x00").hex()


def bytes_or_none(input: str | bytes | None, default=None) -> bytes | None:
    """
    Converts a bytes or string to bytes or returns a default (None).
    """
    if input is None:
        return default
    elif type(input) == str:
        if input.startswith("0x"):
            input = input[2:]
        if len(input) % 2 != 0:
            input = "0" + input
        return bytes.fromhex(input)
    elif isinstance(input, bytes):
        return input
    raise ValueError(f"Invalid bytes type: {type(input)}")


def hash_to_bytes(input: str | bytes | int | None) -> bytes:
    """
    Converts a hash string or int to bytes.
    """
    if input is None:
        return bytes(32)
    elif type(input) == int:
        return int.to_bytes(input, length=32, byteorder="big")
    elif type(input) == str:
        if input.startswith("0x"):
            input = input[2:]
        if len(input) % 2 != 0:
            input = "0" + input
        b = bytes.fromhex(input)
        if len(b) > 32:
            raise ValueError(f"Hash is too long: {input}")
        return b.rjust(32, b"\x00")
    elif isinstance(input, bytes):
        if len(input) > 32:
            raise ValueError(f"Hash is too long: {input.hex()}")
        return input.rjust(32, b"\x00")
    raise ValueError(f"Invalid hash type: {type(input)}")


def hash_to_int(input: str | bytes | int | None) -> int:
    """
    Converts a hash bytes, string or int to int.
    """
    if input is None:
        return 0
    elif type(input) == int:
        return input
    elif type(input) == str:
        return int(input, 0)
    elif isinstance(input, bytes):
        return int.from_bytes(input, byteorder="big")
    raise ValueError(f"Invalid hash type: {type(input)}")


def code_or_none(input: str | bytes | Code | None, default=None) -> str | None:
    """
    Converts an int to hex or returns a default (None).
    """
    if input is None:
        return default
    return code_to_hex(input)


def hex_or_none(input: int | bytes | None, default=None) -> str | None:
    """
    Converts an int or bytes to hex or returns a default (None).
    """
    if input is None:
        return default
    elif type(input) == int:
        return hex(input)
    elif isinstance(input, bytes):
        return "0x" + input.hex()
    raise ValueError(f"Invalid type to convert to hex: {type(input)}")


def int_or_none(input: Any, default=None) -> int | None:
    """
    Converts a value to int or returns a default (None).
    """
    if input is None:
        return default
    if type(input) == int:
        return input
    return int(input, 0)


def str_or_none(input: Any, default=None) -> str | None:
    """
    Converts a value to string or returns a default (None).
    """
    if input is None:
        return default
    if type(input) == str:
        return input
    return str(input)
