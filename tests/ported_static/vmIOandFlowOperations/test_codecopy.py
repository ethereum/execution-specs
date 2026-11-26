"""
Test CODECOPY of the executing contract's code.

The original tests were written by Ori Pomerantz.

Ported from:
state_tests/VMTests/vmIOandFlowOperations/codecopyFiller.yml
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

SENTINEL = 0x0BAD
MAX_UINT = 2**256 - 1


def store_words(count: int) -> Bytecode:
    """Store the first `count` memory words in slots 0..count-1."""
    return sum(
        (Op.SSTORE(i, Op.MLOAD(i * 32)) for i in range(count)), Bytecode()
    )


def code_words(code: Bytecode, count: int) -> dict[int, int]:
    """Return the first `count` 32-byte words of `code`, zero padded."""
    padded = bytes(code).ljust(count * 32, b"\0")
    return {
        i: int.from_bytes(padded[i * 32 : (i + 1) * 32]) for i in range(count)
    }


@pytest.mark.ported_from(
    ["state_tests/VMTests/vmIOandFlowOperations/codecopyFiller.yml"],
)
@pytest.mark.valid_from("Frontier")
@pytest.mark.parametrize(
    "case",
    [
        "codecopy",
        "codecopy_infbuff",
        "codecopy_bigbuff",
        "codecopy_2buff",
        "codecopy_opcodes",
    ],
)
def test_codecopy(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    case: str,
) -> None:
    """Copy the contract's code to memory and store it word by word."""
    words = 2
    if case == "codecopy":
        code = Op.CODECOPY(dest_offset=0, offset=0, size=0x40)
    elif case == "codecopy_infbuff":
        code = Op.CODECOPY(dest_offset=0, offset=0, size=MAX_UINT)
    elif case == "codecopy_bigbuff":
        code = Op.CODECOPY(dest_offset=0, offset=0, size=0x1000)
    elif case == "codecopy_2buff":
        words = 3
        # Pad the code so the second copy reads a full word of real code
        # and then crosses the end of the code, which must zero-fill.
        padding: Bytecode | int = 1
        for i in range(2, 17):
            padding = Op.ADD(padding, i)
        code = (
            Op.MSTORE(0x100, padding)
            + Op.CODECOPY(dest_offset=0, offset=0, size=0x20)
            + Op.CODECOPY(dest_offset=0x20, offset=0x20, size=0x40)
        )
    elif case == "codecopy_opcodes":
        words = 6
        code = (
            Op.SSTORE(0xFF, Op.CODESIZE)
            + Op.CODECOPY(dest_offset=0, offset=0, size=Op.SLOAD(0xFF))
            + Op.SSTORE(0, 0x60A7)
            + Op.SSTORE(1, 0x60A7)
            + Op.SSTORE(2, 0x60A7)
        )
    else:
        raise ValueError(f"Unknown case: {case}")
    code += store_words(words) + Op.STOP
    if case == "codecopy_2buff":
        assert 0x40 < len(code) < 0x60, "code must end inside word 2"
    if case == "codecopy_opcodes":
        # Unreachable, potentially problematic opcodes after the STOP:
        # CODECOPY must copy them verbatim as plain data, without
        # interpreting them or truncating the code at a terminator.
        code += (
            Op.SELFDESTRUCT(address=0xDEAD)
            + Op.RETURN(offset=0, size=Op.SLOAD(0xFF))
            + Op.DELEGATECALL(
                gas=0xFF,
                address=0xEE,
                args_offset=0xDD,
                args_size=0xCC,
                ret_offset=0xBB,
                ret_size=0xAA,
            )
            + Op.STOP
        )

    pre_storage: dict = dict.fromkeys(range(words), SENTINEL)
    contract = pre.deploy_contract(code=code, storage=pre_storage)
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract,
        protected=fork.supports_protected_txs(),
    )
    if case == "codecopy_infbuff":
        storage = pre_storage
    else:
        storage = code_words(code, words)
        if case == "codecopy_opcodes":
            storage[0xFF] = len(code)
    post = {contract: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)
