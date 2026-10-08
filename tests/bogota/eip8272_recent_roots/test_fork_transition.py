"""
Tests for the EIP-8272 fork transition.

The recent root contract is an ordinary contract created by its
deployment transaction, so the fork writes nothing at
`Spec.RECENT_ROOT_ADDRESS` when it activates. These fixtures start with
the contract already deployed and cross the fork boundary.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    BalAccountExpectation,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    Fork,
    Op,
    Transaction,
)

from ..eip8141_frame_transactions.helpers import sender_frame, verify_frame
from .helpers import recent_root_frame, write_frame
from .spec import (
    Spec,
    entry_hash,
    ref_spec_8272,
    source_id,
    storage_key,
    validation_tuple,
)

REFERENCE_SPEC_GIT_PATH = ref_spec_8272.git_path
REFERENCE_SPEC_VERSION = ref_spec_8272.version

pytestmark = pytest.mark.valid_at_transition_to("Bogota")

FORK_TIMESTAMP = 15_000
"""Timestamp at which the transition fork activates EIP-8272."""

SLOT_EXECUTED = 0x01
"""Storage slot used by target contracts to record execution."""

FORK_SLOT = 500
"""Slot of the block activating the fork."""

SALT = bytes(32)

CONTRACT_WITHOUT_CODE_CHANGE = BlockAccessListExpectation(
    account_expectations={
        Spec.RECENT_ROOT_ADDRESS: BalAccountExpectation(code_changes=[]),
    }
)
"""
The contract's address is in the block access list, reached by a
transaction, and records no code change: the fork writes nothing at the
address, in the fork block included.
"""

CONTRACT_UNTOUCHED = BlockAccessListExpectation(
    account_expectations={
        Spec.RECENT_ROOT_ADDRESS: BalAccountExpectation.empty(),
    }
)
"""The contract's address is read by a transaction and records no change."""


def test_fork_transition_leaves_recent_root_contract_unchanged(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Leave the deployed recent root contract as it was when the fork
    activates.

    The contract is an ordinary contract created by its deployment
    transaction, so activation writes nothing at its address. A probe
    records `EXTCODESIZE` of the address keyed by block number: the same
    code is there before, at and after the fork block, and the account
    keeps nonce one and a zero balance.
    """
    sender = pre.fund_eoa()
    probe = pre.deploy_contract(
        Op.SSTORE(Op.NUMBER, Op.EXTCODESIZE(Spec.RECENT_ROOT_ADDRESS))
        + Op.STOP
    )
    blocks = [
        Block(
            timestamp=timestamp,
            slot_number=slot_number,
            txs=[Transaction(sender=sender, to=probe)],
            expected_block_access_list=CONTRACT_UNTOUCHED,
        )
        for timestamp, slot_number in (
            (FORK_TIMESTAMP - 1, FORK_SLOT - 1),
            (FORK_TIMESTAMP, FORK_SLOT),
            (FORK_TIMESTAMP + 1, FORK_SLOT + 1),
        )
    ]
    code_size = len(Spec.RECENT_ROOT_CODE)
    post = {
        probe: Account(storage={1: code_size, 2: code_size, 3: code_size}),
        Spec.RECENT_ROOT_ADDRESS: Account(
            nonce=Spec.RECENT_ROOT_NONCE,
            balance=0,
            code=Spec.RECENT_ROOT_CODE,
            storage={},
        ),
    }

    blockchain_test(pre=pre, blocks=blocks, post=post)


def test_publish_in_fork_block_and_verify_after(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Publish a root in the block that activates the fork and verify it in
    the next block.

    The contract is deployed before the fork, so a write in the fork
    block finds the code in place; a reference to the fork block's slot
    verifies from the following slot on.
    """
    sender = pre.fund_eoa()
    target = pre.deploy_contract(code=Op.SSTORE(SLOT_EXECUTED, 1) + Op.STOP)
    source = source_id(sender, SALT)
    root = (0xF0).to_bytes(32, "big")
    key = storage_key(source, FORK_SLOT)

    blocks = [
        Block(timestamp=FORK_TIMESTAMP - 1, slot_number=FORK_SLOT - 1),
        Block(
            timestamp=FORK_TIMESTAMP,
            slot_number=FORK_SLOT,
            txs=[
                Transaction(
                    sender=sender,
                    frames=[verify_frame(), write_frame(SALT, root)],
                )
            ],
            expected_block_access_list=CONTRACT_WITHOUT_CODE_CHANGE,
        ),
        Block(
            timestamp=FORK_TIMESTAMP + 1,
            slot_number=FORK_SLOT + 1,
            txs=[
                Transaction(
                    sender=sender,
                    frames=[
                        recent_root_frame(
                            validation_tuple(source, FORK_SLOT, root)
                        ),
                        verify_frame(),
                        sender_frame(target=target),
                    ],
                )
            ],
        ),
    ]
    post = {
        Spec.RECENT_ROOT_ADDRESS: Account(
            nonce=Spec.RECENT_ROOT_NONCE,
            code=Spec.RECENT_ROOT_CODE,
            storage={
                key: int.from_bytes(entry_hash(source, FORK_SLOT, root), "big")
            },
        ),
        target: Account(storage={SLOT_EXECUTED: 1}),
    }

    blockchain_test(pre=pre, blocks=blocks, post=post)
