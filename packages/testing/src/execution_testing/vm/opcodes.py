"""
Ethereum Virtual Machine opcode definitions.

Acknowledgments: The individual opcode documentation below is due to the work
by [smlXL](https://github.com/smlxl) on [evm.codes](https://www.evm.codes/),
available as open source [`smlxl/evm.codes`][0]; thank you! And thanks to
@ThreeHrSleep for integrating it in the docstrings.

[0]: https://github.com/smlxl/evm.codes
"""

from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    SupportsBytes,
)

from execution_testing.base_types import to_bytes

from .bases import OpcodeBase
from .bytecode import Bytecode


def _get_int_size(n: int) -> int:
    """Return size of an integer in bytes."""
    if n < 0:
        # Negative numbers in the EVM are represented as two's complement
        # of 32 bytes
        return 32
    byte_count = 0
    while n:
        byte_count += 1
        n >>= 8
    return byte_count


KW_ARGS_DEFAULTS_TYPE = Mapping[str, "int | bytes | str | Opcode | Bytecode"]


def _stack_argument_to_bytecode(
    arg: (
        "int | bytes | SupportsBytes | str | Opcode | Bytecode | Iterable[int]"
    ),
) -> Bytecode:
    """Convert stack argument in an opcode or macro to bytecode."""
    if isinstance(arg, Bytecode):
        return arg

    # We are going to push a constant to the stack.
    data_size = 0
    if isinstance(arg, int):
        signed = arg < 0
        data_size = _get_int_size(arg)
        if data_size > 32:
            raise ValueError("Opcode stack data must be less than 32 bytes")
        elif data_size == 0:
            # Pushing 0 is done with the PUSH1 opcode
            # for compatibility reasons.
            data_size = 1
        arg = arg.to_bytes(
            length=data_size,
            byteorder="big",
            signed=signed,
        )
    else:
        arg = to_bytes(arg).lstrip(b"\0")  # type: ignore
        if arg == b"":
            # Pushing 0 is done with the PUSH1 opcode for
            # compatibility reasons.
            arg = b"\x00"
        data_size = len(arg)

    assert isinstance(arg, bytes)
    assert data_size > 0
    new_opcode = _push_opcodes_byte_list[data_size - 1][arg]
    return new_opcode


class Opcode(Bytecode, OpcodeBase):
    """
    Represents a single Opcode instruction in the EVM, with extra
    metadata useful to parametrize tests.

    Parameters
    ----------
    - data_portion_length: number of bytes after the opcode in the bytecode
        that represent data
    - data_portion_formatter: function to format the data portion of the
        opcode, if any
    - stack_properties_modifier: function to modify the stack properties of
    the opcode after the data portion has been processed
    - kwargs: list of keyword arguments that can be passed to the opcode,
    in the order they are meant to be placed in the stack
    - kwargs_defaults: default values for the keyword arguments if any,
    otherwise 0
    - unchecked_stack: whether the bytecode should ignore stack checks
    when being called
    - metadata: dictionary containing extra metadata about the opcode instance,
    useful for gas cost calculations and other analysis

    """

    data_portion_length: int
    data_portion_formatter: Optional[Callable[[Any], bytes]]
    stack_properties_modifier: Optional[
        Callable[[Any], tuple[int, int, int, int]]
    ]
    kwargs: List[str]
    kwargs_defaults: KW_ARGS_DEFAULTS_TYPE
    original_opcode: Optional["Opcode"] = None
    unchecked_stack: bool = False

    def __new__(
        cls,
        opcode_or_byte: "int | bytes | Opcode",
        *,
        popped_stack_items: int = 0,
        pushed_stack_items: int = 0,
        max_stack_height: int | None = None,
        min_stack_height: int | None = None,
        data_portion_length: int = 0,
        data_portion_formatter: Any = None,
        stack_properties_modifier: Any = None,
        unchecked_stack: bool = False,
        terminating: bool = False,
        kwargs: List[str] | None = None,
        kwargs_defaults: KW_ARGS_DEFAULTS_TYPE | None = None,
        metadata: Dict[str, Any] | None = None,
        original_opcode: Optional["Opcode"] = None,
    ) -> "Opcode":
        """Create new opcode instance."""
        if kwargs_defaults is None:
            kwargs_defaults = {}
        if metadata is None:
            metadata = {}
        if type(opcode_or_byte) is Opcode:
            # Required because Enum class calls the base class
            # with the instantiated object as parameter.
            return opcode_or_byte
        elif isinstance(opcode_or_byte, int) or isinstance(
            opcode_or_byte, bytes
        ):
            obj_bytes = (
                bytes([opcode_or_byte])
                if isinstance(opcode_or_byte, int)
                else opcode_or_byte
            )
            if min_stack_height is None:
                min_stack_height = popped_stack_items
            if max_stack_height is None:
                max_stack_height = max(
                    min_stack_height - popped_stack_items + pushed_stack_items,
                    min_stack_height,
                )
            obj = super().__new__(
                cls,
                obj_bytes,
                popped_stack_items=popped_stack_items,
                pushed_stack_items=pushed_stack_items,
                max_stack_height=max_stack_height,
                min_stack_height=min_stack_height,
                terminating=terminating,
            )
            obj.data_portion_length = data_portion_length
            obj.data_portion_formatter = data_portion_formatter
            obj.stack_properties_modifier = stack_properties_modifier
            obj.unchecked_stack = unchecked_stack
            if kwargs is None:
                obj.kwargs = []
            else:
                obj.kwargs = kwargs
            obj.kwargs_defaults = kwargs_defaults
            obj.metadata = metadata
            obj.original_opcode = original_opcode
            obj.opcode_list = [obj]
            return obj
        raise TypeError(
            "Opcode constructor '__new__' didn't return an instance!"
        )

    def __getitem__(
        self, *args: "int | bytes | str | Iterable[int]"
    ) -> "Opcode":
        """
        Initialize a new instance of the opcode with the data portion set,
        and also clear the data portion variables to avoid reusing them.
        """
        if (
            self.data_portion_formatter is None
            and self.data_portion_length == 0
        ):
            raise ValueError(
                "Opcode does not have a data portion or has already been set"
            )
        data_portion = bytes()

        if self.data_portion_formatter is not None:
            if (
                len(args) == 1
                and isinstance(args[0], Iterable)
                and not isinstance(args[0], bytes)
            ):
                data_portion = self.data_portion_formatter(*args[0])
            else:
                data_portion = self.data_portion_formatter(*args)
        elif self.data_portion_length > 0:
            # For opcodes with a data portion, the first argument is the
            # data and the rest of the arguments form the stack.
            assert len(args) == 1, (
                "Opcode with data portion requires exactly one argument"
            )
            data = args[0]
            if (
                isinstance(data, bytes)
                or isinstance(data, SupportsBytes)
                or isinstance(data, str)
            ):
                if isinstance(data, str):
                    if data.startswith("0x"):
                        data = data[2:]
                    data = bytes.fromhex(data)
                elif isinstance(data, SupportsBytes):
                    data = bytes(data)
                assert len(data) <= self.data_portion_length
                data_portion = data.rjust(self.data_portion_length, b"\x00")
            elif isinstance(data, int):
                signed = data < 0
                data_portion = data.to_bytes(
                    length=self.data_portion_length,
                    byteorder="big",
                    signed=signed,
                )
            else:
                raise TypeError(
                    "Opcode data portion must be either an int or bytes/hex "
                    "string"
                )
        popped_stack_items = self.popped_stack_items
        pushed_stack_items = self.pushed_stack_items
        min_stack_height = self.min_stack_height
        max_stack_height = self.max_stack_height
        assert (
            popped_stack_items is not None
            and pushed_stack_items is not None
            and min_stack_height is not None
        )
        if self.stack_properties_modifier is not None:
            (
                popped_stack_items,
                pushed_stack_items,
                min_stack_height,
                max_stack_height,
            ) = self.stack_properties_modifier(data_portion)

        new_opcode = Opcode(
            bytes(self) + data_portion,
            popped_stack_items=popped_stack_items,
            pushed_stack_items=pushed_stack_items,
            min_stack_height=min_stack_height,
            max_stack_height=max_stack_height,
            data_portion_length=0,
            data_portion_formatter=None,
            unchecked_stack=self.unchecked_stack,
            terminating=self.terminating,
            kwargs=self.kwargs,
            kwargs_defaults=self.kwargs_defaults,
            metadata=self.metadata,
            original_opcode=self,
        )
        new_opcode.opcode_list = [new_opcode]
        new_opcode._name_ = f"{self._name_}_0x{data_portion.hex()}"
        return new_opcode

    def with_metadata(self, **metadata: Any) -> "Opcode":
        """
        Create a copy of this opcode with updated metadata.

        Validates metadata keys against metadata and merges with existing
        metadata.

        Args:
            **metadata: Metadata key-value pairs to set or update

        Returns:
            A new Opcode instance with the updated metadata

        Raises:
            ValueError: If invalid metadata keys are provided

        Example:
            >>> warm_sstore = Op.SSTORE.with_metadata(key_warm=True,
                new_value=2)

        """
        # Validate metadata keys
        for key in metadata:
            if key not in self.metadata:
                raise ValueError(
                    f"Invalid metadata key '{key}' for opcode {self._name_}. "
                    f"Valid metadata keys: {list(self.metadata.keys())}"
                )

        # Create a new opcode instance with updated metadata
        new_opcode = Opcode(
            bytes(self),
            popped_stack_items=self.popped_stack_items,
            pushed_stack_items=self.pushed_stack_items,
            min_stack_height=self.min_stack_height,
            max_stack_height=self.max_stack_height,
            data_portion_length=self.data_portion_length,
            data_portion_formatter=self.data_portion_formatter,
            unchecked_stack=self.unchecked_stack,
            terminating=self.terminating,
            kwargs=self.kwargs,
            kwargs_defaults=self.kwargs_defaults,
            # Merge defaults, existing metadata, and new metadata
            metadata={**self.metadata, **metadata},
            original_opcode=self,
        )
        new_opcode.opcode_list = [new_opcode]
        new_opcode._name_ = self._name_
        return new_opcode

    def __call__(
        self,
        *args_t: "int | bytes | str | Opcode | Bytecode | Iterable[int]",
        unchecked: bool = False,
        **kwargs: "int | bytes | str | Opcode | Bytecode",
    ) -> "Bytecode | Opcode":
        """
        Make all opcode instances callable to return formatted bytecode, which
        constitutes a data portion, that is located after the opcode byte,
        and pre-opcode bytecode, which is normally used to set up the stack.

        This useful to automatically format, e.g., call opcodes and their
        stack arguments as
        `Opcodes.CALL(Opcodes.GAS, 0x1234, 0x0, 0x0, 0x0, 0x0, 0x0)`.

        Data sign is automatically detected but for this reason the range
        of the input must be:
        `[-2^(data_portion_bits-1), 2^(data_portion_bits)]`
        where:
        `data_portion_bits == data_portion_length * 8`

        For the stack, the arguments are set up in the opposite order they
        are given, so the first argument is the last item pushed to the stack.

        The resulting stack arrangement does not take into account
        opcode stack element consumption, so the stack height is not
        guaranteed to be correct and the user must take this into
        consideration.

        Integers can also be used as stack elements, in which case they
        are automatically converted to PUSH operations, and negative numbers
        always use a PUSH32 operation.

        Hex-strings will be automatically converted to bytes.
        """
        args: List["int | bytes | str | Opcode | Bytecode | Iterable[int]"] = (
            list(args_t)
        )
        opcode = self

        # handle metadata first
        metadata = {}
        for key in opcode.metadata:
            if key in kwargs:
                metadata[key] = kwargs.pop(key)
        if metadata:
            opcode = opcode.with_metadata(**metadata)
            if len(args) == 0 and len(kwargs) == 0:
                # Nothing else to do, return
                return opcode

        if opcode.has_data_portion():
            if len(args) == 0:
                raise ValueError(
                    "Opcode with data portion requires at least one argument"
                )
            assert type(opcode) is Opcode
            get_item_arg = args.pop()
            assert not isinstance(get_item_arg, Bytecode)
            return opcode[get_item_arg](*args)

        if opcode.kwargs is not None and len(kwargs) > 0:
            assert len(args) == 0, (
                f"Cannot mix positional and keyword arguments {args} {kwargs}"
            )

            # Validate that all provided kwargs are valid
            invalid_kwargs = set(kwargs.keys()) - set(opcode.kwargs)
            if invalid_kwargs:
                raise ValueError(
                    f"Invalid keyword argument(s) {list(invalid_kwargs)} for "
                    f"opcode {opcode._name_}. "
                    f"Valid arguments are: {opcode.kwargs}"
                )

            for kw in opcode.kwargs:
                args.append(
                    kwargs[kw]
                    if kw in kwargs
                    else opcode.kwargs_defaults.get(kw, 0)
                )

        # The rest of the arguments form the stack.
        if len(args) != opcode.popped_stack_items and not (
            unchecked or opcode.unchecked_stack
        ):
            raise ValueError(
                f"Opcode {opcode._name_} requires {opcode.popped_stack_items} "
                f"stack elements, but {len(args)} were provided. "
                "Use 'unchecked=True' parameter to ignore this check."
            )

        pre_opcode_bytecode = Bytecode()
        while len(args) > 0:
            pre_opcode_bytecode += _stack_argument_to_bytecode(args.pop())
        return pre_opcode_bytecode + opcode

    def __lt__(self, other: "Opcode") -> bool:
        """Compare two opcodes by their integer value."""
        return self.int() < other.int()

    def __gt__(self, other: "Opcode") -> bool:
        """Compare two opcodes by their integer value."""
        return self.int() > other.int()

    def get_original_opcode(self) -> "Opcode":
        """Return the original opcode instance."""
        if self.original_opcode is not None:
            return self.original_opcode
        return self

    def __hash__(self) -> int:
        """Hash the opcode by its integer value."""
        return hash(self.get_original_opcode().int())

    def __eq__(self, other: object) -> bool:
        """Compare two opcodes by their integer value."""
        if isinstance(other, Opcode):
            return (
                self.get_original_opcode().int()
                == other.get_original_opcode().int()
            )
        return super().__eq__(other)

    def int(self) -> int:
        """Return integer representation of the opcode."""
        return int.from_bytes(self, byteorder="big")

    def has_data_portion(self) -> bool:
        """Return whether the opcode has a data portion."""
        return (
            self.data_portion_length > 0
            or self.data_portion_formatter is not None
        )

    def get_metadata(self) -> Dict[str, Any]:
        """
        Get a copy of the current metadata.

        Returns:
            A dictionary containing the current metadata values

        """
        return self.metadata.copy()


