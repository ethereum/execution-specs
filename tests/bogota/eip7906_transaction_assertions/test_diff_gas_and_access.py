"""
Gas and state access of the diff instructions (EIP-7906): the flat
`TXTRACE` cost, the `EVENTDATACOPY` copy cost, the EIP-2929 pricing of
the live `TXDIFF` lookups, and the block access list entries those
lookups leave.
"""

from typing import Callable

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    BalAccountExpectation,
    BalNonceChange,
    BalStorageChange,
    BalStorageSlot,
    BlockAccessListExpectation,
    Bytecode,
    Fork,
    FrameReceipt,
    Op,
    StateTestFiller,
    Transaction,
    TransactionReceipt,
)

from tests.bogota.eip8141_frame_transactions.helpers import verify_frame
from tests.bogota.eip8141_frame_transactions.spec import Spec as Spec8141

from .helpers import (
    CAROL_FUNDS,
    EMITTER_CODE,
    EVENT_DATA,
    FACTORY_CODE,
    KEY_A,
    KEY_U,
    NEVER_EXISTED,
    TOPIC_1,
    TOPIC_2,
    TOPIC_3,
    TOPIC_4,
    WRITER_CODE,
    WRITER_POST,
    WRITER_STORAGE,
    assertion_transaction,
    body_frame,
    expect_eq,
    factory_state_gas,
    frame_gas,
    measured_gas,
    post_tx_frame,
    probe_overhead,
    reverted_body_receipts,
    success_receipts,
)
from .spec import Spec, ref_spec_7906

REFERENCE_SPEC_GIT_PATH = ref_spec_7906.git_path
REFERENCE_SPEC_VERSION = ref_spec_7906.version

pytestmark = pytest.mark.valid_from("EIP7906")

SOURCE_CODE = (
    Op.SSTORE(KEY_A, 1)
    + Op.MSTORE(0, int.from_bytes(EVENT_DATA[:32], "big"))
    + Op.MSTORE(32, int.from_bytes(EVENT_DATA[32:].ljust(32, b"\x00"), "big"))
    + Op.LOG4(0, len(EVENT_DATA), TOPIC_1, TOPIC_2, TOPIC_3, TOPIC_4)
    + Op.STOP
)
"""Change a slot and emit an event with every topic and data."""

TXTRACE_PARAMS = [
    pytest.param(value, id=name.removeprefix("TXTRACE_").lower())
    for name, value in vars(Spec).items()
    if name.startswith("TXTRACE_")
    and name not in ("TXTRACE_OPCODE", "TXTRACE_UNDEFINED")
]
"""Every defined `TXTRACE` parameter."""


def fill_on_every_table(
    state_test: StateTestFiller, pre: Alloc, fork: Fork, checks: Bytecode
) -> None:
    """
    Fill a transaction whose body leaves an entry at index zero of
    every table, followed by a `POST_TX` frame running `checks`.
    """
    sender = pre.fund_eoa()
    source = pre.deploy_contract(code=SOURCE_CODE)
    factory = pre.deploy_contract(code=FACTORY_CODE)
    state_test(
        pre=pre,
        tx=assertion_transaction(
            fork,
            sender,
            body=[
                body_frame(fork, target=source),
                body_frame(
                    fork,
                    target=factory,
                    state_gas_limit=factory_state_gas(fork),
                ),
            ],
            assertion=pre.deploy_contract(code=checks + Op.STOP),
            frame_receipts=success_receipts(4),
        ),
        post={sender: Account(nonce=1), source: Account(storage={KEY_A: 1})},
    )


@pytest.mark.parametrize("param", TXTRACE_PARAMS)
def test_txtrace_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    param: int,
) -> None:
    """Charge `TXTRACE` its flat cost for a parameter at index zero."""
    probe = Op.TXTRACE(param, 0)
    checks = expect_eq(
        measured_gas(probe),
        fork.gas_costs().OPCODE_TXTRACE + probe_overhead(fork, probe),
    )
    fill_on_every_table(state_test, pre, fork, checks)


