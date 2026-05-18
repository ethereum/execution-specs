"""Tests for EIP-7843 fork transition behavior."""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Op,
    Transaction,
)

from .spec import ref_spec_7843

REFERENCE_SPEC_GIT_PATH = ref_spec_7843.git_path
REFERENCE_SPEC_VERSION = ref_spec_7843.version


@pytest.mark.valid_at_transition_to("EIP7843")
def test_slotnum_at_fork_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Test SLOTNUM behavior across the EIP-7843 fork transition.

    Before EIP-7843, opcode 0x4B is undefined: execution halts with an
    invalid-opcode exception and consumes all gas, so no SSTORE is observed.

    From EIP-7843 onward, SLOTNUM pushes the block's slot number provided
    by the consensus layer and the SSTORE succeeds.

    The contract keys storage by block number so each block's outcome is
    independently visible in the final post-state:

    * block 1 (pre-fork): slot 1 stays 0 — execution halted before SSTORE.
    * block 2 (transition): slot 2 == ``at_fork_slot``.
    * block 3 (post-fork): slot 3 == ``post_fork_slot``.
    """
    sender = pre.fund_eoa()
    contract = pre.deploy_contract(Op.SSTORE(Op.NUMBER, Op.SLOTNUM) + Op.STOP)

    at_fork_slot = 200
    post_fork_slot = 201

    blocks = [
        Block(
            timestamp=ts,
            slot_number=slot,
            txs=[Transaction(sender=sender, to=contract, gas_limit=100_000)],
        )
        for ts, slot in [
            (14_999, None),
            (15_000, at_fork_slot),
            (15_001, post_fork_slot),
        ]
    ]
    post = {
        contract: Account(
            storage={
                1: 0,
                2: at_fork_slot,
                3: post_fork_slot,
            },
        ),
    }

    blockchain_test(pre=pre, blocks=blocks, post=post)
