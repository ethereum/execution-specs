"""
Helper functions/classes used to generate Ethereum tests.
"""

from dataclasses import dataclass

from ..code import Code, code_to_bytes


def to_address(input: int | str) -> str:
    """
    Converts an int or str into proper address 20-byte hex string.
    """
    if type(input) is str:
        # Convert to int
        input = int(input, 0)
    if type(input) is int:
        return "0x" + input.to_bytes(20, "big").hex()
    raise Exception("invalid type to convert to account address")


def to_hash(input: int | str) -> str:
    """
    Converts an int or str into proper address 20-byte hex string.
    """
    if type(input) is str:
        # Convert to int
        input = int(input, 0)
    if type(input) is int:
        return "0x" + input.to_bytes(32, "big").hex()
    raise Exception("invalid type to convert to hash")