OpcodeCallArg = int | bytes | str | Bytecode | Iterable[int]


class Macro(Bytecode):
    """Represents opcode macro replacement, basically holds bytes."""

    lambda_operation: Callable[..., Bytecode] | None

    def __new__(
        cls,
        macro_or_bytes: Optional["Bytecode | Macro"] = None,
        *,
        lambda_operation: Callable[..., Bytecode] | None = None,
    ) -> "Macro":
        """Create new opcode macro instance."""
        if macro_or_bytes is None:
            macro_or_bytes = Bytecode()
        if isinstance(macro_or_bytes, Macro):
            # Required because Enum class calls the base class
            # with the instantiated object as parameter.
            return macro_or_bytes
        else:
            instance = super().__new__(cls, macro_or_bytes)
            instance.lambda_operation = lambda_operation
            return instance

    def __call__(self, *args_t: OpcodeCallArg, **kwargs: Any) -> Bytecode:
        """Perform macro operation if any. Otherwise is a no-op."""
        del kwargs
        if self.lambda_operation is not None:
            return self.lambda_operation(*args_t)

        pre_opcode_bytecode = Bytecode()
        for arg in args_t:
            pre_opcode_bytecode += _stack_argument_to_bytecode(arg)
        return pre_opcode_bytecode + self


