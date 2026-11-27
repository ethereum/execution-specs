"""
`CALLER` and `ORIGIN` tests for
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

Every frame runs as a top-level call from the frame's `caller`: the
transaction sender in a `SENDER` frame, and `ENTRY_POINT` in a `DEFAULT`
or `VERIFY` frame. `CALLER` at the frame's top level is that caller, and
below it follows the usual call rules. `ORIGIN` "returns frame's
`caller` throughout all call depths" (§Behavior), so it changes from
frame to frame within one transaction.

The code reading `CALLER` and `ORIGIN` checks them where it runs and
reverts on a mismatch. The revert reaches the frame, so a `SENDER` or
`DEFAULT` frame's receipt no longer matches, and a `VERIFY` frame leaves
the payment unapproved, which makes the transaction invalid.
"""

from typing import Self

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytecode,
    Bytes,
    Conditional,
    Fork,
    Frame,
    FrameFlag,
    FrameMode,
    Hash,
    Op,
    Opcode,
    StateTestFiller,
    Transaction,
    create_op,
)

from .helpers import APPROVE_ALL
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")


class CallerOriginGuard(Bytecode):
    """
    Code that stops, or grants `approve`, when `CALLER` is `caller` and
    `ORIGIN` is `origin`, and reverts otherwise. `caller` defaults to the
    word the call data holds, and `origin` to `caller`.
    """

    def __new__(
        cls,
        *,
        caller: Bytecode | Address | None = None,
        origin: Bytecode | Address | None = None,
        approve: FrameFlag = Spec.APPROVE_NONE,
    ) -> Self:
        """Assemble the check, granting `approve` when it passes."""
        if caller is None:
            caller = Op.CALLDATALOAD(0)
        if origin is None:
            origin = caller
        if_true = Op.APPROVE(0, 0, approve) if approve else Op.STOP
        return super().__new__(
            cls,
            Conditional(
                condition=Op.AND(
                    Op.EQ(Op.CALLER, caller), Op.EQ(Op.ORIGIN, origin)
                ),
                if_true=if_true,
                if_false=Op.REVERT(0, 0),
            ),
        )


@pytest.mark.parametrize(
    "mode",
    [
        pytest.param(Spec.MODE_DEFAULT, id="default_frame"),
        pytest.param(Spec.MODE_SENDER, id="sender_frame"),
    ],
)
@pytest.mark.parametrize(
    "contract_sender",
    [
        pytest.param(False, id="eoa_sender"),
        pytest.param(True, id="contract_sender"),
    ],
)
def test_caller_and_origin_at_frame_top_level(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    mode: FrameMode,
    contract_sender: bool,
) -> None:
    """
    Test that `CALLER` and `ORIGIN` at a frame's top level are both the
    frame's `caller`, for an EOA and a contract sender.
    """
    sender: Address
    if contract_sender:
        sender = pre.deploy_contract(code=APPROVE_ALL, balance=10**18)
        verify = Frame.verify(code=APPROVE_ALL)
    else:
        sender = pre.fund_eoa()
        verify = Frame.verify()
    checker = pre.deploy_contract(code=CallerOriginGuard())

    tx = Transaction(
        sender=sender,
        nonce=1 if contract_sender else 0,
        frames=[
            verify,
            Frame(
                mode=mode,
                target=checker,
                data=Hash(Frame.caller(mode, sender), left_padding=True),
                pin_gas=False,
            ),
        ],
    ).resolve_frames(fork)

    state_test(pre=pre, tx=tx, post={sender: Account(nonce_change=1)})


@pytest.mark.parametrize(
    "mode",
    [
        pytest.param(Spec.MODE_DEFAULT, id="default_frame"),
        pytest.param(Spec.MODE_SENDER, id="sender_frame"),
    ],
)
@pytest.mark.with_all_call_opcodes
def test_caller_and_origin_in_nested_call(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    mode: FrameMode,
    call_opcode: Opcode,
) -> None:
    """
    Test that `ORIGIN` in a call below the frame's top level is still the
    frame's `caller`, while `CALLER` follows the usual call rules.
    """
    sender = pre.fund_eoa()
    caller = Frame.caller(mode, sender)
    # The frame's data holds the callee, so the target deploys first.
    target = pre.deploy_contract(
        code=Conditional(
            condition=call_opcode(gas=Op.GAS, address=Op.CALLDATALOAD(0)),
            if_true=Op.STOP,
            if_false=Op.REVERT(0, 0),
        )
    )
    nested_caller = caller if call_opcode == Op.DELEGATECALL else target
    callee = pre.deploy_contract(
        code=CallerOriginGuard(caller=nested_caller, origin=caller)
    )

    tx = Transaction(
        sender=sender,
        frames=[
            Frame.verify(),
            Frame(
                mode=mode,
                target=target,
                data=Hash(callee, left_padding=True),
                pin_gas=False,
            ),
        ],
    ).resolve_frames(fork)

    state_test(pre=pre, tx=tx, post={sender: Account(nonce_change=1)})


