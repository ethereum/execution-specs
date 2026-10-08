"""
`TXTRACE` and `EVENTDATACOPY` (EIP-7906): enumeration of the
transaction's balance, slot, deployment and event tables, the gas
payment parameters, and the event data reads.
"""

from typing import Callable, List

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytecode,
    Fork,
    Initcode,
    Op,
    StateTestFiller,
    Transaction,
    TransactionReceipt,
    compute_create2_address,
    compute_create_address,
    keccak256,
)

from tests.amsterdam.eip7708_eth_transfer_logs.spec import Spec as Spec7708
from tests.bogota.eip8141_frame_transactions.helpers import verify_frame
from tests.bogota.eip8141_frame_transactions.spec import Spec as Spec8141

from .helpers import (
    BOB_FUNDS,
    DEPLOYED_RUNTIME,
    EMITTER_CODE,
    EVENT_DATA,
    FACTORY_CODE,
    FEE_PER_GAS,
    FOUR_TOPIC_CODE,
    FUNDS,
    INITCODE_DEPLOYING,
    KEY_A,
    KEY_B,
    SILENT_CODE,
    TOPIC_1,
    TOPIC_2,
    TOPIC_3,
    TOPIC_4,
    VALUE,
    WRITER_CODE,
    WRITER_POST,
    WRITER_STORAGE,
    as_int,
    assertion_transaction,
    body_frame,
    creation_state_gas,
    expect_eq,
    factory_state_gas,
    initcode_word,
    post_tx_frame,
    reverted_body_receipts,
    success_receipts,
)
from .spec import Spec, ref_spec_7906

REFERENCE_SPEC_GIT_PATH = ref_spec_7906.git_path
REFERENCE_SPEC_VERSION = ref_spec_7906.version

pytestmark = pytest.mark.valid_from("EIP7906")

TransferChecks = Callable[[EOA, EOA], Bytecode]
"""Build an assertion's checks from the payer and the recipient."""


def balance_entry(
    account: EOA,
    others: List[EOA],
    before: int,
    after: int | Bytecode,
) -> Bytecode:
    """Return checks of one account's `balances_changed` entry."""
    index = sorted([account, *others], key=as_int).index(account)
    return (
        expect_eq(
            Op.TXTRACE(Spec.TXTRACE_BALANCE_ADDRESS, index), as_int(account)
        )
        + expect_eq(Op.TXTRACE(Spec.TXTRACE_BALANCE_BEFORE, index), before)
        + expect_eq(Op.TXTRACE(Spec.TXTRACE_BALANCE_AFTER, index), after)
    )


def transfer_event(sender: EOA, recipient: EOA) -> Bytecode:
    """Return checks of the transfer's EIP-7708 log, the only event."""
    return (
        expect_eq(
            Op.TXTRACE(Spec.TXTRACE_EVENT_ADDRESS, 0),
            as_int(Spec7708.SYSTEM_ADDRESS),
        )
        + expect_eq(Op.TXTRACE(Spec.TXTRACE_EVENT_TOPIC_COUNT, 0), 3)
        + expect_eq(
            Op.TXTRACE(Spec.TXTRACE_EVENT_TOPIC0, 0),
            int.from_bytes(Spec7708.TRANSFER_TOPIC, "big"),
        )
        + expect_eq(Op.TXTRACE(Spec.TXTRACE_EVENT_TOPIC1, 0), as_int(sender))
        + expect_eq(
            Op.TXTRACE(Spec.TXTRACE_EVENT_TOPIC2, 0), as_int(recipient)
        )
    )


