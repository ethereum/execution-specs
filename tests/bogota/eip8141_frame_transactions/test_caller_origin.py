"""
`CALLER` and `ORIGIN` tests for
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

Every frame runs as a top-level call from the frame's `caller`: the
transaction sender in a `SENDER` frame, and `ENTRY_POINT` in a `DEFAULT`
or `VERIFY` frame. `CALLER` at the frame's top level is that caller, and
below it follows the usual call rules. `ORIGIN` "returns frame's
`caller` throughout all call depths" (§Behavior), so it changes from
frame to frame within one transaction.
"""

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
    Op,
    Opcode,
    StateTestFiller,
    Transaction,
)

from .helpers import (
    APPROVE_ALL,
    CURRENT_FRAME_INDEX,
    created_address,
    frame_data_create_code,
)
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")

SLOT_CALLER = 0x00
"""Storage slot the recorder writes `CALLER` into."""

SLOT_ORIGIN = 0x01
"""Storage slot the recorder writes `ORIGIN` into."""

RECORDER_CODE = (
    Op.SSTORE(SLOT_CALLER, Op.CALLER)
    + Op.SSTORE(SLOT_ORIGIN, Op.ORIGIN)
    + Op.STOP
)
"""Record the `CALLER` and `ORIGIN` the code runs with."""

REPORTER_CODE = (
    Op.MSTORE(0, Op.CALLER) + Op.MSTORE(32, Op.ORIGIN) + Op.RETURN(0, 64)
)
"""Return the `CALLER` and `ORIGIN` the code runs with, as two words."""

MODES = [
    pytest.param(Spec.MODE_DEFAULT, id="default_frame"),
    pytest.param(Spec.MODE_SENDER, id="sender_frame"),
]
"""Frame modes whose code can record to storage."""


def frame_caller(mode: int, sender: Address) -> Address:
    """
    Return the frame's `caller`: the sender in a `SENDER` frame, the
    entry point in a `DEFAULT` or `VERIFY` frame.
    """
    if mode == Spec.MODE_SENDER:
        return sender
    if mode in (Spec.MODE_DEFAULT, Spec.MODE_VERIFY):
        return Spec.ENTRY_POINT
    raise ValueError(f"unknown mode: {mode!r}")


@pytest.mark.parametrize("mode", MODES)
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
    mode: int,
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
    recorder = pre.deploy_contract(code=RECORDER_CODE)
    caller = frame_caller(mode, sender)

    tx = Transaction(
        sender=sender,
        nonce=1 if contract_sender else 0,
        frames=[
            verify,
            Frame(mode=mode, target=recorder, code=RECORDER_CODE),
        ],
    ).resolve_frames(fork)

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce_change=1),
            recorder: Account(
                storage={SLOT_CALLER: caller, SLOT_ORIGIN: caller}
            ),
        },
    )


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.with_all_call_opcodes
def test_caller_and_origin_in_nested_call(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    mode: int,
    call_opcode: Opcode,
) -> None:
    """
    Test that `ORIGIN` in a call below the frame's top level is still the
    frame's `caller`, while `CALLER` follows the usual call rules.
    """
    sender = pre.fund_eoa()
    reporter = pre.deploy_contract(code=REPORTER_CODE)
    target_code = (
        Op.POP(call_opcode(gas=Op.GAS, address=reporter, ret_size=64))
        + Op.SSTORE(SLOT_CALLER, Op.MLOAD(0))
        + Op.SSTORE(SLOT_ORIGIN, Op.MLOAD(32))
        + Op.STOP
    )
    target = pre.deploy_contract(code=target_code)
    caller = frame_caller(mode, sender)
    if call_opcode == Op.DELEGATECALL:
        nested_caller = caller
    elif call_opcode in (Op.CALL, Op.CALLCODE, Op.STATICCALL):
        nested_caller = target
    else:
        raise ValueError(f"unknown call_opcode: {call_opcode!r}")

    tx = Transaction(
        sender=sender,
        frames=[
            Frame.verify(),
            Frame(
                mode=mode,
                target=target,
                code=target_code,
                pin_gas=False,
            ),
        ],
    ).resolve_frames(fork)

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce_change=1),
            target: Account(
                storage={SLOT_CALLER: nested_caller, SLOT_ORIGIN: caller}
            ),
        },
    )


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
    expected_caller: Bytecode | Address
    if nested:
        reporter = pre.deploy_contract(code=REPORTER_CODE)
        observe = Op.POP(
            Op.STATICCALL(gas=Op.GAS, address=reporter, ret_size=64)
        )
        observed_caller, observed_origin = Op.MLOAD(0), Op.MLOAD(32)
        # The frame's target, the sender, makes the call.
        expected_caller = Op.ADDRESS
    else:
        observe = Bytecode()
        observed_caller, observed_origin = Op.CALLER, Op.ORIGIN
        expected_caller = Spec.ENTRY_POINT
    # A `VERIFY` frame cannot write storage, so the sender checks the
    # values in place: any other value reverts the frame, which makes
    # the transaction invalid.
    sender_code = observe + Conditional(
        condition=Op.AND(
            Op.EQ(observed_caller, expected_caller),
            Op.EQ(observed_origin, Spec.ENTRY_POINT),
        ),
        if_true=APPROVE_ALL,
        if_false=Op.REVERT(0, 0),
    )
    sender = pre.deploy_contract(code=sender_code, balance=10**18)

    tx = Transaction(
        sender=sender,
        nonce=1,
        frames=[Frame.verify(pin_gas=False)],
    ).resolve_frames(fork)

    state_test(pre=pre, tx=tx, post={sender: Account(nonce_change=1)})


