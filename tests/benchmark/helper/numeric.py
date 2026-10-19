"""Numeric and stack-manipulation helpers for benchmark bytecode."""

from execution_testing import Op

DEFAULT_BINOP_ARGS = (
    0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F,
    0x73EDA753299D7D483339D80809A1D80553BDA402FFFE5BFEFFFFFFFF00000001,
)


def neg(x: int) -> int:
    """Negate the given integer in the two's complement 256-bit range."""
    assert 0 <= x < 2**256
    return 2**256 - x


def make_dup(index: int) -> Op:
    """
    Create a DUP instruction which duplicates the index-th (counting from 0)
    element from the top of the stack. E.g. make_dup(0) → DUP1.
    """
    assert 0 <= index < 16, f"DUP index {index} out of range [0, 15]"
    return getattr(Op, f"DUP{index + 1}")


def to_signed(x: int) -> int:
    """Convert an unsigned integer to a signed integer."""
    return x if x < 2**255 else x - 2**256


def to_unsigned(x: int) -> int:
    """Convert a signed integer to an unsigned integer."""
    return x if x >= 0 else x + 2**256


def shr(x: int, s: int) -> int:
    """Shift right."""
    return x >> s


def shl(x: int, s: int) -> int:
    """Shift left."""
    return x << s


def sar(x: int, s: int) -> int:
    """Arithmetic shift right."""
    return to_unsigned(to_signed(x) >> s)
