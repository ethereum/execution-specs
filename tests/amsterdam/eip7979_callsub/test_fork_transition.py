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

from .helpers import MARKER_IN_SUBROUTINE, TX_GAS_LIMIT
from .spec import ref_spec_7979

REFERENCE_SPEC_GIT_PATH = ref_spec_7979.git_path
REFERENCE_SPEC_VERSION = ref_spec_7979.version

FORK_TIMESTAMP = 15_000


def marker_via_callsub() -> Bytecode:
    """
    Return code that calls a subroutine and stores the marker at the slot
    keyed by block NUMBER. Before the fork, CALLSUB is undefined and the
    frame halts before any write.
    """
    main = Op.PUSH1[0] + Op.CALLSUB + Op.STOP  # patched below
    offset = len(main)
    main = Op.PUSH1[offset] + Op.CALLSUB + Op.STOP
    subroutine = (
        Op.CALLDEST
        + Op.PUSH1[MARKER_IN_SUBROUTINE]
        + Op.NUMBER
        + Op.SSTORE
        + Op.RETURNSUB
    )
    return main + subroutine


def marker_via_jump_to_calldest() -> Bytecode:
    """
    Return code that JUMPs to a CALLDEST and stores the marker at the slot
    keyed by block NUMBER. Before the fork a 0xB1 byte is not a valid jump
    destination, so the JUMP halts the frame.
    """
    main = Op.PUSH1[0] + Op.JUMP + Op.STOP
    offset = len(main)
    main = Op.PUSH1[offset] + Op.JUMP + Op.STOP
    subroutine = (
        Op.CALLDEST
        + Op.PUSH1[MARKER_IN_SUBROUTINE]
        + Op.NUMBER
        + Op.SSTORE
        + Op.STOP
    )
    return main + subroutine


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
    Before the fork the new opcodes are undefined and 0xB1 is not a jump
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
