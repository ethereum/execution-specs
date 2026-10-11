"""Shared scenario code for the EIP-8298 `SETCODEFROM` tests."""

from typing import Any

from execution_testing import Address, BalCodeChange, Bytecode, Hash, Op

RESULT_SLOT = 0
MARKER_SLOT = 0x7E
TEMPLATE_MARKER = 0x7E3A
TEMPLATE_B_MARKER = 0x7E3B
MARKED_SHELL_MARKER = 0x7E3C
SENTINEL = 0xDEAD  # pre-set so an expected 0 proves a write

TEMPLATE_CODE = Op.SSTORE(MARKER_SLOT, TEMPLATE_MARKER) + Op.STOP
TEMPLATE_B_CODE = Op.SSTORE(MARKER_SLOT, TEMPLATE_B_MARKER) + Op.STOP
# Adopt the source in the first calldata word and store the result.
SHELL_CODE = (
    Op.SSTORE(RESULT_SLOT, Op.SETCODEFROM(Op.CALLDATALOAD(0))) + Op.STOP
)
# A shell with its own marker, so its bytes differ from SHELL_CODE.
MARKED_SHELL_CODE = Op.SSTORE(MARKER_SLOT, MARKED_SHELL_MARKER) + SHELL_CODE
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