def test_origin_follows_each_frame(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test that `CALLER` and `ORIGIN` change from frame to frame when one
    recorder runs in alternating `SENDER` and `DEFAULT` frames.
    """
    code = (
        Op.SSTORE(Op.MUL(2, CURRENT_FRAME_INDEX), Op.CALLER)
        + Op.SSTORE(Op.ADD(Op.MUL(2, CURRENT_FRAME_INDEX), 1), Op.ORIGIN)
        + Op.STOP
    )
    sender = pre.fund_eoa()
    recorder = pre.deploy_contract(code=code)
    modes = [
        Spec.MODE_SENDER,
        Spec.MODE_DEFAULT,
        Spec.MODE_SENDER,
        Spec.MODE_DEFAULT,
    ]

    tx = Transaction(
        sender=sender,
        frames=[
            Frame.verify(),
            *(
                # Each frame after the first finds the recorder warm.
                Frame(mode=mode, target=recorder, code=code, warm=index > 0)
                for index, mode in enumerate(modes)
            ),
        ],
    ).resolve_frames(fork)

    storage = {}
    for index, mode in enumerate(modes, start=1):
        storage[2 * index] = frame_caller(mode, sender)
        storage[2 * index + 1] = frame_caller(mode, sender)

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce_change=1),
            recorder: Account(storage=storage),
        },
    )


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
    recorder = pre.deploy_contract(code=RECORDER_CODE)
    # The sponsor approves payment only if it sees `ENTRY_POINT`;
    # otherwise its `VERIFY` frame reverts and the transaction is
    # invalid.
    sponsor_code = Conditional(
        condition=Op.AND(
            Op.EQ(Op.CALLER, Spec.ENTRY_POINT),
            Op.EQ(Op.ORIGIN, Spec.ENTRY_POINT),
        ),
        if_true=Op.APPROVE(0, 0, Spec.APPROVE_PAYMENT),
        if_false=Op.REVERT(0, 0),
    )
    sponsor = pre.deploy_contract(code=sponsor_code, balance=10**18)

    tx = Transaction(
        sender=sender,
        frames=[
            Frame.verify(flags=Spec.APPROVE_EXECUTION),
            Frame.sender(target=recorder, code=RECORDER_CODE),
            Frame.verify(
                flags=Spec.APPROVE_PAYMENT, target=sponsor, pin_gas=False
            ),
        ],
    ).resolve_frames(fork, payer=sponsor)

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce_change=1, balance_change=0),
            recorder: Account(
                storage={SLOT_CALLER: sender, SLOT_ORIGIN: sender}
            ),
        },
    )


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.with_all_create_opcodes
def test_caller_and_origin_in_create_initcode(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    mode: int,
    create_opcode: Op,
) -> None:
    """
    Test that initcode run by a create opcode in a frame sees the creating
    contract as `CALLER` and the frame's `caller` as `ORIGIN`.
    """
    sender = pre.fund_eoa()
    factory_code = frame_data_create_code(create_opcode, RECORDER_CODE)
    factory = pre.deploy_contract(code=factory_code)
    created = created_address(factory, create_opcode, RECORDER_CODE)
    caller = frame_caller(mode, sender)

    tx = Transaction(
        sender=sender,
        frames=[
            Frame.verify(),
            Frame(
                mode=mode,
                target=factory,
                data=Bytes(bytes(RECORDER_CODE)),
                pin_gas=False,
                # The new account, then the initcode's two writes.
                state_gas_used=factory_code.state_cost(fork)
                + RECORDER_CODE.state_cost(fork),
            ),
        ],
    ).resolve_frames(fork)

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce_change=1),
            created: Account(
                storage={SLOT_CALLER: factory, SLOT_ORIGIN: caller}
            ),
        },
    )