@pytest.mark.parametrize(
    "probe,copied",
    [
        pytest.param(
            Op.EVENTDATACOPY(0, 0, 0, len(EVENT_DATA)),
            len(EVENT_DATA),
            id="whole_data",
        ),
        pytest.param(Op.EVENTDATACOPY(0, 0, 0, 0), 0, id="zero_size"),
        pytest.param(
            Op.EVENTDATACOPY(0, 2**256 - 1, 0, 0),
            0,
            id="zero_size_at_huge_memory_offset",
        ),
    ],
)
def test_eventdatacopy_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    probe: Bytecode,
    copied: int,
) -> None:
    """
    Charge `EVENTDATACOPY` the `CALLDATACOPY` price, the base cost plus
    a per-word copy cost, with the destination memory already expanded,
    and no expansion for a zero-size copy at any memory offset.
    """
    checks = Op.MSTORE(32, 0) + expect_eq(
        measured_gas(probe, pushes_result=False),
        Op.EVENTDATACOPY.with_metadata(data_size=copied).gas_cost(fork)
        + probe_overhead(fork, probe, pushes_result=False),
    )
    fill_on_every_table(state_test, pre, fork, checks)


@pytest.mark.parametrize("shortfall", [0, 1])
@pytest.mark.parametrize(
    "operation",
    [
        pytest.param("trace", id="txtrace"),
        pytest.param("copy", id="eventdatacopy"),
        pytest.param(
            Spec.TXDIFF_ADDRESS_SLOTS_COUNT, id="address_slots_count"
        ),
        pytest.param(Spec.TXDIFF_ADDRESS_SLOT_INDEX, id="address_slot_index"),
        pytest.param(
            Spec.TXDIFF_ADDRESS_EVENTS_COUNT, id="address_events_count"
        ),
        pytest.param(
            Spec.TXDIFF_ADDRESS_EVENT_INDEX, id="address_event_index"
        ),
        pytest.param(
            Spec.TXDIFF_ACCOUNT_CHANGE_FLAGS, id="account_change_flags"
        ),
        pytest.param(Spec.TXDIFF_TOPIC_EVENTS_COUNT, id="topic_events_count"),
        pytest.param(Spec.TXDIFF_TOPIC_EVENT_INDEX, id="topic_event_index"),
    ],
)
def test_diff_view_gas_boundary(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    shortfall: int,
    operation: str | int,
) -> None:
    """Charge exact gas for table views and copying across a word boundary."""
    sender = pre.fund_eoa()
    emitter = pre.deploy_contract(code=Op.SSTORE(KEY_A, 1) + EMITTER_CODE)
    if operation == "trace":
        probe = Op.TXTRACE(Spec.TXTRACE_SLOTS_CHANGED, 0)
    elif operation == "copy":
        probe = Op.EVENTDATACOPY(0, 1, 0, 40, data_size=40, new_memory_size=41)
    else:
        assert isinstance(operation, int)
        key = (
            TOPIC_2 if operation >= Spec.TXDIFF_TOPIC_EVENTS_COUNT else emitter
        )
        probe = Op.TXDIFF(operation, key, 0)
    code = probe + Op.STOP
    assertion = pre.deploy_contract(code=code)
    gas = fork.frame_entry_gas_calculator()() + code.execution_cost(fork)
    tx = Transaction(
        sender=sender,
        frames=[
            verify_frame(),
            body_frame(fork, target=emitter),
            post_tx_frame(fork, target=assertion, gas_limit=gas - shortfall),
        ],
        expected_receipt=TransactionReceipt(
            payer=sender,
            frame_receipts=[
                FrameReceipt(status=Spec8141.STATUS_SUCCESS),
                FrameReceipt(status=Spec8141.STATUS_SUCCESS),
                FrameReceipt(
                    status=Spec8141.STATUS_FAILURE
                    if shortfall
                    else Spec8141.STATUS_SUCCESS,
                    gas_used=gas - shortfall,
                ),
            ],
        ),
    )
    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            emitter: Account(storage={KEY_A: 0 if shortfall else 1}),
        },
    )


