"""
Frame call environment tests for
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

Each frame runs as a top-level call (§Behavior: "Execute a call with
the specified `mode`, `flags`, `target`, `limits`, `value`, and
`data`."). These tests pin frame-level `CALLVALUE` and isolation of
logs in per-frame receipts.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    Frame,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
    TransactionLog,
)

from tests.amsterdam.eip7708_eth_transfer_logs.spec import transfer_log

from .helpers import CURRENT_FRAME_INDEX
from .spec import ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")

FRAME_VALUE = 10**9
"""Value carried by the value-bearing `SENDER` frames."""


def test_callvalue_is_the_frame_value(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test that `CALLVALUE` at a frame's top level is the frame's value:
    `frame.value` in a `SENDER` frame carrying value, zero in a `DEFAULT`
    frame.
    """
    sender = pre.fund_eoa()
    record = Op.SSTORE(CURRENT_FRAME_INDEX, Op.CALLVALUE) + Op.STOP
    storage = Storage()
    storage[1] = FRAME_VALUE
    storage[2] = 0
    # The `DEFAULT` frame's slot starts nonzero, so a zero recorded there
    # is told apart from a slot never written.
    recorder = pre.deploy_contract(code=record, storage=storage.canary())

    tx = Transaction(
        sender=sender,
        frames=[
            Frame.verify(),
            Frame.sender(
                target=recorder,
                value=FRAME_VALUE,
                pin_gas=False,
                state_gas_used=record.state_cost(fork),
                logs=[transfer_log(sender, recorder, FRAME_VALUE)],
            ),
            Frame.default(target=recorder, pin_gas=False, logs=[]),
        ],
    ).resolve_frames(fork)

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce_change=1),
            recorder: Account(balance_change=FRAME_VALUE, storage=storage),
        },
    )


def test_frame_receipt_drops_logs_of_reverted_calls(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test that each frame's receipt holds only its own logs, and drops the
    log of a call inside the frame that reverted.
    """
    sender = pre.fund_eoa()
    first = pre.deploy_contract(code=Op.LOG1(0, 0, 1) + Op.STOP)
    second = pre.deploy_contract(code=Op.LOG1(0, 0, 2) + Op.STOP)
    reverting = pre.deploy_contract(code=Op.LOG1(0, 0, 3) + Op.REVERT(0, 0))
    third = pre.deploy_contract(
        code=Op.POP(Op.CALL(gas=Op.GAS, address=reverting))
        + Op.LOG1(0, 0, 4)
        + Op.STOP
    )

    tx = Transaction(
        sender=sender,
        frames=[
            Frame.verify(logs=[]),
            Frame.default(
                target=first,
                pin_gas=False,
                logs=[TransactionLog(address=first, topics=[1])],
            ),
            Frame.default(
                target=second,
                pin_gas=False,
                logs=[TransactionLog(address=second, topics=[2])],
            ),
            Frame.default(
                target=third,
                gas_limit=200_000,
                pin_gas=False,
                logs=[TransactionLog(address=third, topics=[4])],
            ),
        ],
    ).resolve_frames(fork)

    state_test(pre=pre, tx=tx, post={sender: Account(nonce_change=1)})
