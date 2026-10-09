"""
Exceptional halts of the diff instructions (EIP-7906): non-zero
reserved inputs, undefined parameters, and indices and data ranges
beyond a table, a view or an event.
"""

from typing import Callable

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytecode,
    Fork,
    Op,
    StateTestFiller,
)

from .helpers import (
    EMITTER_CODE,
    EVENT_DATA,
    KEY_A,
    SILENT_CODE,
    TOPIC_1,
    TOPIC_2,
    assertion_transaction,
    body_frame,
    expect_eq,
    reverted_body_receipts,
)
from .spec import Spec, ref_spec_7906

REFERENCE_SPEC_GIT_PATH = ref_spec_7906.git_path
REFERENCE_SPEC_VERSION = ref_spec_7906.version

pytestmark = pytest.mark.valid_from("EIP7906")


@pytest.mark.parametrize(
    "halting_read",
    [
        pytest.param(
            Op.TXTRACE(Spec.TXTRACE_BALANCES_CHANGED, 1),
            id="reserved_index_count",
        ),
        pytest.param(
            Op.TXTRACE(Spec.TXTRACE_GAS_PRE_CHARGE, 1),
            id="reserved_index_pre_charge",
        ),
        pytest.param(
            Op.TXTRACE(Spec.TXTRACE_GAS_PAYER, 1),
            id="reserved_index_payer",
        ),
        pytest.param(
            Op.TXTRACE(Spec.TXTRACE_SLOTS_CHANGED, 1),
            id="reserved_index_slots_count",
        ),
        pytest.param(
            Op.TXTRACE(Spec.TXTRACE_CONTRACTS_DEPLOYED, 1),
            id="reserved_index_deployed_count",
        ),
        pytest.param(
            Op.TXTRACE(Spec.TXTRACE_EVENTS_COUNT, 1),
            id="reserved_index_events_count",
        ),
        pytest.param(
            Op.TXTRACE(Spec.TXTRACE_EVENTS_COUNT, 2**255),
            id="reserved_index_high_bit",
        ),
        pytest.param(
            Op.TXTRACE(Spec.TXTRACE_UNDEFINED, 0), id="undefined_param"
        ),
        pytest.param(Op.TXTRACE(2**64, 0), id="undefined_param_above_64_bits"),
        pytest.param(Op.TXTRACE(2**255, 0), id="undefined_param_high_bit"),
        pytest.param(
            Op.TXTRACE(Spec.TXTRACE_BALANCE_ADDRESS, 1),
            id="balance_index_out_of_bounds",
        ),
        pytest.param(
            Op.TXTRACE(Spec.TXTRACE_SLOT_AFTER, 1),
            id="slot_index_out_of_bounds",
        ),
        pytest.param(
            Op.TXTRACE(Spec.TXTRACE_BALANCE_ADDRESS, 2**64),
            id="index_above_64_bits",
        ),
        pytest.param(
            Op.TXTRACE(Spec.TXTRACE_DEPLOYED_ADDRESS, 0),
            id="deployed_index_out_of_bounds",
        ),
        pytest.param(
            Op.TXTRACE(Spec.TXTRACE_EVENT_ADDRESS, 2),
            id="event_index_out_of_bounds",
        ),
        pytest.param(
            Op.TXTRACE(Spec.TXTRACE_EVENT_TOPIC2, 0),
            id="topic_beyond_count",
        ),
        pytest.param(
            Op.TXTRACE(Spec.TXTRACE_EVENT_TOPIC0, 1),
            id="topic_of_topicless_event",
        ),
        pytest.param(
            Op.EVENTDATACOPY(2, 0, 0, 0), id="copy_event_out_of_bounds"
        ),
        pytest.param(Op.EVENTDATACOPY(0, 0, 32, 32), id="copy_range_past_end"),
        pytest.param(
            Op.EVENTDATACOPY(0, 0, len(EVENT_DATA), 1),
            id="copy_one_byte_past_end",
        ),
        pytest.param(Op.EVENTDATACOPY(1, 0, 0, 1), id="copy_from_empty_data"),
        pytest.param(
            Op.EVENTDATACOPY(0, 0, len(EVENT_DATA) + 1, 0),
            id="copy_zero_size_past_end",
        ),
        pytest.param(
            Op.EVENTDATACOPY(0, 0, 2**64 - 1, 1),
            id="copy_range_beyond_64_bits",
        ),
        pytest.param(
            # `dataOffset + length` would wrap to zero in 256-bit
            # arithmetic, which the range check must not do.
            Op.EVENTDATACOPY(0, 0, 2**256 - 1, 1),
            id="copy_range_wraps_past_256_bits",
        ),
        pytest.param(
            Op.EVENTDATACOPY(2**64, 0, 0, 0),
            id="copy_event_index_above_64_bits",
        ),
    ],
)
def test_txtrace_halts(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    halting_read: Bytecode,
) -> None:
    """
    Halt `TXTRACE` and `EVENTDATACOPY` exceptionally on a non-zero
    reserved input, an undefined parameter, an index beyond a table, a
    topic beyond an event's topic count, and a data range past an
    event's data, operands wider than 64 bits included. The halt
    consumes the assertion frame's budget and reverts the body, whose
    tables hold one changed slot, the payer's balance, no deployment
    and two events.
    """
    sender = pre.fund_eoa()
    writer = pre.deploy_contract(code=Op.SSTORE(KEY_A, 1) + Op.STOP)
    emitter = pre.deploy_contract(code=EMITTER_CODE)
    silent = pre.deploy_contract(code=SILENT_CODE)
    assertion = pre.deploy_contract(code=halting_read + Op.STOP)

    state_test(
        pre=pre,
        tx=assertion_transaction(
            fork,
            sender,
            body=[
                body_frame(fork, target=writer),
                body_frame(fork, target=emitter),
                body_frame(fork, target=silent),
            ],
            assertion=assertion,
            frame_receipts=reverted_body_receipts(
                fork, 3, assertion_halts=True
            ),
        ),
        post={
            sender: Account(nonce=1),
            writer: Account(storage={KEY_A: 0}),
        },
    )


