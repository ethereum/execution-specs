"""
Ethereum Virtual Machine opcode definitions.
"""
from enum import Enum
from typing import Union


class Opcode(bytes):
    """
    Represents a single Opcode instruction in the EVM, with extra
    metadata useful to parametrize tests.

    Parameters
    ----------
    - popped_stack_items: number of items the opcode pops from the stack
    - pushed_stack_items: number of items the opcode pushes to the stack
    - min_stack_height: minimum stack height required by the opcode
    - data_portion_length: number of bytes after the opcode in the bytecode
        that represent data
    """

    popped_stack_items: int
    pushed_stack_items: int
    min_stack_height: int
    data_portion_length: int

    def __new__(
        cls,
        opcode_or_byte: Union[int, "Opcode"],
        *,
        popped_stack_items: int = 0,
        pushed_stack_items: int = 0,
        min_stack_height: int = 0,
        data_portion_length: int = 0
    ):
        """
        Creates a new opcode instance.
        """
        if type(opcode_or_byte) is Opcode:
            # Required because Enum class calls the base class with the
            # instantiated object as parameter.
            return opcode_or_byte
        elif isinstance(opcode_or_byte, int):
            obj = super().__new__(cls, [opcode_or_byte])
            obj.popped_stack_items = popped_stack_items
            obj.pushed_stack_items = pushed_stack_items
            obj.min_stack_height = min_stack_height
            obj.data_portion_length = data_portion_length
            return obj

    def __call__(self, data: int = 0) -> bytes:
        """
        Makes all opcode instances callable to return a bytes object containing
        the opcode byte plus a formatted data portion.

        This useful to automatically format, e.g., push opcodes and their
        data sections as `Opcodes.PUSH1(0x00)`.

        Data sign is automatically detected but for this reason the range
        of the input must be:
        `[-2^(data_portion_bits-1), 2^(data_portion_bits)]`
        where:
        `data_portion_bits == data_portion_length * 8`
        """
        if self.data_portion_length == 0:
            if data == 0:
                return self
            raise OverflowError(
                "Attempted to append data to an opcode without data portion"
            )

        if data < 0:
            data_portion = data.to_bytes(
                length=self.data_portion_length, byteorder="big", signed=True
            )
        else:
            data_portion = data.to_bytes(
                length=self.data_portion_length, byteorder="big", signed=False
            )

        return self + data_portion

    def __len__(self) -> int:
        """
        Returns the total bytecode length of the opcode, taking into account
        its data portion.
        """
        return self.data_portion_length + 1

    def int(self) -> int:
        """
        Returns the integer representation of the opcode.
        """
        return int.from_bytes(bytes=self, byteorder="big")


