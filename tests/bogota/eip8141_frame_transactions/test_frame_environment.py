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
    Conditional,
    Fork,
    Frame,
    Hash,
    Op,
    StateTestFiller,
    Transaction,
    TransactionLog,
)

from tests.amsterdam.eip7708_eth_transfer_logs.spec import transfer_log

from .helpers import CALL_VALUE
from .spec import ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")


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
    # Each frame's data holds the `CALLVALUE` its target expects; on a
    # mismatch the frame reverts and its receipt no longer matches.
    checker = pre.deploy_contract(
        code=Conditional(
            condition=Op.EQ(Op.CALLVALUE, Op.CALLDATALOAD(0)),
            if_true=Op.STOP,
            if_false=Op.REVERT(0, 0),
        )
    )

    tx = Transaction(
        sender=sender,
        frames=[
            Frame.verify(),
            Frame.sender(
                target=checker,
                value=CALL_VALUE,
                data=Hash(CALL_VALUE),
                pin_gas=False,
                logs=[transfer_log(sender, checker, CALL_VALUE)],
            ),
            Frame.default(
                target=checker, data=Hash(0), pin_gas=False, logs=[]
            ),
        ],
    ).resolve_frames(fork)

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce_change=1),
            checker: Account(balance_change=CALL_VALUE),
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
    reverting = pre.deploy_contract(code=Op.LOG1(0, 0, 0) + Op.REVERT(0, 0))
    frames = [Frame.verify(logs=[])]
    for topic in [1, 2, 3]:
        target = pre.deploy_contract(
            code=Op.POP(Op.CALL(gas=Op.GAS, address=reverting))
            + Op.LOG1(0, 0, topic)
            + Op.STOP
        )
        frames.append(
            Frame.default(
                target=target,
                pin_gas=False,
                logs=[TransactionLog(address=target, topics=[topic])],
            )
        )

    tx = Transaction(sender=sender, frames=frames).resolve_frames(fork)

    state_test(pre=pre, tx=tx, post={sender: Account(nonce_change=1)})