HaltingRead = Callable[[Address], Bytecode]
"""Build a halting `TXDIFF` read keyed on the body's writer if needed."""


@pytest.mark.parametrize(
    "halting_read",
    [
        pytest.param(
            lambda _: Op.TXDIFF(Spec.TXDIFF_BALANCE_BEFORE, 0xBEEF, 1),
            id="reserved_index_balance_before",
        ),
        pytest.param(
            lambda _: Op.TXDIFF(Spec.TXDIFF_BALANCE_AFTER, 0xBEEF, 1),
            id="reserved_index_balance_after",
        ),
        pytest.param(
            lambda _: Op.TXDIFF(Spec.TXDIFF_CODEHASH_BEFORE, 0xBEEF, 1),
            id="reserved_index_codehash_before",
        ),
        pytest.param(
            lambda _: Op.TXDIFF(Spec.TXDIFF_CODEHASH_AFTER, 0xBEEF, 1),
            id="reserved_index_codehash_after",
        ),
        pytest.param(
            lambda _: Op.TXDIFF(Spec.TXDIFF_ADDRESS_SLOTS_COUNT, 0xBEEF, 1),
            id="reserved_index_slots_count",
        ),
        pytest.param(
            lambda _: Op.TXDIFF(Spec.TXDIFF_ADDRESS_EVENTS_COUNT, 0xBEEF, 1),
            id="reserved_index_events_count",
        ),
        pytest.param(
            lambda _: Op.TXDIFF(Spec.TXDIFF_ACCOUNT_CHANGE_FLAGS, 0xBEEF, 1),
            id="reserved_index_flags",
        ),
        pytest.param(
            lambda _: Op.TXDIFF(
                Spec.TXDIFF_ACCOUNT_CHANGE_FLAGS, 0xBEEF, 2**255
            ),
            id="reserved_index_high_bit",
        ),
        pytest.param(
            lambda _: Op.TXDIFF(Spec.TXDIFF_TOPIC_EVENTS_COUNT, TOPIC_1, 1),
            id="reserved_index_topic_count",
        ),
        pytest.param(
            lambda _: Op.TXDIFF(Spec.TXDIFF_UNDEFINED, 0, 0),
            id="undefined_param",
        ),
        pytest.param(
            lambda _: Op.TXDIFF(2**64, 0, 0),
            id="undefined_param_above_64_bits",
        ),
        pytest.param(
            lambda _: Op.TXDIFF(2**255, 0, 0),
            id="undefined_param_high_bit",
        ),
        pytest.param(
            lambda _: Op.TXDIFF(Spec.TXDIFF_ADDRESS_EVENT_INDEX, 0xBEEF, 0),
            id="event_index_of_silent_address",
        ),
        pytest.param(
            lambda writer: Op.TXDIFF(
                Spec.TXDIFF_ADDRESS_EVENT_INDEX, writer, 1
            ),
            id="event_index_at_count",
        ),
        pytest.param(
            lambda _: Op.TXDIFF(Spec.TXDIFF_TOPIC_EVENT_INDEX, TOPIC_1, 0),
            id="topic_index_of_signature_topic",
        ),
        pytest.param(
            lambda _: Op.TXDIFF(Spec.TXDIFF_TOPIC_EVENT_INDEX, TOPIC_2, 1),
            id="topic_index_at_count",
        ),
    ],
)
def test_txdiff_halts(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    halting_read: HaltingRead,
) -> None:
    """
    Halt `TXDIFF` exceptionally on a non-zero reserved input, an
    undefined parameter, and a per-address or per-topic index at or
    beyond the view's count. The halt consumes the assertion frame's
    budget and reverts the body, whose writer changed one slot and
    emitted one event.
    """
    sender = pre.fund_eoa()
    writer = pre.deploy_contract(
        code=Op.SSTORE(KEY_A, 1) + Op.LOG2(0, 0, TOPIC_1, TOPIC_2) + Op.STOP
    )
    assertion = pre.deploy_contract(code=halting_read(writer) + Op.STOP)

    state_test(
        pre=pre,
        tx=assertion_transaction(
            fork,
            sender,
            body=[body_frame(fork, target=writer)],
            assertion=assertion,
            frame_receipts=reverted_body_receipts(
                fork, 1, assertion_halts=True
            ),
        ),
        post={
            sender: Account(nonce=1),
            writer: Account(storage={KEY_A: 0}),
        },
    )


def test_txdiff_slot_index_out_of_bounds(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Halt the per-address slot view on a local index equal to the view's
    count: the writer changed exactly one slot.
    """
    sender = pre.fund_eoa()
    writer = pre.deploy_contract(code=Op.SSTORE(KEY_A, 1) + Op.STOP)
    assertion = pre.deploy_contract(
        code=expect_eq(Op.TXDIFF(Spec.TXDIFF_ADDRESS_SLOT_INDEX, writer, 0), 0)
        + Op.TXDIFF(Spec.TXDIFF_ADDRESS_SLOT_INDEX, writer, 1)
        + Op.STOP
    )

    state_test(
        pre=pre,
        tx=assertion_transaction(
            fork,
            sender,
            body=[body_frame(fork, target=writer)],
            assertion=assertion,
            frame_receipts=reverted_body_receipts(
                fork, 1, assertion_halts=True
            ),
        ),
        post={
            sender: Account(nonce=1),
            writer: Account(storage={KEY_A: 0}),
        },
    )
