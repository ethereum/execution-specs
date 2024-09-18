"""
Ethereum Virtual Machine bytecode primitives and utilities.
"""
from typing import SupportsBytes

from ethereum.crypto.hash import keccak256


class Bytecode:
    """
    Base class to represent EVM bytecode.

    Stack calculations are automatically done after an addition operation between two bytecode
    objects. The stack height is not guaranteed to be correct, so the user must take this into
    consideration.

    Parameters
    ----------
    - popped_stack_items: number of items the bytecode pops from the stack
    - pushed_stack_items: number of items the bytecode pushes to the stack
    - min_stack_height: minimum stack height required by the bytecode
    - max_stack_height: maximum stack height reached by the bytecode
    """

    _name_: str = ""
    _bytes_: bytes

    popped_stack_items: int
    pushed_stack_items: int
    max_stack_height: int
    min_stack_height: int

    terminating: bool

    def __new__(
        cls,
        bytes_or_byte_code_base: "bytes | Bytecode | None" = None,
        *,
        popped_stack_items: int | None = None,
        pushed_stack_items: int | None = None,
        max_stack_height: int | None = None,
        min_stack_height: int | None = None,
        terminating: bool = False,
        name: str = "",
    ):
        """
        Creates a new opcode instance.
        """
        if bytes_or_byte_code_base is None:
            instance = super().__new__(cls)
            instance._bytes_ = b""
            instance.popped_stack_items = 0
            instance.pushed_stack_items = 0
            instance.min_stack_height = 0
            instance.max_stack_height = 0
            instance.terminating = False
            instance._name_ = name
            return instance

        if type(bytes_or_byte_code_base) is Bytecode:
            # Required because Enum class calls the base class with the instantiated object as
            # parameter.
            obj = super().__new__(cls)
            obj._bytes_ = bytes_or_byte_code_base._bytes_
            obj.popped_stack_items = bytes_or_byte_code_base.popped_stack_items
            obj.pushed_stack_items = bytes_or_byte_code_base.pushed_stack_items
            obj.min_stack_height = bytes_or_byte_code_base.min_stack_height
            obj.max_stack_height = bytes_or_byte_code_base.max_stack_height
            obj.terminating = bytes_or_byte_code_base.terminating
            obj._name_ = bytes_or_byte_code_base._name_
            return obj

        if isinstance(bytes_or_byte_code_base, bytes):
            obj = super().__new__(cls)
            obj._bytes_ = bytes_or_byte_code_base
            assert popped_stack_items is not None
            assert pushed_stack_items is not None
            obj.popped_stack_items = popped_stack_items
            obj.pushed_stack_items = pushed_stack_items
            if min_stack_height is None:
                obj.min_stack_height = obj.popped_stack_items
            else:
                obj.min_stack_height = min_stack_height
            if max_stack_height is None:
                obj.max_stack_height = max(obj.popped_stack_items, obj.pushed_stack_items)
            else:
                obj.max_stack_height = max_stack_height
            obj.terminating = terminating
            obj._name_ = name
            return obj

        raise TypeError("Bytecode constructor '__new__' didn't return an instance!")

    def __bytes__(self) -> bytes:
        """
        Return the opcode byte representation.
        """
        return self._bytes_

    def __len__(self) -> int:
        """
        Return the length of the opcode byte representation.
        """
        return len(self._bytes_)

    def __str__(self) -> str:
        """
        Return the name of the opcode, assigned at Enum creation.
        """
        return self._name_

    def __eq__(self, other):
        """
        Allows comparison between Bytecode instances and bytes objects.

        Raises:
        - NotImplementedError: if the comparison is not between an Bytecode
            or a bytes object.
        """
        if isinstance(other, SupportsBytes):
            return bytes(self) == bytes(other)
        raise NotImplementedError(f"Unsupported type for comparison f{type(other)}")

    def __hash__(self):
        """
        Return the hash of the bytecode representation.
        """
        return hash(
            (
                bytes(self),
                self.popped_stack_items,
                self.pushed_stack_items,
                self.max_stack_height,
                self.min_stack_height,
            )
        )

    def __add__(self, other: "Bytecode | int | None") -> "Bytecode":
        """
        Concatenate the bytecode representation with another bytecode object.
        """
        if other is None or (isinstance(other, int) and other == 0):
            # Edge case for sum() function
            return self
        assert isinstance(other, Bytecode), "Can only concatenate Bytecode instances"
        # Figure out the stack height after executing the two opcodes.
        a_pop, a_push = self.popped_stack_items, self.pushed_stack_items
        a_min, a_max = self.min_stack_height, self.max_stack_height
        b_pop, b_push = other.popped_stack_items, other.pushed_stack_items
        b_min, b_max = other.min_stack_height, other.max_stack_height

        # NOTE: "_pop" is understood as the number of elements required by an instruction or
        # bytecode to be popped off the stack before it starts returning (pushing).

        # Auxiliary variables representing "stages" of the execution of `c = a + b` bytecode:
        # Assume starting point 0 as reference:
        a_start = 0
        # A (potentially) pops some elements and reaches its "bottom", might be negative:
        a_bottom = a_start - a_pop
        # After this A pushes some elements, then B pops and reaches its "bottom":
        b_bottom = a_bottom + a_push - b_pop

        # C's bottom is either at the bottom of A or B:
        c_bottom = min(a_bottom, b_bottom)
        if c_bottom == a_bottom:
            # C pops the same as A to reach its bottom, then the rest of A and B are C's "push"
            c_pop = a_pop
            c_push = a_push - b_pop + b_push
        else:
            # A and B are C's "pop" to reach its bottom, then pushes the same as B
            c_pop = a_pop - a_push + b_pop
            c_push = b_push

        # C's minimum required stack is either A's or B's shifted by the net stack balance of A
        c_min = max(a_min, b_min + a_pop - a_push)

        # C starts from c_min, then reaches max either in the spot where A reached a_max or in the
        # spot where B reached b_max, after A had completed.
        c_max = max(c_min + a_max - a_min, c_min - a_pop + a_push + b_max - b_min)

        return Bytecode(
            bytes(self) + bytes(other),
            popped_stack_items=c_pop,
            pushed_stack_items=c_push,
            min_stack_height=c_min,
            max_stack_height=c_max,
            terminating=other.terminating,
        )

    def __radd__(self, other: "Bytecode | int | None") -> "Bytecode":
        """
        Concatenate the opcode byte representation with another bytes object.
        """
        if other is None or (isinstance(other, int) and other == 0):
            # Edge case for sum() function
            return self
        assert isinstance(other, Bytecode), "Can only concatenate Bytecode instances"
        return other.__add__(self)

    def __mul__(self, other: int) -> "Bytecode":
        """
        Concatenate another bytes object with the opcode byte representation.
        """
        if other < 0:
            raise ValueError("Cannot multiply by a negative number")
        if other == 0:
            return Bytecode()
        output = self
        for _ in range(other - 1):
            output += self
        return output

    def hex(self) -> str:
        """
        Return the hexadecimal representation of the opcode byte representation.
        """
        return bytes(self).hex()

    def keccak256(self) -> bytes:
        """
        Return the keccak256 hash of the opcode byte representation.
        """
        return keccak256(self._bytes_)
