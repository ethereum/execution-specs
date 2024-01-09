"""
Define an entry point wrapper for pytest.
"""

import sys
from typing import Any, List, Optional

from ethereum_test_tools import Opcodes as Op


def process_evm_bytes(evm_bytes_hex_string: Any) -> str:  # noqa: D103
    if evm_bytes_hex_string.startswith("0x"):
        evm_bytes_hex_string = evm_bytes_hex_string[2:]

    evm_bytes = bytearray(bytes.fromhex(evm_bytes_hex_string))

    opcodes_strings: List[str] = []

    while evm_bytes:
        opcode_byte = evm_bytes.pop(0)

        opcode: Optional[Op] = None
        for op in Op:
            if op.int() == opcode_byte:
                opcode = op
                break

        if opcode is None:
            raise ValueError(f"Unknown opcode: {opcode_byte}")

        if opcode.data_portion_length > 0:
            data_portion = evm_bytes[: opcode.data_portion_length]
            evm_bytes = evm_bytes[opcode.data_portion_length :]
            opcodes_strings.append(f'Op.{opcode._name_}("0x{data_portion.hex()}")')
        else:
            opcodes_strings.append(f"Op.{opcode._name_}")

    return " + ".join(opcodes_strings)


def print_help():  # noqa: D103
    print("Usage: evm_bytes_to_python <EVM bytes hex string>")


def main():  # noqa: D103
    if len(sys.argv) != 2:
        print_help()
        sys.exit(1)
    if sys.argv[1] in ["-h", "--help"]:
        print_help()
        sys.exit(0)
    evm_bytes_hex_string = sys.argv[1]
    print(process_evm_bytes(evm_bytes_hex_string))


if __name__ == "__main__":
    main()
