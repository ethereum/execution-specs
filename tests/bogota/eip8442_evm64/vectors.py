"""
The EIP's test vectors: (opcode name, inputs top of stack first, output).

Mirrors the Test Cases table of the EIP; `test_evm64.py` in the EIP's
assets generates that table from the same list.
"""

from typing import List, Tuple

VECTORS: List[Tuple[str, List[int], int]] = [
    ("ADD64", [0xFFFFFFFFFFFFFFFF, 0x1], 0x0),
    ("ADD64", [0x10000000000000005, 0x7], 0xC),
    ("SUB64", [0x0, 0x1], 0xFFFFFFFFFFFFFFFF),
    ("MUL64", [0x100000000, 0x100000000], 0x0),
    ("DIV64", [0x10, 0x3], 0x5),
    ("DIV64", [0x1, 0x0], 0x0),
    ("SDIV64", [0xFFFFFFFFFFFFFFF8, 0x2], 0xFFFFFFFFFFFFFFFC),
    ("SDIV64", [0x8000000000000000, 0xFFFFFFFFFFFFFFFF], 0x8000000000000000),
    ("MOD64", [0x11, 0x5], 0x2),
    ("SMOD64", [0xFFFFFFFFFFFFFFF9, 0x3], 0xFFFFFFFFFFFFFFFF),
    ("ADDMOD64", [0xFFFFFFFFFFFFFFFF, 0xFFFFFFFFFFFFFFFF, 0x7], 0x2),
    (
        "MULMOD64",
        [0x8000000000000000, 0x8000000000000000, 0xFFFFFFFFFFFFFFFF],
        0x4000000000000000,
    ),
    ("EXP64", [0x2, 0x40], 0x0),
    ("EXP64", [0x3, 0x28], 0xA8B8B452291FE821),
    ("SIGNEXTEND64", [0x0, 0x80], 0xFFFFFFFFFFFFFF80),
    ("SIGNEXTEND64", [0x1, 0x80], 0x80),
    ("SIGNEXTEND64", [0x7, 0x80], 0x80),
    ("LT64", [0x10000000000000005, 0x7], 0x1),
    ("GT64", [0x7, 0x10000000000000005], 0x1),
    ("SLT64", [0xFFFFFFFFFFFFFFFF, 0x0], 0x1),
    ("SGT64", [0x0, 0xFFFFFFFFFFFFFFFF], 0x1),
    ("EQ64", [0x10000000000000005, 0x5], 0x1),
    ("ISZERO64", [0x10000000000000000], 0x1),
    ("AND64", [0x10000000000000005, 0xFF], 0x5),
    ("OR64", [0x10000000000000005, 0x2], 0x7),
    ("XOR64", [0xFF, 0xF], 0xF0),
    ("NOT64", [0x0], 0xFFFFFFFFFFFFFFFF),
    ("SHL64", [0x3F, 0x1], 0x8000000000000000),
    ("SHL64", [0x40, 0x1], 0x0),
    ("SHR64", [0x1, 0x8000000000000000], 0x4000000000000000),
    ("SAR64", [0x1, 0x8000000000000000], 0xC000000000000000),
    ("SAR64", [0x64, 0x8000000000000000], 0xFFFFFFFFFFFFFFFF),
    ("CLZ64", [0x1], 0x3F),
    ("CLZ64", [0x10000000000000000], 0x40),
]

# EXP64: (base, exponent), gas.  An exponent of 2**64 reads as 0.
EXP64_GAS: List[Tuple[Tuple[int, int], int]] = [
    ((2, 0), 5),
    ((2, 255), 30),
    ((2, 256), 55),
    ((2, 0x10000000000000000), 5),
]

# Static gas of each instruction with a static cost, by name.
STATIC_GAS = {
    "ADD64": 2,
    "ADDMOD64": 5,
    "AND64": 2,
    "CALLDATALOAD64": 2,
    "CLZ64": 3,
    "DIV64": 3,
    "EQ64": 2,
    "GT64": 2,
    "ISZERO64": 2,
    "LT64": 2,
    "MOD64": 3,
    "MUL64": 3,
    "MULMOD64": 5,
    "NOT64": 2,
    "OR64": 2,
    "SAR64": 2,
    "SDIV64": 3,
    "SGT64": 2,
    "SHL64": 2,
    "SHR64": 2,
    "SIGNEXTEND64": 3,
    "SLT64": 2,
    "SMOD64": 3,
    "SUB64": 2,
    "XOR64": 2,
}

# Stack inputs of each instruction, by name.
POPS = {
    "ADD64": 2,
    "ADDMOD64": 3,
    "AND64": 2,
    "CALLDATALOAD64": 1,
    "CLZ64": 1,
    "DIV64": 2,
    "EQ64": 2,
    "EXP64": 2,
    "GT64": 2,
    "ISZERO64": 1,
    "LT64": 2,
    "MLOAD64": 1,
    "MOD64": 2,
    "MSTORE64": 2,
    "MUL64": 2,
    "MULMOD64": 3,
    "NOT64": 1,
    "OR64": 2,
    "SAR64": 2,
    "SDIV64": 2,
    "SGT64": 2,
    "SHL64": 2,
    "SHR64": 2,
    "SIGNEXTEND64": 2,
    "SLT64": 2,
    "SMOD64": 2,
    "SUB64": 2,
    "XOR64": 2,
}
