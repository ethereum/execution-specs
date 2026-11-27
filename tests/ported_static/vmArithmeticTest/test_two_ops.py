"""
Test arithmetic and logic opcodes applied to each other's results.

The original tests were written by Ori Pomerantz.

Ported from:
state_tests/VMTests/vmArithmeticTest/twoOpsFiller.yml

@manually-enhanced: Do not overwrite. Built from a model of the opcodes.

Every inner operation runs on the constants 2, 1 and 3 (as many as it
takes), and its result becomes the first operand of the outer operation,
whose remaining operands are 3, 1 or -2, then 2. Each case runs one contract
per outer operation that stores the result for every inner operation in
its own slot, pre-set to a sentinel so that a zero result is still
observable, and the expected storage comes from a Python model of the
opcodes. The shift opcodes take part from the fork that introduced them.
"""

from typing import Callable, Generator

import pytest
from _pytest.mark.structures import ParameterSet
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Fork,
    StateTestFiller,
    Storage,
    Transaction,
)
from execution_testing.vm import Op, Opcode

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

pytestmark = [
    pytest.mark.ported_from(
        ["state_tests/VMTests/vmArithmeticTest/twoOpsFiller.yml"],
    ),
    pytest.mark.valid_from("Frontier"),
]

WORD_MODULUS = 2**256
MAX_UINT = WORD_MODULUS - 1
SENTINEL = 0x0BAD

INNER_OPERANDS = (2, 1, 3)
# -2 as a 256-bit word.
NEGATIVE_TWO = WORD_MODULUS - 2
# The outer operation's second operand takes each of these values. The
# negative one makes the sign visible to SMOD, whose dividend NOT(2) is
# negative, and to SAR, which then shifts a negative value.
OUTER_SECOND_OPERANDS = (3, 1, NEGATIVE_TWO)
OUTER_THIRD_OPERAND = 2


def signed(value: int) -> int:
    """Return the two's complement reading of a 256-bit word."""
    return value - WORD_MODULUS if value >> 255 else value


def sdiv(a: int, b: int) -> int:
    """Return `SDIV(a, b)`: truncated signed division, zero for `b == 0`."""
    if b == 0:
        return 0
    quotient = abs(signed(a)) // abs(signed(b))
    if (signed(a) < 0) != (signed(b) < 0):
        quotient = -quotient
    return quotient % WORD_MODULUS


def smod(a: int, b: int) -> int:
    """Return `SMOD(a, b)`: the remainder takes the sign of `a`."""
    if b == 0:
        return 0
    remainder = abs(signed(a)) % abs(signed(b))
    if signed(a) < 0:
        remainder = -remainder
    return remainder % WORD_MODULUS


def byte(index: int, value: int) -> int:
    """Return `BYTE(index, value)`, counting from the most significant."""
    if index >= 32:
        return 0
    return (value >> (8 * (31 - index))) & 0xFF


def shl(shift: int, value: int) -> int:
    """Return `SHL(shift, value)`, zero once every bit is shifted out."""
    if shift >= 256:
        return 0
    return (value << shift) % WORD_MODULUS


# The result of each operation, as a function of its stack operands.
MODEL: dict[Opcode, Callable[..., int]] = {
    Op.ADD: lambda a, b: (a + b) % WORD_MODULUS,
    Op.MUL: lambda a, b: (a * b) % WORD_MODULUS,
    Op.SUB: lambda a, b: (a - b) % WORD_MODULUS,
    Op.DIV: lambda a, b: a // b if b else 0,
    Op.SDIV: sdiv,
    Op.MOD: lambda a, b: a % b if b else 0,
    Op.SMOD: smod,
    Op.ADDMOD: lambda a, b, n: (a + b) % n if n else 0,
    Op.MULMOD: lambda a, b, n: (a * b) % n if n else 0,
    Op.EXP: lambda a, b: pow(a, b, WORD_MODULUS),
    Op.LT: lambda a, b: int(a < b),
    Op.GT: lambda a, b: int(a > b),
    Op.SLT: lambda a, b: int(signed(a) < signed(b)),
    Op.SGT: lambda a, b: int(signed(a) > signed(b)),
    Op.EQ: lambda a, b: int(a == b),
    Op.ISZERO: lambda a: int(a == 0),
    Op.AND: lambda a, b: a & b,
    Op.OR: lambda a, b: a | b,
    Op.XOR: lambda a, b: a ^ b,
    Op.NOT: lambda a: a ^ MAX_UINT,
    Op.BYTE: byte,
    Op.SHL: shl,
    Op.SHR: lambda shift, value: value >> shift,
    Op.SAR: lambda shift, value: (signed(value) >> shift) % WORD_MODULUS,
}


def operations(fork: Fork) -> list[Opcode]:
    """Return the modelled operations that exist on `fork`."""
    valid_opcodes = set(fork.valid_opcodes())
    return [opcode for opcode in MODEL if opcode in valid_opcodes]


def outer_operations_by_fork(
    fork: Fork,
) -> Generator[ParameterSet, None, None]:
    """Yield each modelled operation that exists on `fork`."""
    for opcode in operations(fork):
        yield pytest.param(opcode, id=opcode._name_.lower())


@pytest.mark.parametrize_by_fork("outer", outer_operations_by_fork)
def test_two_ops(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    outer: Opcode,
) -> None:
    """Store `outer` applied to the result of every inner operation."""
    if outer.popped_stack_items == 1:
        # A unary operation takes no second operand to vary.
        outer_operand_tails: list[tuple[int, ...]] = [()]
    elif outer.popped_stack_items == 2:
        outer_operand_tails = [(second,) for second in OUTER_SECOND_OPERANDS]
    elif outer.popped_stack_items == 3:
        outer_operand_tails = [
            (second, OUTER_THIRD_OPERAND) for second in OUTER_SECOND_OPERANDS
        ]
    else:
        raise ValueError(f"Unexpected arity of {outer}")

    code = Bytecode()
    storage = Storage()
    for inner in operations(fork):
        inner_operands = INNER_OPERANDS[: inner.popped_stack_items]
        inner_result = MODEL[inner](*inner_operands)
        for tail in outer_operand_tails:
            slot = storage.store_next(
                MODEL[outer](inner_result, *tail),
                hint=f"{outer}({inner}{inner_operands}, {tail})",
            )
            code += Op.SSTORE(slot, outer(inner(*inner_operands), *tail))
    code += Op.STOP

    contract = pre.deploy_contract(
        code=code, storage=dict.fromkeys(storage.keys(), SENTINEL)
    )
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract,
        protected=fork.supports_protected_txs(),
    )
    post = {contract: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)