def test_txdiff_gas_and_warmth(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Price the live lookups per EIP-2929: a cold slot or account on first
    access, warm on the next, warm for a slot the body wrote and warm
    for a precompile. Read a delegated account without accessing its
    delegation target. Price the view and flags parameters at the flat
    `TXTRACE` cost, without warming the account they are keyed on.
    """
    sender = pre.fund_eoa()
    carol = pre.fund_eoa(amount=CAROL_FUNDS)
    dave = pre.fund_eoa(amount=CAROL_FUNDS)
    writer = pre.deploy_contract(code=WRITER_CODE, storage=WRITER_STORAGE)
    delegated = pre.fund_eoa(
        amount=CAROL_FUNDS, delegation=pre.deploy_contract(code=Op.STOP)
    )
    gas_costs = fork.gas_costs()

    checks = Bytecode()
    for probe, cost in (
        (
            Op.TXDIFF(Spec.TXDIFF_ACCOUNT_CHANGE_FLAGS, dave, 0),
            gas_costs.OPCODE_TXTRACE,
        ),
        (
            Op.TXDIFF(Spec.TXDIFF_BALANCE_AFTER, dave, 0),
            gas_costs.COLD_ACCOUNT_ACCESS,
        ),
        (
            Op.TXDIFF(Spec.TXDIFF_SLOT_AFTER, writer, KEY_A),
            gas_costs.WARM_ACCESS,
        ),
        (
            Op.TXDIFF(Spec.TXDIFF_SLOT_AFTER, writer, KEY_U),
            gas_costs.COLD_STORAGE_ACCESS,
        ),
        (
            Op.TXDIFF(Spec.TXDIFF_SLOT_BEFORE, writer, KEY_U),
            gas_costs.WARM_ACCESS,
        ),
        (
            Op.TXDIFF(Spec.TXDIFF_BALANCE_AFTER, carol, 0),
            gas_costs.COLD_ACCOUNT_ACCESS,
        ),
        (
            Op.TXDIFF(Spec.TXDIFF_CODEHASH_BEFORE, carol, 0),
            gas_costs.WARM_ACCESS,
        ),
        (
            Op.TXDIFF(Spec.TXDIFF_ADDRESS_SLOTS_COUNT, writer, 0),
            gas_costs.OPCODE_TXTRACE,
        ),
        (
            Op.TXDIFF(Spec.TXDIFF_ACCOUNT_CHANGE_FLAGS, carol, 0),
            gas_costs.OPCODE_TXTRACE,
        ),
        (
            Op.TXDIFF(Spec.TXDIFF_TOPIC_EVENTS_COUNT, TOPIC_1, 0),
            gas_costs.OPCODE_TXTRACE,
        ),
        (
            Op.TXDIFF(Spec.TXDIFF_BALANCE_AFTER, fork.precompiles()[0], 0),
            gas_costs.WARM_ACCESS,
        ),
        (
            Op.TXDIFF(Spec.TXDIFF_CODEHASH_AFTER, delegated, 0),
            gas_costs.COLD_ACCOUNT_ACCESS,
        ),
    ):
        checks += expect_eq(
            measured_gas(probe), cost + probe_overhead(fork, probe)
        )
    assertion = pre.deploy_contract(code=checks + Op.STOP)

    state_test(
        pre=pre,
        tx=assertion_transaction(
            fork,
            sender,
            body=[body_frame(fork, target=writer)],
            assertion=assertion,
            frame_receipts=success_receipts(3),
        ),
        post={
            sender: Account(nonce=1),
            writer: Account(storage=WRITER_POST),
        },
    )


@pytest.mark.parametrize(
    "account_read",
    [
        pytest.param(
            lambda target: Op.BALANCE(target, address_warm=False),
            id="balance",
        ),
        pytest.param(
            lambda target: Op.EXTCODEHASH(target, address_warm=False),
            id="extcodehash",
        ),
        pytest.param(
            lambda target: Op.TXDIFF(
                Spec.TXDIFF_BALANCE_AFTER,
                target,
                0,
                state_access="account",
                address_warm=False,
            ),
            id="txdiff_balance_after",
        ),
    ],
)
def test_txdiff_slot_lookup_leaves_address_cold(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    account_read: Callable[[Address], Bytecode],
) -> None:
    """
    Price and warm only the `(address, slot)` pair on a slot lookup, so
    a later read of the account still pays the cold account access.
    """
    sender = pre.fund_eoa()
    target = pre.deploy_contract(code=Op.STOP, storage={KEY_U: 3})
    closing = Op.POP + Op.GAS
    checks = Bytecode()
    for probe in (
        Op.TXDIFF(
            Spec.TXDIFF_SLOT_AFTER,
            target,
            KEY_U,
            state_access="slot",
            key_warm=False,
        ),
        account_read(target),
    ):
        checks += expect_eq(
            measured_gas(probe), probe.gas_cost(fork) + closing.gas_cost(fork)
        )
    assertion = pre.deploy_contract(code=checks + Op.STOP)

    state_test(
        pre=pre,
        tx=assertion_transaction(
            fork,
            sender,
            body=[],
            assertion=assertion,
            frame_receipts=success_receipts(2),
        ),
        post={sender: Account(nonce=1), target: Account(storage={KEY_U: 3})},
    )


def test_txdiff_records_accesses(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Record a live `TXDIFF` lookup in the block access list like any
    other state read: the unwritten slot the assertion reads is a
    storage read of the writer, and the untouched account it reads
    appears as a touched account without changes.
    """
    sender = pre.fund_eoa()
    carol = pre.fund_eoa(amount=CAROL_FUNDS)
    writer = pre.deploy_contract(
        code=Op.SSTORE(KEY_A, 1) + Op.STOP, storage={KEY_U: 3}
    )
    assertion = pre.deploy_contract(
        code=expect_eq(Op.TXDIFF(Spec.TXDIFF_SLOT_AFTER, writer, KEY_U), 3)
        + expect_eq(
            Op.TXDIFF(Spec.TXDIFF_BALANCE_AFTER, carol, 0), CAROL_FUNDS
        )
        + Op.STOP
    )

    tx = assertion_transaction(
        fork,
        sender,
        body=[body_frame(fork, target=writer)],
        assertion=assertion,
        frame_receipts=success_receipts(3),
    )

    state_test(
        pre=pre,
        tx=tx,
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                writer: BalAccountExpectation(
                    storage_changes=[
                        BalStorageSlot(
                            slot=KEY_A,
                            slot_changes=[
                                BalStorageChange(
                                    block_access_index=1,
                                    post_value=1,
                                )
                            ],
                        )
                    ],
                    storage_reads=[KEY_U],
                ),
                carol: BalAccountExpectation.empty(),
                sender: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
            },
        ),
        post={
            sender: Account(nonce=1),
            writer: Account(storage={KEY_A: 1, KEY_U: 3}),
            carol: Account(balance=CAROL_FUNDS),
        },
    )


