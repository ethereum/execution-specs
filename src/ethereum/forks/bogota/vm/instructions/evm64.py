"""
Ethereum Virtual Machine (EVM) 64-bit Instructions.

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Implementations of the EVM 64-bit instructions: the twins of the
arithmetic, comparison, bitwise, and three memory instructions, operating
on the low 64 bits of their operands.

Each instruction reads only the low 64 bits of each operand — the operand
modulo 2**64 — and pushes its 64-bit result zero-extended to 256 bits.
Signed instructions read the low 64 bits as a two's-complement integer.
Equivalently, each computes what its twin computes on the operands' low 64
bits, zero- or sign-extended, reduced modulo 2**64.
"""

from ethereum_types.numeric import U256, Uint

from ethereum.utils.numeric import get_sign

from ...fork_types import ExecutionGas
from .. import Evm
from ..gas import GasCosts, calculate_gas_extend_memory, charge_gas
from ..memory import buffer_read, memory_read_bytes, memory_write
from ..stack import pop, push

U64_MAX_VALUE = 2**64 - 1
U64_CEIL_VALUE = 2**64
U63_CEIL_VALUE = 2**63


def low64(x: U256) -> int:
    """
    The low 64 bits of a word, as an unsigned integer.
    """
    return int(x) & U64_MAX_VALUE


def signed64(x: U256) -> int:
    """
    The low 64 bits of a word, as a two's-complement integer.
    """
    value = low64(x)
    return value - U64_CEIL_VALUE if value >> 63 else value


def push64(evm: Evm, value: int) -> None:
    """
    Push a 64-bit result: `value` reduced modulo 2**64, zero-extended to a
    256-bit word.
    """
    push(evm.stack, U256(value % U64_CEIL_VALUE))


# Arithmetic


