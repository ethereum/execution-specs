"""Fork-transition tests for EIP-7979 (CALLSUB, CALLDEST, RETURNSUB)."""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytecode,
    Op,
    Transaction,
)

from .helpers import MARKER_IN_SUBROUTINE, TX_GAS_LIMIT, program
from .spec import ref_spec_7979

REFERENCE_SPEC_GIT_PATH = ref_spec_7979.git_path
REFERENCE_SPEC_VERSION = ref_spec_7979.version

FORK_TIMESTAMP = 15_000


def store_marker_at_block_number() -> Bytecode:
    """Store the marker at the slot keyed by block NUMBER."""
    return Op.SSTORE(Op.NUMBER, MARKER_IN_SUBROUTINE)


def marker_via_callsub() -> Bytecode:
    """
    Return code that calls a subroutine which stores the marker. Before the
    fork, CALLSUB is undefined and the frame halts before any write.
    """
    code, _ = program(
        lambda offset: Op.CALLSUB(offset),
        Op.CALLDEST + store_marker_at_block_number() + Op.RETURNSUB,
    )
    return code


def marker_via_jump_to_calldest() -> Bytecode:
    """
    Return code that JUMPs to a CALLDEST and stores the marker. Before the
    fork a 0xBB byte is not a valid jump destination, so the JUMP halts the
    frame.
    """
    code, _ = program(
        lambda offset: Op.JUMP(offset),
        Op.CALLDEST + store_marker_at_block_number() + Op.STOP,
    )
    return code


@pytest.mark.valid_at_transition_to("EIP7979")
@pytest.mark.parametrize(
    "code",
    [
        pytest.param(marker_via_callsub(), id="callsub"),
        pytest.param(marker_via_jump_to_calldest(), id="jump_to_calldest"),
    ],
)
def test_opcodes_at_fork_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    code: Bytecode,
) -> None:
    """
    Before the fork the new opcodes are undefined and 0xBB is not a jump
    destination; from the fork onward the code runs and stores its marker.

    Storage is keyed by block NUMBER so each block's outcome is visible:
    block 1 (pre-fork) stays 0; blocks 2 and 3 hold the marker.
    """
    sender = pre.fund_eoa()
    contract = pre.deploy_contract(code)
    blocks = [
        Block(
            timestamp=ts,
            txs=[
                Transaction(sender=sender, to=contract, gas_limit=TX_GAS_LIMIT)
            ],
        )
        for ts in (FORK_TIMESTAMP - 1, FORK_TIMESTAMP, FORK_TIMESTAMP + 1)
    ]
    post = {
        contract: Account(
            storage={
                1: 0,
                2: MARKER_IN_SUBROUTINE,
                3: MARKER_IN_SUBROUTINE,
            }
        )
    }
    blockchain_test(pre=pre, blocks=blocks, post=post)
