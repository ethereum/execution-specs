"""
Block access list tests for
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

The EIP-7928 block-level access list is committed to in the block
header, so it is consensus-visible on the frame-specific rollback
paths. A write discarded by an atomic-batch unroll or by a frame revert
must be dropped from the BAL and the slot re-filed as a bare access,
while the sender's nonce bump — which no rollback undoes — must stay
recorded.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    BalAccountExpectation,
    BalBalanceChange,
    BalNonceChange,
    BalStorageChange,
    BalStorageSlot,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    Bytes,
    FrameReceipt,
    FrameSignature,
    Op,
    Transaction,
    TransactionReceipt,
)

from .helpers import sender_frame, verify_frame
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")

SLOT = 0x01
"""Storage slot the target contracts write."""

WRITTEN_VALUE = 0x42
"""Value the target contracts write to `SLOT`."""

# A fresh SSTORE is charged state gas under EIP-8037 and a frame
# transaction holds no state gas reservoir, so a writing frame needs
# more than the default frame gas.
WRITE_FRAME_GAS = 200_000

GAS_PRICE = 7
"""
Fee per gas of the sponsored transaction, pinned to the genesis base
fee so the payer's charge is the base fee alone with no priority tip.
"""

SPONSORED_GAS_USED = 137_735
"""Gas charged to the payer of the sponsored transaction."""

PAYER_START_BALANCE = 10**18
"""Sponsoring payer's balance before settling the transaction fee."""

PAYER_POST_BALANCE = PAYER_START_BALANCE - SPONSORED_GAS_USED * GAS_PRICE
"""Sponsoring payer's balance after settling the transaction fee."""


@pytest.mark.parametrize(
    "committed",
    [
        pytest.param(True, id="committed"),
        pytest.param(False, id="unrolled"),
    ],
)
def test_bal_atomic_batch_write(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    committed: bool,
) -> None:
    """
    Record an atomic batch's storage write in the BAL only when the
    batch commits; an unrolled batch's write is re-filed as a bare
    access (EIP-8141 atomic batch behavior; EIP-7928 exceptional halts).
    """
    sender = pre.fund_eoa()
    target = pre.deploy_contract(code=Op.SSTORE(SLOT, WRITTEN_VALUE) + Op.STOP)
    terminator = pre.deploy_contract(
        code=Op.STOP if committed else Op.REVERT(0, 0)
    )

    tx = Transaction(
        sender=sender,
        frames=[
            verify_frame(),
            sender_frame(
                flags=Spec.ATOMIC_BATCH_FLAG,
                target=target,
                gas_limit=WRITE_FRAME_GAS,
            ),
            sender_frame(target=terminator),
        ],
        expected_receipt=TransactionReceipt(
            payer=sender,
            frame_receipts=[
                FrameReceipt(status=Spec.STATUS_SUCCESS),
                # Succeeds either way; an unrolled batch keeps the status.
                FrameReceipt(status=Spec.STATUS_SUCCESS),
                FrameReceipt(
                    status=Spec.STATUS_SUCCESS
                    if committed
                    else Spec.STATUS_FAILURE
                ),
            ],
        ),
    )

    if committed:
        target_expectation = BalAccountExpectation(
            storage_changes=[
                BalStorageSlot(
                    slot=SLOT,
                    slot_changes=[
                        BalStorageChange(
                            block_access_index=1, post_value=WRITTEN_VALUE
                        )
                    ],
                )
            ]
        )
        target_post = Account(storage={SLOT: WRITTEN_VALUE})
    else:
        # Unrolled write: the slot is a bare access, not a change.
        target_expectation = BalAccountExpectation(
            storage_changes=[],
            storage_reads=[SLOT],
        )
        target_post = Account(storage={SLOT: 0})

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                target: target_expectation,
                # An unroll rolls back the batch's writes but never the
                # sender's nonce bump.
                sender: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
            },
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            sender: Account(nonce=1),
            target: target_post,
        },
    )