class Opcodes(Opcode, Enum):
    """
    Enum containing all known opcodes.

    Contains deprecated and not yet implemented opcodes.

    This enum is !! NOT !! meant to be iterated over by the tests.
    Instead, create a list with cherry-picked opcodes from this Enum
    within the test if iteration is needed.

    Do !! NOT !! remove or modify existing opcodes from this list.
    """

    STOP = Opcode(0x00, terminating=True)
    """
    STOP()
    ----

    Description
    ----
    Stop execution

    Inputs
    ----
    - None

    Outputs
    ----
    - None

    Fork
    ----
    Frontier

    Gas
    ----
    0

    Source: [evm.codes/#00](https://www.evm.codes/#00)
    """

    ADD = Opcode(0x01, popped_stack_items=2, pushed_stack_items=1)
    """
    ADD(a, b) = c
    ----

    Description
    ----
    Addition operation

    Inputs
    ----
    - a: first integer value to add
    - b: second integer value to add

    Outputs
    ----
    - c: integer result of the addition modulo 2**256

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#01](https://www.evm.codes/#01)
    """

    MUL = Opcode(0x02, popped_stack_items=2, pushed_stack_items=1)
    """
    MUL(a, b) = c
    ----

    Description
    ----
    Multiplication operation

    Inputs
    ----
    - a: first integer value to multiply
    - b: second integer value to multiply

    Outputs
    ----
    - c: integer result of the multiplication modulo 2**256

    Fork
    ----
    Frontier

    Gas
    ----
    5

    Source: [evm.codes/#02](https://www.evm.codes/#02)
    """

    SUB = Opcode(0x03, popped_stack_items=2, pushed_stack_items=1)
    """
    SUB(a, b) = c
    ----

    Description
    ----
    Subtraction operation

    Inputs
    ----
    - a: first integer value
    - b: second integer value

    Outputs
    ----
    - c: integer result of the subtraction modulo 2**256

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#03](https://www.evm.codes/#03)
    """

    DIV = Opcode(0x04, popped_stack_items=2, pushed_stack_items=1)
    """
    DIV(a, b) = c
    ----

    Description
    ----
    Division operation

    Inputs
    ----
    - a: numerator
    - b: denominator (must be non-zero)

    Outputs
    ----
    - c: integer result of the division

    Fork
    ----
    Frontier

    Gas
    ----
    5

    Source: [evm.codes/#04](https://www.evm.codes/#04)
    """

    SDIV = Opcode(0x05, popped_stack_items=2, pushed_stack_items=1)
    """
    SDIV(a, b) = c
    ----

    Description
    ----
    Signed division operation

    Inputs
    ----
    - a: signed numerator
    - b: signed denominator

    Outputs
    ----
    - c: signed integer result of the division. If the denominator is 0,
         the result will be 0
    ----

    Fork
    ----
    Frontier

    Gas
    ----
    5

    Source: [evm.codes/#05](https://www.evm.codes/#05)
    """

    MOD = Opcode(0x06, popped_stack_items=2, pushed_stack_items=1)
    """
    MOD(a, b) = c
    ----

    Description
    ----
    Modulo operation

    Inputs
    ----
    - a: integer numerator
    - b: integer denominator

    Outputs
    ----
    - a % b: integer result of the integer modulo. If the denominator is 0,
             the result will be 0

    Fork
    ----
    Frontier

    Gas
    ----
    5

    Source: [evm.codes/#06](https://www.evm.codes/#06)
    """

    SMOD = Opcode(0x07, popped_stack_items=2, pushed_stack_items=1)
    """
    SMOD(a, b) = c
    ----

    Description
    ----
    Signed modulo remainder operation

    Inputs
    ----
    - a: integer numerator
    - b: integer denominator

    Outputs
    ----
    - a % b: integer result of the signed integer modulo. If the denominator
             is 0, the result will be 0

    Fork
    ----
    Frontier

    Gas
    ----
    5

    Source: [evm.codes/#07](https://www.evm.codes/#07)
    """

    ADDMOD = Opcode(0x08, popped_stack_items=3, pushed_stack_items=1)
    """
    ADDMOD(a, b, c) = d
    ----

    Description
    ----
    Modular addition operation with overflow check

    Inputs
    ----
    - a: first integer value
    - b: second integer value
    - c: integer denominator

    Outputs
    ----
    - (a + b) % N: integer result of the addition followed by a modulo.
                   If the denominator is 0, the result will be 0

    Fork
    ----
    Frontier

    Gas
    ----
    8

    Source: [evm.codes/#08](https://www.evm.codes/#08)
    """

    MULMOD = Opcode(0x09, popped_stack_items=3, pushed_stack_items=1)
    """
    MULMOD(a, b, N) = d
    ----

    Description
    ----
    Modulo multiplication operation

    Inputs
    ----
    - a: first integer value to multiply
    - b: second integer value to multiply
    - N: integer denominator

    Outputs
    ----
    - (a * b) % N: integer result of the multiplication followed by a modulo.
                   If the denominator is 0, the result will be 0

    Fork
    ----
    Frontier

    Gas
    ----
    8

    Source: [evm.codes/#09](https://www.evm.codes/#09)
    """

    EXP = Opcode(
        0x0A,
        popped_stack_items=2,
        pushed_stack_items=1,
        metadata={"exponent": 0},
    )
    """
    EXP(a, exponent) = a ** exponent
    ----

    Description
    ----
    Exponential operation

    Inputs
    ----
    - a: integer base
    - exponent: integer exponent

    Outputs
    ----
    - a ** exponent: integer result of the exponential operation modulo 2**256

    Fork
    ----
    Frontier

    Gas
    ----
    - static_gas = 10
    - dynamic_gas = 50 * exponent_byte_size

    Metadata
    ----
    - exponent: the exponent value (default: 0)

    Source: [evm.codes/#0A](https://www.evm.codes/#0A)
    """

    SIGNEXTEND = Opcode(0x0B, popped_stack_items=2, pushed_stack_items=1)
    """
    SIGNEXTEND(b, x) = y
    ----

    Description
    ----
    Sign extension operation

    Inputs
    ----
    - b: size in byte - 1 of the integer to sign extend
    - x: integer value to sign extend

    Outputs
    ----
    - y: integer result of the sign extend

    Fork
    ----
    Frontier

    Gas
    ----
    5

    Source: [evm.codes/#0B](https://www.evm.codes/#0B)
    """

    LT = Opcode(0x10, popped_stack_items=2, pushed_stack_items=1)
    """
    LT(a, b) = a < b
    ----

    Description
    ----
    Less-than comparison

    Inputs
    ----
    - a: left side integer value
    - b: right side integer value

    Outputs
    ----
    - a < b: 1 if the left side is smaller, 0 otherwise

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#10](https://www.evm.codes/#10)
    """

    GT = Opcode(0x11, popped_stack_items=2, pushed_stack_items=1)
    """
    GT(a, b) = a > b
    ----

    Description
    ----
    Greater-than comparison

    Inputs
    ----
    - a: left side integer
    - b: right side integer

    Outputs
    ----
    - a > b: 1 if the left side is bigger, 0 otherwise

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#11](https://www.evm.codes/#11)
    """

    SLT = Opcode(0x12, popped_stack_items=2, pushed_stack_items=1)
    """
    SLT(a, b) = a < b
    ----

    Description
    ----
    Signed less-than comparison

    Inputs
    ----
    - a: left side signed integer
    - b: right side signed integer

    Outputs
    ----
    - a < b: 1 if the left side is smaller, 0 otherwise

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#12](https://www.evm.codes/#12)
    """

    SGT = Opcode(0x13, popped_stack_items=2, pushed_stack_items=1)
    """
    SGT(a, b) = a > b
    ----

    Description
    ----
    Signed greater-than comparison

    Inputs
    ----
    - a: left side signed integer
    - b: right side signed integer

    Outputs
    ----
    - a > b: 1 if the left side is bigger, 0 otherwise

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#13](https://www.evm.codes/#13)
    """

    EQ = Opcode(0x14, popped_stack_items=2, pushed_stack_items=1)
    """
    EQ(a, b) = a == b
    ----

    Description
    ----
    Equality comparison

    Inputs
    ----
    - a: left side integer
    - b: right side integer

    Outputs
    ----
    - a == b: 1 if the left side is equal to the right side, 0 otherwise

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#14](https://www.evm.codes/#14)
    """

    ISZERO = Opcode(0x15, popped_stack_items=1, pushed_stack_items=1)
    """
    ISZERO(a) = a == 0
    ----

    Description
    ----
    Is-zero comparison

    Inputs
    ----
    - a: integer

    Outputs
    ----
    - a == 0: 1 if a is 0, 0 otherwise

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#15](https://www.evm.codes/#15)
    """

    AND = Opcode(0x16, popped_stack_items=2, pushed_stack_items=1)
    """
    AND(a, b) = a & b
    ----

    Description
    ----
    Bitwise AND operation

    Inputs
    ----
    - a: first binary value
    - b: second binary value

    Outputs
    ----
    - a & b: the bitwise AND result

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#16](https://www.evm.codes/#16)
    """

    OR = Opcode(0x17, popped_stack_items=2, pushed_stack_items=1)
    """
    OR(a, b) = a | b
    ----

    Description
    ----
    Bitwise OR operation

    Inputs
    ----
    - a: first binary value
    - b: second binary value

    Outputs
    ----
    - a | b: the bitwise OR result

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#17](https://www.evm.codes/#17)
    """

    XOR = Opcode(0x18, popped_stack_items=2, pushed_stack_items=1)
    """
    XOR(a, b) = a ^ b
    ----

    Description
    ----
    Bitwise XOR operation

    Inputs
    ----
    - a: first binary value
    - b: second binary value

    Outputs
    ----
    - a ^ b: the bitwise XOR result

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#18](https://www.evm.codes/#18)
    """

    NOT = Opcode(0x19, popped_stack_items=1, pushed_stack_items=1)
    """
    NOT(a) = ~a
    ----

    Description
    ----
    Bitwise NOT operation

    Inputs
    ----
    - a: binary value

    Outputs
    ----
    - ~a: the bitwise NOT result

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#19](https://www.evm.codes/#19)
    """

    BYTE = Opcode(0x1A, popped_stack_items=2, pushed_stack_items=1)
    """
    BYTE(i, x) = y
    ----

    Description
    ----
    Extract a byte from the given position in the value

    Inputs
    ----
    - i: byte offset starting from the most significant byte
    - x: 32-byte value

    Outputs
    ----
    - y: the indicated byte at the least significant position.
         If the byte offset is out of range, the result is 0

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#1A](https://www.evm.codes/#1A)
    """

    SHL = Opcode(0x1B, popped_stack_items=2, pushed_stack_items=1)
    """
    SHL(shift, value) = value << shift
    ----

    Description
    ----
    Shift left operation

    Inputs
    ----
    - shift: number of bits to shift to the left
    - value: 32 bytes to shift

    Outputs
    ----
    - value << shift: the shifted value. If shift is bigger than 255, returns 0

    Fork
    ----
    Constantinople

    Gas
    ----
    3

    Source: [evm.codes/#1B](https://www.evm.codes/#1B)
    """

    SHR = Opcode(0x1C, popped_stack_items=2, pushed_stack_items=1)
    """
    SHR(shift, value) = value >> shift
    ----

    Description
    ----
    Logical shift right operation

    Inputs
    ----
    - shift: number of bits to shift to the right.
    - value: 32 bytes to shift

    Outputs
    ----
    - value >> shift: the shifted value. If shift is bigger than 255, returns 0

    Fork
    ----
    Constantinople

    Gas
    ----
    3

    Source: [evm.codes/#1C](https://www.evm.codes/#1C)
    """

    SAR = Opcode(0x1D, popped_stack_items=2, pushed_stack_items=1)
    """
    SAR(shift, value) = value >> shift
    ----

    Description
    ----
    Arithmetic shift right operation

    Inputs
    ----
    - shift: number of bits to shift to the right
    - value: integer to shift

    Outputs
    ----
    - value >> shift: the shifted value

    Fork
    ----
    Constantinople

    Gas
    ----
    3

    Source: [evm.codes/#1D](https://www.evm.codes/#1D)
    """

    CLZ = Opcode(0x1E, popped_stack_items=1, pushed_stack_items=1)
    """
    CLZ(value) = count_leading_zeros(value)
    ----

    Description
    ----
    Counts leading zeros (bitwise).

    Inputs
    ----
    - value: integer to count zeros on

    Outputs
    ----
    - zeros: leading zero bits

    Fork
    ----
    Osaka

    Gas
    ----
    3

    Source: [evm.codes/#1E](https://www.evm.codes/#1E)
    """

    SHA3 = Opcode(
        0x20,
        popped_stack_items=2,
        pushed_stack_items=1,
        kwargs=["offset", "size"],
        metadata={"data_size": 0, "new_memory_size": 0, "old_memory_size": 0},
    )
    """
    SHA3(offset, size) = hash
    ----

    Description
    ----
    Compute Keccak-256 hash

    Inputs
    ----
    - offset: byte offset in the memory
    - size: byte size to read in the memory

    Outputs
    ----
    - hash: Keccak-256 hash of the given data in memory

    Fork
    ----
    Frontier

    Gas
    ----
    - minimum_word_size = (size + 31) / 32
    - static_gas = 30
    - dynamic_gas = 6 * minimum_word_size + memory_expansion_cost

    Metadata
    ----
    - data_size: number of bytes being hashed (default: 0)
    - new_memory_size: memory size after expansion in bytes (default: 0)
    - old_memory_size: memory size before expansion in bytes (default: 0)

    Source: [evm.codes/#20](https://www.evm.codes/#20)
    """

    ADDRESS = Opcode(0x30, pushed_stack_items=1)
    """
    ADDRESS() = address
    ----

    Description
    ----
    Get address of currently executing account

    Inputs
    ----
    - None

    Outputs
    ----
    - address: the 20-byte address of the current account

    Fork
    ----
    Frontier

    Gas
    ----
    2

    Source: [evm.codes/#30](https://www.evm.codes/#30)
    """

    BALANCE = Opcode(
        0x31,
        popped_stack_items=1,
        pushed_stack_items=1,
        kwargs=["address"],
        metadata={"address_warm": False},
    )
    """
    BALANCE(address) = balance
    ----

    Description
    ----
    Get the balance of the specified account

    Inputs
    ----
    - address: 20-byte address of the account to check

    Outputs
    ----
    - balance: balance of the given account in wei. Returns 0 if the
               account doesn't exist

    Fork
    ----
    Frontier

    Gas
    ----
    - static_gas = 0
    - dynamic_gas = 100 if warm_address, 2600 if cold_address

    Metadata
    ----
    - address_warm: whether the address is already warm (default: False)

    Source: [evm.codes/#31](https://www.evm.codes/#31)
    """

    ORIGIN = Opcode(0x32, pushed_stack_items=1)
    """
    ORIGIN() = address
    ----

    Description
    ----
    Get execution origination address

    Inputs
    ----
    - None

    Outputs
    ----
    - address: the 20-byte address of the sender of the transaction.
               It can only be an account without code

    Fork
    ----
    Frontier

    Gas
    ----
    2

    Source: [evm.codes/#32](https://www.evm.codes/#32)
    """

    CALLER = Opcode(0x33, pushed_stack_items=1)
    """
    CALLER() = address
    ----

    Description
    ----
    Get caller address

    Inputs
    ----
    - None

    Outputs
    ----
    - address: the 20-byte address of the caller account.
               This is the account that did the last
               call (except delegate call)

    Fork
    ----
    Frontier

    Gas
    ----
    2

    Source: [evm.codes/#33](https://www.evm.codes/#33)
    """

    CALLVALUE = Opcode(0x34, pushed_stack_items=1)
    """
    CALLVALUE() = value
    ----

    Description
    ----
    Get deposited value by the instruction/transaction responsible
    for this execution

    Inputs
    ----
    - None

    Outputs
    ----
    - value: the value of the current call in wei

    Fork
    ----
    Frontier

    Gas
    ----
    2

    Source: [evm.codes/#34](https://www.evm.codes/#34)
    """

    CALLDATALOAD = Opcode(
        0x35, popped_stack_items=1, pushed_stack_items=1, kwargs=["offset"]
    )
    """
    CALLDATALOAD(offset) = data[offset]
    ----

    Description
    ----
    Get input data of current environment

    Inputs
    ----
    - offset: byte offset in the calldata

    Outputs
    ----
    - data[offset]: 32-byte value starting from the given offset of
                    the calldata. All bytes after the end of the calldata
                    are set to 0

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#35](https://www.evm.codes/#35)
    """

    CALLDATASIZE = Opcode(0x36, pushed_stack_items=1)
    """
    CALLDATASIZE() = size
    ----

    Description
    ----
    Get size of input data in current environment

    Inputs
    ----
    - None

    Outputs
    ----
    - size: byte size of the calldata

    Fork
    ----
    Frontier

    Gas
    ----
    2

    Source: [evm.codes/#36](https://www.evm.codes/#36)
    """

    CALLDATACOPY = Opcode(
        0x37,
        popped_stack_items=3,
        kwargs=["dest_offset", "offset", "size"],
        metadata={"data_size": 0, "new_memory_size": 0, "old_memory_size": 0},
    )
    """
    CALLDATACOPY(dest_offset, offset, size)
    ----

    Description
    ----
    Copy input data in current environment to memory

    Inputs
    ----
    - dest_offset: byte offset in the memory where the result will be copied
    - offset: byte offset in the calldata to copy
    - size: byte size to copy

    Outputs
    ----
    - None

    Fork
    ----
    Frontier

    Gas
    ----
    - minimum_word_size = (size + 31) / 32
    - static_gas = 3
    - dynamic_gas = 3 * minimum_word_size + memory_expansion_cost

    Metadata
    ----
    - data_size: number of bytes being copied (default: 0)
    - new_memory_size: memory size after expansion in bytes (default: 0)
    - old_memory_size: memory size before expansion in bytes (default: 0)

    Source: [evm.codes/#37](https://www.evm.codes/#37)
    """

    CODESIZE = Opcode(0x38, pushed_stack_items=1)
    """
    CODESIZE() = size
    ----

    Description
    ----
    Get size of code running in current environment

    Inputs
    ----
    - None

    Outputs
    ----
    - size: byte size of the code

    Fork
    ----
    Frontier

    Gas
    ----
    2

    Source: [evm.codes/#38](https://www.evm.codes/#38)
    """

    CODECOPY = Opcode(
        0x39,
        popped_stack_items=3,
        kwargs=["dest_offset", "offset", "size"],
        metadata={"data_size": 0, "new_memory_size": 0, "old_memory_size": 0},
    )
    """
    CODECOPY(dest_offset, offset, size)
    ----

    Description
    ----
    Copy code running in current environment to memory

    Inputs
    ----
    - dest_offset: byte offset in the memory where the result will be copied.
    - offset: byte offset in the code to copy.
    - size: byte size to copy

    Fork
    ----
    Frontier

    Gas
    ----
    - minimum_word_size = (size + 31) / 32
    - static_gas = 3
    - dynamic_gas = 3 * minimum_word_size + memory_expansion_cost

    Metadata
    ----
    - data_size: number of bytes being copied (default: 0)
    - new_memory_size: memory size after expansion in bytes (default: 0)
    - old_memory_size: memory size before expansion in bytes (default: 0)

    Source: [evm.codes/#39](https://www.evm.codes/#39)
    """

    GASPRICE = Opcode(0x3A, pushed_stack_items=1)
    """
    GASPRICE() = price
    ----

    Description
    ----
    Get price of gas in current environment

    Outputs
    ----
    - price: gas price in wei per gas

    Fork
    ----
    Frontier

    Gas
    ----
    2

    Source: [evm.codes/#3A](https://www.evm.codes/#3A)
    """

    EXTCODESIZE = Opcode(
        0x3B,
        popped_stack_items=1,
        pushed_stack_items=1,
        kwargs=["address"],
        metadata={"address_warm": False},
    )
    """
    EXTCODESIZE(address) = size
    ----

    Description
    ----
    Get size of an account's code

    Inputs
    ----
    - address: 20-byte address of the contract to query

    Outputs
    ----
    - size: byte size of the code

    Fork
    ----
    Frontier

    Gas
    ----
    - static_gas = 0
    - dynamic_gas = 100 if warm_address, 2600 if cold_address

    Metadata
    ----
    - address_warm: whether the address is already warm (default: False)

    Source: [evm.codes/#3B](https://www.evm.codes/#3B)
    """

    EXTCODECOPY = Opcode(
        0x3C,
        popped_stack_items=4,
        kwargs=["address", "dest_offset", "offset", "size"],
        metadata={
            "address_warm": False,
            "data_size": 0,
            "new_memory_size": 0,
            "old_memory_size": 0,
        },
    )
    """
    EXTCODECOPY(address, dest_offset, offset, size)
    ----

    Description
    ----
    Copy an account's code to memory

    Inputs
    ----
    - address: 20-byte address of the contract to query
    - dest_offset: byte offset in the memory where the result will be copied
    - offset: byte offset in the code to copy
    - size: byte size to copy

    Outputs
    ----
    - None

    Fork
    ----
    Frontier

    Gas
    ----
    - minimum_word_size = (size + 31) / 32
    - static_gas = 0
    - dynamic_gas = 3 * minimum_word_size +
                    memory_expansion_cost + address_access_cost

    Metadata
    ----
    - address_warm: whether the address is already warm (default: False)
    - data_size: number of bytes being copied (default: 0)
    - new_memory_size: memory size after expansion in bytes (default: 0)
    - old_memory_size: memory size before expansion in bytes (default: 0)

    Source: [evm.codes/#3C](https://www.evm.codes/#3C)
    """

    RETURNDATASIZE = Opcode(0x3D, pushed_stack_items=1)
    """
    RETURNDATASIZE() = size
    ----

    Description
    ----
    Get size of output data from the previous call from the current environment

    Outputs
    ----
    - size: byte size of the return data from the last executed sub context

    Fork
    ----
    Byzantium

    Gas
    ----
    2

    Source: [evm.codes/#3D](https://www.evm.codes/#3D)
    """

    RETURNDATACOPY = Opcode(
        0x3E,
        popped_stack_items=3,
        kwargs=["dest_offset", "offset", "size"],
        metadata={"data_size": 0, "new_memory_size": 0, "old_memory_size": 0},
    )
    """
    RETURNDATACOPY(dest_offset, offset, size)
    ----

    Description
    ----
    Copy output data from the previous call to memory

    Inputs
    ----
    - dest_offset: byte offset in the memory where the result will be copied
    - offset: byte offset in the return data from the last
              executed sub context to copy
    - size: byte size to copy

    Fork
    ----
    Byzantium

    Gas
    ----
    - minimum_word_size = (size + 31) / 32
    - static_gas = 3
    - dynamic_gas = 3 * minimum_word_size + memory_expansion_cost

    Metadata
    ----
    - data_size: number of bytes being copied (default: 0)
    - new_memory_size: memory size after expansion in bytes (default: 0)
    - old_memory_size: memory size before expansion in bytes (default: 0)

    Source: [evm.codes/#3E](https://www.evm.codes/#3E)
    """

    EXTCODEHASH = Opcode(
        0x3F,
        popped_stack_items=1,
        pushed_stack_items=1,
        kwargs=["address"],
        metadata={"address_warm": False},
    )
    """
    EXTCODEHASH(address) = hash
    ----

    Description
    ----
    Get hash of an account's code

    Inputs
    ----
    - address: 20-byte address of the account

    Outputs
    ----
    - hash: hash of the chosen account's code, the empty hash (0xc5d24601...)
            if the account has no code, or 0 if the account does not exist or
            has been destroyed

    Fork
    ----
    Constantinople

    Gas
    ----
    - static_gas = 0
    - dynamic_gas = 100 if warm_address, 2600 if cold_address

    Metadata
    ----
    - address_warm: whether the address is already warm (default: False)

    Source: [evm.codes/#3F](https://www.evm.codes/#3F)
    """

    BLOCKHASH = Opcode(
        0x40,
        popped_stack_items=1,
        pushed_stack_items=1,
        kwargs=["block_number"],
    )
    """
    BLOCKHASH(block_number) = hash
    ----

    Description
    ----
    Get the hash of one of the 256 most recent complete blocks

    Inputs
    ----
    - blockNumber: block number to get the hash from. Valid range is the
                   last 256 blocks (not including the current one). Current
                   block number can be queried with NUMBER

    Outputs
    ----
    - hash: hash of the chosen block, or 0 if the block number is not
            in the valid range

    Fork
    ----
    Frontier

    Gas
    ----
    20

    Source: [evm.codes/#40](https://www.evm.codes/#40)
    """

    COINBASE = Opcode(0x41, pushed_stack_items=1)
    """
    COINBASE() = address
    ----

    Description
    ----
    Get the block's beneficiary address

    Inputs
    ----
    - None

    Outputs
    ----
    - address: miner's 20-byte address

    Fork
    ----
    Frontier

    Gas
    ----
    2

    Source: [evm.codes/#41](https://www.evm.codes/#41)
    """

    TIMESTAMP = Opcode(0x42, pushed_stack_items=1)
    """
    TIMESTAMP() = timestamp
    ----

    Description
    ----
    Get the block's timestamp

    Inputs
    ----
    - None

    Outputs
    ----
    - timestamp: unix timestamp of the current block

    Fork
    ----
    Frontier

    Gas
    ----
    2

    Source: [evm.codes/#42](https://www.evm.codes/#42)
    """

    NUMBER = Opcode(0x43, pushed_stack_items=1)
    """
    NUMBER() = blockNumber
    ----

    Description
    ----
    Get the block's number

    Inputs
    ----
    - None

    Outputs
    ----
    - blockNumber: current block number

    Fork
    ----
    Frontier

    Gas
    ----
    2

    Source: [evm.codes/#43](https://www.evm.codes/#43)
    """

    PREVRANDAO = Opcode(0x44, pushed_stack_items=1)
    """
    PREVRANDAO() = prevRandao
    ----

    Description
    ----
    Get the previous block's RANDAO mix

    Inputs
    ----
    - None

    Outputs
    ----
    - prevRandao: previous block's RANDAO mix

    Fork
    ----
    Merge

    Gas
    ----
    2

    Source: [evm.codes/#44](https://www.evm.codes/#44)
    """

    GASLIMIT = Opcode(0x45, pushed_stack_items=1)
    """
    GASLIMIT() = gasLimit
    ----

    Description
    ----
    Get the block's gas limit

    Inputs
    ----
    - None

    Outputs
    ----
    - gasLimit: gas limit

    Fork
    ----
    Frontier

    Gas
    ----
    2

    Source: [evm.codes/#45](https://www.evm.codes/#45)
    """

    CHAINID = Opcode(0x46, pushed_stack_items=1)
    """
    CHAINID() = chainId
    ----

    Description
    ----
    Get the chain ID

    Inputs
    ----
    - None

    Outputs
    ----
    - chainId: chain id of the network

    Fork
    ----
    Istanbul

    Gas
    ----
    2

    Source: [evm.codes/#46](https://www.evm.codes/#46)
    """

    SELFBALANCE = Opcode(0x47, pushed_stack_items=1)
    """
    SELFBALANCE() = balance
    ----

    Description
    ----
    Get balance of currently executing account

    Inputs
    ----
    - None

    Outputs
    ----
    - balance: balance of the current account in wei

    Fork
    ----
    Istanbul

    Gas
    ----
    5

    Source: [evm.codes/#47](https://www.evm.codes/#47)
    """

    BASEFEE = Opcode(0x48, pushed_stack_items=1)
    """
    BASEFEE() = baseFee
    ----

    Description
    ----
    Get the base fee

    Outputs
    ----
    - baseFee: base fee in wei

    Fork
    ----
    London

    Gas
    ----
    2

    Source: [evm.codes/#48](https://www.evm.codes/#48)
    """

    BLOBHASH = Opcode(
        0x49, popped_stack_items=1, pushed_stack_items=1, kwargs=["index"]
    )
    """
    BLOBHASH(index) = versionedHash
    ----

    Description
    ----
    Returns the versioned hash of a single blob contained in
    the type-3 transaction

    Inputs
    ----
    - index: index of the blob

    Outputs
    ----
    - versionedHash: versioned hash of the blob

    Fork
    ----
    Cancun

    Gas
    ----
    3

    Source: [EIP-4844](https://eips.ethereum.org/EIPS/eip-4844)
    """

    BLOBBASEFEE = Opcode(0x4A, popped_stack_items=0, pushed_stack_items=1)
    """
    BLOBBASEFEE() = fee
    ----

    Description
    ----
    Returns the value of the blob base fee of the block it is executing in

    Inputs
    ----
    - None

    Outputs
    ----
    - baseFeePerBlobGas: base fee for the blob gas in wei

    Fork
    ----
    Cancun

    Gas
    ----
    2

    Source: [EIP-7516](https://eips.ethereum.org/EIPS/eip-7516)
    """

    POP = Opcode(0x50, popped_stack_items=1)
    """
    POP()
    ----

    Description
    ----
    Remove item from stack

    Inputs
    ----
    - None

    Outputs
    ----
    - None

    Fork
    ----
    Frontier

    Gas
    ----
    2

    Source: [evm.codes/#50](https://www.evm.codes/#50)
    """

    MLOAD = Opcode(
        0x51,
        popped_stack_items=1,
        pushed_stack_items=1,
        kwargs=["offset"],
        metadata={"new_memory_size": 0, "old_memory_size": 0},
    )
    """
    MLOAD(offset) = value
    ----

    Description
    ----
    Load word from memory

    Inputs
    ----
    - offset: offset in the memory in bytes

    Outputs
    ----
    - value: the 32 bytes in memory starting at that offset.
    If it goes beyond its current size (see MSIZE), writes 0s

    Fork
    ----
    Frontier

    Gas
    ----
    - static_gas = 3
    - dynamic_gas = memory_expansion_cost

    Metadata
    ----
    - new_memory_size: memory size after expansion in bytes (default: 0)
    - old_memory_size: memory size before expansion in bytes (default: 0)

    Source: [evm.codes/#51](https://www.evm.codes/#51)
    """

    MSTORE = Opcode(
        0x52,
        popped_stack_items=2,
        kwargs=["offset", "value"],
        metadata={"new_memory_size": 0, "old_memory_size": 0},
    )
    """
    MSTORE(offset, value)
    ----

    Description
    ----
    Save word to memory

    Inputs
    ----
    - offset: offset in the memory in bytes
    - value: 32-byte value to write in the memory

    Outputs
    ----
    - None

    Fork
    ----
    Frontier

    Gas
    ----
    - static_gas = 3
    - dynamic_gas = memory_expansion_cost

    Metadata
    ----
    - new_memory_size: memory size after expansion in bytes (default: 0)
    - old_memory_size: memory size before expansion in bytes (default: 0)

    Source: [evm.codes/#52](https://www.evm.codes/#52)
    """

    MSTORE8 = Opcode(
        0x53,
        popped_stack_items=2,
        kwargs=["offset", "value"],
        metadata={"new_memory_size": 0, "old_memory_size": 0},
    )
    """
    MSTORE8(offset, value)
    ----

    Description
    ----
    Save byte to memory

    Inputs
    ----
    - offset: offset in the memory in bytes
    - value: 1-byte value to write in the memory (the least significant
             byte of the 32-byte stack value)

    Fork
    ----
    Frontier

    Gas
    ----
    - static_gas = 3
    - dynamic_gas = memory_expansion_cost

    Metadata
    ----
    - new_memory_size: memory size after expansion in bytes (default: 0)
    - old_memory_size: memory size before expansion in bytes (default: 0)

    Source: [evm.codes/#53](https://www.evm.codes/#53)
    """

    SLOAD = Opcode(
        0x54,
        popped_stack_items=1,
        pushed_stack_items=1,
        kwargs=["key"],
        metadata={"key_warm": False},
    )
    """
    SLOAD(key) = value
    ----

    Description
    ----
    Load word from storage

    Inputs
    ----
    - key: 32-byte key in storage

    Outputs
    ----
    - value: 32-byte value corresponding to that key. 0 if that
             key was never written before

    Fork
    ----
    Frontier

    Gas
    ----
    - static_gas = 0
    - dynamic_gas = 100 if warm_address, 2600 if cold_address

    Metadata
    ----
    - key_warm: whether the storage key is already warm (default: False)

    Source: [evm.codes/#54](https://www.evm.codes/#54)
    """

    SSTORE = Opcode(
        0x55,
        popped_stack_items=2,
        kwargs=["key", "value"],
        metadata={
            "key_warm": False,
            "original_value": 0,
            "current_value": None,
            "new_value": 1,
        },
    )
    """
    SSTORE(key, value)
    ----

    Description
    ----
    Save word to storage

    Inputs
    ----
    - key: 32-byte key in storage
    - value: 32-byte value to store

    Outputs
    ----
    - None

    Fork
    ----
    Frontier

    Gas
    ----
    ```
    static_gas = 0

    if value == current_value
        if key is warm
            base_dynamic_gas = 100
        else
            base_dynamic_gas = 100
    else if current_value == original_value
        if original_value == 0
            base_dynamic_gas = 20000
        else
            base_dynamic_gas = 2900
    else
        base_dynamic_gas = 100

    if key is cold:
        base_dynamic_gas += 2100
    ```

    Metadata
    ----
    - key_warm: whether the key had already been accessed during the
        transaction, either by SLOAD or SSTORE (default: False)
    - original_value: value the storage key had at the beginning of
        the transaction (default: 0)
    - current_value: value the storage key holds at the execution
        of the opcode (default: None, which means same as original_value)
    - new_value: value being set by the opcode (default: 1)

    Source: [evm.codes/#55](https://www.evm.codes/#55)
    """

    JUMP = Opcode(0x56, popped_stack_items=1, kwargs=["pc"])
    """
    JUMP(pc)
    ----

    Description
    ----
    Alter the program counter

    Inputs
    ----
    - pc: byte offset in the deployed code where execution will continue from.
          Must be a JUMPDEST instruction

    Outputs
    ----
    - None

    Fork
    ----
    Frontier

    Gas
    ----
    8

    Source: [evm.codes/#56](https://www.evm.codes/#56)
    """

    JUMPI = Opcode(0x57, popped_stack_items=2, kwargs=["pc", "condition"])
    """
    JUMPI(pc, condition)
    ----

    Description
    ----
    Conditionally alter the program counter

    Inputs
    ----
    - pc: byte offset in the deployed code where execution will continue from.
          Must be a JUMPDEST instruction
    - condition: the program counter will be altered with the new value only
                 if this value is different from 0. Otherwise, the program
                 counter is simply incremented and the next instruction
                 will be executed

    Fork
    ----
    Frontier

    Gas
    ----
    10

    Source: [evm.codes/#57](https://www.evm.codes/#57)
    """

    PC = Opcode(0x58, pushed_stack_items=1)
    """
    PC() = counter
    ----

    Description
    ----
    Get the value of the program counter prior to the increment corresponding
    to this instruction

    Inputs
    ----
    - None

    Outputs
    ----
    - counter: PC of this instruction in the current program.

    Fork
    ----
    Frontier

    Gas
    ----
    2

    Source: [evm.codes/#58](https://www.evm.codes/#58)
    """

    MSIZE = Opcode(0x59, pushed_stack_items=1)
    """
    MSIZE() = size
    ----

    Description
    ----
    Get the size of active memory in bytes

    Outputs
    ----
    - size: current memory size in bytes (higher offset accessed until now + 1)

    Fork
    ----
    Frontier

    Gas
    ----
    2

    Source: [evm.codes/#59](https://www.evm.codes/#59)
    """

    GAS = Opcode(0x5A, pushed_stack_items=1)
    """
    GAS() = gas_remaining
    ----

    Description
    ----
    Get the amount of available gas, including the corresponding reduction
    for the cost of this instruction

    Inputs
    ----
    - None

    Outputs
    ----
    - gas: remaining gas (after this instruction)

    Fork
    ----
    Frontier

    Gas
    ----
    2

    Source: [evm.codes/#5A](https://www.evm.codes/#5A)
    """

    JUMPDEST = Opcode(0x5B)
    """
    JUMPDEST()
    ----

    Description
    ----
    Mark a valid destination for jumps

    Inputs
    ----
    - None

    Outputs
    ----
    - None

    Fork
    ----
    Frontier

    Gas
    ----
    1

    Source: [evm.codes/#5B](https://www.evm.codes/#5B)
    """

    NOOP = Opcode(0x5B)
    """
    NOOP()
    ----

    Description
    ----
    Synonym for JUMPDEST. Performs no operation.

    Inputs
    ----
    - None

    Outputs
    ----
    - None

    Fork
    ----
    Frontier

    Gas
    ----
    1

    Source: [evm.codes/#5B](https://www.evm.codes/#5B)
    """

    TLOAD = Opcode(
        0x5C, popped_stack_items=1, pushed_stack_items=1, kwargs=["key"]
    )
    """
    TLOAD(key) = value
    ----

    Description
    ----
    Load word from transient storage

    Inputs
    ----
    - key: 32-byte key in transient storage

    Outputs
    ----
    - value: 32-byte value corresponding to that key. 0 if that key
             was never written

    Fork
    ----
    Cancun

    Gas
    ----
    100

    Source: [eips.ethereum.org/EIPS/eip-1153](https://eips.ethereum.org/EIPS/eip-1153)
    """

    TSTORE = Opcode(0x5D, popped_stack_items=2, kwargs=["key", "value"])
    """
    TSTORE(key, value)
    ----

    Description
    ----
    Save word to transient storage

    Inputs
    ----
    - key: 32-byte key in transient storage
    - value: 32-byte value to store

    Fork
    ----
    Cancun

    Gas
    ----
    100

    Source: [EIP-1153](https://eips.ethereum.org/EIPS/eip-1153)
    """

    MCOPY = Opcode(
        0x5E,
        popped_stack_items=3,
        kwargs=["dest_offset", "offset", "size"],
        metadata={"data_size": 0, "new_memory_size": 0, "old_memory_size": 0},
    )
    """
    MCOPY(dest_offset, offset, size)
    ----

    Description
    ----
    Copies areas in memory

    Inputs
    ----
    - dest_offset: byte offset in the memory where the result will be copied
    - offset: byte offset in the calldata to copy
    - size: byte size to copy

    Outputs
    ----
    - None

    Fork
    ----
    Cancun

    Gas
    ----
    - minimum_word_size = (size + 31) / 32
    - static_gas = 3
    - dynamic_gas = 3 * minimum_word_size + memory_expansion_cost

    Metadata
    ----
    - data_size: number of bytes being copied (default: 0)
    - new_memory_size: memory size after expansion in bytes (default: 0)
    - old_memory_size: memory size before expansion in bytes (default: 0)

    Source: [EIP-5656](https://eips.ethereum.org/EIPS/eip-5656)
    """

    PUSH0 = Opcode(0x5F, pushed_stack_items=1)
    """
    PUSH0() = value
    ----

    Description
    ----
    Place value 0 on stack

    Inputs
    ----
    - None

    Outputs
    ----
    - value: pushed value, equal to 0

    Fork
    ----
    Shanghai

    Gas
    ----
    2

    Source: [evm.codes/#5F](https://www.evm.codes/#5F)
    """

    PUSH1 = Opcode(0x60, pushed_stack_items=1, data_portion_length=1)
    """
    PUSH1() = value
    ----

    Description
    ----
    Place 1 byte item on stack

    Inputs
    ----
    - None

    Outputs
    ----
    - value: pushed value, aligned to the right (put in the
             lowest significant bytes)

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#60](https://www.evm.codes/#60)
    """

    PUSH2 = Opcode(0x61, pushed_stack_items=1, data_portion_length=2)
    """
    PUSH2() = value
    ----

    Description
    ----
    Place 2 byte item on stack

    Inputs
    ----
    - None

    Outputs
    ----
    - value: pushed value, aligned to the right (put in the lowest
             significant bytes)

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#61](https://www.evm.codes/#61)
    """

    PUSH3 = Opcode(0x62, pushed_stack_items=1, data_portion_length=3)
    """
    PUSH3() = value
    ----

    Description
    ----
    Place 3 byte item on stack

    Inputs
    ----
    - None

    Outputs
    ----
    - value: pushed value, aligned to the right (put in the
             lowest significant bytes)

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#62](https://www.evm.codes/#62)
    """

    PUSH4 = Opcode(0x63, pushed_stack_items=1, data_portion_length=4)
    """
    PUSH4() = value
    ----

    Description
    ----
    Place 4 byte item on stack

    Inputs
    ----
    - None

    Outputs
    ----
    - value: pushed value, aligned to the right (put in the lowest
             significant bytes)

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#63](https://www.evm.codes/#63)
    """

    PUSH5 = Opcode(0x64, pushed_stack_items=1, data_portion_length=5)
    """
    PUSH5() = value
    ----

    Description
    ----
    Place 5 byte item on stack

    Inputs
    ----
    - None

    Outputs
    ----
    - value: pushed value, aligned to the right (put in the lowest
             significant bytes)

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#64](https://www.evm.codes/#64)
    """

    PUSH6 = Opcode(0x65, pushed_stack_items=1, data_portion_length=6)
    """
    PUSH6() = value
    ----

    Description
    ----
    Place 6 byte item on stack

    Inputs
    ----
    - None

    Outputs
    ----
    - value: pushed value, aligned to the right (put in the
             lowest significant bytes)

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#65](https://www.evm.codes/#65)
    """

    PUSH7 = Opcode(0x66, pushed_stack_items=1, data_portion_length=7)
    """
    PUSH7() = value
    ----

    Description
    ----
    Place 7 byte item on stack

    Inputs
    ----
    - None

    Outputs
    ----
    - value: pushed value, aligned to the right (put in the
             lowest significant bytes)

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#66](https://www.evm.codes/#66)
    """

    PUSH8 = Opcode(0x67, pushed_stack_items=1, data_portion_length=8)
    """
    PUSH8() = value
    ----

    Description
    ----
    Place 8 byte item on stack

    Inputs
    ----
    - None

    Outputs
    ----
    - value: pushed value, aligned to the right (put in the
             lowest significant bytes)

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#67](https://www.evm.codes/#67)
    """

    PUSH9 = Opcode(0x68, pushed_stack_items=1, data_portion_length=9)
    """
    PUSH9() = value
    ----

    Description
    ----
    Place 9 byte item on stack

    Inputs
    ----
    - None

    Outputs
    ----
    - value: pushed value, aligned to the right (put in the
             lowest significant bytes)

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#68](https://www.evm.codes/#68)
    """

    PUSH10 = Opcode(0x69, pushed_stack_items=1, data_portion_length=10)
    """
    PUSH10() = value
    ----

    Description
    ----
    Place 10 byte item on stack

    Inputs
    ----
    - None

    Outputs
    ----
    - value: pushed value, aligned to the right (put in
             the lowest significant bytes)

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#69](https://www.evm.codes/#69)
    """

    PUSH11 = Opcode(0x6A, pushed_stack_items=1, data_portion_length=11)
    """
    PUSH11() = value
    ----

    Description
    ----
    Place 11 byte item on stack

    Inputs
    ----
    - None

    Outputs
    ----
    - value: pushed value, aligned to the right (put in
             the lowest significant bytes)

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#6A](https://www.evm.codes/#6A)
    """

    PUSH12 = Opcode(0x6B, pushed_stack_items=1, data_portion_length=12)
    """
    PUSH12() = value
    ----

    Description
    ----
    Place 12 byte item on stack

    Inputs
    ----
    - None

    Outputs
    ----
    - value: pushed value, aligned to the right (put in the
             lowest significant bytes)

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#6B](https://www.evm.codes/#6B)
    """

    PUSH13 = Opcode(0x6C, pushed_stack_items=1, data_portion_length=13)
    """
    PUSH13() = value
    ----

    Description
    ----
    Place 13 byte item on stack

    Inputs
    ----
    - None

    Outputs
    ----
    - value: pushed value, aligned to the right (put in
             the lowest significant bytes)

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#6C](https://www.evm.codes/#6C)
    """

    PUSH14 = Opcode(0x6D, pushed_stack_items=1, data_portion_length=14)
    """
    PUSH14() = value
    ----

    Description
    ----
    Place 14 byte item on stack

    Inputs
    ----
    - None

    Outputs
    ----
    - value: pushed value, aligned to the right (put in
             the lowest significant bytes)

    Fork
    ----
    Frontier


    Gas
    ----
    3

    Source: [evm.codes/#6D](https://www.evm.codes/#6D)
    """

    PUSH15 = Opcode(0x6E, pushed_stack_items=1, data_portion_length=15)
    """
    PUSH15() = value
    ----

    Description
    ----
    Place 15 byte item on stack

    Inputs
    ----
    - None

    Outputs
    ----
    - value: pushed value, aligned to the right (put in
             the lowest significant bytes)

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#6E](https://www.evm.codes/#6E)
    """

    PUSH16 = Opcode(0x6F, pushed_stack_items=1, data_portion_length=16)
    """
    PUSH16() = value
    ----

    Description
    ----
    Place 16 byte item on stack

    Inputs
    ----
    - None

    Outputs
    ----
    - value: pushed value, aligned to the right (put in
             the lowest significant bytes)

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#6F](https://www.evm.codes/#6F)
    """

    PUSH17 = Opcode(0x70, pushed_stack_items=1, data_portion_length=17)
    """
    PUSH17() = value
    ----

    Description
    ----
    Place 17 byte item on stack

    Inputs
    ----
    - None

    Outputs
    ----
    - value: pushed value, aligned to the right (put in
             the lowest significant bytes)

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#70](https://www.evm.codes/#70)
    """

    PUSH18 = Opcode(0x71, pushed_stack_items=1, data_portion_length=18)
    """
    PUSH18() = value
    ----

    Description
    ----
    Place 18 byte item on stack

    Inputs
    ----
    - None

    Outputs
    ----
    - value: pushed value, aligned to the right (put in
             the lowest significant bytes)

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#71](https://www.evm.codes/#71)
    """

    PUSH19 = Opcode(0x72, pushed_stack_items=1, data_portion_length=19)
    """
    PUSH19() = value
    ----

    Description
    ----
    Place 19 byte item on stack

    Inputs
    ----
    - None

    Outputs
    ----
    - value: pushed value, aligned to the right (put in
             the lowest significant bytes)

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#72](https://www.evm.codes/#72)
    """

    PUSH20 = Opcode(0x73, pushed_stack_items=1, data_portion_length=20)
    """
    PUSH20() = value
    ----

    Description
    ----
    Place 20 byte item on stack

    Inputs
    ----
    - None

    Outputs
    ----
    - value: pushed value, aligned to the right (put in
             the lowest significant bytes)

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#73](https://www.evm.codes/#73)
    """

    PUSH21 = Opcode(0x74, pushed_stack_items=1, data_portion_length=21)
    """
    PUSH21() = value
    ----

    Description
    ----
    Place 21 byte item on stack

    Inputs
    ----
    - None

    Outputs
    ----
    - value: pushed value, aligned to the right (put in
             the lowest significant bytes)

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#74](https://www.evm.codes/#74)
    """

    PUSH22 = Opcode(0x75, pushed_stack_items=1, data_portion_length=22)
    """
    PUSH22() = value
    ----

    Description
    ----
    Place 22 byte item on stack

    Inputs
    ----
    - None

    Outputs
    ----
    - value: pushed value, aligned to the right (put in
             the lowest significant bytes)

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#75](https://www.evm.codes/#75)
    """

    PUSH23 = Opcode(0x76, pushed_stack_items=1, data_portion_length=23)
    """
    PUSH23() = value
    ----

    Description
    ----
    Place 23 byte item on stack

    Inputs
    ----
    - None

    Outputs
    ----
    - value: pushed value, aligned to the right (put in
             the lowest significant bytes)

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#76](https://www.evm.codes/#76)
    """

    PUSH24 = Opcode(0x77, pushed_stack_items=1, data_portion_length=24)
    """
    PUSH24() = value
    ----

    Description
    ----
    Place 24 byte item on stack

    Inputs
    ----
    - None

    Outputs
    ----
    - value: pushed value, aligned to the right (put in
             the lowest significant bytes)

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#77](https://www.evm.codes/#77)
    """

    PUSH25 = Opcode(0x78, pushed_stack_items=1, data_portion_length=25)
    """
    PUSH25() = value
    ----

    Description
    ----
    Place 25 byte item on stack

    Inputs
    ----
    - None

    Outputs
    ----
    - value: pushed value, aligned to the right (put in
             the lowest significant bytes)

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#78](https://www.evm.codes/#78)
    """

    PUSH26 = Opcode(0x79, pushed_stack_items=1, data_portion_length=26)
    """
    PUSH26() = value
    ----

    Description
    ----
    Place 26 byte item on stack

    Inputs
    ----
    - None

    Outputs
    ----
    - value: pushed value, aligned to the right (put in
             the lowest significant bytes)

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#79](https://www.evm.codes/#79)
    """

    PUSH27 = Opcode(0x7A, pushed_stack_items=1, data_portion_length=27)
    """
    PUSH27() = value
    ----

    Description
    ----
    Place 27 byte item on stack

    Inputs
    ----
    - None

    Outputs
    ----
    - value: pushed value, aligned to the right (put in
             the lowest significant bytes)

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#7A](https://www.evm.codes/#7A)
    """

    PUSH28 = Opcode(0x7B, pushed_stack_items=1, data_portion_length=28)
    """
    PUSH28() = value
    ----

    Description
    ----
    Place 28 byte item on stack

    Inputs
    ----
    - None

    Outputs
    ----
    - value: pushed value, aligned to the right (put in
             the lowest significant bytes)

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#7B](https://www.evm.codes/#7B)
    """

    PUSH29 = Opcode(0x7C, pushed_stack_items=1, data_portion_length=29)
    """
    PUSH29() = value
    ----

    Description
    ----
    Place 29 byte item on stack

    Inputs
    ----
    - None

    Outputs
    ----
    - value: pushed value, aligned to the right (put in
             the lowest significant bytes)

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#7C](https://www.evm.codes/#7C)
    """

    PUSH30 = Opcode(0x7D, pushed_stack_items=1, data_portion_length=30)
    """
    PUSH30() = value
    ----

    Description
    ----
    Place 30 byte item on stack

    Inputs
    ----
    - None

    Outputs
    ----
    - value: pushed value, aligned to the right (put in
             the lowest significant bytes)

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#7D](https://www.evm.codes/#7D)
    """

    PUSH31 = Opcode(0x7E, pushed_stack_items=1, data_portion_length=31)
    """
    PUSH31() = value
    ----

    Description
    ----
    Place 31 byte item on stack

    Inputs
    ----
    - None

    Outputs
    ----
    - value: pushed value, aligned to the right (put in
             the lowest significant bytes)

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#7E](https://www.evm.codes/#7E)
    """

    PUSH32 = Opcode(0x7F, pushed_stack_items=1, data_portion_length=32)
    """
    PUSH32() = value
    ----

    Description
    ----
    Place 32 byte item on stack

    Inputs
    ----
    - None

    Outputs
    ----
    - value: pushed value, aligned to the right (put in
             the lowest significant bytes)

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#7F](https://www.evm.codes/#7F)
    """

    DUP1 = Opcode(0x80, pushed_stack_items=1, min_stack_height=1)
    """
    DUP1(value) = value, value
    ----

    Description
    ----
    Duplicate 1st stack item

    Inputs
    ----
    - value: value to duplicate

    Outputs
    ----
    - value: duplicated value
    - value: original value

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#80](https://www.evm.codes/#80)
    """

    DUP2 = Opcode(0x81, pushed_stack_items=1, min_stack_height=2)
    """
    DUP2(v1, v2) = v2, v1, v2
    ----

    Description
    ----
    Duplicate 2nd stack item

    Inputs
    ----
    - v1: ignored value
    - v2: value to duplicate

    Outputs
    ----
    - v2: duplicated value
    - v1: ignored value
    - v2: original value

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#81](https://www.evm.codes/#81)
    """

    DUP3 = Opcode(0x82, pushed_stack_items=1, min_stack_height=3)
    """
    DUP3(v1, v2, v3) = v3, v1, v2, v3
    ----

    Description
    ----
    Duplicate 3rd stack item

    Inputs
    ----
    - v1: ignored value
    - v2: ignored value
    - v3: value to duplicate

    Outputs
    ----
    - v3: duplicated value
    - v1: ignored value
    - v2: ignored value
    - v3: original value

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#82](https://www.evm.codes/#82)
    """

    DUP4 = Opcode(0x83, pushed_stack_items=1, min_stack_height=4)
    """
    DUP4(v1, v2, v3, v4) = v4, v1, v2, v3, v4
    ----

    Description
    ----
    Duplicate 4th stack item

    Inputs
    ----
    - v1: ignored value
    - v2: ignored value
    - v3: ignored value
    - v4: value to duplicate

    Outputs
    ----
    - v4: duplicated value
    - v1: ignored value
    - v2: ignored value
    - v3: ignored value
    - v4: original value

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#83](https://www.evm.codes/#83)
    """

    DUP5 = Opcode(0x84, pushed_stack_items=1, min_stack_height=5)
    """
    DUP5(v1, v2, v3, v4, v5) = v5, v1, v2, v3, v4, v5
    ----

    Description
    ----
    Duplicate 5th stack item

    Inputs
    ----
    - v1: ignored value
    - v2: ignored value
    - v3: ignored value
    - v4: ignored value
    - v5: value to duplicate

    Outputs
    ----
    - v5: duplicated value
    - v1: ignored value
    - v2: ignored value
    - v3: ignored value
    - v4: ignored value
    - v5: original value

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#84](https://www.evm.codes/#84)
    """

    DUP6 = Opcode(0x85, pushed_stack_items=1, min_stack_height=6)
    """
    DUP6(v1, v2, ..., v5, v6) = v6, v1, v2, ..., v5, v6
    ----

    Description
    ----
    Duplicate 6th stack item

    Inputs
    ----
    - v1: ignored value
    - v2: ignored value
    - ...
    - v5: ignored value
    - v6: value to duplicate

    Outputs
    ----
    - v6: duplicated value
    - v1: ignored value
    - v2: ignored value
    - ...
    - v5: ignored value
    - v6: original value

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#85](https://www.evm.codes/#85)
    """

    DUP7 = Opcode(0x86, pushed_stack_items=1, min_stack_height=7)
    """
    DUP7(v1, v2, ..., v6, v7) = v7, v1, v2, ..., v6, v7
    ----

    Description
    ----
    Duplicate 7th stack item

    Inputs
    ----
    - v1: ignored value
    - v2: ignored value
    - ...
    - v6: ignored value
    - v7: value to duplicate

    Outputs
    ----
    - v7: duplicated value
    - v1: ignored value
    - v2: ignored value
    - ...
    - v6: ignored value
    - v7: original value

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#86](https://www.evm.codes/#86)
    """

    DUP8 = Opcode(0x87, pushed_stack_items=1, min_stack_height=8)
    """
    DUP8(v1, v2, ..., v7, v8) = v8, v1, v2, ..., v7, v8
    ----

    Description
    ----
    Duplicate 8th stack item

    Inputs
    ----
    - v1: ignored value
    - v2: ignored value
    - ...
    - v7: ignored value
    - v8: value to duplicate

    Outputs
    ----
    - v8: duplicated value
    - v1: ignored value
    - v2: ignored value
    - ...
    - v7: ignored value
    - v8: original value

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#87](https://www.evm.codes/#87)
    """

    DUP9 = Opcode(0x88, pushed_stack_items=1, min_stack_height=9)
    """
    DUP9(v1, v2, ..., v8, v9) = v9, v1, v2, ..., v8, v9
    ----

    Description
    ----
    Duplicate 9th stack item

    Inputs
    ----
    - v1: ignored value
    - v2: ignored value
    - ...
    - v8: ignored value
    - v9: value to duplicate

    Outputs
    ----
    - v9: duplicated value
    - v1: ignored value
    - v2: ignored value
    - ...
    - v8: ignored value
    - v9: original value

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#88](https://www.evm.codes/#88)
    """
    DUP10 = Opcode(0x89, pushed_stack_items=1, min_stack_height=10)
    """
    DUP10(v1, v2, ..., v9, v10) = v10, v1, v2, ..., v9, v10
    ----

    Description
    ----
    Duplicate 10th stack item

    Inputs
    ----
    - v1: ignored value
    - v2: ignored value
    - ...
    - v9: ignored value
    - v10: value to duplicate

    Outputs
    ----
    - v10: duplicated value
    - v1: ignored value
    - v2: ignored value
    - ...
    - v9: ignored value
    - v10: original value

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#89](https://www.evm.codes/#89)
    """

    DUP11 = Opcode(0x8A, pushed_stack_items=1, min_stack_height=11)
    """
    DUP11(v1, v2, ..., v10, v11) = v11, v1, v2, ..., v10, v11
    ----

    Description
    ----
    Duplicate 11th stack item

    Inputs
    ----
    - v1: ignored value
    - v2: ignored value
    - ...
    - v10: ignored value
    - v11: value to duplicate

    Outputs
    ----
    - v11: duplicated value
    - v1: ignored value
    - v2: ignored value
    - ...
    - v10: ignored value
    - v11: original value

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#8A](https://www.evm.codes/#8A)
    """

    DUP12 = Opcode(0x8B, pushed_stack_items=1, min_stack_height=12)
    """
    DUP12(v1, v2, ..., v11, v12) = v12, v1, v2, ..., v11, v12
    ----

    Description
    ----
    Duplicate 12th stack item

    Inputs
    ----
    - v1: ignored value
    - v2: ignored value
    - ...
    - v11: ignored value
    - v12: value to duplicate

    Outputs
    ----
    - v12: duplicated value
    - v1: ignored value
    - v2: ignored value
    - ...
    - v11: ignored value
    - v12: original value

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#8B](https://www.evm.codes/#8B)
    """

    DUP13 = Opcode(0x8C, pushed_stack_items=1, min_stack_height=13)
    """
    DUP13(v1, v2, ..., v12, v13) = v13, v1, v2, ..., v12, v13
    ----

    Description
    ----
    Duplicate 13th stack item

    Inputs
    ----
    - v1: ignored value
    - v2: ignored value
    - ...
    - v12: ignored value
    - v13: value to duplicate

    Outputs
    ----
    - v13: duplicated value
    - v1: ignored value
    - v2: ignored value
    - ...
    - v12: ignored value
    - v13: original value

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#8C](https://www.evm.codes/#8C)
    """

    DUP14 = Opcode(0x8D, pushed_stack_items=1, min_stack_height=14)
    """
    DUP14(v1, v2, ..., v13, v14) = v14, v1, v2, ..., v13, v14
    ----

    Description
    ----
    Duplicate 14th stack item

    Inputs
    ----
    - v1: ignored value
    - v2: ignored value
    - ...
    - v13: ignored value
    - v14: value to duplicate

    Outputs
    ----
    - v14: duplicated value
    - v1: ignored value
    - v2: ignored value
    - ...
    - v13: ignored value
    - v14: original value

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#8D](https://www.evm.codes/#8D)
    """

    DUP15 = Opcode(0x8E, pushed_stack_items=1, min_stack_height=15)
    """
    DUP15(v1, v2, ..., v14, v15) = v15, v1, v2, ..., v14, v15
    ----

    Description
    ----
    Duplicate 15th stack item

    Inputs
    ----
    - v1: ignored value
    - v2: ignored value
    - ...
    - v14: ignored value
    - v15: value to duplicate

    Outputs
    ----
    - v15: duplicated value
    - v1: ignored value
    - v2: ignored value
    - ...
    - v14: ignored value
    - v15: original value

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#8E](https://www.evm.codes/#8E)
    """

    DUP16 = Opcode(0x8F, pushed_stack_items=1, min_stack_height=16)
    """
    DUP16(v1, v2, ..., v15, v16) = v16, v1, v2, ..., v15, v16
    ----

    Description
    ----
    Duplicate 16th stack item

    Inputs
    ----
    - v1: ignored value
    - v2: ignored value
    - ...
    - v15: ignored value
    - v16: value to duplicate

    Outputs
    ----
    - v16: duplicated value
    - v1: ignored value
    - v2: ignored value
    - ...
    - v15: ignored value
    - v16: original value

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#8F](https://www.evm.codes/#8F)
    """

    SWAP1 = Opcode(0x90, min_stack_height=2)
    """
    SWAP1(v1, v2) = v2, v1
    ----

    Description
    ----
    Exchange the top stack item with the second stack item.

    Inputs
    ----
    - v1: value to swap
    - v2: value to swap

    Outputs
    ----
    - v1: swapped value
    - v2: swapped value

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#90](https://www.evm.codes/#90)
    """

    SWAP2 = Opcode(0x91, min_stack_height=3)
    """
    SWAP2(v1, v2, v3) = v3, v2, v1
    ----

    Description
    ----
    Exchange 1st and 3rd stack items

    Inputs
    ----
    - v1: value to swap
    - v2: ignored value
    - v3: value to swap

    Outputs
    ----
    - v3: swapped value
    - v2: ignored value
    - v1: swapped value

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#91](https://www.evm.codes/#91)
    """

    SWAP3 = Opcode(0x92, min_stack_height=4)
    """
    SWAP3(v1, v2, v3, v4) = v4, v2, v3, v1
    ----

    Description
    ----
    Exchange 1st and 4th stack items

    Inputs
    ----
    - v1: value to swap
    - v2: ignored value
    - v3: ignored value
    - v4: value to swap

    Outputs
    ----
    - v4: swapped value
    - v2: ignored value
    - v3: ignored value
    - v1: swapped value

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#92](https://www.evm.codes/#92)
    """

    SWAP4 = Opcode(0x93, min_stack_height=5)
    """
    SWAP4(v1, v2, ..., v4, v5) = v5, v2, ..., v4, v1
    ----

    Description
    ----
    Exchange 1st and 5th stack items

    Inputs
    ----
    - v1: value to swap
    - v2: ignored value
    - ...
    - v4: ignored value
    - v5: value to swap

    Outputs
    ----
    - v5: swapped value
    - v2: ignored value
    - ...
    - v4: ignored value
    - v1: swapped value

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#93](https://www.evm.codes/#93)
    """

    SWAP5 = Opcode(0x94, min_stack_height=6)
    """
    SWAP5(v1, v2, ..., v5, v6) = v6, v2, ..., v5, v1
    ----

    Description
    ----
    Exchange 1st and 6th stack items

    Inputs
    ----
    - v1: value to swap
    - v2: ignored value
    - ...
    - v5: ignored value
    - v6: value to swap

    Outputs
    ----
    - v6: swapped value
    - v2: ignored value
    - ...
    - v5: ignored value
    - v1: swapped value

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#94](https://www.evm.codes/#94)
    """

    SWAP6 = Opcode(0x95, min_stack_height=7)
    """
    SWAP6(v1, v2, ..., v6, v7) = v7, v2, ..., v6, v1
    ----

    Description
    ----
    Exchange 1st and 7th stack items

    Inputs
    ----
    - v1: value to swap
    - v2: ignored value
    - ...
    - v6: ignored value
    - v7: value to swap

    Outputs
    ----
    - v7: swapped value
    - v2: ignored value
    - ...
    - v6: ignored value
    - v1: swapped value

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#95](https://www.evm.codes/#95)
    """

    SWAP7 = Opcode(0x96, min_stack_height=8)
    """
    SWAP7(v1, v2, ..., v7, v8) = v8, v2, ..., v7, v1
    ----

    Description
    ----
    Exchange 1st and 8th stack items

    Inputs
    ----
    - v1: value to swap
    - v2: ignored value
    - ...
    - v7: ignored value
    - v8: value to swap

    Outputs
    ----
    - v8: swapped value
    - v2: ignored value
    - ...
    - v7: ignored value
    - v1: swapped value

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#96](https://www.evm.codes/#96)
    """

    SWAP8 = Opcode(0x97, min_stack_height=9)
    """
    SWAP8(v1, v2, ..., v8, v9) = v9, v2, ..., v8, v1
    ----

    Description
    ----
    Exchange 1st and 9th stack items

    Inputs
    ----
    - v1: value to swap
    - v2: ignored value
    - ...
    - v8: ignored value
    - v9: value to swap

    Outputs
    ----
    - v9: swapped value
    - v2: ignored value
    - ...
    - v8: ignored value
    - v1: swapped value

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#97](https://www.evm.codes/#97)
    """

    SWAP9 = Opcode(0x98, min_stack_height=10)
    """
    SWAP9(v1, v2, ..., v9, v10) = v10, v2, ..., v9, v1
    ----

    Description
    ----
    Exchange 1st and 10th stack items

    Inputs
    ----
    - v1: value to swap
    - v2: ignored value
    - ...
    - v9: ignored value
    - v10: value to swap

    Outputs
    ----
    - v10: swapped value
    - v2: ignored value
    - ...
    - v9: ignored value
    - v1: swapped value

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#98](https://www.evm.codes/#98)
    """

    SWAP10 = Opcode(0x99, min_stack_height=11)
    """
    SWAP10(v1, v2, ..., v10, v11) = v11, v2, ..., v10, v1
    ----

    Description
    ----
    Exchange 1st and 11th stack items

    Inputs
    ----
    - v1: value to swap
    - v2: ignored value
    - ...
    - v10: ignored value
    - v11: value to swap

    Outputs
    ----
    - v11: swapped value
    - v2: ignored value
    - ...
    - v10: ignored value
    - v1: swapped value

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#99](https://www.evm.codes/#99)
    """

    SWAP11 = Opcode(0x9A, min_stack_height=12)
    """
    SWAP11(v1, v2, ..., v11, v12) = v12, v2, ..., v11, v1
    ----

    Description
    ----
    Exchange 1st and 12th stack items

    Inputs
    ----
    - v1: value to swap
    - v2: ignored value
    - ...
    - v11: ignored value
    - v12: value to swap

    Outputs
    ----
    - v12: swapped value
    - v2: ignored value
    - ...
    - v11: ignored value
    - v1: swapped value

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#9A](https://www.evm.codes/#9A)
    """

    SWAP12 = Opcode(0x9B, min_stack_height=13)
    """
    SWAP12(v1, v2, ..., v12, v13) = v13, v2, ..., v12, v1
    ----

    Description
    ----
    Exchange 1st and 13th stack items

    Inputs
    ----
    - v1: value to swap
    - v2: ignored value
    - ...
    - v12: ignored value
    - v13: value to swap

    Outputs
    ----
    - v13: swapped value
    - v2: ignored value
    - ...
    - v12: ignored value
    - v1: swapped value

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#9B](https://www.evm.codes/#9B)
    """

    SWAP13 = Opcode(0x9C, min_stack_height=14)
    """
    SWAP13(v1, v2, ..., v13, v14) = v14, v2, ..., v13, v1
    ----

    Description
    ----
    Exchange 1st and 14th stack items

    Inputs
    ----
    - v1: value to swap
    - v2: ignored value
    - ...
    - v13: ignored value
    - v14: value to swap

    Outputs
    ----
    - v14: swapped value
    - v2: ignored value
    - ...
    - v13: ignored value
    - v1: swapped value

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#9C](https://www.evm.codes/#9C)
    """

    SWAP14 = Opcode(0x9D, min_stack_height=15)
    """
    SWAP14(v1, v2, ..., v14, v15) = v15, v2, ..., v14, v1
    ----

    Description
    ----
    Exchange 1st and 15th stack items

    Inputs
    ----
    - v1: value to swap
    - v2: ignored value
    - ...
    - v14: ignored value
    - v15: value to swap

    Outputs
    ----
    - v15: swapped value
    - v2: ignored value
    - ...
    - v14: ignored value
    - v1: swapped value

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#9D](https://www.evm.codes/#9D)
    """

    SWAP15 = Opcode(0x9E, min_stack_height=16)
    """
    SWAP15(v1, v2, ..., v15, v16) = v16, v2, ..., v15, v1
    ----

    Description
    ----
    Exchange 1st and 16th stack items

    Inputs
    ----
    - v1: value to swap
    - v2: ignored value
    - ...
    - v15: ignored value
    - v16: value to swap

    Outputs
    ----
    - v16: swapped value
    - v2: ignored value
    - ...
    - v15: ignored value
    - v1: swapped value

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#9E](https://www.evm.codes/#9E)
    """

    SWAP16 = Opcode(0x9F, min_stack_height=17)
    """
    SWAP16(v1, v2, ..., v16, v17) = v17, v2, ..., v16, v1
    ----

    Description
    ----
    Exchange 1st and 17th stack items

    Inputs
    ----
    - v1: value to swap
    - v2: ignored value
    - ...
    - v16: ignored value
    - v17: value to swap

    Outputs
    ----
    - v17: swapped value
    - v2: ignored value
    - ...
    - v16: ignored value
    - v1: swapped value

    Fork
    ----
    Frontier

    Gas
    ----
    3

    Source: [evm.codes/#9F](https://www.evm.codes/#9F)
    """

    LOG0 = Opcode(
        0xA0,
        popped_stack_items=2,
        kwargs=["offset", "size"],
        metadata={"data_size": 0, "new_memory_size": 0, "old_memory_size": 0},
    )
    """
    LOG0(offset, size)
    ----

    Description
    ----
    Append log record with no topics

    Inputs
    ----
    - offset: byte offset in the memory in bytes
    - size: byte size to copy

    Outputs
    ----
    - None

    Fork
    ----
    Frontier

    Gas
    ----
    - static_gas = 375
    - dynamic_gas = 375 * topic_count + 8 * size + memory_expansion_cost

    Metadata
    ----
    - data_size: number of bytes in the log data (default: 0)
    - new_memory_size: memory size after expansion in bytes (default: 0)
    - old_memory_size: memory size before expansion in bytes (default: 0)

    Source: [evm.codes/#A0](https://www.evm.codes/#A0)
    """

    LOG1 = Opcode(
        0xA1,
        popped_stack_items=3,
        kwargs=["offset", "size", "topic_1"],
        metadata={"data_size": 0, "new_memory_size": 0, "old_memory_size": 0},
    )
    """
    LOG1(offset, size, topic_1)
    ----

    Description
    ----
    Append log record with one topic

    Inputs
    ----
    - offset: byte offset in the memory in bytes
    - size: byte size to copy
    - topic_1: 32-byte value

    Outputs
    ----
    - None

    Fork
    ----
    Frontier

    Gas
    ----
    - static_gas = 375
    - dynamic_gas = 375 * topic_count + 8 * size + memory_expansion_cost

    Metadata
    ----
    - data_size: number of bytes in the log data (default: 0)
    - new_memory_size: memory size after expansion in bytes (default: 0)
    - old_memory_size: memory size before expansion in bytes (default: 0)

    Source: [evm.codes/#A1](https://www.evm.codes/#A1)
    """

    LOG2 = Opcode(
        0xA2,
        popped_stack_items=4,
        kwargs=["offset", "size", "topic_1", "topic_2"],
        metadata={"data_size": 0, "new_memory_size": 0, "old_memory_size": 0},
    )
    """
    LOG2(offset, size, topic_1, topic_2)
    ----

    Description
    ----
    Append log record with two topics

    Inputs
    ----
    - offset: byte offset in the memory in bytes
    - size: byte size to copy
    - topic_1: 32-byte value
    - topic_2: 32-byte value

    Outputs
    ----
    - None

    Fork
    ----
    Frontier

    Gas
    ----
    - static_gas = 375
    - dynamic_gas = 375 * topic_count + 8 * size + memory_expansion_cost

    Metadata
    ----
    - data_size: number of bytes in the log data (default: 0)
    - new_memory_size: memory size after expansion in bytes (default: 0)
    - old_memory_size: memory size before expansion in bytes (default: 0)

    Source: [evm.codes/#A2](https://www.evm.codes/#A2)
    """

    LOG3 = Opcode(
        0xA3,
        popped_stack_items=5,
        kwargs=["offset", "size", "topic_1", "topic_2", "topic_3"],
        metadata={"data_size": 0, "new_memory_size": 0, "old_memory_size": 0},
    )
    """
    LOG3(offset, size, topic_1, topic_2, topic_3)
    ----

    Description
    ----
    Append log record with three topics

    Inputs
    ----
    - offset: byte offset in the memory in bytes
    - size: byte size to copy
    - topic_1: 32-byte value
    - topic_2: 32-byte value
    - topic_3: 32-byte value

    Outputs
    ----
    - None

    Fork
    ----
    Frontier

    Gas
    ----
    - static_gas = 375
    - dynamic_gas = 375 * topic_count + 8 * size + memory_expansion_cost

    Metadata
    ----
    - data_size: number of bytes in the log data (default: 0)
    - new_memory_size: memory size after expansion in bytes (default: 0)
    - old_memory_size: memory size before expansion in bytes (default: 0)

    Source: [evm.codes/#A3](https://www.evm.codes/#A3)
    """

    LOG4 = Opcode(
        0xA4,
        popped_stack_items=6,
        kwargs=["offset", "size", "topic_1", "topic_2", "topic_3", "topic_4"],
        metadata={"data_size": 0, "new_memory_size": 0, "old_memory_size": 0},
    )
    """
    LOG4(offset, size, topic_1, topic_2, topic_3, topic_4)
    ----

    Description
    ----
    Append log record with four topics

    Inputs
    ----
    - offset: byte offset in the memory in bytes
    - size: byte size to copy
    - topic_1: 32-byte value
    - topic_2: 32-byte value
    - topic_3: 32-byte value
    - topic_4: 32-byte value

    Outputs
    ----
    - None

    Fork
    ----
    Frontier

    Gas
    ----
    - static_gas = 375
    - dynamic_gas = 375 * topic_count + 8 * size + memory_expansion_cost

    Metadata
    ----
    - data_size: number of bytes in the log data (default: 0)
    - new_memory_size: memory size after expansion in bytes (default: 0)
    - old_memory_size: memory size before expansion in bytes (default: 0)

    Source: [evm.codes/#A4](https://www.evm.codes/#A4)
    """

    CREATE = Opcode(
        0xF0,
        popped_stack_items=3,
        pushed_stack_items=1,
        kwargs=["value", "offset", "size"],
        metadata={
            "init_code_size": 0,
            "new_memory_size": 0,
            "old_memory_size": 0,
        },
    )
    """
    CREATE(value, offset, size) = address
    ----

    Description
    ----
    Create a new contract with the given code

    Inputs
    ----
    - value: value in wei to send to the new account
    - offset: byte offset in the memory in bytes, the initialization code
              for the new account
    - size: byte size to copy (size of the initialization code)

    Outputs
    ----
    - address: the address of the deployed contract, 0 if the deployment failed

    Fork
    ----
    Frontier

    Gas
    ----
    ```
    minimum_word_size = (size + 31) / 32
    init_code_cost = 2 * minimum_word_size
    code_deposit_cost = 200 * deployed_code_size

    static_gas = 32000
    dynamic_gas = init_code_cost + memory_expansion_cost +
                  deployment_code_execution_cost +
                  code_deposit_cost
    ```

    Metadata
    ----
    - init_code_size: size of the initialization code in bytes (default: 0)
    - new_memory_size: memory size after expansion in bytes (default: 0)
    - old_memory_size: memory size before expansion in bytes (default: 0)

    Source: [evm.codes/#F0](https://www.evm.codes/#F0)
    """

    CALL = Opcode(
        0xF1,
        popped_stack_items=7,
        pushed_stack_items=1,
        kwargs=[
            "gas",
            "address",
            "value",
            "args_offset",
            "args_size",
            "ret_offset",
            "ret_size",
        ],
        kwargs_defaults={"gas": GAS},
        metadata={
            "address_warm": False,
            "value_transfer": False,
            "account_new": False,
            "new_memory_size": 0,
            "old_memory_size": 0,
            "delegated_address": False,
            "delegated_address_warm": False,
        },
    )
    """
    CALL(gas, address, value, args_offset, args_size, ret_offset, ret_size)
    = success
    ----

    Description
    ----
    Message-call into an account

    Inputs
    ----
    - gas: amount of gas to send to the sub context to execute. The gas that
           is not used by the sub context is returned to this one
    - address: the account which context to execute
    - value: value in wei to send to the account
    - args_offset: byte offset in the memory in bytes, the calldata of
                   the sub context
    - args_size: byte size to copy (size of the calldata)
    - ret_offset: byte offset in the memory in bytes, where to store the
                  return data of the sub context
    - ret_size: byte size to copy (size of the return data)

    Outputs
    ----
    - success: return 0 if the sub context reverted, 1 otherwise

    Fork
    ----
    Frontier

    Gas
    ----
    ```
    static_gas = 0
    dynamic_gas = memory_expansion_cost + code_execution_cost +
                  address_access_cost + positive_value_cost +
                  value_to_empty_account_cost
    ```

    Metadata
    ----
    - address_warm: whether the address is already warm (default: False)
    - value_transfer: whether value is being transferred (default: False)
    - account_new: whether creating a new account (default: False)
    - new_memory_size: memory size after expansion in bytes (default: 0)
    - old_memory_size: memory size before expansion in bytes (default: 0)
    - delegated_address: whether the target is a delegated account
                          (default: False)
    - delegated_address_warm: whether the delegated address of the target
                              is already warm (default: False)

    Source: [evm.codes/#F1](https://www.evm.codes/#F1)
    """

    CALLCODE = Opcode(
        0xF2,
        popped_stack_items=7,
        pushed_stack_items=1,
        kwargs=[
            "gas",
            "address",
            "value",
            "args_offset",
            "args_size",
            "ret_offset",
            "ret_size",
        ],
        kwargs_defaults={"gas": GAS},
        metadata={
            "address_warm": False,
            "value_transfer": False,
            "account_new": False,
            "new_memory_size": 0,
            "old_memory_size": 0,
            "delegated_address": False,
            "delegated_address_warm": False,
        },
    )
    """
    CALLCODE(gas, address, value, args_offset, args_size, ret_offset, ret_size)
    = success
    ----

    Description
    ----
    Message-call into this account with an alternative account's code.
    Executes code starting at the address to which the call is made.

    Inputs
    ----
    - gas: amount of gas to send to the sub context to execute. The gas that
    is not used by the sub context is returned to this one
    - address: the account which code to execute
    - value: value in wei to send to the account
    - args_offset: byte offset in the memory in bytes, the calldata of
                   the sub context
    - args_size: byte size to copy (size of the calldata)
    - ret_offset: byte offset in the memory in bytes, where to store the
                  return data of the sub context
    - ret_size: byte size to copy (size of the return data)

    Outputs
    ----
    - success: return 0 if the sub context reverted, 1 otherwise

    Fork
    ----
    Frontier

    Gas
    ----
    ```
    static_gas = 0
    dynamic_gas = memory_expansion_cost + code_execution_cost +
                  address_access_cost + positive_value_cost
    ```

    Metadata
    ----
    - address_warm: whether the address is already warm (default: False)
    - value_transfer: whether value is being transferred (default: False)
    - account_new: whether creating a new account (default: False)
    - new_memory_size: memory size after expansion in bytes (default: 0)
    - old_memory_size: memory size before expansion in bytes (default: 0)
    - delegated_address: whether the target is a delegated account
                          (default: False)
    - delegated_address_warm: whether the delegated address of the target
                              is already warm (default: False)

    Source: [evm.codes/#F2](https://www.evm.codes/#F2)
    """

    RETURN = Opcode(
        0xF3,
        popped_stack_items=2,
        kwargs=["offset", "size"],
        terminating=True,
        metadata={
            "new_memory_size": 0,
            "old_memory_size": 0,
            "code_deposit_size": 0,
        },
    )
    """
    RETURN(offset, size)
    ----

    Description
    ----
    Halt execution returning output data

    Inputs
    ----
    - offset: byte offset in the memory in bytes, to copy what will be
              the return data of this context
    - size: byte size to copy (size of the return data)

    Outputs
    ----
    - None

    Fork
    ----
    Frontier

    Gas
    ----
    - static_gas = 0
    - dynamic_gas = memory_expansion_cost

    Metadata
    ----
    - new_memory_size: memory size after expansion in bytes (default: 0)
    - old_memory_size: memory size before expansion in bytes (default: 0)
    - code_deposit_size: size of bytecode being deployed in bytes (default: 0,
                         only for RETURN in initcode)

    Source: [evm.codes/#F3](https://www.evm.codes/#F3)
    """

    DELEGATECALL = Opcode(
        0xF4,
        popped_stack_items=6,
        pushed_stack_items=1,
        kwargs=[
            "gas",
            "address",
            "args_offset",
            "args_size",
            "ret_offset",
            "ret_size",
        ],
        kwargs_defaults={"gas": GAS},
        metadata={
            "address_warm": False,
            "value_transfer": False,
            "account_new": False,
            "new_memory_size": 0,
            "old_memory_size": 0,
            "delegated_address": False,
            "delegated_address_warm": False,
        },
    )
    """
    DELEGATECALL(gas, address, args_offset, args_size, ret_offset, ret_size)
    = success
    ----

    Description
    ----
    Message-call into this account with an alternative account's code, but
    persisting the current values for sender and value

    Inputs
    ----
    - gas: amount of gas to send to the sub context to execute. The gas that
    is not used by the sub context is returned to this one
    - address: the account which code to execute
    - args_offset: byte offset in the memory in bytes, the calldata of
                   the sub context
    - args_size: byte size to copy (size of the calldata)
    - ret_offset: byte offset in the memory in bytes, where to store
                  the return data of the sub context
    - ret_size: byte size to copy (size of the return data)

    Outputs
    ----
    - success: return 0 if the sub context reverted, 1 otherwise

    Fork
    ----
    Byzantium

    Gas
    ----
    - static_gas = 0
    - dynamic_gas = memory_expansion_cost + code_execution_cost +
                    address_access_cost

    Metadata
    ----
    - address_warm: whether the address is already warm (default: False)
    - value_transfer: always False for DELEGATECALL (default: False)
    - account_new: always False for DELEGATECALL (default: False)
    - new_memory_size: memory size after expansion in bytes (default: 0)
    - old_memory_size: memory size before expansion in bytes (default: 0)
    - delegated_address: whether the target is a delegated account
                          (default: False)
    - delegated_address_warm: whether the delegated address of the target
                              is already warm (default: False)

    Source: [evm.codes/#F4](https://www.evm.codes/#F4)
    """

    CREATE2 = Opcode(
        0xF5,
        popped_stack_items=4,
        pushed_stack_items=1,
        kwargs=["value", "offset", "size", "salt"],
        metadata={
            "init_code_size": 0,
            "new_memory_size": 0,
            "old_memory_size": 0,
        },
    )
    """
    CREATE2(value, offset, size, salt) = address
    ----

    Description
    ----
    Creates a new contract

    Inputs
    ----
    - value: value in wei to send to the new account
    - offset: byte offset in the memory in bytes, the initialization code
              of the new account
    - size: byte size to copy (size of the initialization code)
    - salt: 32-byte value used to create the new account at a
            deterministic address

    Outputs
    ----
    - address: the address of the deployed contract, 0 if the deployment failed

    Fork
    ----
    Constantinople

    Gas
    ----
    ```
    minimum_word_size = (size + 31) / 32
    init_code_cost = 2 * minimum_word_size
    hash_cost = 6 * minimum_word_size
    code_deposit_cost = 200 * deployed_code_size

    static_gas = 32000
    dynamic_gas = init_code_cost + hash_cost + memory_expansion_cost
        + deployment_code_execution_cost + code_deposit_cost
    ```

    Metadata
    ----
    - init_code_size: size of the initialization code in bytes (default: 0)
    - new_memory_size: memory size after expansion in bytes (default: 0)
    - old_memory_size: memory size before expansion in bytes (default: 0)

    Source: [evm.codes/#F5](https://www.evm.codes/#F5)
    """

    STATICCALL = Opcode(
        0xFA,
        popped_stack_items=6,
        pushed_stack_items=1,
        kwargs=[
            "gas",
            "address",
            "args_offset",
            "args_size",
            "ret_offset",
            "ret_size",
        ],
        kwargs_defaults={"gas": GAS},
        metadata={
            "address_warm": False,
            "new_memory_size": 0,
            "old_memory_size": 0,
            "delegated_address": False,
            "delegated_address_warm": False,
        },
    )
    """
    STATICCALL(gas, address, args_offset, args_size, ret_offset, ret_size)
    = success
    ----

    Description
    ----
    Static message-call into an account

    Inputs
    ----
    - gas: amount of gas to send to the sub context to execute. The gas
    that is not used by the sub context is returned to this one
    - address: the account which context to execute
    - args_offset: byte offset in the memory in bytes, the calldata of the
                   sub context
    - args_size: byte size to copy (size of the calldata)
    - ret_offset: byte offset in the memory in bytes, where to store the
                  return data of the sub context
    - ret_size: byte size to copy (size of the return data)

    Outputs
    ----
    - success: return 0 if the sub context reverted, 1 otherwise

    Fork
    ----
    Byzantium

    Gas
    ----
    - static_gas = 0
    - dynamic_gas = memory_expansion_cost + code_execution_cost +
                    address_access_cost

    Metadata
    ----
    - address_warm: whether the address is already warm (default: False)
    - value_transfer: always False for STATICCALL (default: False)
    - account_new: always False for STATICCALL (default: False)
    - new_memory_size: memory size after expansion in bytes (default: 0)
    - old_memory_size: memory size before expansion in bytes (default: 0)
    - delegated_address: whether the target is a delegated account
                          (default: False)
    - delegated_address_warm: whether the delegated address of the target
                              is already warm (default: False)

    Source: [evm.codes/#FA](https://www.evm.codes/#FA)
    """

    REVERT = Opcode(
        0xFD,
        popped_stack_items=2,
        kwargs=["offset", "size"],
        terminating=True,
        metadata={"new_memory_size": 0, "old_memory_size": 0},
    )
    """
    REVERT(offset, size)
    ----

    Description
    ----
    Halt execution reverting state changes but returning data and remaining gas

    Inputs
    ----
    - offset: byte offset in the memory in bytes. The return data of
              the calling context
    - size: byte size to copy (size of the return data)

    Fork
    ----
    Byzantium

    Gas
    ----
    static_gas = 0
    dynamic_gas = memory_expansion_cost

    Metadata
    ----
    - new_memory_size: memory size after expansion in bytes (default: 0)
    - old_memory_size: memory size before expansion in bytes (default: 0)

    Source: [evm.codes/#FD](https://www.evm.codes/#FD)
    """

    INVALID = Opcode(0xFE, terminating=True)
    """
    INVALID()
    ----

    Description
    ----
    Designated invalid instruction

    Inputs
    ----
    None

    Outputs
    ----
    None

    Fork
    ----
    Frontier

    Gas
    ----
    All the remaining gas in this context is consumed

    Source: [evm.codes/#FE](https://www.evm.codes/#FE)
    """

    SELFDESTRUCT = Opcode(
        0xFF,
        popped_stack_items=1,
        kwargs=["address"],
        metadata={"address_warm": False, "account_new": False},
    )
    """
    SELFDESTRUCT(address)
    ----

    Description
    ----
    Halt execution and register the account for later deletion

    Inputs
    ----
    - address: account to send the current balance to

    Fork
    ----
    Frontier

    Gas
    ----
    5000

    Metadata
    ----
    - address_warm: whether the beneficiary address is already warm
                    (default: False)
    - account_new: whether creating a new beneficiary account, requires
                   non-zero balance in the source account (default: False)

    Source: [evm.codes/#FF](https://www.evm.codes/#FF)
    """


