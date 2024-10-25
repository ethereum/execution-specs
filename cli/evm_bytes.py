"""
Define an entry point wrapper for pytest.
"""

from dataclasses import dataclass, field
from typing import List

import click

from ethereum_test_base_types import ZeroPaddedHexNumber
from ethereum_test_vm import Macro
from ethereum_test_vm import Opcodes as Op
from ethereum_test_vm.bytecode import Bytecode

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

    opcode: Op | None
    operands: List[int] = field(default_factory=list)

    def format(self, assembly: bool) -> str:
        """Format the opcode with its operands."""
        if self.opcode is None:
            return ""
        if assembly:
            return self.format_assembly()
        if self.operands:
            operands = ", ".join(hex(operand) for operand in self.operands)
            return f"Op.{self.opcode._name_}[{operands}]"
        return f"Op.{self.opcode._name_}"

    def format_assembly(self) -> str:
        """Format the opcode with its operands as assembly."""
        if self.opcode is None:
            return ""
        opcode_name = self.opcode._name_.lower()
        if self.opcode.data_portion_length == 0:
            return f"{opcode_name}"
        elif self.opcode == Op.RJUMPV:
            operands = ", ".join(str(ZeroPaddedHexNumber(operand)) for operand in self.operands)
            return f"{opcode_name} {operands}"
        else:
            operands = ", ".join(str(ZeroPaddedHexNumber(operand)) for operand in self.operands)
            return f"{opcode_name} {operands}"

    @property
    def terminating(self) -> bool:
        """Whether the opcode is terminating or not"""
        return self.opcode.terminating if self.opcode else False

    @property
    def bytecode(self) -> Bytecode:
        """Opcode as bytecode with its operands if any."""
        # opcode.opcode[*opcode.operands] crashes `black` formatter and doesn't work.
        if self.opcode:
            return self.opcode.__getitem__(*self.operands) if self.operands else self.opcode
        else:
            return Bytecode()


def process_evm_bytes(evm_bytes: bytes) -> List[OpcodeWithOperands]:  # noqa: D103
    evm_bytes = bytearray(evm_bytes)

    opcodes: List[OpcodeWithOperands] = []

    while evm_bytes:
        opcode_byte = evm_bytes.pop(0)

        opcode: Op
        for op in Op:
            if not isinstance(op, Macro) and op.int() == opcode_byte:
                opcode = op
                break
        else:
            raise ValueError(f"Unknown opcode: {opcode_byte}")

        if opcode.data_portion_length > 0:
            signed = opcode in [Op.RJUMP, Op.RJUMPI]
            opcodes.append(
                OpcodeWithOperands(
                    opcode=opcode,
                    operands=[
                        int.from_bytes(
                            evm_bytes[: opcode.data_portion_length], "big", signed=signed
                        )
                    ],
                )
            )
            evm_bytes = evm_bytes[opcode.data_portion_length :]
        elif opcode == Op.RJUMPV:
            if len(evm_bytes) == 0:
                opcodes.append(OpcodeWithOperands(opcode=opcode))
            else:
                max_index = evm_bytes.pop(0)
                operands: List[int] = []
                for _ in range(max_index + 1):
                    operands.append(int.from_bytes(evm_bytes[:2], "big", signed=True))
                    evm_bytes = evm_bytes[2:]
                opcodes.append(OpcodeWithOperands(opcode=opcode, operands=operands))
        else:
            opcodes.append(OpcodeWithOperands(opcode=opcode))

    return opcodes


def format_opcodes(opcodes: List[OpcodeWithOperands], assembly: bool = False) -> str:  # noqa: D103
    if assembly:
        opcodes_with_empty_lines: List[OpcodeWithOperands] = []
        for i, op_with_operands in enumerate(opcodes):
            if (
                op_with_operands.opcode in OPCODES_WITH_EMPTY_LINES_BEFORE
                and len(opcodes_with_empty_lines) > 0
                and opcodes_with_empty_lines[-1].opcode is not None
            ):
                opcodes_with_empty_lines.append(OpcodeWithOperands(opcode=None))
            opcodes_with_empty_lines.append(op_with_operands)
            if op_with_operands.opcode in OPCODES_WITH_EMPTY_LINES_AFTER and i < len(opcodes) - 1:
                opcodes_with_empty_lines.append(OpcodeWithOperands(opcode=None))
        return "\n".join(op.format(assembly) for op in opcodes_with_empty_lines)
    return " + ".join(op.format(assembly) for op in opcodes)


def process_evm_bytes_string(evm_bytes_hex_string: str, assembly: bool = False) -> str:
    """Process the given EVM bytes hex string."""
    if evm_bytes_hex_string.startswith("0x"):
        evm_bytes_hex_string = evm_bytes_hex_string[2:]

    evm_bytes = bytes.fromhex(evm_bytes_hex_string)
    return format_opcodes(process_evm_bytes(evm_bytes), assembly=assembly)


assembly_option = click.option(
    "-a",
    "--assembly",
    default=False,
    is_flag=True,
    help="Output the code as assembly instead of python.",
)


@click.group(context_settings=dict(help_option_names=["-h", "--help"]))
def cli():
    """
    Convert the given EVM bytes to EEST's python opcodes or assembly string.

    The input can be either a hex string or a binary file containing EVM bytes.
    """
    pass


@cli.command()
@assembly_option
@click.argument("hex_string")
def hex_string(hex_string: str, assembly: bool):
    """
    Process a hex string representing EVM bytes and convert it into EEST's Python opcodes.

    Args:
        hex_string (str): The hex string representing the EVM bytes.
        assembly (bool): Whether to print the output as assembly or Python opcodes.

    Returns:
        (str): The processed EVM opcodes in Python or assembly format.

    Example: Convert a hex string to EEST Python `Opcodes`
        ```bash
        uv run evm_bytes hex-string 604260005260206000F3
        ```

        Output:

        ```python
        Op.PUSH1[0x42] + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.RETURN
        ```

    Example: Convert a hex string to assembly
        ```bash
        uv run evm_bytes hex-string --assembly 604260005260206000F3
        ```

        Output:

        ```text
        push1 0x42
        push1 0x00
        mstore
        push1 0x20
        push1 0x00
        return
        ```
    """  # noqa: E501
    processed_output = process_evm_bytes_string(hex_string, assembly=assembly)
    click.echo(processed_output)


@cli.command()
@assembly_option
@click.argument("binary_file_path", type=click.File("rb"))
def binary_file(binary_file_path, assembly: bool):
    """
    Convert the given EVM bytes binary file.

    Args:
        binary_file_path (BinaryIO): A binary file containing EVM bytes to be processed or use `-`
            to read from stdin.
        assembly (bool): Whether to print the output as assembly or Python opcodes.

    Example: Convert the Withdrawal Request contract to assembly
        ```bash
        uv run evm_bytes binary-file ./src/ethereum_test_forks/forks/contracts/withdrawal_request.bin --assembly
        ```

        Output:

        ```text
        caller
        push20 0xfffffffffffffffffffffffffffffffffffffffe
        eq
        push1 0x90
        jumpi
        ...
        ```
    """  # noqa: E501
    processed_output = format_opcodes(
        process_evm_bytes(binary_file_path.read()), assembly=assembly
    )
    click.echo(processed_output)
