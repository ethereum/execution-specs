"""
Test PC.

The original tests were written by Ori Pomerantz.

Ported from:
state_tests/VMTests/vmIOandFlowOperations/pcFiller.yml

@manually-enhanced: Do not overwrite. Each case names the code that runs
before `PC`, and the stored `PC` must equal that code's length: the byte
offset of the `PC` opcode, counting PUSH data and skipped code, not the
number of executed instructions.
"""

from enum import StrEnum

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
# Slot 0, so PUSH0 can push it.
PC_SLOT = 0
PRIOR_STORE_SLOT = 1
PRIOR_STORE_VALUE = 0xFF
SKIPPED_CODE_LENGTH = 16


class CodeBeforePc(StrEnum):
    """The code that runs before the `PC` under test."""

    CODE_START = "code_start"
    AFTER_SSTORE = "after_sstore"
    AFTER_PUSH32 = "after_push32"
    AFTER_JUMP = "after_jump"
    TWO_BYTE_PC = "two_byte_pc"
    MAX_CODE_SIZE = "max_code_size"


def store_pc(fork: Fork) -> Bytecode:
    """
    Return the code that stores `PC`.

    It ends the code without a STOP, so execution halts by running off
    the end, and pushes the slot with PUSH0 where the fork has it, so the
    `PC` sits as close to the end of the code as it can.
    """
    slot: int | Bytecode = PC_SLOT
    if Op.PUSH0 in fork.valid_opcodes():
        slot = Op.PUSH0
    return Op.SSTORE(slot, Op.PC)


def code_before_pc(kind: CodeBeforePc, fork: Fork) -> Bytecode:
    """Return the code that `kind` runs before `PC`."""
    match kind:
        case CodeBeforePc.CODE_START:
            return Bytecode()
        case CodeBeforePc.AFTER_SSTORE:
            return Op.SSTORE(PRIOR_STORE_SLOT, PRIOR_STORE_VALUE)
        case CodeBeforePc.AFTER_PUSH32:
            # PC counts the 32 data bytes as well as the opcode.
            return Op.POP(Op.PUSH32[2**256 - 1])
        case CodeBeforePc.AFTER_JUMP:
            # Jump over invalid code; PC is the offset after the landing
            # JUMPDEST, not the count of executed instructions.
            code = Op.JUMP(pc=Op.PUSH1(data_placeholder="landing"))
            code += Op.INVALID * SKIPPED_CODE_LENGTH
            code.substitute(landing=len(code))
            return code + Op.JUMPDEST
        case CodeBeforePc.TWO_BYTE_PC:
            # PC no longer fits in one byte.
            return Op.JUMPDEST * 0x100
        case CodeBeforePc.MAX_CODE_SIZE:
            # The `PC` sits at the end of the largest deployable code.
            return Op.JUMPDEST * (fork.max_code_size() - len(store_pc(fork)))
    raise ValueError(f"Unknown code before PC: {kind}")


@pytest.mark.ported_from(
    ["state_tests/VMTests/vmIOandFlowOperations/pcFiller.yml"],
)
@pytest.mark.valid_from("Frontier")
@pytest.mark.parametrize("kind", list(CodeBeforePc), ids=str)
def test_pc(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    kind: CodeBeforePc,
) -> None:
    """Store `PC` after `kind` and expect the offset of the `PC` opcode."""
    prefix = code_before_pc(kind, fork)
    code = prefix + store_pc(fork)
    if kind == CodeBeforePc.MAX_CODE_SIZE:
        assert len(code) == fork.max_code_size()
    contract = pre.deploy_contract(code=code, storage={PC_SLOT: SENTINEL})
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract,
        protected=fork.supports_protected_txs(),
    )
    storage = {PC_SLOT: len(prefix)}
    if kind == CodeBeforePc.AFTER_SSTORE:
        storage[PRIOR_STORE_SLOT] = PRIOR_STORE_VALUE
    post = {contract: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)
