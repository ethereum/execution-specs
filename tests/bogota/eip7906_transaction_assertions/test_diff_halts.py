"""
Exceptional halts of the diff instructions (EIP-7906): non-zero
reserved inputs, undefined parameters, indices and data ranges beyond
a table or an event, and the undefined opcode the EIP dropped.
"""

import pytest
from execution_testing import (
    Account,
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
    assertion_transaction,
    body_frame,
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
            Op.TXTRACE(Spec.TXTRACE_CODES_CHANGED, 1),
            id="reserved_index_codes_count",
        ),
        pytest.param(
            Op.TXTRACE(Spec.TXTRACE_NONCES_CHANGED, 1),
            id="reserved_index_nonces_count",
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
            Op.TXTRACE(Spec.TXTRACE_CODE_ADDRESS, 0),
            id="code_index_out_of_bounds",
        ),
        pytest.param(
            Op.TXTRACE(Spec.TXTRACE_CODE_AFTER, 0),
            id="code_after_index_out_of_bounds",
        ),
        pytest.param(
            Op.TXTRACE(Spec.TXTRACE_NONCE_ADDRESS, 1),
            id="nonce_index_out_of_bounds",
        ),
        pytest.param(
            Op.TXTRACE(Spec.TXTRACE_NONCE_AFTER, 1),
            id="nonce_after_index_out_of_bounds",
        ),
        pytest.param(
            Bytecode(
                bytes([Spec.UNDEFINED_OPCODE]),
                popped_stack_items=0,
                pushed_stack_items=0,
            ),
            id="undefined_opcode",
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
    tables hold one changed slot, the payer's balance, the sender's
    nonce, no code change and two events. The opcode the EIP dropped is
    undefined.
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
