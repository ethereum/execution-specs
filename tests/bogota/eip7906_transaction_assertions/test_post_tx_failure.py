"""
Failure of `POST_TX` frames (EIP-7906): a failed assertion reverts the
execution body after the validation prefix without invalidating the
transaction, skips the frames after it, and settles the reverted body's
gas, refunds, events and block access list entries.
"""

from typing import List

import pytest
from execution_testing import (
    Account,
    Alloc,
    BalAccountExpectation,
    BalBalanceChange,
    BalNonceChange,
    BalStorageChange,
    BalStorageSlot,
    BlockAccessListExpectation,
    Bytecode,
    Fork,
    FrameReceipt,
    Header,
    Initcode,
    Op,
    StateTestFiller,
    Transaction,
    TransactionReceipt,
    compute_create_address,
)

from tests.bogota.eip8141_frame_transactions.helpers import (
    default_code_frame_gas,
    default_frame,
    verify_frame,
)
from tests.bogota.eip8141_frame_transactions.spec import Spec as Spec8141

from .helpers import (
    BODY_EFFECTS,
    CAROL_FUNDS,
    DEPLOYED_RUNTIME,
    FEE_PER_GAS,
    FUNDS,
    INITCODE_DEPLOYING,
    SLOT_A,
    SLOT_B,
    VALUE,
    WORKER_STORAGE,
    BodyEffect,
    as_int,
    assertion_transaction,
    body_frame,
    creation_state_gas,
    expect_eq,
    frame_gas,
    frame_transaction_gas,
    initcode_word,
    post_tx_frame,
    reverted_body_receipts,
    settled_receipt,
    state_creations,
    success_receipts,
)
from .spec import Spec, ref_spec_7906

REFERENCE_SPEC_GIT_PATH = ref_spec_7906.git_path
REFERENCE_SPEC_VERSION = ref_spec_7906.version

pytestmark = pytest.mark.valid_from("EIP7906")

RECIPIENT_FUNDS = 1_000


@pytest.mark.parametrize(
    "failure,halts",
    [
        pytest.param(Op.REVERT(0, 0), False, id="revert"),
        pytest.param(Op.INVALID, True, id="invalid_opcode"),
        pytest.param(Op.JUMP(1), True, id="bad_jump"),
        pytest.param(Op.POP, True, id="stack_underflow"),
    ],
)
def test_post_tx_failure_reverts_body(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    failure: Bytecode,
    halts: bool,
) -> None:
    """
    Revert the execution body when the `POST_TX` frame reverts or halts
    exceptionally, keeping the transaction valid: the validation
    prefix's nonce bump stays, the body's slot write and log are
    discarded, and the assertion frame's receipt reports failure, with
    its whole budget used on a halt.
    """
    sender = pre.fund_eoa()
    writer = pre.deploy_contract(
        code=Op.SSTORE(SLOT_A, 1) + Op.LOG0(0, 0) + Op.STOP
    )
    assertion = pre.deploy_contract(code=failure)

    state_test(
        pre=pre,
        tx=assertion_transaction(
            fork,
            sender,
            body=[body_frame(fork, target=writer)],
            assertion=assertion,
            frame_receipts=reverted_body_receipts(
                fork, 1, assertion_halts=halts
            ),
        ),
        post={
            sender: Account(nonce=1),
            writer: Account(storage={SLOT_A: 0}),
        },
    )


