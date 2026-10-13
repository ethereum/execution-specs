"""Shared scenario code for the EIP-8298 `SETCODEFROM` tests."""

from typing import Any

from execution_testing import Address, BalCodeChange, Bytecode, Hash, Op

RESULT_SLOT = 0
MARKER_SLOT = 0x7E
MARKER_A = 0x7E3A
MARKER_B = 0x7E3B
MARKER_C = 0x7E3C
SENTINEL = 0xDEAD  # pre-set so an expected 0 proves a write

SSTORE_MARKER_A = Op.SSTORE(MARKER_SLOT, MARKER_A) + Op.STOP
SSTORE_MARKER_B = Op.SSTORE(MARKER_SLOT, MARKER_B) + Op.STOP
# Adopt the source in the first calldata word and store the result.
ADOPT_FROM_CALLDATA = (
    Op.SSTORE(RESULT_SLOT, Op.SETCODEFROM(Op.CALLDATALOAD(0))) + Op.STOP
)
# Like ADOPT_FROM_CALLDATA, with a marker first so its bytes differ.
SSTORE_MARKER_C_THEN_ADOPT = (
    Op.SSTORE(MARKER_SLOT, MARKER_C) + ADOPT_FROM_CALLDATA
)
# Revert with the current account's code hash as the revert data.
REVERT_WITH_CODE_HASH = Op.MSTORE(0, Op.EXTCODEHASH(Op.ADDRESS)) + Op.REVERT(
    0, 32
)


def adopt_code(**metadata: bool) -> Bytecode:
    """Return code that adopts the source in the first calldata word."""
    return Op.SETCODEFROM(Op.CALLDATALOAD(0), **metadata) + Op.STOP


def multi_code(**metadata: bool) -> Bytecode:
    """Return code that adopts the sources in calldata words 0 to 2."""
    adoptions = sum(
        (
            Op.POP(Op.SETCODEFROM(Op.CALLDATALOAD(offset), **metadata))
            for offset in (0, 32, 64)
        ),
        Bytecode(),
    )
    return adoptions + Op.STOP


def word(address: Address) -> Hash:
    """Return `address` as a 32-byte calldata word."""
    return Hash(address, left_padding=True)


def call_with(
    target: Address | Bytecode,
    source: Address | Bytecode | None = None,
    *,
    call_opcode: Op = Op.CALL,
    **kwargs: Any,
) -> Bytecode:
    """
    Call `target` with `source` as its only calldata word, leaving the
    call result on the stack.
    """
    if source is None:
        return call_opcode(address=target, **kwargs)
    return Op.MSTORE(0, source) + call_opcode(
        address=target, args_size=32, **kwargs
    )


def adoption(index: int, code: Bytecode) -> list[BalCodeChange]:
    """Return the BAL code change that records adopting `code`."""
    return [
        BalCodeChange(
            block_access_index=index,
            new_code=b"",
            new_code_hash=code.keccak256(),
        )
    ]