@pytest.mark.parametrize(
    "nested",
    [
        pytest.param(False, id="top_level"),
        pytest.param(True, id="nested_staticcall"),
    ],
)
def test_caller_and_origin_in_verify_frame(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    nested: bool,
) -> None:
    """
    Test that a contract sender's `VERIFY` frame sees `ENTRY_POINT` as
    `CALLER` and `ORIGIN` at its top level, and the sender as `CALLER`
    with `ENTRY_POINT` as `ORIGIN` in a contract it calls.
    """
    if nested:
        # The frame's data holds the callee, so the sender deploys first.
        sender = pre.deploy_contract(
            code=Conditional(
                condition=Op.STATICCALL(
                    gas=Op.GAS, address=Op.CALLDATALOAD(0)
                ),
                if_true=APPROVE_ALL,
                if_false=Op.REVERT(0, 0),
            ),
            balance=10**18,
        )
        callee = pre.deploy_contract(
            code=CallerOriginGuard(caller=sender, origin=Spec.ENTRY_POINT)
        )
        verify = Frame.verify(
            data=Hash(callee, left_padding=True), pin_gas=False
        )
    else:
        sender = pre.deploy_contract(
            code=CallerOriginGuard(
                caller=Spec.ENTRY_POINT,
                approve=Spec.APPROVE_EXECUTION_AND_PAYMENT,
            ),
            balance=10**18,
        )
        verify = Frame.verify(pin_gas=False)

    tx = Transaction(sender=sender, nonce=1, frames=[verify]).resolve_frames(
        fork
    )

    state_test(pre=pre, tx=tx, post={sender: Account(nonce_change=1)})


def test_origin_follows_each_frame(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test that `CALLER` and `ORIGIN` change from frame to frame when one
    checker runs in alternating `SENDER` and `DEFAULT` frames.
    """
    sender = pre.fund_eoa()
    checker = pre.deploy_contract(code=CallerOriginGuard())
    as_sender = Hash(sender, left_padding=True)
    as_entry_point = Hash(Spec.ENTRY_POINT, left_padding=True)

    tx = Transaction(
        sender=sender,
        frames=[
            Frame.verify(),
            Frame.sender(target=checker, data=as_sender, pin_gas=False),
            Frame.default(target=checker, data=as_entry_point, pin_gas=False),
            Frame.sender(target=checker, data=as_sender, pin_gas=False),
            Frame.default(target=checker, data=as_entry_point, pin_gas=False),
        ],
    ).resolve_frames(fork)

    state_test(pre=pre, tx=tx, post={sender: Account(nonce_change=1)})


def test_origin_returns_to_entry_point_in_verify_frame(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test that a `VERIFY` frame right after a `SENDER` frame sees
    `ENTRY_POINT` as `CALLER` and `ORIGIN`, not the sender the previous
    frame ran as.
    """
    sender = pre.fund_eoa()
    checker = pre.deploy_contract(code=CallerOriginGuard())
    sponsor = pre.deploy_contract(
        code=CallerOriginGuard(approve=Spec.APPROVE_PAYMENT), balance=10**18
    )

    tx = Transaction(
        sender=sender,
        frames=[
            Frame.verify(flags=Spec.APPROVE_EXECUTION),
            Frame.sender(
                target=checker,
                data=Hash(sender, left_padding=True),
                pin_gas=False,
            ),
            Frame.verify(
                flags=Spec.APPROVE_PAYMENT,
                target=sponsor,
                data=Hash(Spec.ENTRY_POINT, left_padding=True),
                pin_gas=False,
            ),
        ],
    ).resolve_frames(fork, payer=sponsor)

    state_test(
        pre=pre,
        tx=tx,
        post={sender: Account(nonce_change=1, balance_change=0)},
    )


@pytest.mark.parametrize(
    "mode",
    [
        pytest.param(Spec.MODE_DEFAULT, id="default_frame"),
        pytest.param(Spec.MODE_SENDER, id="sender_frame"),
    ],
)
@pytest.mark.with_all_create_opcodes
def test_caller_and_origin_in_create_initcode(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    mode: FrameMode,
    create_opcode: Op,
) -> None:
    """
    Test that initcode run by a create opcode in a frame sees the creating
    contract as `CALLER` and the frame's `caller` as `ORIGIN`.
    """
    sender = pre.fund_eoa()
    caller = Frame.caller(mode, sender)
    # The frame's data holds the initcode, so the factory deploys first.
    factory_code = Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE) + Conditional(
        condition=create_op(create_opcode, size=Op.CALLDATASIZE),
        if_true=Op.STOP,
        if_false=Op.REVERT(0, 0),
    )
    factory = pre.deploy_contract(code=factory_code)
    init_code = CallerOriginGuard(caller=factory, origin=caller)

    tx = Transaction(
        sender=sender,
        frames=[
            Frame.verify(),
            Frame(
                mode=mode,
                target=factory,
                data=Bytes(bytes(init_code)),
                code=factory_code,
                pin_gas=False,
            ),
        ],
    ).resolve_frames(fork)

    state_test(pre=pre, tx=tx, post={sender: Account(nonce_change=1)})
