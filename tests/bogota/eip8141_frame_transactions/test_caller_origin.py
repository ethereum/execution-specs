"""
`CALLER` and `ORIGIN` tests for
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

Every frame runs as a top-level call from the frame's `caller`
(§Behavior, "Set frame's `caller`"): the transaction sender in a
`SENDER` frame, and `ENTRY_POINT` (`address(0xaa)`) in a `DEFAULT` or
`VERIFY` frame. `CALLER` at the frame's top level is therefore that
caller, and below it follows the usual call rules. `ORIGIN` does not:
it "returns frame's `caller` throughout all call depths", so it changes
from frame to frame within one transaction.
"""

from typing import Dict

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytecode,
    Bytes,
    Conditional,
    Fork,
    Op,
    Opcode,
    StateTestFiller,
)

from .helpers import (
    APPROVE_ALL,
    CURRENT_FRAME_INDEX,
    FrameCase,
    FrameTransaction,
    approving_contract_sender,
    created_address,
    frame_data_copy,
    frame_data_create,
    sender_frame,
    verify_frame,
)
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")

SLOT_CALLER = 0x00
"""Storage slot the recorder writes `CALLER` into."""

SLOT_ORIGIN = 0x01
"""Storage slot the recorder writes `ORIGIN` into."""

FRAME_GAS = 200_000
"""Execution gas budget of the frames that call a reporter."""

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