def test_post_tx_failure_overrides_atomic_batch(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Revert a committed atomic batch together with the rest of the body
    when the `POST_TX` frame fails: the batch's own all-or-nothing rule
    is superseded by the unconditional body revert.
    """
    sender = pre.fund_eoa()
    writer_a = pre.deploy_contract(code=Op.SSTORE(SLOT_A, 1) + Op.STOP)
    writer_b = pre.deploy_contract(code=Op.SSTORE(SLOT_B, 1) + Op.STOP)
    assertion = pre.deploy_contract(code=Op.REVERT(0, 0))

    state_test(
        pre=pre,
        tx=assertion_transaction(
            fork,
            sender,
            body=[
                body_frame(
                    fork, target=writer_a, flags=Spec8141.ATOMIC_BATCH_FLAG
                ),
                body_frame(fork, target=writer_b),
            ],
            assertion=assertion,
            frame_receipts=reverted_body_receipts(fork, 2),
        ),
        post={
            sender: Account(nonce=1),
            writer_a: Account(storage={SLOT_A: 0}),
            writer_b: Account(storage={SLOT_B: 0}),
        },
    )


@pytest.mark.parametrize(
    "post_tx_fails",
    [pytest.param(False, id="holds"), pytest.param(True, id="fails")],
)
def test_failed_body_batch_runs_post_tx(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    post_tx_fails: bool,
) -> None:
    """
    Run the assertion after a failed atomic batch inside the execution
    body. The unrolled batch skips only its own frames, and the
    assertion still decides whether the rest of the body commits.
    """
    sender = pre.fund_eoa()
    writer = pre.deploy_contract(code=Op.SSTORE(SLOT_A, 1) + Op.STOP)
    failure = pre.deploy_contract(code=Op.REVERT(0, 0))
    noop = pre.deploy_contract(code=Op.STOP)
    receipts = [
        FrameReceipt(status=Spec8141.STATUS_SUCCESS),
        FrameReceipt(status=Spec8141.STATUS_SUCCESS),
        FrameReceipt(status=Spec8141.STATUS_FAILURE),
        FrameReceipt(
            status=Spec8141.STATUS_SKIPPED, gas_used=0, state_gas_used=0
        ),
        FrameReceipt(
            status=Spec8141.STATUS_FAILURE
            if post_tx_fails
            else Spec8141.STATUS_SUCCESS
        ),
    ]
    state_test(
        pre=pre,
        tx=assertion_transaction(
            fork,
            sender,
            body=[
                body_frame(fork, target=writer),
                body_frame(
                    fork, target=failure, flags=Spec8141.ATOMIC_BATCH_FLAG
                ),
                body_frame(fork, target=noop),
            ],
            assertion=failure if post_tx_fails else noop,
            frame_receipts=receipts,
        ),
        post={
            sender: Account(nonce=1),
            writer: Account(storage={SLOT_A: 0 if post_tx_fails else 1}),
        },
    )


def test_diff_excludes_unrolled_batch(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Leave an unrolled body batch out of the diff: the assertion sees
    neither its slot write nor its event, only the frame after it.
    """
    sender = pre.fund_eoa()
    batched = pre.deploy_contract(
        code=Op.SSTORE(SLOT_A, 1) + Op.LOG0(0, 0) + Op.STOP
    )
    failing = pre.deploy_contract(code=Op.REVERT(0, 0))
    survivor = pre.deploy_contract(code=Op.SSTORE(SLOT_B, 1) + Op.STOP)
    checks = expect_eq(Op.TXTRACE(Spec.TXTRACE_SLOTS_CHANGED, 0), 1)
    checks += expect_eq(
        Op.TXTRACE(Spec.TXTRACE_SLOT_ADDRESS, 0), as_int(survivor)
    )
    checks += expect_eq(Op.TXTRACE(Spec.TXTRACE_EVENTS_COUNT, 0), 0)
    checks += expect_eq(Op.TXDIFF(Spec.TXDIFF_SLOT_AFTER, batched, SLOT_A), 0)
    assertion = pre.deploy_contract(code=checks + Op.STOP)

    state_test(
        pre=pre,
        tx=assertion_transaction(
            fork,
            sender,
            body=[
                body_frame(
                    fork, target=batched, flags=Spec8141.ATOMIC_BATCH_FLAG
                ),
                body_frame(fork, target=failing),
                body_frame(fork, target=survivor),
            ],
            assertion=assertion,
            frame_receipts=[
                FrameReceipt(status=Spec8141.STATUS_SUCCESS),
                FrameReceipt(status=Spec8141.STATUS_SUCCESS, logs=[]),
                FrameReceipt(status=Spec8141.STATUS_FAILURE),
                FrameReceipt(status=Spec8141.STATUS_SUCCESS),
                FrameReceipt(status=Spec8141.STATUS_SUCCESS),
            ],
        ),
        post={
            sender: Account(nonce=1),
            batched: Account(storage={SLOT_A: 0}),
            survivor: Account(storage={SLOT_B: 1}),
        },
    )


@pytest.mark.parametrize(
    "post_tx_fails",
    [pytest.param(False, id="holds"), pytest.param(True, id="fails")],
)
@pytest.mark.parametrize(
    "assertion_reads",
    [pytest.param(False, id="blind"), pytest.param(True, id="reads")],
)
def test_post_tx_block_access_list(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    post_tx_fails: bool,
    assertion_reads: bool,
) -> None:
    """
    Record the execution body's changes in the block access list only
    when the assertion holds. A failed `POST_TX` frame re-files the
    body's storage write as a bare access and leaves the transfer
    recipient as a touched account without changes, as an atomic batch
    unroll does. The sender's nonce bump in the validation prefix stays,
    and the assertion, which only reads, is touched either way. An
    assertion that looks up the written slot and an untouched account
    before deciding adds no entry for the slot and leaves the account
    touched, its own failure included.
    """
    sender = pre.fund_eoa()
    recipient = pre.fund_eoa(amount=RECIPIENT_FUNDS)
    carol = pre.fund_eoa(amount=CAROL_FUNDS)
    writer = pre.deploy_contract(code=Op.SSTORE(SLOT_A, 1) + Op.STOP)
    lookups = Bytecode()
    if assertion_reads:
        lookups = Op.POP(
            Op.TXDIFF(Spec.TXDIFF_SLOT_AFTER, writer, SLOT_A)
        ) + Op.POP(Op.TXDIFF(Spec.TXDIFF_BALANCE_AFTER, carol, 0))
    assertion = pre.deploy_contract(
        code=lookups + (Op.REVERT(0, 0) if post_tx_fails else Op.STOP)
    )

    tx = assertion_transaction(
        fork,
        sender,
        body=[
            body_frame(fork, target=writer),
            body_frame(fork, target=recipient, value=VALUE),
        ],
        assertion=assertion,
        frame_receipts=reverted_body_receipts(fork, 2)
        if post_tx_fails
        else success_receipts(4),
    )

    if post_tx_fails:
        writer_expectation = BalAccountExpectation(
            storage_changes=[], storage_reads=[SLOT_A]
        )
        recipient_expectation = BalAccountExpectation.empty()
    else:
        writer_expectation = BalAccountExpectation(
            storage_changes=[
                BalStorageSlot(
                    slot=SLOT_A,
                    slot_changes=[
                        BalStorageChange(block_access_index=1, post_value=1)
                    ],
                )
            ],
            storage_reads=[],
        )
        recipient_expectation = BalAccountExpectation(
            balance_changes=[
                BalBalanceChange(
                    block_access_index=1,
                    post_balance=RECIPIENT_FUNDS + VALUE,
                )
            ]
        )

    state_test(
        pre=pre,
        tx=tx,
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                writer: writer_expectation,
                recipient: recipient_expectation,
                carol: BalAccountExpectation.empty()
                if assertion_reads
                else None,
                assertion: BalAccountExpectation.empty(),
                sender: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
            },
        ),
        post={
            sender: Account(nonce=1),
            writer: Account(storage={SLOT_A: 0 if post_tx_fails else 1}),
            recipient: Account(
                balance=RECIPIENT_FUNDS
                if post_tx_fails
                else RECIPIENT_FUNDS + VALUE
            ),
            carol: Account(balance=CAROL_FUNDS),
        },
    )


