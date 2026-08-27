"""Ethereum Virtual Machine bytecode primitives and utilities."""

from typing import Any, Dict, List, Self, SupportsBytes, Type

from pydantic import GetCoreSchemaHandler
from pydantic_core.core_schema import (
    PlainValidatorFunctionSchema,
    no_info_plain_validator_function,
    plain_serializer_function_ser_schema,
)

from execution_testing.base_types import Bytes, Hash

from .bases import ForkOpcodeInterface, OpcodeBase


class Bytecode:
    """
    Base class to represent EVM bytecode.

    Stack calculations are automatically done after an addition operation
    between two bytecode objects. The stack height is not guaranteed to be
    correct, so the user must take this into consideration.

    Parameters
    ----------
    - popped_stack_items: number of items the bytecode pops from the stack
    - pushed_stack_items: number of items the bytecode pushes to the stack
    - min_stack_height: minimum stack height required by the bytecode
    - max_stack_height: maximum stack height reached by the bytecode

    """

    _name_: str = ""
    _bytes_: bytes
    _keccak_256_: Hash | None = None
    _gas_cost_: int | None = None
    _gas_cost_fork_: Type[ForkOpcodeInterface] | None = None
    _state_cost_: int | None = None
    _state_cost_fork_: Type[ForkOpcodeInterface] | None = None
    _execution_cost_: int | None = None
    _execution_cost_fork_: Type[ForkOpcodeInterface] | None = None
    _refund_: int | None = None
    _refund_fork_: Type[ForkOpcodeInterface] | None = None
    _state_refund_: int | None = None
    _state_refund_fork_: Type[ForkOpcodeInterface] | None = None

    popped_stack_items: int
    pushed_stack_items: int
    max_stack_height: int
    min_stack_height: int

    terminating: bool
    opcode_list: List[OpcodeBase]
    _placeholder_offsets: Dict[str, int]
    _placeholder_sizes: Dict[str, int]

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
        opcode_list: List[OpcodeBase] | None = None,
        placeholder_offsets: Dict[str, int] | None = None,
        placeholder_sizes: Dict[str, int] | None = None,
    ) -> Self:
        """Create new opcode instance."""
        if opcode_list is None:
            opcode_list = []
        if placeholder_offsets is not None or placeholder_sizes is not None:
            if placeholder_offsets is None or placeholder_sizes is None:
                raise Exception(
                    f"incongruent parameters: placeholder_offsets "
                    f"({placeholder_offsets}) placeholder_sizes "
                    f"({placeholder_sizes})"
                )
            if len(placeholder_offsets) != len(placeholder_sizes):
                raise Exception(
                    f"incongruent parameters: len(placeholder_offsets) "
                    f"({len(placeholder_offsets)}) len(placeholder_sizes) "
                    f"({len(placeholder_sizes)})"
                )
        if bytes_or_byte_code_base is None:
            instance = super().__new__(cls)
            instance._bytes_ = b""
            instance.popped_stack_items = 0
            instance.pushed_stack_items = 0
            instance.min_stack_height = 0
            instance.max_stack_height = 0
            instance.terminating = False
            instance._name_ = name
            instance.opcode_list = opcode_list
            instance._placeholder_offsets = placeholder_offsets or {}
            instance._placeholder_sizes = placeholder_sizes or {}

            return instance

        if isinstance(bytes_or_byte_code_base, Bytecode):
            # Required because Enum class calls the base class with the
            # instantiated object as parameter.
            obj = super().__new__(cls)
            obj._bytes_ = bytes_or_byte_code_base._bytes_
            obj.popped_stack_items = bytes_or_byte_code_base.popped_stack_items
            obj.pushed_stack_items = bytes_or_byte_code_base.pushed_stack_items
            obj.min_stack_height = bytes_or_byte_code_base.min_stack_height
            obj.max_stack_height = bytes_or_byte_code_base.max_stack_height
            obj.terminating = bytes_or_byte_code_base.terminating
            obj.opcode_list = bytes_or_byte_code_base.opcode_list[:]
            obj._name_ = bytes_or_byte_code_base._name_
            obj._placeholder_offsets = (
                bytes_or_byte_code_base._placeholder_offsets.copy()
            )
            obj._placeholder_sizes = (
                bytes_or_byte_code_base._placeholder_sizes.copy()
            )
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
                obj.max_stack_height = max(
                    obj.popped_stack_items, obj.pushed_stack_items
                )
            else:
                obj.max_stack_height = max_stack_height
            obj.terminating = terminating
            obj.opcode_list = opcode_list
            obj._name_ = name
            obj._placeholder_offsets = placeholder_offsets or {}
            obj._placeholder_sizes = placeholder_sizes or {}
            return obj

        raise TypeError(
            "Bytecode constructor '__new__' didn't return an instance!"
        )

    def __bytes__(self) -> bytes:
        """Return the opcode byte representation."""
        return self._bytes_

    def __len__(self) -> int:
        """Return the length of the opcode byte representation."""
        return len(self._bytes_)

    def __str__(self) -> str:
        """Return the name of the opcode, assigned at Enum creation."""
        return self._name_

    def __eq__(self, other: object) -> bool:
        """
        Allow comparison between Bytecode instances and bytes objects.

        Raises:
          - NotImplementedError: if the comparison is not between an
                                 Bytecode or a bytes object.

        """
        if isinstance(other, Bytecode):
            return (
                bytes(self) == bytes(other)
                and self.popped_stack_items == other.popped_stack_items
                and self.pushed_stack_items == other.pushed_stack_items
                and self.max_stack_height == other.max_stack_height
                and self.min_stack_height == other.min_stack_height
            )
        if isinstance(other, SupportsBytes) or isinstance(other, bytes):
            return bytes(self) == bytes(other)
        raise NotImplementedError(
            f"Unsupported type for comparison: {type(other)}"
        )

    def __hash__(self) -> int:
        """Return the hash of the bytecode representation."""
        return hash(
            (
                bytes(self),
                self.popped_stack_items,
                self.pushed_stack_items,
                self.max_stack_height,
                self.min_stack_height,
            )
        )

    def __add__(self, other: "Bytecode | bytes | int | None") -> "Bytecode":
        """
        Concatenate the bytecode representation with another bytecode object.
        """
        if other is None or (isinstance(other, int) and other == 0):
            # Edge case for sum() function
            return self

        if isinstance(other, bytes):
            c = Bytecode(self)
            c._bytes_ += other
            c._name_ = ""
            return c

        assert isinstance(other, Bytecode), (
            "Can only concatenate Bytecode instances"
        )
        # Figure out the stack height after executing the two opcodes.
        a_pop, a_push = self.popped_stack_items, self.pushed_stack_items
        a_min, a_max = self.min_stack_height, self.max_stack_height
        b_pop, b_push = other.popped_stack_items, other.pushed_stack_items
        b_min, b_max = other.min_stack_height, other.max_stack_height

        # NOTE: "_pop" is understood as the number of elements required by an
        # instruction or bytecode to be popped off the stack before it starts
        # returning (pushing).

        # Auxiliary variables representing "stages" of the execution of
        # `c = a + b` bytecode: Assume starting point 0 as reference:
        a_start = 0
        # A (potentially) pops some elements and reaches its "bottom", might be
        # negative:
        a_bottom = a_start - a_pop
        # After this A pushes some elements, then B pops and reaches its
        # "bottom":
        b_bottom = a_bottom + a_push - b_pop

        # C's bottom is either at the bottom of A or B:
        c_bottom = min(a_bottom, b_bottom)
        if c_bottom == a_bottom:
            # C pops the same as A to reach its bottom, then the rest of A and
            # B are C's "push"
            c_pop = a_pop
            c_push = a_push - b_pop + b_push
        else:
            # A and B are C's "pop" to reach its bottom, then pushes the same
            # as B
            c_pop = a_pop - a_push + b_pop
            c_push = b_push

        # C's minimum required stack is either A's or B's shifted by the net
        # stack balance of A
        c_min = max(a_min, b_min + a_pop - a_push)

        # C starts from c_min, then reaches max either in the spot where A
        # reached a_max or in the spot where B reached b_max, after A had
        # completed.
        c_max = max(
            c_min + a_max - a_min, c_min - a_pop + a_push + b_max - b_min
        )

        c = Bytecode(
            self._bytes_ + other._bytes_,
            popped_stack_items=c_pop,
            pushed_stack_items=c_push,
            min_stack_height=c_min,
            max_stack_height=c_max,
            terminating=other.terminating,
            opcode_list=self.opcode_list + other.opcode_list,
        )
        # Merge placeholders, adjusting offsets for 'other'
        if (
            len(
                self._placeholder_offsets.keys()
                & other._placeholder_offsets.keys()
            )
            != 0
        ):
            raise Exception(
                "Conflicting data placeholders between bytecode objects: "
                f"{self._placeholder_offsets.keys()}, "
                f"{other._placeholder_offsets.keys()}"
            )
        c._placeholder_offsets = self._placeholder_offsets.copy()
        c._placeholder_sizes = (
            self._placeholder_sizes | other._placeholder_sizes
        )
        for placeholder, offset in other._placeholder_offsets.items():
            c._placeholder_offsets[placeholder] = len(self) + offset
        return c

    def __radd__(self, other: "Bytecode | int | None") -> "Bytecode":
        """
        Repeat the bytecode a given number of times.
        """
        if other is None or (isinstance(other, int) and other == 0):
            # Edge case for sum() function
            return self
        assert isinstance(other, Bytecode), (
            "Can only concatenate Bytecode instances"
        )
        return other.__add__(self)

    def __mul__(self, other: int) -> "Bytecode":
        """
        Concatenate another bytes object with the opcode byte representation.
        """
        if other < 0:
            raise ValueError("Cannot multiply by a negative number")
        if other == 0:
            return Bytecode()
        if other == 1:
            return Bytecode(self)

        if self._placeholder_offsets or self._placeholder_sizes:
            raise ValueError(
                "Cannot multiply bytecode containing placeholders"
            )

        result_bytes = self._bytes_ * other

        a_pop = self.popped_stack_items
        a_push = self.pushed_stack_items
        a_min = self.min_stack_height
        a_max = self.max_stack_height
        net = a_push - a_pop
        repeats = other - 1

        c_pop = a_pop + max(0, -net) * repeats
        c_push = a_push + max(0, net) * repeats
        c_min = a_min + max(0, -net) * repeats
        c_max = a_max + abs(net) * repeats

        return Bytecode(
            result_bytes,
            popped_stack_items=c_pop,
            pushed_stack_items=c_push,
            min_stack_height=c_min,
            max_stack_height=c_max,
            terminating=self.terminating,
            opcode_list=self.opcode_list * other,
        )

    def hex(self) -> str:
        """
        Return the hexadecimal representation of the opcode byte
        representation.
        """
        return bytes(self).hex()

    def keccak256(self) -> Hash:
        """Return the keccak256 hash of the opcode byte representation."""
        if self._keccak_256_ is None:
            self._keccak_256_ = Bytes(self._bytes_).keccak256()
        return self._keccak_256_

    def gas_cost(self, fork: Type[ForkOpcodeInterface]) -> int:
        """Use a fork object to calculate the gas used by this bytecode."""
        if self._gas_cost_ is None or self._gas_cost_fork_ != fork:
            self._gas_cost_fork_ = fork
            opcode_gas_calculator = fork.opcode_gas_calculator()
            self._gas_cost_ = 0
            for opcode in self.opcode_list:
                self._gas_cost_ += opcode_gas_calculator(opcode)
        return self._gas_cost_

    def state_cost(self, fork: Type[ForkOpcodeInterface]) -> int:
        """
        Use a fork object to calculate the state gas used by this
        bytecode.
        """
        if self._state_cost_ is None or self._state_cost_fork_ != fork:
            self._state_cost_fork_ = fork
            opcode_state_calculator = fork.opcode_state_calculator()
            self._state_cost_ = 0
            for opcode in self.opcode_list:
                self._state_cost_ += opcode_state_calculator(opcode)
        return self._state_cost_

    def execution_cost(self, fork: Type[ForkOpcodeInterface]) -> int:
        """
        Use a fork object to calculate the execution gas used by this
        bytecode (i.e. excluding the state-gas portion under EIP-8037).

        Useful for OOG-boundary tests that need to land at the execution
        gas charge of an opcode rather than its combined execution + state
        cost.
        """
        if self._execution_cost_ is None or self._execution_cost_fork_ != fork:
            self._execution_cost_fork_ = fork
            self._execution_cost_ = self.gas_cost(fork) - self.state_cost(fork)
        return self._execution_cost_

    def refund(self, fork: Type[ForkOpcodeInterface]) -> int:
        """Use a fork object to calculate the gas refund from this bytecode."""
        if self._refund_ is None or self._refund_fork_ != fork:
            self._refund_fork_ = fork
            opcode_refund_calculator = fork.opcode_refund_calculator()
            self._refund_ = 0
            for opcode in self.opcode_list:
                self._refund_ += opcode_refund_calculator(opcode)
        return self._refund_

    def substitute(self, **kwargs: int) -> "Bytecode":
        """
        Replace named placeholders with actual values.

        Args:
            kwargs: The placeholders and their values to set

        Returns:
            New Bytecode with the placeholders replaced

        Raises:
            ValueError: If a value doesn't fit in the placeholder's size
            KeyError: If a placeholder name is not found in this bytecode

        """
        placeholder_offsets = self._placeholder_offsets.copy()
        placeholder_sizes = self._placeholder_sizes.copy()

        new_bytes = self._bytes_
        for placeholder, value in kwargs.items():
            if placeholder not in placeholder_offsets:
                raise KeyError(
                    f"Placeholder {placeholder} not found in bytecode"
                )

            offset, size = (
                placeholder_offsets.pop(placeholder),
                placeholder_sizes.pop(placeholder),
            )

            max_value = (1 << (size * 8)) - 1
            if value < 0 or value > max_value:
                raise ValueError(
                    f"Value {value} doesn't fit in {size} bytes "
                    f"(max {max_value})"
                )

            # Replace the placeholder bytes with the actual value
            new_bytes = (
                new_bytes[:offset]
                + value.to_bytes(size, "big")
                + new_bytes[(offset + size) :]
            )

        return Bytecode(
            new_bytes,
            popped_stack_items=self.popped_stack_items,
            pushed_stack_items=self.pushed_stack_items,
            max_stack_height=self.max_stack_height,
            min_stack_height=self.min_stack_height,
            terminating=self.terminating,
            opcode_list=self.opcode_list[:],
            placeholder_offsets=placeholder_offsets,
            placeholder_sizes=placeholder_sizes,
        )

    def state_refund(self, fork: Type[ForkOpcodeInterface]) -> int:
        """
        Use a fork object to calculate the state refund from this bytecode.
        """
        if self._state_refund_ is None or self._state_refund_fork_ != fork:
            self._state_refund_fork_ = fork
            opcode_state_refund_calculator = (
                fork.opcode_state_refund_calculator()
            )
            self._state_refund_ = 0
            for opcode in self.opcode_list:
                self._state_refund_ += opcode_state_refund_calculator(opcode)
        return self._state_refund_

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> PlainValidatorFunctionSchema:
        """
        Provide Pydantic core schema for Bytecode
        serialization and validation.
        """
        return no_info_plain_validator_function(
            cls,
            serialization=plain_serializer_function_ser_schema(
                lambda bytecode: "0x" + bytecode.hex(),
                info_arg=False,
            ),
        )