class Opcodes(Opcode, Enum):
    """
    Enum containing all known opcodes.

    Contains deprecated and not yet implemented opcodes.

    This enum is !! NOT !! meant to be iterated over by the tests. Instead,
    create a list with cherry-picked opcodes from this Enum within the test
    if iteration is needed.

    Do !! NOT !! remove or modify existing opcodes from this list.
    """

    STOP = Opcode(0x00)
    ADD = Opcode(0x01, popped_stack_items=2, pushed_stack_items=1)
    MUL = Opcode(0x02, popped_stack_items=2, pushed_stack_items=1)
    SUB = Opcode(0x03, popped_stack_items=2, pushed_stack_items=1)
    DIV = Opcode(0x04, popped_stack_items=2, pushed_stack_items=1)
    SDIV = Opcode(0x05, popped_stack_items=2, pushed_stack_items=1)
    MOD = Opcode(0x06, popped_stack_items=2, pushed_stack_items=1)
    SMOD = Opcode(0x07, popped_stack_items=2, pushed_stack_items=1)
    ADDMOD = Opcode(0x08, popped_stack_items=3, pushed_stack_items=1)
    MULMOD = Opcode(0x09, popped_stack_items=3, pushed_stack_items=1)
    EXP = Opcode(0x0A, popped_stack_items=2, pushed_stack_items=1)
    SIGNEXTEND = Opcode(0x0B, popped_stack_items=2, pushed_stack_items=1)

    LT = Opcode(0x10, popped_stack_items=2, pushed_stack_items=1)
    GT = Opcode(0x11, popped_stack_items=2, pushed_stack_items=1)
    SLT = Opcode(0x12, popped_stack_items=2, pushed_stack_items=1)
    SGT = Opcode(0x13, popped_stack_items=2, pushed_stack_items=1)
    EQ = Opcode(0x14, popped_stack_items=2, pushed_stack_items=1)
    ISZERO = Opcode(0x15, popped_stack_items=1, pushed_stack_items=1)
    AND = Opcode(0x16, popped_stack_items=2, pushed_stack_items=1)
    OR = Opcode(0x17, popped_stack_items=2, pushed_stack_items=1)
    XOR = Opcode(0x18, popped_stack_items=2, pushed_stack_items=1)
    NOT = Opcode(0x19, popped_stack_items=1, pushed_stack_items=1)
    BYTE = Opcode(0x1A, popped_stack_items=2, pushed_stack_items=1)
    SHL = Opcode(0x1B, popped_stack_items=2, pushed_stack_items=1)
    SHR = Opcode(0x1C, popped_stack_items=2, pushed_stack_items=1)
    SAR = Opcode(0x1D, popped_stack_items=2, pushed_stack_items=1)

    SHA3 = Opcode(0x20, popped_stack_items=2, pushed_stack_items=1)

    ADDRESS = Opcode(0x30, pushed_stack_items=1)
    BALANCE = Opcode(0x31, popped_stack_items=1, pushed_stack_items=1)
    ORIGIN = Opcode(0x32, pushed_stack_items=1)
    CALLER = Opcode(0x33, pushed_stack_items=1)
    CALLVALUE = Opcode(0x34, pushed_stack_items=1)
    CALLDATALOAD = Opcode(0x35, popped_stack_items=1, pushed_stack_items=1)
    CALLDATASIZE = Opcode(0x36, pushed_stack_items=1)
    CALLDATACOPY = Opcode(0x37, popped_stack_items=3)
    CODESIZE = Opcode(0x38, pushed_stack_items=1)
    CODECOPY = Opcode(0x39, popped_stack_items=3)
    GASPRICE = Opcode(0x3A, pushed_stack_items=1)
    EXTCODESIZE = Opcode(0x3B, popped_stack_items=1, pushed_stack_items=1)
    EXTCODECOPY = Opcode(0x3C, popped_stack_items=4)
    RETURNDATASIZE = Opcode(0x3D, pushed_stack_items=1)
    RETURNDATACOPY = Opcode(0x3E, popped_stack_items=3)
    EXTCODEHASH = Opcode(0x3F, popped_stack_items=1, pushed_stack_items=1)

    BLOCKHASH = Opcode(0x40, popped_stack_items=1, pushed_stack_items=1)
    COINBASE = Opcode(0x41, pushed_stack_items=1)
    TIMESTAMP = Opcode(0x42, pushed_stack_items=1)
    NUMBER = Opcode(0x43, pushed_stack_items=1)
    PREVRANDAO = Opcode(0x44, pushed_stack_items=1)
    GASLIMIT = Opcode(0x45, pushed_stack_items=1)
    CHAINID = Opcode(0x46, pushed_stack_items=1)
    SELFBALANCE = Opcode(0x47, pushed_stack_items=1)
    BASEFEE = Opcode(0x48, pushed_stack_items=1)

    POP = Opcode(0x50, popped_stack_items=1)
    MLOAD = Opcode(0x51, popped_stack_items=1, pushed_stack_items=1)
    MSTORE = Opcode(0x52, popped_stack_items=2)
    MSTORE8 = Opcode(0x53, popped_stack_items=2)
    SLOAD = Opcode(0x54, popped_stack_items=1, pushed_stack_items=1)
    SSTORE = Opcode(0x55, popped_stack_items=2)
    JUMP = Opcode(0x56, popped_stack_items=1)
    JUMPI = Opcode(0x57, popped_stack_items=2)
    PC = Opcode(0x58, pushed_stack_items=1)
    MSIZE = Opcode(0x59, pushed_stack_items=1)
    GAS = Opcode(0x5A, pushed_stack_items=1)
    JUMPDEST = Opcode(0x5B)
    RJUMP = Opcode(0x5C, data_portion_length=2)
    RJUMPI = Opcode(0x5D, popped_stack_items=1, data_portion_length=2)
    CALLF = Opcode(0x5E, data_portion_length=2)
    RETF = Opcode(0x49)

    PUSH0 = Opcode(0x5F, pushed_stack_items=1)
    PUSH1 = Opcode(0x60, pushed_stack_items=1, data_portion_length=1)
    PUSH2 = Opcode(0x61, pushed_stack_items=1, data_portion_length=2)
    PUSH3 = Opcode(0x62, pushed_stack_items=1, data_portion_length=3)
    PUSH4 = Opcode(0x63, pushed_stack_items=1, data_portion_length=4)
    PUSH5 = Opcode(0x64, pushed_stack_items=1, data_portion_length=5)
    PUSH6 = Opcode(0x65, pushed_stack_items=1, data_portion_length=6)
    PUSH7 = Opcode(0x66, pushed_stack_items=1, data_portion_length=7)
    PUSH8 = Opcode(0x67, pushed_stack_items=1, data_portion_length=8)
    PUSH9 = Opcode(0x68, pushed_stack_items=1, data_portion_length=9)
    PUSH10 = Opcode(0x69, pushed_stack_items=1, data_portion_length=10)
    PUSH11 = Opcode(0x6A, pushed_stack_items=1, data_portion_length=11)
    PUSH12 = Opcode(0x6B, pushed_stack_items=1, data_portion_length=12)
    PUSH13 = Opcode(0x6C, pushed_stack_items=1, data_portion_length=13)
    PUSH14 = Opcode(0x6D, pushed_stack_items=1, data_portion_length=14)
    PUSH15 = Opcode(0x6E, pushed_stack_items=1, data_portion_length=15)
    PUSH16 = Opcode(0x6F, pushed_stack_items=1, data_portion_length=16)
    PUSH17 = Opcode(0x70, pushed_stack_items=1, data_portion_length=17)
    PUSH18 = Opcode(0x71, pushed_stack_items=1, data_portion_length=18)
    PUSH19 = Opcode(0x72, pushed_stack_items=1, data_portion_length=19)
    PUSH20 = Opcode(0x73, pushed_stack_items=1, data_portion_length=20)
    PUSH21 = Opcode(0x74, pushed_stack_items=1, data_portion_length=21)
    PUSH22 = Opcode(0x75, pushed_stack_items=1, data_portion_length=22)
    PUSH23 = Opcode(0x76, pushed_stack_items=1, data_portion_length=23)
    PUSH24 = Opcode(0x77, pushed_stack_items=1, data_portion_length=24)
    PUSH25 = Opcode(0x78, pushed_stack_items=1, data_portion_length=25)
    PUSH26 = Opcode(0x79, pushed_stack_items=1, data_portion_length=26)
    PUSH27 = Opcode(0x7A, pushed_stack_items=1, data_portion_length=27)
    PUSH28 = Opcode(0x7B, pushed_stack_items=1, data_portion_length=28)
    PUSH29 = Opcode(0x7C, pushed_stack_items=1, data_portion_length=29)
    PUSH30 = Opcode(0x7D, pushed_stack_items=1, data_portion_length=30)
    PUSH31 = Opcode(0x7E, pushed_stack_items=1, data_portion_length=31)
    PUSH32 = Opcode(0x7F, pushed_stack_items=1, data_portion_length=32)

    DUP1 = Opcode(0x80, pushed_stack_items=1, min_stack_height=1)
    DUP2 = Opcode(0x81, pushed_stack_items=1, min_stack_height=2)
    DUP3 = Opcode(0x82, pushed_stack_items=1, min_stack_height=3)
    DUP4 = Opcode(0x83, pushed_stack_items=1, min_stack_height=4)
    DUP5 = Opcode(0x84, pushed_stack_items=1, min_stack_height=5)
    DUP6 = Opcode(0x85, pushed_stack_items=1, min_stack_height=6)
    DUP7 = Opcode(0x86, pushed_stack_items=1, min_stack_height=7)
    DUP8 = Opcode(0x87, pushed_stack_items=1, min_stack_height=8)
    DUP9 = Opcode(0x88, pushed_stack_items=1, min_stack_height=9)
    DUP10 = Opcode(0x89, pushed_stack_items=1, min_stack_height=10)
    DUP11 = Opcode(0x8A, pushed_stack_items=1, min_stack_height=11)
    DUP12 = Opcode(0x8B, pushed_stack_items=1, min_stack_height=12)
    DUP13 = Opcode(0x8C, pushed_stack_items=1, min_stack_height=13)
    DUP14 = Opcode(0x8D, pushed_stack_items=1, min_stack_height=14)
    DUP15 = Opcode(0x8E, pushed_stack_items=1, min_stack_height=15)
    DUP16 = Opcode(0x8F, pushed_stack_items=1, min_stack_height=16)

    SWAP1 = Opcode(0x90, min_stack_height=2)
    SWAP2 = Opcode(0x91, min_stack_height=3)
    SWAP3 = Opcode(0x92, min_stack_height=4)
    SWAP4 = Opcode(0x93, min_stack_height=5)
    SWAP5 = Opcode(0x94, min_stack_height=6)
    SWAP6 = Opcode(0x95, min_stack_height=7)
    SWAP7 = Opcode(0x96, min_stack_height=8)
    SWAP8 = Opcode(0x97, min_stack_height=9)
    SWAP9 = Opcode(0x98, min_stack_height=10)
    SWAP10 = Opcode(0x99, min_stack_height=11)
    SWAP11 = Opcode(0x9A, min_stack_height=12)
    SWAP12 = Opcode(0x9B, min_stack_height=13)
    SWAP13 = Opcode(0x9C, min_stack_height=14)
    SWAP14 = Opcode(0x9D, min_stack_height=15)
    SWAP15 = Opcode(0x9E, min_stack_height=16)
    SWAP16 = Opcode(0x9F, min_stack_height=17)

    LOG0 = Opcode(0xA0, popped_stack_items=2)
    LOG1 = Opcode(0xA1, popped_stack_items=3)
    LOG2 = Opcode(0xA2, popped_stack_items=4)
    LOG3 = Opcode(0xA3, popped_stack_items=5)
    LOG4 = Opcode(0xA4, popped_stack_items=6)

    TLOAD = Opcode(0xB3, popped_stack_items=1, pushed_stack_items=1)
    TSTORE = Opcode(0xB4, popped_stack_items=2)

    CREATE = Opcode(0xF0, popped_stack_items=3, pushed_stack_items=1)
    CALL = Opcode(0xF1, popped_stack_items=7, pushed_stack_items=1)
    CALLCODE = Opcode(0xF2, popped_stack_items=7, pushed_stack_items=1)
    RETURN = Opcode(0xF3, popped_stack_items=2)
    DELEGATECALL = Opcode(0xF4, popped_stack_items=6, pushed_stack_items=1)
    CREATE2 = Opcode(0xF5, popped_stack_items=4, pushed_stack_items=1)

    STATICCALL = Opcode(0xFA, popped_stack_items=6, pushed_stack_items=1)

    REVERT = Opcode(0xFD, popped_stack_items=2)
    INVALID = Opcode(0xFE)

    SELFDESTRUCT = Opcode(0xFF, popped_stack_items=1)
    SENDALL = Opcode(0xFF, popped_stack_items=1)