def test_post_tx_failure_skips_remaining_frames(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Skip the `POST_TX` frames after a failed one: the body is already
    reverted, so the later assertion has nothing left to observe and
    reports the skipped status with no gas used.
    """
    sender = pre.fund_eoa()
    writer = pre.deploy_contract(code=Op.SSTORE(SLOT_A, 1) + Op.STOP)
    failing = pre.deploy_contract(code=Op.REVERT(0, 0))
    passing = pre.deploy_contract(code=Op.STOP)

    tx = assertion_transaction(
        fork,
        sender,
        body=[body_frame(fork, target=writer)],
        assertion=[failing, passing],
        frame_receipts=[
            *reverted_body_receipts(fork, 1),
            FrameReceipt(status=Spec8141.STATUS_SKIPPED, gas_used=0),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            writer: Account(storage={SLOT_A: 0}),
        },
    )


@pytest.mark.parametrize(
    "outcomes",
    [
        pytest.param([True, True], id="both_hold"),
        pytest.param([True, False], id="second_fails"),
        pytest.param([True, False, True], id="middle_of_three_fails"),
    ],
)
def test_multiple_post_tx_frames(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    outcomes: List[bool],
) -> None:
    """
    Compose independent assertions: every `POST_TX` frame must pass for
    the body to commit, a later one failing reverts the body even
    though an earlier one accepted it, and the frames after a failed
    one are skipped.
    """
    sender = pre.fund_eoa()
    writer = pre.deploy_contract(code=Op.SSTORE(SLOT_A, 1) + Op.STOP)
    accepting = expect_eq(Op.TXTRACE(Spec.TXTRACE_SLOTS_CHANGED, 0), 1)
    assertions = [
        pre.deploy_contract(
            code=accepting + Op.STOP if holds else Op.REVERT(0, 0)
        )
        for holds in outcomes
    ]
    commits = all(outcomes)
    failed_at = len(outcomes) if commits else outcomes.index(False)
    receipts = [
        FrameReceipt(status=Spec8141.STATUS_SUCCESS),
        FrameReceipt(status=Spec8141.STATUS_SUCCESS)
        if commits
        else FrameReceipt(status=Spec8141.STATUS_SUCCESS, logs=[]),
        *[
            FrameReceipt(status=Spec8141.STATUS_SUCCESS)
            for _ in range(failed_at)
        ],
    ]
    if not commits:
        receipts.append(FrameReceipt(status=Spec8141.STATUS_FAILURE))
        receipts += [
            FrameReceipt(status=Spec8141.STATUS_SKIPPED, gas_used=0)
            for _ in outcomes[failed_at + 1 :]
        ]

    state_test(
        pre=pre,
        tx=assertion_transaction(
            fork,
            sender,
            body=[body_frame(fork, target=writer)],
            assertion=assertions,
            frame_receipts=receipts,
        ),
        post={
            sender: Account(nonce=1),
            writer: Account(storage={SLOT_A: 1 if commits else 0}),
        },
    )


@pytest.mark.parametrize("effect", BODY_EFFECTS)
@pytest.mark.parametrize("failure", ["none", "revert", "exception"])
def test_post_tx_gas_settlement(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    effect: BodyEffect,
    failure: str,
) -> None:
    """
    Settle a body frame's state gas, refund and event against exact
    receipts, payer balance and block gas when the assertion holds,
    reverts or halts, a failed assertion dropping all three and
    skipping the `POST_TX` frame after it.
    """
    sender = pre.fund_eoa(amount=FUNDS)
    worker = pre.deploy_contract(code=effect.code, storage=WORKER_STORAGE)
    assertion_code = {
        "none": Op.STOP,
        "revert": Op.REVERT(0, 0),
        "exception": Op.INVALID,
    }[failure]
    assertion = pre.deploy_contract(code=assertion_code)
    later = pre.deploy_contract(code=Op.STOP)
    entry = fork.frame_entry_gas_calculator()()
    holds = failure == "none"
    receipts = [
        FrameReceipt(
            status=Spec8141.STATUS_SUCCESS,
            gas_used=default_code_frame_gas(fork, target_warm=True),
            state_gas_used=0,
        ),
        settled_receipt(fork, worker, effect, kept=holds),
        FrameReceipt(
            status=Spec8141.STATUS_SUCCESS
            if holds
            else Spec8141.STATUS_FAILURE,
            gas_used=frame_gas(fork)
            if failure == "exception"
            else entry + assertion_code.execution_cost(fork),
            state_gas_used=0,
        ),
        FrameReceipt(
            status=Spec8141.STATUS_SUCCESS
            if holds
            else Spec8141.STATUS_SKIPPED,
            gas_used=entry if holds else 0,
            state_gas_used=0,
        ),
    ]
    tx = Transaction(
        sender=sender,
        max_fee_per_gas=FEE_PER_GAS,
        max_priority_fee_per_gas=0,
        frames=[
            verify_frame(),
            body_frame(
                fork,
                target=worker,
                state_gas_limit=effect.code.state_cost(fork),
            ),
            post_tx_frame(fork, target=assertion),
            post_tx_frame(fork, target=later),
        ],
    )
    payer_used, block_gas_used = frame_transaction_gas(
        fork,
        tx,
        receipts,
        refundable=effect.code.refund(fork) if holds else 0,
    )
    tx.expected_receipt = TransactionReceipt(
        payer=sender, cumulative_gas_used=payer_used, frame_receipts=receipts
    )
    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1, balance=FUNDS - FEE_PER_GAS * payer_used),
            worker: Account(
                storage=effect.kept_storage if holds else WORKER_STORAGE
            ),
        },
        blockchain_test_header_verify=Header(gas_used=block_gas_used),
    )


def test_failed_assertion_keeps_prefix_deployment(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Keep a contract a `DEFAULT` frame deploys before the payment
    approval when the assertion fails: the frame is part of the
    validation prefix, which the body revert never reaches.
    """
    sender = pre.fund_eoa()
    factory = pre.deploy_contract(
        code=Op.MSTORE(0, initcode_word(INITCODE_DEPLOYING))
        + Op.POP(Op.CREATE(0, 0, len(bytes(INITCODE_DEPLOYING))))
        + Op.STOP
    )
    deployed = compute_create_address(address=factory, nonce=1)
    writer = pre.deploy_contract(code=Op.SSTORE(SLOT_A, 1) + Op.STOP)
    assertion = pre.deploy_contract(code=Op.REVERT(0, 0))

    state_test(
        pre=pre,
        tx=Transaction(
            sender=sender,
            frames=[
                default_frame(
                    target=factory,
                    gas_limit=frame_gas(fork),
                    state_gas_limit=creation_state_gas(
                        fork,
                        creations=1,
                        deposited_bytes=len(DEPLOYED_RUNTIME),
                    ),
                ),
                verify_frame(),
                body_frame(fork, target=writer),
                post_tx_frame(fork, target=assertion),
            ],
            expected_receipt=TransactionReceipt(
                payer=sender,
                frame_receipts=[
                    FrameReceipt(status=Spec8141.STATUS_SUCCESS),
                    *reverted_body_receipts(fork, 1),
                ],
            ),
        ),
        post={
            sender: Account(nonce=1),
            factory: Account(nonce=2),
            deployed: Account(nonce=1, code=DEPLOYED_RUNTIME),
            writer: Account(storage={SLOT_A: 0}),
        },
    )


def test_failed_assertion_charges_sponsor(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Keep a sponsor as the payer when the assertion fails: the sponsor's
    approval is in the validation prefix, and the sender pays nothing.
    """
    sender = pre.fund_eoa(amount=FUNDS)
    sponsor = pre.deploy_contract(
        code=Op.APPROVE(0, 0, Spec8141.APPROVE_PAYMENT), balance=FUNDS
    )
    writer = pre.deploy_contract(code=Op.SSTORE(SLOT_A, 1) + Op.STOP)
    assertion = pre.deploy_contract(code=Op.REVERT(0, 0))

    state_test(
        pre=pre,
        tx=Transaction(
            sender=sender,
            frames=[
                verify_frame(flags=Spec8141.APPROVE_EXECUTION),
                verify_frame(target=sponsor, flags=Spec8141.APPROVE_PAYMENT),
                body_frame(fork, target=writer),
                post_tx_frame(fork, target=assertion),
            ],
            expected_receipt=TransactionReceipt(
                payer=sponsor,
                frame_receipts=[
                    FrameReceipt(status=Spec8141.STATUS_SUCCESS),
                    *reverted_body_receipts(fork, 1),
                ],
            ),
        ),
        post={
            sender: Account(nonce=1, balance=FUNDS),
            writer: Account(storage={SLOT_A: 0}),
        },
    )


@pytest.mark.parametrize(
    "post_tx_fails",
    [pytest.param(False, id="holds"), pytest.param(True, id="fails")],
)
def test_body_revert_restores_prefix_state_charge(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    post_tx_fails: bool,
) -> None:
    """
    Restore a prefix frame's state gas charge that the body refilled by
    clearing the slot again, when the assertion fails and the body's
    clear is reverted.
    """
    sender = pre.fund_eoa()
    toggler = pre.deploy_contract(
        code=Op.SSTORE(SLOT_A, Op.ISZERO(Op.SLOAD(SLOT_A))) + Op.STOP
    )
    charge = Op.SSTORE(SLOT_A, 1, original_value=0, new_value=1).state_cost(
        fork
    )
    assertion = pre.deploy_contract(
        code=Op.REVERT(0, 0) if post_tx_fails else Op.STOP
    )
    receipts = [
        FrameReceipt(
            status=Spec8141.STATUS_SUCCESS,
            state_gas_used=charge if post_tx_fails else 0,
        ),
        FrameReceipt(status=Spec8141.STATUS_SUCCESS, state_gas_used=0),
        FrameReceipt(status=Spec8141.STATUS_SUCCESS, state_gas_used=0),
        FrameReceipt(
            status=Spec8141.STATUS_FAILURE
            if post_tx_fails
            else Spec8141.STATUS_SUCCESS,
            state_gas_used=0,
        ),
    ]

    state_test(
        pre=pre,
        tx=Transaction(
            sender=sender,
            frames=[
                default_frame(
                    target=toggler,
                    gas_limit=frame_gas(fork),
                    state_gas_limit=charge,
                ),
                verify_frame(),
                body_frame(fork, target=toggler),
                post_tx_frame(fork, target=assertion),
            ],
            expected_receipt=TransactionReceipt(
                payer=sender, frame_receipts=receipts
            ),
        ),
        post={
            sender: Account(nonce=1),
            toggler: Account(storage={SLOT_A: 1 if post_tx_fails else 0}),
        },
    )


@pytest.mark.parametrize(
    "post_tx_fails",
    [pytest.param(False, id="holds"), pytest.param(True, id="fails")],
)
def test_body_revert_drops_scheduled_deletion(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    post_tx_fails: bool,
) -> None:
    """
    Drop the deletion the body scheduled for a contract a prefix frame
    created, when the assertion fails: the contract survives the
    transaction, while a passing assertion lets the deletion happen.
    """
    sender = pre.fund_eoa()
    runtime = Op.SELFDESTRUCT(0)
    initcode = Initcode(deploy_code=runtime)
    factory = pre.deploy_contract(
        code=Op.MSTORE(0, initcode_word(initcode))
        + Op.POP(Op.CREATE(0, 0, len(initcode)))
        + Op.STOP
    )
    created = compute_create_address(address=factory, nonce=1)
    assertion = pre.deploy_contract(
        code=Op.REVERT(0, 0) if post_tx_fails else Op.STOP
    )

    state_test(
        pre=pre,
        tx=Transaction(
            sender=sender,
            frames=[
                default_frame(
                    target=factory,
                    gas_limit=frame_gas(fork),
                    state_gas_limit=creation_state_gas(
                        fork, creations=1, deposited_bytes=len(runtime)
                    ),
                ),
                verify_frame(),
                body_frame(fork, target=created),
                post_tx_frame(fork, target=assertion),
            ],
        ),
        post={
            sender: Account(nonce=1),
            created: Account(code=bytes(runtime))
            if post_tx_fails
            else Account.NONEXISTENT,
        },
    )


def test_frames_before_payment_approval_survive_failed_assertion(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Keep a `SENDER` frame that runs between the execution and payment
    approvals when the assertion fails, and charge its state gas to the
    sponsor. It belongs to the validation prefix, which ends at the
    payment approval, so only the frames after that revert.
    """
    sender = pre.fund_eoa(amount=FUNDS)
    approve = Op.APPROVE(0, 0, Spec8141.APPROVE_PAYMENT)
    sponsor = pre.deploy_contract(code=approve, balance=FUNDS)
    prefix_write = Op.SSTORE(SLOT_A, 1) + Op.STOP
    body_write = Op.SSTORE(SLOT_B, 1) + Op.STOP
    prefix_writer = pre.deploy_contract(code=prefix_write)
    body_writer = pre.deploy_contract(code=body_write)
    revert = Op.REVERT(0, 0)
    assertion = pre.deploy_contract(code=revert)
    entry = fork.frame_entry_gas_calculator()()
    receipts = [
        FrameReceipt(
            status=Spec8141.STATUS_SUCCESS,
            gas_used=default_code_frame_gas(fork, target_warm=True),
            state_gas_used=0,
        ),
        FrameReceipt(
            status=Spec8141.STATUS_SUCCESS,
            gas_used=entry + prefix_write.execution_cost(fork),
            state_gas_used=prefix_write.state_cost(fork),
        ),
        FrameReceipt(
            status=Spec8141.STATUS_SUCCESS,
            gas_used=entry + approve.execution_cost(fork),
            state_gas_used=0,
        ),
        FrameReceipt(
            status=Spec8141.STATUS_SUCCESS,
            gas_used=entry + body_write.execution_cost(fork),
            state_gas_used=0,
            logs=[],
        ),
        FrameReceipt(
            status=Spec8141.STATUS_FAILURE,
            gas_used=entry + revert.execution_cost(fork),
            state_gas_used=0,
        ),
    ]
    tx = Transaction(
        sender=sender,
        max_fee_per_gas=FEE_PER_GAS,
        max_priority_fee_per_gas=0,
        frames=[
            verify_frame(flags=Spec8141.APPROVE_EXECUTION),
            body_frame(fork, target=prefix_writer),
            verify_frame(target=sponsor, flags=Spec8141.APPROVE_PAYMENT),
            body_frame(fork, target=body_writer),
            post_tx_frame(fork, target=assertion),
        ],
    )
    payer_used, block_gas_used = frame_transaction_gas(
        fork, tx, receipts, refundable=0
    )
    tx.expected_receipt = TransactionReceipt(
        payer=sponsor, cumulative_gas_used=payer_used, frame_receipts=receipts
    )
    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1, balance=FUNDS),
            sponsor: Account(balance=FUNDS - FEE_PER_GAS * payer_used),
            prefix_writer: Account(storage={SLOT_A: 1}),
            body_writer: Account(storage={SLOT_B: 0}),
        },
        blockchain_test_header_verify=Header(gas_used=block_gas_used),
    )


