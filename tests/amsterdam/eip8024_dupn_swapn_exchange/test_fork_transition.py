"""Fork-transition tests for EIP-8024 (DUPN, SWAPN, EXCHANGE)."""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytecode,
    EIPChecklist,
    Op,
    Transaction,
)

from .spec import ref_spec_8024

REFERENCE_SPEC_GIT_PATH = ref_spec_8024.git_path
REFERENCE_SPEC_VERSION = ref_spec_8024.version

FORK_TIMESTAMP = 15_000


def marker_storing_code(opcode: Op) -> tuple[Bytecode, int]:
    """
    Build code that stores an opcode-specific marker at storage key NUMBER.

    Each snippet plants the marker at the exact stack depth the opcode
    accesses, executes the opcode, and stores the resulting stack top so
    the write only happens if the opcode moved the marker as specified.
    """
    if opcode == Op.DUPN:
        marker = 0xA1
        code = Op.PUSH1(marker) + Op.PUSH0 * 16 + Op.DUPN[17]
    elif opcode == Op.SWAPN:
        marker = 0xB2
        code = Op.PUSH1(marker) + Op.PUSH0 * 17 + Op.SWAPN[17]
    else:
        marker = 0xC3
        code = Op.PUSH1(marker) + Op.PUSH0 * 2 + Op.EXCHANGE[1, 2] + Op.POP
    return code + Op.NUMBER + Op.SSTORE + Op.STOP, marker


@EIPChecklist.Opcode.Test.ForkTransition.Invalid()
@EIPChecklist.Opcode.Test.ForkTransition.At()
@pytest.mark.valid_at_transition_to("EIP8024")
@pytest.mark.parametrize("opcode", [Op.DUPN, Op.SWAPN, Op.EXCHANGE])
def test_opcode_at_fork_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    opcode: Op,
) -> None:
    """
    Test DUPN/SWAPN/EXCHANGE behavior across the EIP-8024 fork transition.

    Before the fork, opcodes 0xE6-0xE8 are undefined: execution halts
    with an invalid-opcode exception and no storage write happens.

    From the fork onward, the opcode executes and stores its marker.
    Storage is keyed by block NUMBER so each block's outcome is
    independently visible in the final post-state:

    * block 1 (pre-fork): slot 1 stays 0 — execution halted.
    * block 2 (transition): slot 2 == marker.
    * block 3 (post-fork): slot 3 == marker.
    """
    sender = pre.fund_eoa()
    code, marker = marker_storing_code(opcode)
    contract = pre.deploy_contract(code)

    blocks = [
        Block(
            timestamp=ts,
            txs=[Transaction(sender=sender, to=contract)],
        )
        for ts in (
            FORK_TIMESTAMP - 1,
            FORK_TIMESTAMP,
            FORK_TIMESTAMP + 1,
        )
    ]

    post = {
        contract: Account(
            storage={
                1: 0,
                2: marker,
                3: marker,
            },
        ),
    }

    blockchain_test(pre=pre, blocks=blocks, post=post)


@EIPChecklist.Opcode.Test.ForkTransition.At()
@EIPChecklist.Opcode.Test.DataPortion.Jump()
@pytest.mark.valid_at_transition_to("EIP8024")
@pytest.mark.parametrize("opcode", [Op.DUPN, Op.SWAPN, Op.EXCHANGE])
def test_jumpdest_in_immediate_at_fork_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    opcode: Op,
) -> None:
    """
    Test a JUMPDEST inside an EIP-8024 immediate across the transition.

    JUMPDEST analysis is unchanged by EIP-8024, so the 0x5b byte in the
    opcode's would-be immediate is a valid jump destination both before
    and after the fork. The jump skips the opcode byte itself, so every
    block stores the marker at its NUMBER-keyed slot.
    """
    sender = pre.fund_eoa()
    marker = 0xD4

    # 00 PUSH1 0x04
    # 02 JUMP
    # 03 <opcode>
    # 04 JUMPDEST (the would-be immediate)
    code = Op.PUSH1(4) + Op.JUMP + opcode[b"\x5b"]
    code += Op.PUSH1(marker) + Op.NUMBER + Op.SSTORE + Op.STOP

    contract = pre.deploy_contract(code)

    blocks = [
        Block(
            timestamp=ts,
            txs=[Transaction(sender=sender, to=contract)],
        )
        for ts in (
            FORK_TIMESTAMP - 1,
            FORK_TIMESTAMP,
            FORK_TIMESTAMP + 1,
        )
    ]

    post = {
        contract: Account(
            storage={
                1: marker,
                2: marker,
                3: marker,
            },
        ),
    }

    blockchain_test(pre=pre, blocks=blocks, post=post)
