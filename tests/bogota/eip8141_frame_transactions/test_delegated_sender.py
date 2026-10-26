"""
EIP-7702-delegated sender tests for
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

A sender whose account holds an EIP-7702 delegation indicator is not a
codeless account: its code hash is the indicator's, not the empty code
hash. Its frames therefore run the delegated code, as an ordinary call
to it would (§Behavior: "Otherwise, if `resolved_target` uses an
EIP-7702 delegation indicator, execute according to EIP-7702's
delegated-code semantics."), and never the default code, which exists
only for "accounts who do not have deployed code, nor an EIP-7702
delegation indicator" (§Default code).

The delegated code runs as the sender: `ADDRESS` is the sender, so an
`APPROVE` in it passes the `ADDRESS == resolved_target` check, and in a
`SENDER` frame `CALLER` and `ORIGIN` are the sender too.
"""

from typing import Callable, Dict

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    Conditional,
    Fork,
    Op,
    StateTestFiller,
    TransactionException,
)

from .helpers import (
    APPROVE_ALL,
    FrameTransaction,
    sender_frame,
    verify_frame,
)
from .spec import ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")

SLOT_CALLER = 0x00
"""Storage slot the delegated code writes `CALLER` into."""

SLOT_ORIGIN = 0x01
"""Storage slot the delegated code writes `ORIGIN` into."""

SLOT_ADDRESS = 0x02
"""Storage slot the delegated code writes `ADDRESS` into."""

SLOT_CALLVALUE = 0x03
"""Storage slot the delegated code writes `CALLVALUE` into."""

SENDER_FRAME_VALUE = 5
"""Value the `SENDER` frame carries, which `CALLVALUE` reports."""

RECORD_ENVIRONMENT = (
    Op.SSTORE(SLOT_CALLER, Op.CALLER)
    + Op.SSTORE(SLOT_ORIGIN, Op.ORIGIN)
    + Op.SSTORE(SLOT_ADDRESS, Op.ADDRESS)
    + Op.SSTORE(SLOT_CALLVALUE, Op.CALLVALUE)
    + Op.STOP
)
"""Record the call environment the delegated code runs with."""


def test_delegated_sender_runs_delegated_code(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Run a delegated sender's delegated code in its `VERIFY` frame,
    which approves through it, and in its `SENDER` frame, which records
    its call environment into the sender's storage.

    EIP-8141 §Behavior: "Otherwise, if `resolved_target` uses an
    EIP-7702 delegation indicator, execute according to EIP-7702's
    delegated-code semantics." §`APPROVE` Behavior: "If `ADDRESS !=
    resolved_target`, revert." Delegated code runs at the sender's
    address, so its `APPROVE` passes. §Behavior, `SENDER` mode: "Set
    `caller` to `tx.sender`." and "The `ORIGIN` opcode returns frame's
    `caller` throughout all call depths." and "In the top-level frame
    call, `CALLVALUE` is `frame.value`."

    The transaction carries no signature entry, so the default code
    could not approve for the sender: the transaction is valid only if
    the `VERIFY` frame ran the delegated `APPROVE`. The `SENDER` frame
    supplies calldata, so the same delegated code records instead of
    approving.
    """
    delegated_code = Conditional(
        condition=Op.CALLDATASIZE,
        if_true=RECORD_ENVIRONMENT,
        if_false=APPROVE_ALL,
    )
    delegate = pre.deploy_contract(code=delegated_code)
    sender = pre.fund_eoa(delegation=delegate)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        signatures=[],
        frames=[
            verify_frame(delegated=True, pin_gas=False),
            # The `VERIFY` frame's success leaves the delegate warm.
            sender_frame(
                value=SENDER_FRAME_VALUE,
                data=Bytes(b"\x01"),
                delegated=True,
                delegation_warm=True,
                pin_gas=False,
                state_gas_used=RECORD_ENVIRONMENT.state_cost(fork),
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(
                # The delegation set the sender's nonce before the
                # transaction; the approval increments it once more.
                nonce_change=1,
                storage={
                    SLOT_CALLER: sender,
                    SLOT_ORIGIN: sender,
                    SLOT_ADDRESS: sender,
                    SLOT_CALLVALUE: SENDER_FRAME_VALUE,
                },
            ),
            delegate: Account(storage={}),
        },
    )


DelegateFactory = Callable[[Alloc], Address]
"""Return the address a sender delegates to, deploying what it needs."""


def approving_delegate(pre: Alloc) -> Address:
    """Return a delegate whose code approves execution and payment."""
    return pre.deploy_contract(code=APPROVE_ALL)


def eoa_delegate(pre: Alloc) -> Address:
    """Return a funded delegate account holding no code."""
    return pre.fund_eoa()


def absent_delegate(pre: Alloc) -> Address:
    """Return a delegate address with no account in the state."""
    return pre.nonexistent_account()


def chained_delegate(pre: Alloc) -> Address:
    """
    Return an account that is itself delegated to an approving
    contract: EIP-7702 follows a single hop, so a sender delegating to
    it runs its delegation indicator as code.
    """
    return pre.fund_eoa(delegation=approving_delegate(pre))


@pytest.mark.parametrize(
    "make_delegate,approves",
    [
        pytest.param(approving_delegate, True, id="delegate_approves"),
        pytest.param(
            eoa_delegate,
            False,
            id="delegate_is_codeless_eoa",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            absent_delegate,
            False,
            id="delegate_is_absent",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            chained_delegate,
            False,
            id="delegate_is_delegated",
            marks=pytest.mark.exception_test,
        ),
    ],
)
def test_delegated_sender_never_runs_default_code(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    make_delegate: DelegateFactory,
    approves: bool,
) -> None:
    """
    Reject a delegated sender whose delegated code does not approve,
    even though the transaction carries the sender's valid signature
    entry over the canonical hash, which the default code would accept.

    EIP-8141 §Default code: "Frame transactions can be used by accounts
    who do not have deployed code, nor an EIP-7702 delegation indicator
    via the "default code" mechanism." The sender holds an indicator,
    so its `VERIFY` frame runs the delegated code (§Behavior: "if
    `resolved_target` uses an EIP-7702 delegation indicator, execute
    according to EIP-7702's delegated-code semantics"):

    - a codeless or absent delegate gives empty code, which returns
      without approving, so after the last frame "`payer` has [not]
      been set" and "the whole transaction is invalid" (§Behavior);
    - a delegate that is itself delegated gives its delegation
      indicator as code, since EIP-7702 follows one hop only; its
      leading `0xef` byte halts, and "If the frame fails by reverting
      or halting exceptionally, the transaction is invalid."

    The `delegate_approves` case is the control: the same sender and
    signature entry, with a delegate whose code approves, is valid.
    """
    delegate = make_delegate(pre)
    sender = pre.fund_eoa(delegation=delegate)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[verify_frame(delegated=True, pin_gas=False)],
        error=(
            None
            if approves
            else TransactionException.TYPE_6_INVALID_FRAME_EXECUTION
        ),
    )

    post: Dict[Address, Account] = {
        sender: Account(nonce_change=1 if approves else 0)
    }
    state_test(pre=pre, tx=tx, post=post)