def caller_and_origin(caller: Address, origin: Address) -> Dict[int, Address]:
    """Return the storage of a recorder that saw `caller` and `origin`."""
    return {SLOT_CALLER: caller, SLOT_ORIGIN: origin}


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
    Record `CALLER` and `ORIGIN` at a frame's top level: both are the
    frame's `caller`, the sender in a `SENDER` frame and `ENTRY_POINT`
    in a `DEFAULT` frame, whether the sender is an EOA or a contract.

    EIP-8141 §Behavior: "If mode is `SENDER`: [...] Set `caller` to
    `tx.sender`. If mode is `DEFAULT` or `VERIFY`: Set `caller` to
    `ENTRY_POINT`. The `ORIGIN` opcode returns frame's `caller`
    throughout all call depths." §Constants: `ENTRY_POINT` is
    `address(0xaa)`. §Transaction origination: "Specifically, `SENDER`
    frames originate calls where `tx.sender` is a contract account."
    """
    if contract_sender:
        sender: Address = approving_contract_sender(pre)
        verify = verify_frame(code=APPROVE_ALL)
    else:
        sender = pre.fund_eoa()
        verify = verify_frame()
    recorder = pre.deploy_contract(code=RECORDER_CODE)
    caller = frame_caller(mode, sender)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        nonce=1 if contract_sender else 0,
        frames=[
            verify,
            FrameCase(mode=mode, target=recorder, code=RECORDER_CODE),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce_change=1),
            recorder: Account(storage=caller_and_origin(caller, caller)),
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
    A frame's target calls a reporter that returns its `CALLER` and
    `ORIGIN`, and records both: `ORIGIN` is still the frame's `caller`,
    while `CALLER` is the frame's target, except under `DELEGATECALL`,
    which keeps the frame's `caller`.

    EIP-8141 §Behavior: "The `ORIGIN` opcode returns frame's `caller`
    throughout all call depths." `CALLER` below the top level follows
    the ordinary call rules, which EIP-8141 leaves unchanged.
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

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            FrameCase(
                mode=mode,
                target=target,
                gas_limit=FRAME_GAS,
                code=target_code,
                pin_gas=False,
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            target: Account(storage=caller_and_origin(nested_caller, caller)),
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
    A contract sender's `VERIFY` frame approves only if it sees the
    expected `CALLER` and `ORIGIN`: at the frame's top level both are
    `ENTRY_POINT`; in a reporter it calls, `CALLER` is the sender and
    `ORIGIN` is still `ENTRY_POINT`.

    EIP-8141 §Behavior: "If mode is `DEFAULT` or `VERIFY`: Set `caller`
    to `ENTRY_POINT`. The `ORIGIN` opcode returns frame's `caller`
    throughout all call depths." A `VERIFY` frame cannot write
    storage, so it checks the values in place: any other value reverts
    the frame, which makes the transaction invalid.
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
    sender_code = observe + Conditional(
        condition=Op.AND(
            Op.EQ(observed_caller, expected_caller),
            Op.EQ(observed_origin, Spec.ENTRY_POINT),
        ),
        if_true=APPROVE_ALL,
        if_false=Op.REVERT(0, 0),
    )
    sender = pre.deploy_contract(code=sender_code, balance=10**18)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        nonce=1,
        frames=[verify_frame(gas_limit=FRAME_GAS, pin_gas=False)],
    )

    state_test(pre=pre, tx=tx, post={sender: Account(nonce=2)})


def test_origin_follows_each_frame(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Run one recorder in alternating `SENDER` and `DEFAULT` frames of
    one transaction, each frame recording into its own slots: every
    frame sees its own `caller` as `CALLER` and `ORIGIN`, so `ORIGIN`
    changes from frame to frame.

    EIP-8141 §Behavior sets the `caller` per frame ("Set frame's
    `caller`" for each frame executed), and "The `ORIGIN` opcode
    returns frame's `caller` throughout all call depths." §Backwards
    Compatibility: "The `ORIGIN` opcode behavior changes for frame
    transactions, returning the frame's caller rather than the
    traditional transaction origin."
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

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            *(
                # Each frame after the first finds the recorder warm.
                FrameCase(
                    mode=mode, target=recorder, code=code, warm=index > 0
                )
                for index, mode in enumerate(modes)
            ),
        ],
    )

    storage: Dict[int, Address] = {}
    for index, mode in enumerate(modes, start=1):
        caller = frame_caller(mode, sender)
        storage[2 * index] = caller
        storage[2 * index + 1] = caller

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            recorder: Account(storage=storage),
        },
    )


def test_origin_returns_to_entry_point_in_verify_frame(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Run a `VERIFY` frame right after a `SENDER` frame: the sponsor it
    targets approves payment only if it sees `ENTRY_POINT` as both
    `CALLER` and `ORIGIN`, not the sender the previous frame ran as.

    EIP-8141 §Behavior: "If mode is `DEFAULT` or `VERIFY`: Set
    `caller` to `ENTRY_POINT`. The `ORIGIN` opcode returns frame's
    `caller` throughout all call depths." The `caller` is set for each
    frame, so `ORIGIN` changes from the `SENDER` frame's sender back to
    `ENTRY_POINT`. A `VERIFY` frame cannot write storage, so it checks
    the values in place: any other value reverts the frame, which
    makes the transaction invalid.
    """
    sender = pre.fund_eoa()
    recorder = pre.deploy_contract(code=RECORDER_CODE)
    sponsor_code = Conditional(
        condition=Op.AND(
            Op.EQ(Op.CALLER, Spec.ENTRY_POINT),
            Op.EQ(Op.ORIGIN, Spec.ENTRY_POINT),
        ),
        if_true=Op.APPROVE(0, 0, Spec.APPROVE_PAYMENT),
        if_false=Op.REVERT(0, 0),
    )
    sponsor = pre.deploy_contract(code=sponsor_code, balance=10**18)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        payer=sponsor,
        frames=[
            verify_frame(flags=Spec.APPROVE_EXECUTION),
            sender_frame(target=recorder, code=RECORDER_CODE),
            verify_frame(
                flags=Spec.APPROVE_PAYMENT, target=sponsor, pin_gas=False
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            recorder: Account(storage=caller_and_origin(sender, sender)),
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
    A frame's target creates a contract whose initcode records `CALLER`
    and `ORIGIN`: `CALLER` is the creating contract, and `ORIGIN` is
    still the frame's `caller`.

    EIP-8141 §Behavior: "The `ORIGIN` opcode returns frame's `caller`
    throughout all call depths." Initcode run by a create opcode is one
    call depth below the creating contract, which the create opcode
    makes its `CALLER`.
    """
    sender = pre.fund_eoa()
    create = frame_data_create(create_opcode, RECORDER_CODE)
    factory = pre.deploy_contract(
        code=frame_data_copy(RECORDER_CODE) + Op.POP(create) + Op.STOP
    )
    created = created_address(factory, create_opcode, RECORDER_CODE)
    caller = frame_caller(mode, sender)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            FrameCase(
                mode=mode,
                target=factory,
                data=Bytes(bytes(RECORDER_CODE)),
                gas_limit=FRAME_GAS,
                pin_gas=False,
                # The new account, then the initcode's two writes.
                state_gas_used=create.state_cost(fork)
                + RECORDER_CODE.state_cost(fork),
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            created: Account(storage=caller_and_origin(factory, caller)),
        },
    )