def test_failed_assertion_keeps_prefix_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Charge the state gas of a validation prefix that revives an
    account, sets slots and deploys a contract when the assertion
    fails, while the body's identical creations revert and charge
    nothing.
    """
    sender = pre.fund_eoa(amount=FUNDS)
    sponsor = pre.deploy_contract(
        code=Op.APPROVE(0, 0, Spec8141.APPROVE_PAYMENT), balance=FUNDS
    )
    prefix = state_creations(pre, fork)
    body = state_creations(pre, fork)
    assertion = pre.deploy_contract(code=Op.REVERT(0, 0))
    receipts = [
        FrameReceipt(status=Spec8141.STATUS_SUCCESS, state_gas_used=0),
        *[
            FrameReceipt(status=Spec8141.STATUS_SUCCESS, state_gas_used=gas)
            for gas in prefix.state_gas(fork)
        ],
        FrameReceipt(status=Spec8141.STATUS_SUCCESS, state_gas_used=0),
        *[
            FrameReceipt(
                status=Spec8141.STATUS_SUCCESS, state_gas_used=0, logs=[]
            )
            for _ in body.frames
        ],
        FrameReceipt(status=Spec8141.STATUS_FAILURE, state_gas_used=0),
    ]

    state_test(
        pre=pre,
        tx=Transaction(
            sender=sender,
            frames=[
                verify_frame(flags=Spec8141.APPROVE_EXECUTION),
                *prefix.frames,
                verify_frame(target=sponsor, flags=Spec8141.APPROVE_PAYMENT),
                *body.frames,
                post_tx_frame(fork, target=assertion),
            ],
            expected_receipt=TransactionReceipt(
                payer=sponsor, frame_receipts=receipts
            ),
        ),
        post={
            sender: Account(nonce=1, balance=FUNDS - VALUE),
            **prefix.post(kept=True),
            **body.post(kept=False),
        },
    )


def test_failed_assertion_keeps_prefix_storage_change(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Keep the validation prefix's write to a slot the reverted body
    overwrote: the block access list records the prefix's value at the
    transaction's index and, the slot having a change, no read of it.
    """
    sender = pre.fund_eoa(amount=FUNDS)
    sponsor = pre.deploy_contract(
        code=Op.APPROVE(0, 0, Spec8141.APPROVE_PAYMENT), balance=FUNDS
    )
    counter = pre.deploy_contract(
        code=Op.SSTORE(SLOT_A, Op.ADD(Op.SLOAD(SLOT_A), 1)) + Op.STOP
    )
    assertion = pre.deploy_contract(code=Op.REVERT(0, 0))

    state_test(
        pre=pre,
        tx=Transaction(
            sender=sender,
            frames=[
                verify_frame(flags=Spec8141.APPROVE_EXECUTION),
                body_frame(fork, target=counter),
                verify_frame(target=sponsor, flags=Spec8141.APPROVE_PAYMENT),
                body_frame(fork, target=counter),
                post_tx_frame(fork, target=assertion),
            ],
            expected_receipt=TransactionReceipt(
                payer=sponsor,
                frame_receipts=[
                    FrameReceipt(status=Spec8141.STATUS_SUCCESS),
                    FrameReceipt(status=Spec8141.STATUS_SUCCESS),
                    FrameReceipt(status=Spec8141.STATUS_SUCCESS),
                    FrameReceipt(status=Spec8141.STATUS_SUCCESS, logs=[]),
                    FrameReceipt(status=Spec8141.STATUS_FAILURE),
                ],
            ),
        ),
        post={
            sender: Account(nonce=1, balance=FUNDS),
            counter: Account(storage={SLOT_A: 1}),
        },
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                counter: BalAccountExpectation(
                    storage_changes=[
                        BalStorageSlot(
                            slot=SLOT_A,
                            slot_changes=[
                                BalStorageChange(
                                    block_access_index=1, post_value=1
                                )
                            ],
                        )
                    ],
                    storage_reads=[],
                ),
                sender: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
            },
        ),
    )