def add64(evm: Evm) -> None:
    """
    Adds the low 64 bits of the top two elements of the stack and pushes
    the result, modulo 2**64, back on the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    x = low64(pop(evm.stack))
    y = low64(pop(evm.stack))

    # GAS
    charge_gas(evm, GasCosts.OPCODE_ADD64)

    # OPERATION
    push64(evm, x + y)

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def mul64(evm: Evm) -> None:
    """
    Multiplies the low 64 bits of the top two elements of the stack and
    pushes the result, modulo 2**64, back on the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    x = low64(pop(evm.stack))
    y = low64(pop(evm.stack))

    # GAS
    charge_gas(evm, GasCosts.OPCODE_MUL64)

    # OPERATION
    push64(evm, x * y)

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def sub64(evm: Evm) -> None:
    """
    Subtracts the low 64 bits of the second element of the stack from
    those of the first and pushes the result, modulo 2**64, back on the
    stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    x = low64(pop(evm.stack))
    y = low64(pop(evm.stack))

    # GAS
    charge_gas(evm, GasCosts.OPCODE_SUB64)

    # OPERATION
    push64(evm, x - y)

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def div64(evm: Evm) -> None:
    """
    Integer division of the low 64 bits of the top two elements of the
    stack. Pushes the quotient, or zero for a zero divisor, back on the
    stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    dividend = low64(pop(evm.stack))
    divisor = low64(pop(evm.stack))

    # GAS
    charge_gas(evm, GasCosts.OPCODE_DIV64)

    # OPERATION
    if divisor == 0:
        quotient = 0
    else:
        quotient = dividend // divisor

    push64(evm, quotient)

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def sdiv64(evm: Evm) -> None:
    """
    Signed integer division of the low 64 bits of the top two elements of
    the stack, truncating toward zero. Pushes the quotient, or zero for a
    zero divisor, back on the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    dividend = signed64(pop(evm.stack))
    divisor = signed64(pop(evm.stack))

    # GAS
    charge_gas(evm, GasCosts.OPCODE_SDIV64)

    # OPERATION
    if divisor == 0:
        quotient = 0
    elif dividend == -U63_CEIL_VALUE and divisor == -1:
        quotient = -U63_CEIL_VALUE
    else:
        sign = get_sign(dividend * divisor)
        quotient = sign * (abs(dividend) // abs(divisor))

    push64(evm, quotient)

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def mod64(evm: Evm) -> None:
    """
    Modulo remainder of the low 64 bits of the top two elements of the
    stack. Pushes the remainder, or zero for a zero divisor, back on the
    stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    x = low64(pop(evm.stack))
    y = low64(pop(evm.stack))

    # GAS
    charge_gas(evm, GasCosts.OPCODE_MOD64)

    # OPERATION
    if y == 0:
        remainder = 0
    else:
        remainder = x % y

    push64(evm, remainder)

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def smod64(evm: Evm) -> None:
    """
    Signed modulo remainder of the low 64 bits of the top two elements of
    the stack, taking the sign of the dividend. Pushes the remainder, or
    zero for a zero divisor, back on the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    x = signed64(pop(evm.stack))
    y = signed64(pop(evm.stack))

    # GAS
    charge_gas(evm, GasCosts.OPCODE_SMOD64)

    # OPERATION
    if y == 0:
        remainder = 0
    else:
        remainder = get_sign(x) * (abs(x) % abs(y))

    push64(evm, remainder)

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def addmod64(evm: Evm) -> None:
    """
    Modulo addition of the low 64 bits of the top three elements of the
    stack: the sum of the first two, not reduced, modulo the third. Pushes
    the result, or zero for a zero modulus, back on the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    x = low64(pop(evm.stack))
    y = low64(pop(evm.stack))
    z = low64(pop(evm.stack))

    # GAS
    charge_gas(evm, GasCosts.OPCODE_ADDMOD64)

    # OPERATION
    if z == 0:
        result = 0
    else:
        result = (x + y) % z

    push64(evm, result)

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def mulmod64(evm: Evm) -> None:
    """
    Modulo multiplication of the low 64 bits of the top three elements of
    the stack: the product of the first two, not reduced, modulo the
    third. Pushes the result, or zero for a zero modulus, back on the
    stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    x = low64(pop(evm.stack))
    y = low64(pop(evm.stack))
    z = low64(pop(evm.stack))

    # GAS
    charge_gas(evm, GasCosts.OPCODE_MULMOD64)

    # OPERATION
    if z == 0:
        result = 0
    else:
        result = (x * y) % z

    push64(evm, result)

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def exp64(evm: Evm) -> None:
    """
    Exponentiation of the low 64 bits of the top two elements of the
    stack. Pushes the result, modulo 2**64, back on the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    base = low64(pop(evm.stack))
    exponent = low64(pop(evm.stack))

    # GAS
    exponent_bytes = (exponent.bit_length() + 7) // 8
    charge_gas(
        evm,
        ExecutionGas(
            GasCosts.OPCODE_EXP64_BASE
            + GasCosts.OPCODE_EXP64_PER_BYTE * Uint(exponent_bytes)
        ),
    )

    # OPERATION
    push64(evm, pow(base, exponent, U64_CEIL_VALUE))

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def signextend64(evm: Evm) -> None:
    """
    Sign-extends the low 64 bits of the second element of the stack from
    the byte indexed by the first: bit 8 * index + 7 is copied upward
    through bit 63. An index above 6 leaves the value unchanged.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    byte_num = low64(pop(evm.stack))
    value = low64(pop(evm.stack))

    # GAS
    charge_gas(evm, GasCosts.OPCODE_SIGNEXTEND64)

    # OPERATION
    if byte_num > 6:
        # Can't extend any further
        result = value
    else:
        sign_bit = 8 * byte_num + 7
        low_bits = (1 << (sign_bit + 1)) - 1
        if (value >> sign_bit) & 1:
            result = value | (U64_MAX_VALUE ^ low_bits)
        else:
            result = value & low_bits

    push64(evm, result)

    # PROGRAM COUNTER
    evm.pc += Uint(1)


# Comparison


def lt64(evm: Evm) -> None:
    """
    Checks if the low 64 bits of the top element are less than those of
    the next. Pushes 1 if so, else 0.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    left = low64(pop(evm.stack))
    right = low64(pop(evm.stack))

    # GAS
    charge_gas(evm, GasCosts.OPCODE_LT64)

    # OPERATION
    push64(evm, 1 if left < right else 0)

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def gt64(evm: Evm) -> None:
    """
    Checks if the low 64 bits of the top element are greater than those of
    the next. Pushes 1 if so, else 0.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    left = low64(pop(evm.stack))
    right = low64(pop(evm.stack))

    # GAS
    charge_gas(evm, GasCosts.OPCODE_GT64)

    # OPERATION
    push64(evm, 1 if left > right else 0)

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def slt64(evm: Evm) -> None:
    """
    Signed comparison: checks if the low 64 bits of the top element, as a
    two's-complement integer, are less than those of the next. Pushes 1 if
    so, else 0.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    left = signed64(pop(evm.stack))
    right = signed64(pop(evm.stack))

    # GAS
    charge_gas(evm, GasCosts.OPCODE_SLT64)

    # OPERATION
    push64(evm, 1 if left < right else 0)

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def sgt64(evm: Evm) -> None:
    """
    Signed comparison: checks if the low 64 bits of the top element, as a
    two's-complement integer, are greater than those of the next. Pushes
    1 if so, else 0.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    left = signed64(pop(evm.stack))
    right = signed64(pop(evm.stack))

    # GAS
    charge_gas(evm, GasCosts.OPCODE_SGT64)

    # OPERATION
    push64(evm, 1 if left > right else 0)

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def eq64(evm: Evm) -> None:
    """
    Checks if the low 64 bits of the top two elements are equal. Pushes 1
    if so, else 0.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    left = low64(pop(evm.stack))
    right = low64(pop(evm.stack))

    # GAS
    charge_gas(evm, GasCosts.OPCODE_EQ64)

    # OPERATION
    push64(evm, 1 if left == right else 0)

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def iszero64(evm: Evm) -> None:
    """
    Checks if the low 64 bits of the top element are zero. Pushes 1 if so,
    else 0.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    x = low64(pop(evm.stack))

    # GAS
    charge_gas(evm, GasCosts.OPCODE_ISZERO64)

    # OPERATION
    push64(evm, 1 if x == 0 else 0)

    # PROGRAM COUNTER
    evm.pc += Uint(1)


# Bitwise


def and64(evm: Evm) -> None:
    """
    Bitwise AND of the low 64 bits of the top two elements of the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    x = low64(pop(evm.stack))
    y = low64(pop(evm.stack))

    # GAS
    charge_gas(evm, GasCosts.OPCODE_AND64)

    # OPERATION
    push64(evm, x & y)

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def or64(evm: Evm) -> None:
    """
    Bitwise OR of the low 64 bits of the top two elements of the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    x = low64(pop(evm.stack))
    y = low64(pop(evm.stack))

    # GAS
    charge_gas(evm, GasCosts.OPCODE_OR64)

    # OPERATION
    push64(evm, x | y)

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def xor64(evm: Evm) -> None:
    """
    Bitwise XOR of the low 64 bits of the top two elements of the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    x = low64(pop(evm.stack))
    y = low64(pop(evm.stack))

    # GAS
    charge_gas(evm, GasCosts.OPCODE_XOR64)

    # OPERATION
    push64(evm, x ^ y)

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def not64(evm: Evm) -> None:
    """
    Bitwise NOT of the low 64 bits of the top element of the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    x = low64(pop(evm.stack))

    # GAS
    charge_gas(evm, GasCosts.OPCODE_NOT64)

    # OPERATION
    push64(evm, x ^ U64_MAX_VALUE)

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def shl64(evm: Evm) -> None:
    """
    Shifts the low 64 bits of the second element of the stack left by the
    number of bits given by the first, modulo 2**64. A shift of 64 or more
    yields zero.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    shift = low64(pop(evm.stack))
    value = low64(pop(evm.stack))

    # GAS
    charge_gas(evm, GasCosts.OPCODE_SHL64)

    # OPERATION
    if shift < 64:
        result = (value << shift) & U64_MAX_VALUE
    else:
        result = 0

    push64(evm, result)

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def shr64(evm: Evm) -> None:
    """
    Shifts the low 64 bits of the second element of the stack right by the
    number of bits given by the first, filling with zeros. A shift of 64 or
    more yields zero.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    shift = low64(pop(evm.stack))
    value = low64(pop(evm.stack))

    # GAS
    charge_gas(evm, GasCosts.OPCODE_SHR64)

    # OPERATION
    if shift < 64:
        result = value >> shift
    else:
        result = 0

    push64(evm, result)

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def sar64(evm: Evm) -> None:
    """
    Shifts the low 64 bits of the second element of the stack right by the
    number of bits given by the first, filling with the sign bit. A shift
    of 64 or more yields zero or all ones, by the sign.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    shift = low64(pop(evm.stack))
    signed_value = signed64(pop(evm.stack))

    # GAS
    charge_gas(evm, GasCosts.OPCODE_SAR64)

    # OPERATION
    if shift < 64:
        result = signed_value >> shift
    elif signed_value >= 0:
        result = 0
    else:
        result = -1

    push64(evm, result)

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def clz64(evm: Evm) -> None:
    """
    Counts the leading zero bits of the low 64 bits of the top element of
    the stack. Pushes 64 for zero.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    x = low64(pop(evm.stack))

    # GAS
    charge_gas(evm, GasCosts.OPCODE_CLZ64)

    # OPERATION
    push64(evm, 64 - x.bit_length())

    # PROGRAM COUNTER
    evm.pc += Uint(1)


# Calldata and memory


def calldataload64(evm: Evm) -> None:
    """
    Pushes the low eight bytes of the 32-byte word of the input data at
    the given offset: what `CALLDATALOAD` would push, modulo 2**64. The
    offset, like every operand, is read modulo 2**64; bytes past the end
    of the input data read as zero.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    start_index = U256(low64(pop(evm.stack)))

    # GAS
    charge_gas(evm, GasCosts.OPCODE_CALLDATALOAD64)

    # OPERATION
    value = buffer_read(evm.call_data, start_index, U256(32))

    push(evm.stack, U256.from_be_bytes(value[24:32]))

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def mload64(evm: Evm) -> None:
    """
    Pushes the low eight bytes of the 32-byte word of memory at the given
    offset: what `MLOAD` would push, modulo 2**64. The offset, like every
    operand, is read modulo 2**64; memory is extended as for `MLOAD`.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    start_position = U256(low64(pop(evm.stack)))

    # GAS
    extend_memory = calculate_gas_extend_memory(
        evm.memory, [(start_position, U256(32))]
    )
    charge_gas(evm, GasCosts.OPCODE_MLOAD64_BASE + extend_memory.cost)

    # OPERATION
    evm.memory += b"\x00" * extend_memory.expand_by
    value = U256.from_be_bytes(
        memory_read_bytes(evm.memory, start_position + U256(24), U256(8))
    )
    push(evm.stack, value)

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def mstore64(evm: Evm) -> None:
    """
    Stores the low 64 bits of a word to memory at the given offset, as the
    32-byte word `MSTORE` would store of that value: 24 zero bytes, then
    the eight bytes of the value. The offset, like every operand, is read
    modulo 2**64; memory is extended as for `MSTORE`.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    start_position = U256(low64(pop(evm.stack)))
    value = U256(low64(pop(evm.stack))).to_be_bytes32()

    # GAS
    extend_memory = calculate_gas_extend_memory(
        evm.memory, [(start_position, U256(len(value)))]
    )
    charge_gas(evm, GasCosts.OPCODE_MSTORE64_BASE + extend_memory.cost)

    # OPERATION
    evm.memory += b"\x00" * extend_memory.expand_by
    memory_write(evm.memory, start_position, value)

    # PROGRAM COUNTER
    evm.pc += Uint(1)