@pytest.mark.parametrize(
    "checks",
    [
        pytest.param(
            lambda *_: expect_eq(
                Op.TXTRACE(Spec.TXTRACE_BALANCES_CHANGED, 0), 2
            ),
            id="balances_changed_count",
        ),
        pytest.param(
            lambda sender, recipient: balance_entry(
                sender, [recipient], FUNDS, Op.BALANCE(sender)
            ),
            id="payer_entry",
        ),
        pytest.param(
            lambda sender, recipient: balance_entry(
                recipient, [sender], BOB_FUNDS, BOB_FUNDS + VALUE
            ),
            id="recipient_entry",
        ),
        pytest.param(
            lambda sender, _: expect_eq(
                Op.TXTRACE(Spec.TXTRACE_GAS_PAYER, 0), as_int(sender)
            ),
            id="gas_payer",
        ),
        pytest.param(
            lambda sender, _: expect_eq(
                Op.TXTRACE(Spec.TXTRACE_GAS_PRE_CHARGE, 0),
                Op.SUB(FUNDS - VALUE, Op.BALANCE(sender)),
            ),
            id="gas_pre_charge",
        ),
        pytest.param(
            lambda *_: expect_eq(Op.TXTRACE(Spec.TXTRACE_SLOTS_CHANGED, 0), 0),
            id="no_slot_changes",
        ),
        pytest.param(
            lambda *_: expect_eq(
                Op.TXTRACE(Spec.TXTRACE_CONTRACTS_DEPLOYED, 0), 0
            ),
            id="no_deployments",
        ),
        pytest.param(
            lambda *_: expect_eq(Op.TXTRACE(Spec.TXTRACE_EVENTS_COUNT, 0), 1),
            id="events_count",
        ),
        pytest.param(transfer_event, id="transfer_event"),
        pytest.param(
            lambda *_: expect_eq(
                Op.TXTRACE(Spec.TXTRACE_EVENT_DATA_LEN, 0), 32
            )
            + Op.EVENTDATACOPY(0, 0, 0, 32)
            + expect_eq(Op.MLOAD(0), VALUE),
            id="transfer_event_data",
        ),
    ],
)
def test_value_transfer_trace(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    checks: TransferChecks,
) -> None:
    """
    Trace a value transfer: the payer's and the recipient's balance
    entries in ascending address order, the gas payment parameters, the
    empty slot and deployment tables, and the EIP-7708 transfer log.
    The payer's escrow is refunded only at settlement, so its live
    balance is its after value and the pre-charge is what the transfer
    does not explain.
    """
    sender = pre.fund_eoa(amount=FUNDS)
    recipient = pre.fund_eoa(amount=BOB_FUNDS)
    assertion = pre.deploy_contract(code=checks(sender, recipient) + Op.STOP)

    state_test(
        pre=pre,
        tx=assertion_transaction(
            fork,
            sender,
            body=[body_frame(fork, target=recipient, value=VALUE)],
            assertion=assertion,
            frame_receipts=success_receipts(3),
        ),
        post={
            sender: Account(nonce=1),
            recipient: Account(balance=BOB_FUNDS + VALUE),
        },
    )


