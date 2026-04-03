"""Define an entry point wrapper for pytest."""

from dataclasses import dataclass, field
from typing import Any, Dict, List

import click

from execution_testing.base_types import HexNumber, ZeroPaddedHexNumber
from execution_testing.vm import Op

OPCODES_WITH_EMPTY_LINES_AFTER = {
    Op.STOP,
    Op.REVERT,
    Op.INVALID,
    Op.JUMP,
    Op.JUMPI,
}

OPCODES_WITH_EMPTY_LINES_BEFORE = {
    Op.JUMPDEST,
}


@dataclass(kw_only=True)
class OpcodeWithOperands:
    """Simple opcode with its operands."""

    opcode: Op
    operands: List[int] = field(default_factory=list)
    args: List["OpcodeWithOperands | HexNumber | str"] = field(
        default_factory=list
    )
    kwargs: Dict[str, "OpcodeWithOperands | HexNumber | str"] = field(
        default_factory=dict
    )

    def __str__(self) -> str:
        """Format into a string."""
        output = ""
        if self.operands:
            operands = ", ".join(hex(operand) for operand in self.operands)
            output = f"Op.{self.opcode._name_}[{operands}]"
        else:
            output = f"Op.{self.opcode._name_}"
        if self.kwargs or self.args:
            args: List[str] = []
            if self.kwargs:
                args = [f"{k}={v}" for k, v in self.kwargs.items()]
            elif self.args:
                args = [f"{arg}" for arg in self.args]
            output = f"{output}({', '.join(args)})"
        return output

    def opcode_or_int(
        self, int_definitions: dict[int, str] | None = None
    ) -> "OpcodeWithOperands | HexNumber | str":
        """
        Return self or an HexNumber if the opcode is a PUSH opcode and can be
        seamlessly converted to int when used as a stack argument or keyword
        argument.

        Only return HexNumber if the PUSH opcode used is the minimum required
        bytesize for the value. E.g. PUSH1[0xff] returns 0xff, but
        PUSH2[0xff] returns the opcode itself because 0xff fits in PUSH1.
        PUSH0 always returns itself.
        """
        if (
            self.opcode is not None
            and self.opcode._name_.startswith("PUSH")
            and self.opcode.data_portion_length > 0
            and len(self.operands) == 1
        ):
            value = self.operands[0]
            min_bytes = max(1, (value.bit_length() + 7) // 8)
            if self.opcode.data_portion_length == min_bytes:
                if int_definitions and value in int_definitions:
                    return int_definitions[value]
                return HexNumber(value)
        return self

    def __eq__(self, other: Any) -> bool:
        """Compare two opcodes with operands."""
        if not isinstance(other, OpcodeWithOperands):
            return False
        if (
            self.opcode == other.opcode
            and self.operands == other.operands
            and self.args == other.args
            and self.kwargs == other.kwargs
        ):
            return True
        return False


@dataclass(kw_only=True)
class OpcodeWithOperandsAssembly(OpcodeWithOperands):
    """Simple opcode with its operands that formats into assembly."""

    def __str__(self) -> str:
        """Format the opcode with its operands as assembly."""
        opcode_name = self.opcode._name_.lower()
        if self.opcode.data_portion_length == 0:
            return f"{opcode_name}"
        else:
            operands = ", ".join(
                str(ZeroPaddedHexNumber(operand)) for operand in self.operands
            )
            return f"{opcode_name} {operands}"


def process_evm_bytes(  # noqa: D103
    evm_bytes: bytes,
    assembly: bool = False,
    int_definitions: dict[int, str] | None = None,
) -> List[OpcodeWithOperands]:
    evm_bytes_array = bytearray(evm_bytes)

    opcodes: List[OpcodeWithOperands] = []

    while evm_bytes_array:
        opcode_byte = evm_bytes_array.pop(0)

        opcode: Op
        for op in Op:
            if op.int() == opcode_byte:
                opcode = op
                break
        else:
            raise ValueError(f"Unknown opcode: {opcode_byte}")
        opcode_with_operands: OpcodeWithOperands
        if opcode.data_portion_length > 0:
            opcode_with_operands = OpcodeWithOperands(
                opcode=opcode,
                operands=[
                    int.from_bytes(
                        evm_bytes_array[: opcode.data_portion_length],
                        "big",
                    )
                ],
            )
            evm_bytes_array = evm_bytes_array[opcode.data_portion_length :]
        else:
            opcode_with_operands = OpcodeWithOperands(opcode=opcode)
        if (
            opcode.popped_stack_items > 0
            and len(opcodes) >= opcode.popped_stack_items
            and not assembly
        ):
            # Check all args push items to the stack, else skip
            args: List[OpcodeWithOperands] = list(
                reversed(opcodes[-opcode.popped_stack_items :])
            )
            if all(arg.opcode.pushed_stack_items == 1 for arg in args):
                args_with_int = [
                    arg.opcode_or_int(int_definitions=int_definitions)
                    for arg in args
                ]
                opcodes = opcodes[: -opcode.popped_stack_items]
                if opcode.kwargs and len(opcode.kwargs) == len(args_with_int):
                    opcode_with_operands.kwargs = dict(
                        zip(opcode.kwargs, args_with_int, strict=True)
                    )
                else:
                    opcode_with_operands.args = args_with_int

        opcodes.append(opcode_with_operands)

    return opcodes


@dataclass(kw_only=True)
class RepeatingOpcodeWithOperands:
    """Opcode that can be repeated `count` times."""

    opcode: OpcodeWithOperands
    count: int = 1

    def __str__(self) -> str:
        """Format into a string."""
        assert self.count > 0
        if self.count == 1:
            return f"{self.opcode}"
        return f"{self.opcode} * {self.count}"


def format_opcodes(  # noqa: D103
    opcodes: List[OpcodeWithOperands],
    assembly: bool = False,
    skip_simplify: bool = False,
) -> str:
    if assembly:
        opcodes_with_empty_lines: List[OpcodeWithOperandsAssembly | str] = []
        for i, op_with_operands in enumerate(opcodes):
            if (
                op_with_operands.opcode in OPCODES_WITH_EMPTY_LINES_BEFORE
                and len(opcodes_with_empty_lines) > 0
                and opcodes_with_empty_lines[-1] != ""
            ):
                opcodes_with_empty_lines.append("")
            opcodes_with_empty_lines.append(
                OpcodeWithOperandsAssembly(
                    opcode=op_with_operands.opcode,
                    operands=list(op_with_operands.operands),
                    args=list(op_with_operands.args),
                    kwargs=dict(op_with_operands.kwargs),
                )
            )
            if (
                op_with_operands.opcode in OPCODES_WITH_EMPTY_LINES_AFTER
                and i < len(opcodes) - 1
            ):
                opcodes_with_empty_lines.append("")
        return "\n".join(f"{op}" for op in opcodes_with_empty_lines)
    if skip_simplify or len(opcodes) < 2:
        return " + ".join(f"{op}" for op in opcodes)
    previous_opcode = RepeatingOpcodeWithOperands(opcode=opcodes[0])
    opcodes_with_multiply: List[RepeatingOpcodeWithOperands] = []
    for op in opcodes[1:]:
        if op == previous_opcode.opcode:
            previous_opcode.count += 1
        else:
            opcodes_with_multiply.append(previous_opcode)
            previous_opcode = RepeatingOpcodeWithOperands(opcode=op)
    opcodes_with_multiply.append(previous_opcode)
    return " + ".join(f"{op}" for op in opcodes_with_multiply)


def process_evm_bytes_string(
    evm_bytes_hex_string: str,
    assembly: bool = False,
    skip_simplify: bool = False,
    int_definitions: dict[int, str] | None = None,
) -> str:
    """Process the given EVM bytes hex string."""
    if evm_bytes_hex_string.startswith("0x"):
        evm_bytes_hex_string = evm_bytes_hex_string[2:]

    evm_bytes = bytes.fromhex(evm_bytes_hex_string)
    return format_opcodes(
        process_evm_bytes(
            evm_bytes,
            assembly=assembly,
            int_definitions=int_definitions,
        ),
        assembly=assembly,
        skip_simplify=skip_simplify,
    )


assembly_option = click.option(
    "-a",
    "--assembly",
    default=False,
    is_flag=True,
    help="Output the code as assembly instead of Python Opcodes.",
)


@click.group(
    "evm_bytes",
    context_settings={
        "help_option_names": ["-h", "--help"],
    },
)
def evm_bytes() -> None:
    """
    Convert EVM bytecode to EEST's Python Opcodes or an assembly string.

    The input can be either a hex string or a binary file.
    """
    pass


@evm_bytes.command(
    short_help="Convert a hex string to Python Opcodes or assembly."
)
@assembly_option
@click.argument("hex_string")
def hex_string(hex_string: str, assembly: bool) -> None:
    """
    Convert the HEX_STRING representing EVM bytes to EEST Python Opcodes.

    HEX_STRING is a string containing EVM bytecode.

    Returns:
        (str): The processed EVM opcodes in Python or assembly format.

    Example 1: Convert a hex string to EEST Python `Opcodes`
        uv run evm_bytes hex-string 604260005260206000F3

    Output 1:
        \b
        Op.PUSH1[0x42] + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x20] +
        Op.PUSH1[0x0] + Op.RETURN

    Example 2: Convert a hex string to assembly
        uv run evm_bytes hex-string --assembly 604260005260206000F3

    Output 2:
        \b
        push1 0x42
        push1 0x00
        mstore
        push1 0x20
        push1 0x00
        return

    """  # noqa: D301
    processed_output = process_evm_bytes_string(hex_string, assembly=assembly)
    click.echo(processed_output)


@evm_bytes.command(
    short_help="Convert a binary file to Python Opcodes or assembly."
)
@assembly_option
@click.argument("binary_file", type=click.File("rb"))
def binary_file(binary_file: Any, assembly: bool) -> None:
    """
    Convert the BINARY_FILE containing EVM bytes to Python Opcodes or assembly.

    BINARY_FILE is a binary file containing EVM bytes, use `-` to read from
    stdin.

    Returns:
        (str): The processed EVM opcodes in Python or assembly format.

    Example: Convert the Withdrawal Request contract to assembly
        \b
        uv run evm_bytes binary-file ./src/execution_testing/forks/
            contracts/withdrawal_request.bin --assembly

    Output:
        \b
        caller
        push20 0xfffffffffffffffffffffffffffffffffffffffe
        eq
        push1 0x90
        jumpi
        ...

    """  # noqa: D301
    processed_output = format_opcodes(
        process_evm_bytes(binary_file.read(), assembly=assembly),
        assembly=assembly,
    )
    click.echo(processed_output)
