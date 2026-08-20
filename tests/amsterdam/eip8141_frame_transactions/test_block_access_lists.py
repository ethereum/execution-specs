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
    Address,
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
    Fork,
    FrameReceipt,
    FrameSignature,
    Op,
    Transaction,
    TransactionReceipt,
    keccak256,
)

from tests.frontier.precompiles.spec import Spec as EcrecoverSpec
from tests.osaka.eip7951_p256verify_precompiles.spec import Spec as Spec7951

from .helpers import sender_frame, verify_frame
from .signature_helpers import P256_SIGNATURE, p256_entry
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")

ECRECOVER_ADDRESS = EcrecoverSpec.ECRECOVER
"""The `ecrecover` precompile, which validates SECP256K1 signature entries."""

P256VERIFY_ADDRESS = Address(Spec7951.P256VERIFY)
"""The `P256VERIFY` precompile (EIP-7951), which validates P256 entries."""

SLOT = 0x01
"""Storage slot the target contracts write."""

WRITTEN_VALUE = 0x42
"""Value the target contracts write to `SLOT`."""

# A fresh SSTORE is charged state gas under EIP-8037 and a frame
# transaction holds no state gas reservoir, so a writing frame needs
# more than the default frame gas.
WRITE_FRAME_GAS = 200_000


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


def test_bal_unaffordable_designation_absent(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Keep a frame's designated address out of the BAL when the frame's
    gas cannot cover the designation's access: resolution halts before
    reading the designated account, while the target it did access is
    filed as a bare access.

    The receipts alone cannot tell this apart from a failure inside the
    resolved code, since either forfeits the whole frame gas limit — the
    BAL is what distinguishes them.
    """
    entry_gas = fork.frame_entry_gas_calculator()
    sender = pre.fund_eoa()
    delegate = pre.deploy_contract(code=Op.SSTORE(SLOT, WRITTEN_VALUE))
    authority = pre.fund_eoa(delegation=delegate)

    # The most gas that still cannot afford the designation's access.
    frame_gas = entry_gas(delegated=True) - 1

    tx = Transaction(
        sender=sender,
        frames=[
            verify_frame(),
            sender_frame(target=authority, gas_limit=frame_gas),
        ],
        expected_receipt=TransactionReceipt(
            payer=sender,
            frame_receipts=[
                FrameReceipt(status=Spec.STATUS_SUCCESS, gas_used=0),
                FrameReceipt(status=Spec.STATUS_FAILURE, gas_used=frame_gas),
            ],
        ),
    )

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                authority: BalAccountExpectation.empty(),
                delegate: None,
            },
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            sender: Account(nonce=1),
            delegate: Account(storage={SLOT: 0}),
        },
    )


def test_bal_sponsored_payer_and_sender(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Attribute a sponsored frame transaction in the BAL: a non-sender
    payer's fee balance change and the sender's nonce bump land on
    distinct accounts (EIP-8141 APPROVE_PAYMENT, no sender-equality).
    """
    # The fee per gas equals the genesis base fee, so the payer's
    # charge carries no priority tip.
    fee_per_gas = 7
    start_balance = 10**18

    sender = pre.fund_eoa(amount=start_balance)
    payer = pre.fund_eoa(amount=start_balance)
    target_code = (
        Op.SSTORE(
            SLOT,
            WRITTEN_VALUE,
            key_warm=False,
            original_value=0,
            current_value=0,
            new_value=WRITTEN_VALUE,
        )
        + Op.STOP
    )
    target = pre.deploy_contract(code=target_code)

    tx = Transaction(
        sender=sender,
        max_fee_per_gas=fee_per_gas,
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
    )
    # Materialize the signature bytes the intrinsic cost charges for.
    tx.sign()
    assert tx.frames is not None and tx.signatures is not None

    # The two VERIFY frames run the protocol default code, which
    # consumes no gas; the SENDER frame charges its cold target's
    # access at entry and then runs the storage write.
    sponsored_gas_used = (
        fork.frame_transaction_intrinsic_cost_calculator()(
            frames=tx.frames,
            signatures=tx.signatures,
            return_cost_deducted_prior_execution=True,
        )
        + fork.frame_entry_gas_calculator()()
        + target_code.gas_cost(fork)
    )
    payer_post_balance = start_balance - sponsored_gas_used * fee_per_gas

    tx.expected_receipt = TransactionReceipt(
        payer=payer,
        # Pinned so a gas change fails here rather than as an
        # opaque payer balance mismatch.
        cumulative_gas_used=sponsored_gas_used,
        frame_receipts=[
            FrameReceipt(status=Spec.STATUS_SUCCESS),
            FrameReceipt(status=Spec.STATUS_SUCCESS),
            FrameReceipt(status=Spec.STATUS_SUCCESS),
        ],
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
                            post_balance=payer_post_balance,
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
            sender: Account(nonce=1, balance=start_balance),
            payer: Account(nonce=0, balance=payer_post_balance),
            target: Account(storage={SLOT: WRITTEN_VALUE}),
        },
    )


def test_bal_omits_signature_validation_precompiles(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Signature validation must leave no trace in the block access list.

    A frame transaction's protocol-validated signatures are checked before
    execution, outside the EVM, so `ecrecover` and `P256VERIFY` are never
    *called* by the transaction: "since the signature validation does not
    happen in EVM execution, the related precompiles `ecrecover` and
    `P256VERIFY` must not be added to the block-level access list."

    The distinction is invisible in state -- a precompile has no storage,
    balance or nonce to change -- but the BAL is committed to in the block
    header, so an implementation that validates signatures by dispatching
    through its own EVM adds the precompile as a touched address, produces a
    different block access list hash, and has its block rejected. Nothing
    else in the transaction's result differs, which is what makes this worth
    pinning.

    The transaction carries one signature of each protocol-validated scheme
    so both precompiles are exercised, and asserts each is absent.
    """
    sender = pre.fund_eoa()
    target = pre.deploy_contract(code=Op.STOP)

    tx = Transaction(
        sender=sender,
        frames=[
            verify_frame(flags=Spec.APPROVE_EXECUTION_AND_PAYMENT),
            sender_frame(target=target),
        ],
        signatures=[
            # Index 0 authorizes the default code, and is validated with
            # `ecrecover`.
            FrameSignature(
                scheme=Spec.SCHEME_SECP256K1,
                signer=Bytes(sender),
            ),
            # Carried only to exercise `P256VERIFY`; no frame references it.
            # A P256 entry's signer is `keccak256(qx || qy)[12:]`.
            p256_entry(
                r=int.from_bytes(P256_SIGNATURE[0:32], "big"),
                s=int.from_bytes(P256_SIGNATURE[32:64], "big"),
                qx=int.from_bytes(P256_SIGNATURE[64:96], "big"),
                qy=int.from_bytes(P256_SIGNATURE[96:128], "big"),
                signer=Bytes(keccak256(P256_SIGNATURE[64:128])[12:]),
            ),
        ],
    )
    tx.sign()

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                # `None` asserts absence: neither precompile belongs in the
                # list, because neither was reached from EVM execution.
                ECRECOVER_ADDRESS: None,
                P256VERIFY_ADDRESS: None,
            },
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={sender: Account(nonce=1)},
    )