def test_balance_count_mismatch_reverts_body(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Revert a value transfer when the assertion expects one more
    `balances_changed` entry than the payer's and the recipient's.
    """
    sender = pre.fund_eoa(amount=FUNDS)
    recipient = pre.fund_eoa(amount=BOB_FUNDS)
    assertion = pre.deploy_contract(
        code=expect_eq(Op.TXTRACE(Spec.TXTRACE_BALANCES_CHANGED, 0), 3)
        + Op.STOP
    )

    state_test(
        pre=pre,
        tx=assertion_transaction(
            fork,
            sender,
            body=[body_frame(fork, target=recipient, value=VALUE)],
            assertion=assertion,
            frame_receipts=reverted_body_receipts(fork, 1),
        ),
        post={
            sender: Account(nonce=1),
            recipient: Account(balance=BOB_FUNDS),
        },
    )


def test_balances_ascend_regardless_of_transfer_order(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Enumerate `balances_changed` in ascending address order when the
    body pays the higher recipient address first.
    """
    sender = pre.fund_eoa(amount=FUNDS)
    low, high = sorted(
        [pre.fund_eoa(amount=BOB_FUNDS), pre.fund_eoa(amount=BOB_FUNDS)],
        key=as_int,
    )
    checks = expect_eq(Op.TXTRACE(Spec.TXTRACE_BALANCES_CHANGED, 0), 3)
    for index, address in enumerate(sorted([sender, low, high], key=as_int)):
        checks += expect_eq(
            Op.TXTRACE(Spec.TXTRACE_BALANCE_ADDRESS, index), as_int(address)
        )
    assertion = pre.deploy_contract(code=checks + Op.STOP)

    state_test(
        pre=pre,
        tx=assertion_transaction(
            fork,
            sender,
            body=[
                body_frame(fork, target=high, value=VALUE),
                body_frame(fork, target=low, value=VALUE),
            ],
            assertion=assertion,
            frame_receipts=success_receipts(4),
        ),
        post={
            sender: Account(nonce=1),
            low: Account(balance=BOB_FUNDS + VALUE),
            high: Account(balance=BOB_FUNDS + VALUE),
        },
    )


def test_txtrace_operand_order(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Take `param` from the top of the stack and the index below it, the
    reverse of `FRAMEPARAM`, so swapped operands read a different entry
    instead of halting.
    """
    sender = pre.fund_eoa(amount=FUNDS)
    recipients = [pre.fund_eoa(amount=BOB_FUNDS) for _ in range(4)]
    entries = sorted([sender, *recipients], key=as_int)
    # Swapped operands read the address of entry `TXTRACE_BALANCE_BEFORE`.
    index = Spec.TXTRACE_BALANCE_ADDRESS
    assert Spec.TXTRACE_BALANCE_BEFORE < len(entries)
    read = Op.PUSH1(index) + Op.PUSH1(Spec.TXTRACE_BALANCE_BEFORE) + Op.TXTRACE
    before = FUNDS if entries[index] == sender else BOB_FUNDS
    assertion = pre.deploy_contract(code=expect_eq(read, before) + Op.STOP)

    state_test(
        pre=pre,
        tx=assertion_transaction(
            fork,
            sender,
            body=[
                body_frame(fork, target=recipient, value=VALUE)
                for recipient in recipients
            ],
            assertion=assertion,
            frame_receipts=success_receipts(len(recipients) + 2),
        ),
        post={
            sender: Account(nonce=1),
            **{
                recipient: Account(balance=BOB_FUNDS + VALUE)
                for recipient in recipients
            },
        },
    )


def test_slots_changed(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Enumerate `slots_changed` across two contracts: entries ascend by
    address then by key, whatever order the body wrote them in, carry
    the prestate and final values, collapse to one entry per slot, and
    omit a slot written then restored. Only the payer's balance moves.
    """
    sender = pre.fund_eoa()
    writers = sorted(
        [
            pre.deploy_contract(code=WRITER_CODE, storage=WRITER_STORAGE),
            pre.deploy_contract(code=WRITER_CODE, storage=WRITER_STORAGE),
        ],
        key=as_int,
    )
    expected = [
        (writer, key, before, after)
        for writer in writers
        for key, before, after in ((KEY_A, 0, 1), (KEY_B, 5, 7))
    ]

    checks = expect_eq(Op.TXTRACE(Spec.TXTRACE_SLOTS_CHANGED, 0), 4)
    for index, (writer, key, before, after) in enumerate(expected):
        checks += expect_eq(
            Op.TXTRACE(Spec.TXTRACE_SLOT_ADDRESS, index), as_int(writer)
        )
        checks += expect_eq(Op.TXTRACE(Spec.TXTRACE_SLOT_KEY, index), key)
        checks += expect_eq(
            Op.TXTRACE(Spec.TXTRACE_SLOT_BEFORE, index), before
        )
        checks += expect_eq(Op.TXTRACE(Spec.TXTRACE_SLOT_AFTER, index), after)
    checks += expect_eq(Op.TXTRACE(Spec.TXTRACE_BALANCES_CHANGED, 0), 1)
    assertion = pre.deploy_contract(code=checks + Op.STOP)

    state_test(
        pre=pre,
        tx=assertion_transaction(
            fork,
            sender,
            body=[
                body_frame(fork, target=writer) for writer in reversed(writers)
            ],
            assertion=assertion,
            frame_receipts=success_receipts(4),
        ),
        post={
            sender: Account(nonce=1),
            **{writer: Account(storage=WRITER_POST) for writer in writers},
        },
    )


def test_contracts_deployed(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Enumerate `contracts_deployed`: a creation that installs runtime
    code is listed with its code hash, while a creation whose initcode
    returns nothing leaves the account without a code change. Accounts
    the creations wrote without moving their balance are not in
    `balances_changed`, where only the payer appears.
    """
    sender = pre.fund_eoa()
    factory = pre.deploy_contract(code=FACTORY_CODE)
    deployed = compute_create_address(address=factory, nonce=1)
    empty = compute_create_address(address=factory, nonce=2)

    checks = expect_eq(Op.TXTRACE(Spec.TXTRACE_CONTRACTS_DEPLOYED, 0), 1)
    checks += expect_eq(
        Op.TXTRACE(Spec.TXTRACE_DEPLOYED_ADDRESS, 0), as_int(deployed)
    )
    checks += expect_eq(
        Op.TXTRACE(Spec.TXTRACE_DEPLOYED_CODEHASH, 0),
        int.from_bytes(keccak256(DEPLOYED_RUNTIME), "big"),
    )
    checks += expect_eq(Op.TXTRACE(Spec.TXTRACE_BALANCES_CHANGED, 0), 1)
    assertion = pre.deploy_contract(code=checks + Op.STOP)

    state_test(
        pre=pre,
        tx=assertion_transaction(
            fork,
            sender,
            body=[
                body_frame(
                    fork,
                    target=factory,
                    state_gas_limit=factory_state_gas(fork),
                )
            ],
            assertion=assertion,
            frame_receipts=success_receipts(3),
        ),
        post={
            sender: Account(nonce=1),
            factory: Account(nonce=3),
            deployed: Account(nonce=1, code=DEPLOYED_RUNTIME),
            empty: Account(nonce=1, code=b""),
        },
    )


def test_contracts_deployed_ascend_regardless_of_creation_order(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Enumerate `contracts_deployed` in ascending address order when the
    body creates the higher address first.
    """
    sender = pre.fund_eoa()
    initcode_size = len(bytes(INITCODE_DEPLOYING))
    factory = pre.deploy_contract(
        code=Op.MSTORE(0, initcode_word(INITCODE_DEPLOYING))
        + Op.POP(Op.CREATE2(0, 0, initcode_size, Op.CALLDATALOAD(0)))
        + Op.POP(Op.CREATE2(0, 0, initcode_size, Op.CALLDATALOAD(32)))
        + Op.STOP
    )
    by_address = sorted(
        (
            compute_create2_address(
                address=factory, salt=salt, initcode=INITCODE_DEPLOYING
            ),
            salt,
        )
        for salt in (1, 2)
    )
    (lower, lower_salt), (higher, higher_salt) = by_address

    checks = expect_eq(Op.TXTRACE(Spec.TXTRACE_CONTRACTS_DEPLOYED, 0), 2)
    checks += expect_eq(
        Op.TXTRACE(Spec.TXTRACE_DEPLOYED_ADDRESS, 0), as_int(lower)
    )
    checks += expect_eq(
        Op.TXTRACE(Spec.TXTRACE_DEPLOYED_ADDRESS, 1), as_int(higher)
    )
    assertion = pre.deploy_contract(code=checks + Op.STOP)

    state_test(
        pre=pre,
        tx=assertion_transaction(
            fork,
            sender,
            body=[
                body_frame(
                    fork,
                    target=factory,
                    data=higher_salt.to_bytes(32, "big")
                    + lower_salt.to_bytes(32, "big"),
                    state_gas_limit=creation_state_gas(
                        fork,
                        creations=2,
                        deposited_bytes=2 * len(DEPLOYED_RUNTIME),
                    ),
                )
            ],
            assertion=assertion,
            frame_receipts=success_receipts(3),
        ),
        post={
            sender: Account(nonce=1),
            factory: Account(nonce=3),
            lower: Account(nonce=1, code=DEPLOYED_RUNTIME),
            higher: Account(nonce=1, code=DEPLOYED_RUNTIME),
        },
    )


EventChecks = Callable[[Address, Address, Address], Bytecode]
"""
Build an assertion's checks from the two-topic emitter, the topic-less
emitter and the four-topic emitter, in emission order.
"""


@pytest.mark.parametrize(
    "checks",
    [
        pytest.param(
            lambda *_: expect_eq(Op.TXTRACE(Spec.TXTRACE_EVENTS_COUNT, 0), 3),
            id="events_count",
        ),
        pytest.param(
            lambda emitter, *_: expect_eq(
                Op.TXTRACE(Spec.TXTRACE_EVENT_ADDRESS, 0), as_int(emitter)
            )
            + expect_eq(Op.TXTRACE(Spec.TXTRACE_EVENT_TOPIC_COUNT, 0), 2)
            + expect_eq(Op.TXTRACE(Spec.TXTRACE_EVENT_TOPIC0, 0), TOPIC_1)
            + expect_eq(Op.TXTRACE(Spec.TXTRACE_EVENT_TOPIC1, 0), TOPIC_2)
            + expect_eq(
                Op.TXTRACE(Spec.TXTRACE_EVENT_DATA_LEN, 0), len(EVENT_DATA)
            ),
            id="two_topic_event",
        ),
        pytest.param(
            lambda _, silent, __: expect_eq(
                Op.TXTRACE(Spec.TXTRACE_EVENT_ADDRESS, 1), as_int(silent)
            )
            + expect_eq(Op.TXTRACE(Spec.TXTRACE_EVENT_TOPIC_COUNT, 1), 0)
            + expect_eq(Op.TXTRACE(Spec.TXTRACE_EVENT_DATA_LEN, 1), 0),
            id="topicless_event",
        ),
        pytest.param(
            lambda *emitters: expect_eq(
                Op.TXTRACE(Spec.TXTRACE_EVENT_ADDRESS, 2), as_int(emitters[2])
            )
            + expect_eq(Op.TXTRACE(Spec.TXTRACE_EVENT_TOPIC_COUNT, 2), 4)
            + expect_eq(Op.TXTRACE(Spec.TXTRACE_EVENT_TOPIC0, 2), TOPIC_1)
            + expect_eq(Op.TXTRACE(Spec.TXTRACE_EVENT_TOPIC1, 2), TOPIC_2)
            + expect_eq(Op.TXTRACE(Spec.TXTRACE_EVENT_TOPIC2, 2), TOPIC_3)
            + expect_eq(Op.TXTRACE(Spec.TXTRACE_EVENT_TOPIC3, 2), TOPIC_4),
            id="four_topic_event",
        ),
        pytest.param(
            lambda *_: Op.EVENTDATACOPY(0, 0, 0, 32)
            + expect_eq(Op.MLOAD(0), int.from_bytes(EVENT_DATA[:32], "big")),
            id="copy_from_start",
        ),
        pytest.param(
            lambda *_: Op.EVENTDATACOPY(0, 0, 8, 32)
            + expect_eq(Op.MLOAD(0), int.from_bytes(EVENT_DATA[8:40], "big")),
            id="copy_from_offset",
        ),
        pytest.param(
            lambda *_: Op.EVENTDATACOPY(0, 0, len(EVENT_DATA), 0),
            id="zero_size_copy_at_end",
        ),
        pytest.param(
            lambda *_: Op.EVENTDATACOPY(1, 0, 0, 0),
            id="zero_size_copy_of_empty_data",
        ),
    ],
)
def test_event_table(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    checks: EventChecks,
) -> None:
    """
    Enumerate the event table in emission order, with each event's
    emitter, topic count, topics and data length, and copy an event's
    data into memory with `EVENTDATACOPY`, a zero-size copy at the end
    of the data being in range.
    """
    sender = pre.fund_eoa()
    emitters = (
        pre.deploy_contract(code=EMITTER_CODE),
        pre.deploy_contract(code=SILENT_CODE),
        pre.deploy_contract(code=FOUR_TOPIC_CODE),
    )
    assertion = pre.deploy_contract(code=checks(*emitters) + Op.STOP)

    state_test(
        pre=pre,
        tx=assertion_transaction(
            fork,
            sender,
            body=[body_frame(fork, target=emitter) for emitter in emitters],
            assertion=assertion,
            frame_receipts=success_receipts(5),
        ),
        post={sender: Account(nonce=1)},
    )


@pytest.mark.parametrize("blob_count", [0, 1])
@pytest.mark.parametrize(
    "fee_headroom",
    [
        pytest.param(1, id="max_fees_at_price"),
        pytest.param(3, id="max_fees_above_price"),
    ],
)
def test_sponsored_gas_pre_charge(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    blob_count: int,
    fee_headroom: int,
) -> None:
    """
    Expose a distinct payer and its entire escrow, including blob fees,
    priced at the maximum fees even when they exceed the prices the
    transaction pays.
    """
    sender = pre.fund_eoa(amount=FUNDS)
    payer = pre.deploy_contract(
        code=Op.APPROVE(0, 0, Spec8141.APPROVE_PAYMENT), balance=FUNDS
    )
    assertion_code = (
        expect_eq(Op.TXTRACE(Spec.TXTRACE_GAS_PAYER, 0), payer)
        + expect_eq(
            Op.TXTRACE(Spec.TXTRACE_GAS_PRE_CHARGE, 0),
            Op.SUB(FUNDS, Op.BALANCE(payer, address_warm=True)),
        )
        + expect_eq(
            Op.TXDIFF(
                Spec.TXDIFF_BALANCE_BEFORE,
                payer,
                0,
                state_access="account",
                address_warm=True,
            ),
            FUNDS,
        )
        + Op.STOP
    )
    assertion = pre.deploy_contract(code=assertion_code)
    tx = Transaction(
        sender=sender,
        max_fee_per_gas=FEE_PER_GAS * fee_headroom,
        max_priority_fee_per_gas=0,
        max_fee_per_blob_gas=(
            fork.min_base_fee_per_blob_gas() * fee_headroom
            if blob_count
            else 0
        ),
        blob_versioned_hashes=[bytes.fromhex("01" + "00" * 31)] * blob_count,
        frames=[
            verify_frame(flags=Spec8141.APPROVE_EXECUTION),
            verify_frame(target=payer, flags=Spec8141.APPROVE_PAYMENT),
            post_tx_frame(fork, target=assertion),
        ],
        expected_receipt=TransactionReceipt(
            payer=payer, frame_receipts=success_receipts(3)
        ),
    )
    state_test(
        pre=pre,
        tx=tx,
        post={sender: Account(nonce=1, balance=FUNDS)},
    )


@pytest.mark.parametrize("assertion_fails", [False, True])
def test_diff_precedes_selfdestruct_cleanup(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    assertion_fails: bool,
) -> None:
    """
    Read a contract the body created and self-destructed as deployed,
    with its code and storage: the diff is taken before the
    transaction's deferred account cleanup.
    """
    sender = pre.fund_eoa()
    runtime = Op.SSTORE(KEY_A, 1) + Op.SELFDESTRUCT(0)
    initcode = Initcode(deploy_code=runtime)
    factory = pre.deploy_contract(
        code=Op.MSTORE(0, initcode_word(initcode))
        + Op.POP(Op.CREATE(0, 0, len(initcode)))
        + Op.STOP
    )
    created = compute_create_address(address=factory, nonce=1)
    checks = expect_eq(Op.TXTRACE(Spec.TXTRACE_CONTRACTS_DEPLOYED, 0), 1)
    checks += expect_eq(Op.TXTRACE(Spec.TXTRACE_SLOTS_CHANGED, 0), 1)
    checks += expect_eq(Op.TXDIFF(Spec.TXDIFF_SLOT_AFTER, created, KEY_A), 1)
    checks += expect_eq(
        Op.TXDIFF(Spec.TXDIFF_CODEHASH_AFTER, created, 0),
        int.from_bytes(keccak256(bytes(runtime)), "big"),
    )
    assertion = pre.deploy_contract(
        code=checks + (Op.REVERT(0, 0) if assertion_fails else Op.STOP)
    )
    state_test(
        pre=pre,
        tx=assertion_transaction(
            fork,
            sender,
            body=[
                body_frame(
                    fork,
                    target=factory,
                    state_gas_limit=creation_state_gas(
                        fork, creations=1, deposited_bytes=len(runtime)
                    ),
                ),
                body_frame(fork, target=created),
            ],
            assertion=assertion,
            frame_receipts=reverted_body_receipts(fork, 2)
            if assertion_fails
            else success_receipts(4),
        ),
        post={
            sender: Account(nonce=1),
            factory: Account(nonce=1 if assertion_fails else 2),
            created: Account.NONEXISTENT,
        },
    )