def test_bal_atomic_batch_skipped_frame_absent(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Keep a skipped atomic-batch frame's target out of the BAL: the
    first batch frame reverts, the remaining batch frame never executes
    and never accesses its target (EIP-8141 atomic batch behavior).
    """
    sender = pre.fund_eoa()
    reverter = pre.deploy_contract(code=Op.REVERT(0, 0))
    skipped_target = pre.deploy_contract(
        code=Op.SSTORE(SLOT, WRITTEN_VALUE) + Op.STOP
    )

    tx = Transaction(
        sender=sender,
        frames=[
            verify_frame(),
            sender_frame(
                flags=Spec.ATOMIC_BATCH_FLAG,
                target=reverter,
            ),
            sender_frame(
                target=skipped_target,
                gas_limit=WRITE_FRAME_GAS,
            ),
        ],
        expected_receipt=TransactionReceipt(
            payer=sender,
            frame_receipts=[
                FrameReceipt(status=Spec.STATUS_SUCCESS),
                FrameReceipt(status=Spec.STATUS_FAILURE),
                FrameReceipt(status=Spec.STATUS_SKIPPED, gas_used=0),
            ],
        ),
    )

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={skipped_target: None},
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            sender: Account(nonce=1),
            skipped_target: Account(storage={SLOT: 0}),
        },
    )


def test_bal_frame_revert_write_dropped(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Drop a reverting (non-batch) frame's storage write from the BAL,
    re-filing the slot as a bare access (EIP-7928 exceptional halts).
    """
    sender = pre.fund_eoa()
    target = pre.deploy_contract(
        code=Op.SSTORE(SLOT, WRITTEN_VALUE) + Op.REVERT(0, 0)
    )

    tx = Transaction(
        sender=sender,
        frames=[
            verify_frame(),
            sender_frame(target=target, gas_limit=WRITE_FRAME_GAS),
        ],
        expected_receipt=TransactionReceipt(
            payer=sender,
            frame_receipts=[
                FrameReceipt(status=Spec.STATUS_SUCCESS),
                FrameReceipt(status=Spec.STATUS_FAILURE),
            ],
        ),
    )

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                target: BalAccountExpectation(
                    storage_changes=[],
                    storage_reads=[SLOT],
                )
            },
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            sender: Account(nonce=1),
            target: Account(storage={SLOT: 0}),
        },
    )


def test_bal_sponsored_payer_and_sender(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Attribute a sponsored frame transaction in the BAL: a non-sender
    payer's fee balance change and the sender's nonce bump land on
    distinct accounts (EIP-8141 APPROVE_PAYMENT, no sender-equality).
    """
    sender = pre.fund_eoa(amount=PAYER_START_BALANCE)
    payer = pre.fund_eoa(amount=PAYER_START_BALANCE)
    target = pre.deploy_contract(code=Op.SSTORE(SLOT, WRITTEN_VALUE) + Op.STOP)

    tx = Transaction(
        sender=sender,
        max_fee_per_gas=GAS_PRICE,
        frames=[
            verify_frame(flags=Spec.APPROVE_EXECUTION),
            verify_frame(flags=Spec.APPROVE_PAYMENT, target=payer),
            sender_frame(target=target, gas_limit=WRITE_FRAME_GAS),
        ],
        signatures=[
            FrameSignature(
                scheme=Spec.SCHEME_SECP256K1,
                signer=Bytes(sender),
            ),
            FrameSignature(
                scheme=Spec.SCHEME_SECP256K1,
                signer=Bytes(payer),
                secret_key=payer.key,
            ),
        ],
        expected_receipt=TransactionReceipt(
            payer=payer,
            # Pinned so a gas change fails here rather than as an
            # opaque payer balance mismatch.
            cumulative_gas_used=SPONSORED_GAS_USED,
            frame_receipts=[
                FrameReceipt(status=Spec.STATUS_SUCCESS),
                FrameReceipt(status=Spec.STATUS_SUCCESS),
                FrameReceipt(status=Spec.STATUS_SUCCESS),
            ],
        ),
    )

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                # The empty lists are the point: the fee lands only on
                # the payer and the nonce bump only on the sender.
                sender: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                    balance_changes=[],
                ),
                payer: BalAccountExpectation(
                    nonce_changes=[],
                    balance_changes=[
                        BalBalanceChange(
                            block_access_index=1,
                            post_balance=PAYER_POST_BALANCE,
                        )
                    ],
                ),
                target: BalAccountExpectation(
                    storage_changes=[
                        BalStorageSlot(
                            slot=SLOT,
                            slot_changes=[
                                BalStorageChange(
                                    block_access_index=1,
                                    post_value=WRITTEN_VALUE,
                                )
                            ],
                        )
                    ],
                ),
            },
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            sender: Account(nonce=1, balance=PAYER_START_BALANCE),
            payer: Account(nonce=0, balance=PAYER_POST_BALANCE),
            target: Account(storage={SLOT: WRITTEN_VALUE}),
        },
    )
