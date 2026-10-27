"""
Gas of the diff instructions (EIP-7906): the flat `TXTRACE` cost and
the `EVENTDATACOPY` copy cost.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
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
    EMITTER_CODE,
    EVENT_DATA,
    FACTORY_CODE,
    KEY_A,
    TOPIC_1,
    TOPIC_2,
    TOPIC_3,
    TOPIC_4,
    assert_frame,
    assertion_transaction,
    body_frame,
    expect_eq,
    factory_state_gas,
    measured_gas,
    probe_overhead,
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
    every table, followed by an `ASSERT` frame running `checks`.
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
    "probe",
    [
        pytest.param(Op.TXTRACE(Spec.TXTRACE_SLOTS_CHANGED, 0), id="txtrace"),
        pytest.param(
            Op.EVENTDATACOPY(0, 1, 0, 40, data_size=40, new_memory_size=41),
            id="eventdatacopy",
        ),
    ],
)
def test_diff_gas_boundary(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    shortfall: int,
    probe: Bytecode,
) -> None:
    """Charge exact gas for a table read and copying across a word boundary."""
    sender = pre.fund_eoa()
    emitter = pre.deploy_contract(code=Op.SSTORE(KEY_A, 1) + EMITTER_CODE)
    code = probe + Op.STOP
    assertion = pre.deploy_contract(code=code)
    gas = fork.frame_entry_gas_calculator()() + code.execution_cost(fork)
    tx = Transaction(
        sender=sender,
        frames=[
            verify_frame(),
            body_frame(fork, target=emitter),
            assert_frame(fork, target=assertion, gas_limit=gas - shortfall),
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
