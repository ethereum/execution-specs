"""
Test RETURN data seen by a DELEGATECALL caller.

Ported from:
state_tests/VMTests/vmIOandFlowOperations/returnFiller.yml
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

SENTINEL = 0x0BAD
DONE = 0x600D
MAX_UINT = 2**256 - 1
WORD = 0x0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF


def return_word(offset: int, size: int) -> Bytecode:
    """Store a word in memory, mark slot 0xFF and return a memory range."""
    return (
        Op.MSTORE(0, WORD)
        + Op.SSTORE(0xFF, DONE)
        + Op.RETURN(offset=offset, size=size)
        + Op.STOP
    )


def returned_words(offset: int) -> dict[int, int]:
    """Return the two words the caller reads from a successful return."""
    memory = WORD.to_bytes(32, "big").ljust(offset + 0x40, b"\0")
    data = memory[offset : offset + 0x40]
    return {0: int.from_bytes(data[:32]), 1: int.from_bytes(data[32:])}


@pytest.mark.ported_from(
    ["state_tests/VMTests/vmIOandFlowOperations/returnFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "case",
    ["return", "returnInfBuff", "returnBigBuff", "returnOffset", "returnOld"],
)
def test_return(
    state_test: StateTestFiller,
    pre: Alloc,
    case: str,
) -> None:
    """Copy 0x40 bytes of return data from a delegated frame into storage."""
    storage: dict[int, int]
    if case == "return":
        code = return_word(offset=0, size=0x40)
        storage = {**returned_words(0), 0xFF: DONE}
    elif case == "returnInfBuff":
        code = return_word(offset=0, size=MAX_UINT)
        storage = {0: 0, 1: 0, 0xFF: SENTINEL}
    elif case == "returnBigBuff":
        code = return_word(offset=0, size=0x1000)
        storage = {**returned_words(0), 0xFF: DONE}
    elif case == "returnOffset":
        code = return_word(offset=5, size=0x20)
        storage = {**returned_words(5), 1: 0, 0xFF: DONE}
    elif case == "returnOld":
        code = (
            Op.MSTORE(offset=0x80, value=0x1)
            + Op.JUMPI(pc=0x1B, condition=Op.GT(Op.MLOAD(offset=0x80), 0x0))
            + Op.MSTORE(offset=0x0, value=0x1)
            + Op.RETURN(offset=0x0, size=0x20)
            + Op.JUMP(pc=0x2B)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x0, value=0x27)
            + Op.RETURN(offset=0x0, size=0x20)
            + Op.MSTORE(offset=0x80, value=0x2)
            + Op.JUMPDEST
            + Op.STOP
        )
        storage = {0: 0x27, 1: 0, 0xFF: SENTINEL}
    else:
        raise ValueError(f"Unknown case: {case}")

    callee = pre.deploy_contract(code=code)
    caller = pre.deploy_contract(
        code=Op.POP(Op.DELEGATECALL(address=callee, ret_size=0x40))
        + Op.SSTORE(0, Op.MLOAD(0))
        + Op.SSTORE(1, Op.MLOAD(0x20))
        + Op.STOP,
        storage={0: SENTINEL, 1: SENTINEL, 0xFF: SENTINEL},
    )
    tx = Transaction(sender=pre.fund_eoa(), to=caller)
    post = {caller: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)