LIVE_LOOKUPS = [
    pytest.param(Spec.TXDIFF_SLOT_BEFORE, id="slot_before"),
    pytest.param(Spec.TXDIFF_SLOT_AFTER, id="slot_after"),
    pytest.param(Spec.TXDIFF_BALANCE_BEFORE, id="balance_before"),
    pytest.param(Spec.TXDIFF_BALANCE_AFTER, id="balance_after"),
    pytest.param(Spec.TXDIFF_CODEHASH_BEFORE, id="codehash_before"),
    pytest.param(Spec.TXDIFF_CODEHASH_AFTER, id="codehash_after"),
]
"""The `TXDIFF` parameters that read live state, slots then accounts."""


@pytest.mark.parametrize("param", LIVE_LOOKUPS)
@pytest.mark.parametrize("warm", [False, True])
@pytest.mark.parametrize("shortfall", [0, 1])
def test_txdiff_access_gas_boundary(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    param: int,
    warm: bool,
    shortfall: int,
) -> None:
    """
    Record live accesses only after the full opcode charge, at exact
    and one-short gas, for both cold and warm account and slot reads.
    """
    sender = pre.fund_eoa()
    target = pre.deploy_contract(code=Op.STOP, storage={KEY_U: 3})
    is_slot = param <= Spec.TXDIFF_SLOT_AFTER
    key = KEY_U if is_slot else 0
    probe = Op.TXDIFF(
        param,
        target,
        key,
        state_access="slot" if is_slot else "account",
        key_warm=warm,
        address_warm=warm,
    )
    prelude = Bytecode()
    if warm:
        prelude = Op.POP(
            Op.TXDIFF(
                param,
                target,
                key,
                state_access="slot" if is_slot else "account",
            )
        )
    code = prelude + probe + Op.STOP
    assertion = pre.deploy_contract(code=code)
    gas = fork.frame_entry_gas_calculator()() + code.execution_cost(fork)
    accessed = warm or shortfall == 0
    expectation = (
        BalAccountExpectation(storage_reads=[KEY_U], storage_changes=[])
        if is_slot
        else BalAccountExpectation.empty()
    )
    state_test(
        pre=pre,
        tx=Transaction(
            sender=sender,
            frames=[
                verify_frame(),
                post_tx_frame(
                    fork, target=assertion, gas_limit=gas - shortfall
                ),
            ],
            expected_receipt=TransactionReceipt(
                payer=sender,
                frame_receipts=[
                    FrameReceipt(status=Spec8141.STATUS_SUCCESS),
                    FrameReceipt(
                        status=Spec8141.STATUS_FAILURE
                        if shortfall
                        else Spec8141.STATUS_SUCCESS,
                        gas_used=gas - shortfall,
                    ),
                ],
            ),
        ),
        post={sender: Account(nonce=1), target: Account(storage={KEY_U: 3})},
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={target: expectation if accessed else None}
        ),
    )


