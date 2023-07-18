"""
Code object that is an interface to different
assembler/compiler backends.
"""
from typing import Optional, Sized, SupportsBytes

from ..common.conversions import to_bytes


class Code(SupportsBytes, Sized):
    """
    Generic code object.
    """

    bytecode: Optional[bytes] = None
    """
    bytes array that represents the bytecode of this object.
    """
    name: Optional[str] = None
    """
    Name used to describe this code.
    Usually used to add extra information to a test case.
    """

    def __init__(
        self,
        code: Optional[str | bytes | SupportsBytes] = None,
        *,
        name: Optional[str] = None,
    ):
        """
        Create a new Code object.
        """
        if code is not None:
            self.bytecode = to_bytes(code)
        self.name = name

    def __bytes__(self) -> bytes:
        """
        Transform the Code object into bytes.
        """
        if self.bytecode is None:
            return bytes()
        else:
            return self.bytecode

    def __len__(self) -> int:
        """
        Get the length of the Code object.
        """
        if self.bytecode is None:
            return 0
        else:
            return len(self.bytecode)

    def __add__(self, other: str | bytes | SupportsBytes) -> "Code":
        """
        Adds two code objects together, by converting both to bytes first.
        """
        return Code(to_bytes(self) + to_bytes(other))

    def __radd__(self, other: str | bytes | SupportsBytes) -> "Code":
        """
        Adds two code objects together, by converting both to bytes first.
        """
        return Code(to_bytes(other) + to_bytes(self))