_push_opcodes_byte_list: List[Opcode] = [
    Opcodes.PUSH1,
    Opcodes.PUSH2,
    Opcodes.PUSH3,
    Opcodes.PUSH4,
    Opcodes.PUSH5,
    Opcodes.PUSH6,
    Opcodes.PUSH7,
    Opcodes.PUSH8,
    Opcodes.PUSH9,
    Opcodes.PUSH10,
    Opcodes.PUSH11,
    Opcodes.PUSH12,
    Opcodes.PUSH13,
    Opcodes.PUSH14,
    Opcodes.PUSH15,
    Opcodes.PUSH16,
    Opcodes.PUSH17,
    Opcodes.PUSH18,
    Opcodes.PUSH19,
    Opcodes.PUSH20,
    Opcodes.PUSH21,
    Opcodes.PUSH22,
    Opcodes.PUSH23,
    Opcodes.PUSH24,
    Opcodes.PUSH25,
    Opcodes.PUSH26,
    Opcodes.PUSH27,
    Opcodes.PUSH28,
    Opcodes.PUSH29,
    Opcodes.PUSH30,
    Opcodes.PUSH31,
    Opcodes.PUSH32,
]


def _mstore_operation(
    data: OpcodeCallArg = b"", offset: OpcodeCallArg = 0
) -> Bytecode:
    """
    Generate the bytecode that stores an arbitrary
    amount of data in memory.
    """
    assert isinstance(offset, int)
    if isinstance(data, int):
        data = data.to_bytes(32, "big")
    data = to_bytes(data)  # type: ignore
    bytecode = Bytecode()
    for i in range(0, len(data), 32):
        chunk = data[i : i + 32]
        if len(chunk) == 32:
            bytecode += Opcodes.MSTORE(offset, chunk)
        else:
            # We need to MLOAD the existing data at the offset and then
            # do a bitwise OR with the new data to store it in memory.
            bytecode += Opcodes.MLOAD(offset)
            # Create a mask to zero out the leftmost bytes of
            # the existing data.
            mask_size = 32 - len(chunk)
            bytecode += _push_opcodes_byte_list[mask_size - 1][-1]
            bytecode += Opcodes.AND
            bytecode += Opcodes.PUSH32[chunk.ljust(32, b"\x00")]
            bytecode += Opcodes.OR
            bytecode += _stack_argument_to_bytecode(offset)
            bytecode += Opcodes.MSTORE
        offset += len(chunk)
    return bytecode


class Macros(Macro, Enum):
    """Enum containing all macros."""

    OOG = Macro(Opcodes.SHA3(0, 100000000000))
    """
    OOG()
    ----

    Halt execution by consuming all available gas.

    Inputs
    ----
    - None. Any input arguments are ignored.

    Outputs
    ----
    - None

    Fork
    ----
    Frontier

    Gas
    ----
    `SHA3(0, 100000000000)` results in 19073514453125027 gas used and an OOG
    exception.

    Note:
    If a value > `100000000000` is used as second argument, the resulting geth
     trace reports gas `30` and an OOG exception.
    `SHA3(0, SUB(0, 1))` causes a gas > u64 exception and an OOG exception.

    Bytecode
    ----
    SHA3(0, 100000000000)
    """

    MSTORE = Macro(lambda_operation=_mstore_operation)
    """
    MSTORE(data, offset)
    ----

    Place data of arbitrary length into memory at a given offset.

    Inputs
    ----
    - data: The data to store in memory. Can be an integer or bytes.
    - offset: The offset in memory to store the data.

    Outputs
    ----
    - None
    """