@pytest.mark.parametrize("param", LIVE_LOOKUPS)
def test_txdiff_never_existing_account_lookup_is_recorded(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    param: int,
) -> None:
    """
    Record a live lookup of an account that never exists: a slot read
    files the address with the slot as its only entry, which `SLOAD`
    can only do for an account whose code is running, and an account
    read files it touched.
    """
    sender = pre.fund_eoa()
    is_slot = param <= Spec.TXDIFF_SLOT_AFTER
    assertion = pre.deploy_contract(
        code=Op.POP(Op.TXDIFF(param, NEVER_EXISTED, KEY_U if is_slot else 0))
        + Op.STOP
    )
    state_test(
        pre=pre,
        tx=assertion_transaction(
            fork,
            sender,
            body=[],
            assertion=assertion,
            frame_receipts=success_receipts(2),
        ),
        post={sender: Account(nonce=1), NEVER_EXISTED: Account.NONEXISTENT},
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                NEVER_EXISTED: BalAccountExpectation(
                    storage_reads=[KEY_U], storage_changes=[]
                )
                if is_slot
                else BalAccountExpectation.empty()
            }
        ),
    )


@pytest.mark.parametrize(
    "param",
    [
        pytest.param(
            Spec.TXDIFF_ADDRESS_SLOTS_COUNT, id="address_slots_count"
        ),
        pytest.param(
            Spec.TXDIFF_ADDRESS_EVENTS_COUNT, id="address_events_count"
        ),
        pytest.param(
            Spec.TXDIFF_ACCOUNT_CHANGE_FLAGS, id="account_change_flags"
        ),
        pytest.param(Spec.TXDIFF_TOPIC_EVENTS_COUNT, id="topic_events_count"),
    ],
)
def test_txdiff_empty_views_do_not_access_state(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    param: int,
) -> None:
    """Leave an untouched view key absent from the block access list."""
    sender = pre.fund_eoa()
    untouched = pre.deploy_contract(code=Op.STOP, storage={KEY_U: 3})
    assertion = pre.deploy_contract(
        code=expect_eq(Op.TXDIFF(param, untouched, 0), 0) + Op.STOP
    )
    state_test(
        pre=pre,
        tx=assertion_transaction(
            fork,
            sender,
            body=[],
            assertion=assertion,
            frame_receipts=success_receipts(2),
        ),
        post={sender: Account(nonce=1)},
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={untouched: None}
        ),
    )


@pytest.mark.parametrize(
    "param,in_post_tx",
    [
        *[
            pytest.param(
                lookup.values[0], True, id=f"reserved_index_{lookup.id}"
            )
            for lookup in LIVE_LOOKUPS[2:]
        ],
        *[
            pytest.param(
                lookup.values[0], False, id=f"outside_post_tx_{lookup.id}"
            )
            for lookup in LIVE_LOOKUPS
        ],
    ],
)
def test_txdiff_halt_records_no_access(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    param: int,
    in_post_tx: bool,
) -> None:
    """
    Halt a live lookup before it reads state, leaving its key out of the
    block access list: on a non-zero reserved input of an account
    lookup, and in any frame other than `POST_TX`.
    """
    sender = pre.fund_eoa()
    carol = pre.fund_eoa(amount=CAROL_FUNDS)
    is_slot = param <= Spec.TXDIFF_SLOT_AFTER
    index = 1 if in_post_tx else (KEY_U if is_slot else 0)
    probe = pre.deploy_contract(code=Op.TXDIFF(param, carol, index) + Op.STOP)
    if in_post_tx:
        tx = assertion_transaction(
            fork,
            sender,
            body=[],
            assertion=probe,
            frame_receipts=reverted_body_receipts(
                fork, 0, assertion_halts=True
            ),
        )
    else:
        tx = Transaction(
            sender=sender,
            frames=[verify_frame(), body_frame(fork, target=probe)],
            expected_receipt=TransactionReceipt(
                payer=sender,
                frame_receipts=[
                    FrameReceipt(status=Spec8141.STATUS_SUCCESS),
                    FrameReceipt(
                        status=Spec8141.STATUS_FAILURE,
                        gas_used=frame_gas(fork),
                    ),
                ],
            ),
        )
    state_test(
        pre=pre,
        tx=tx,
        post={sender: Account(nonce=1), carol: Account(balance=CAROL_FUNDS)},
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={carol: None}
        ),
    )
