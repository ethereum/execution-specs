"""
`APPROVE` edge-case tests for
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

Each test isolates one check of §`APPROVE` Behavior, or one consequence
of it, so that a client skipping that check alone fails it:

- who may approve (`ADDRESS == resolved_target`, however the code at
  that address was reached);
- which scopes a frame may approve, in which order, and how often;
- what `APPROVE` returns, what it costs, and that it ends its call;
- when `max_cost` leaves the payer;
- that only the `VERIFY`-mode default code approves for a codeless
  account.

That an exceptional halt discards an approval as a revert does is
pinned by `test_frame_revert_discards_the_approval_it_granted[halts]`
in `test_frame_transactions.py`.

A refused `APPROVE` reverts only its own call frame (§`APPROVE`
Behavior: "revert the current call frame"), so most tests reach it
through a call back into the frame's target and record the call's
result: the recorded value pins the refusal, and the transaction stays
valid through an approval made elsewhere.
"""

from typing import Dict, List

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytecode,
    Bytes,
    CodeGasMeasure,
    Conditional,
    Environment,
    Fork,
    FrameSignature,
    Op,
    Opcode,
    StateTestFiller,
    TransactionException,
)

from .helpers import (
    APPROVE_ALL,
    BASE_FEE,
    CANARY,
    PRIORITY_FEE,
    FrameCase,
    FrameTransaction,
    default_frame,
    fee_budget,
    sponsored_signatures,
    verify_frame,
)
from .signature_helpers import canonical_entry
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")

SLOT_FIRST_CALL = 0x00
"""Storage slot recording the outcome of a target's first self-call."""

SLOT_SECOND_CALL = 0x01
"""Storage slot recording the outcome of a target's second self-call."""

SLOT_RETURN_DATA_SIZE = 0x01
"""Storage slot recording `RETURNDATASIZE` after the approving call."""

SLOT_RETURN_DATA = 0x02
"""Storage slot recording the word the approving call returned."""

SLOT_PAYER_BALANCE = 0x00
"""Storage slot the balance probe records the payer's balance into."""

SLOT_AFTER_APPROVE = 0x01
"""Storage slot only code after a successful `APPROVE` would write."""

FUNDS = 10**18
"""Balance of every approving account: far above any `max_cost` here."""

FRAME_GAS = 400_000
"""Execution gas budget of the frames whose code makes nested calls."""

RETURNED_WORD = 0xBEEF
"""Word an approving call places in memory and returns."""

CALL_SELF = Op.CALL(gas=Op.GAS, address=Op.ADDRESS)
"""Call back into the executing account with no calldata."""

CALL_SELF_ONE_BYTE = Op.CALL(
    gas=Op.GAS, address=Op.ADDRESS, args_offset=0, args_size=1
)
"""Call back into the executing account with one byte of calldata."""

PLACEHOLDER_ENTRY = FrameSignature(
    scheme=Spec.SCHEME_ARBITRARY, signature=Bytes(b"\x01")
)
"""
Signature entry 0 of a contract sender's sponsored transaction: the
payer's default code reads entry 1, so entry 0 only has to exist, and
an `ARBITRARY` entry needs no protocol validation.
"""


def record_call(slot: int, call: Bytecode) -> Bytecode:
    """
    Record a call's result plus one, so a successful call reads 2, a
    failed one 1, and a slot the code never reached 0.
    """
    return Op.SSTORE(slot, Op.ADD(1, call))


@pytest.mark.parametrize(
    "reentry",
    [
        pytest.param(True, id="helper_calls_back_into_target"),
        pytest.param(False, id="helper_approves_itself"),
    ],
)
def test_approve_reached_through_another_contract(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    reentry: bool,
) -> None:
    """
    The sender's frame code calls a helper contract. In
    `helper_calls_back_into_target` the helper calls back into the
    sender, whose code approves: the approval succeeds, since only the
    approving code's `ADDRESS` is checked, not the call chain that
    reached it. In `helper_approves_itself` the helper runs `APPROVE`
    at its own address: the approval is refused, and the sender then
    approves at the frame's top level.

    EIP-8141 §`APPROVE` Behavior: "If `ADDRESS != resolved_target`,
    revert." Nothing else in the behavior refers to the caller.

    Nothing is approved before the helper runs, the frame allows both
    scopes, and both the sender and the helper can afford `max_cost`,
    so in `helper_approves_itself` the `ADDRESS` check is the only one
    that refuses, even for a client that checks the balance of
    `ADDRESS` rather than of the resolved target. Had the helper's
    approval succeeded, the sender's own `APPROVE` would revert the
    frame, discarding both approvals, and the transaction would have no
    payer.
    """
    helper_code = (
        Op.POP(
            Op.CALL(gas=Op.GAS, address=Op.CALLER, args_offset=0, args_size=1)
        )
        + Op.STOP
        if reentry
        else APPROVE_ALL
    )
    helper = pre.deploy_contract(code=helper_code, balance=FUNDS)
    record = record_call(SLOT_FIRST_CALL, Op.CALL(gas=Op.GAS, address=helper))
    # The frame supplies no calldata; the helper's call back supplies
    # one byte.
    sender_code = Conditional(
        condition=Op.CALLDATASIZE,
        if_true=APPROVE_ALL,
        if_false=record + (Op.STOP if reentry else APPROVE_ALL),
    )
    sender = pre.deploy_contract(code=sender_code, balance=FUNDS)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        nonce=1,
        frames=[
            default_frame(
                flags=Spec.APPROVE_EXECUTION_AND_PAYMENT,
                target=sender,
                gas_limit=FRAME_GAS,
                pin_gas=False,
                state_gas_used=record.state_cost(fork),
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(
                nonce=2,
                # 2: the helper's call succeeded; 1: it was refused.
                storage={SLOT_FIRST_CALL: 2 if reentry else 1},
            ),
        },
    )


@pytest.mark.with_all_call_opcodes(
    # `CALL` and `STATICCALL` run the library at its own `ADDRESS`, so
    # its `APPROVE` is refused and the transaction is invalid.
    marks=lambda call_opcode: (
        pytest.mark.exception_test
        if call_opcode in (Op.CALL, Op.STATICCALL)
        else None
    ),
)
def test_approve_in_library_code(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    call_opcode: Opcode,
) -> None:
    """
    A contract sender's `VERIFY` frame runs a library's `APPROVE`
    through `DELEGATECALL` or `CALLCODE`, and the approval succeeds;
    through `CALL` or `STATICCALL`, the library's `APPROVE` is refused
    and the frame reverts.

    EIP-8141 §`APPROVE` Behavior: "If `ADDRESS != resolved_target`,
    revert." §Rationale, `APPROVE` calling convention: "Because
    `DELEGATECALL` preserves `ADDRESS`, code executed via
    `DELEGATECALL` from the resolved target may also execute `APPROVE`
    successfully." `CALLCODE` also runs the library's code at the
    caller's `ADDRESS`; `CALL` and `STATICCALL` run it at the library's
    own. A `VERIFY` frame is already static and `APPROVE` writes past
    that restriction, so `STATICCALL` adds no check of its own.

    The frame reverts unless the library call succeeded, and a failed
    `VERIFY` frame makes the transaction invalid. The library can
    afford `max_cost` too, so under `CALL` and `STATICCALL` the
    `ADDRESS` check is the only one that refuses, even for a client
    that checks the balance of `ADDRESS` rather than of the resolved
    target.
    """
    if call_opcode in (Op.DELEGATECALL, Op.CALLCODE):
        approves = True
    elif call_opcode in (Op.CALL, Op.STATICCALL):
        approves = False
    else:
        raise ValueError(f"unknown call_opcode: {call_opcode!r}")
    library = pre.deploy_contract(code=APPROVE_ALL, balance=FUNDS)
    sender_code = Conditional(
        condition=call_opcode(gas=Op.GAS, address=library),
        if_true=Op.STOP,
        if_false=Op.REVERT(0, 0),
    )
    sender = pre.deploy_contract(code=sender_code, balance=FUNDS)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        nonce=1,
        frames=[verify_frame(gas_limit=FRAME_GAS, pin_gas=False)],
        error=(
            None
            if approves
            else TransactionException.TYPE_6_INVALID_FRAME_EXECUTION
        ),
    )

    state_test(
        pre=pre,
        tx=tx,
        post={sender: Account(nonce=2 if approves else 1)},
    )


@pytest.mark.parametrize(
    "execution_first",
    [
        pytest.param(True, id="execution_then_payment"),
        pytest.param(False, id="payment_then_execution"),
    ],
)
def test_split_approval_order(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    execution_first: bool,
) -> None:
    """
    Approve execution and payment in two separate self-calls of one
    frame. Execution first, both approvals succeed. Payment first, the
    payment approval is refused, the execution approval then succeeds,
    and a later sponsor frame approves payment instead.

    EIP-8141 §`APPROVE` Behavior, `APPROVE_PAYMENT`: "If
    `sender_approved == false`, revert the current call frame."
    `APPROVE_EXECUTION` has no such ordering condition.

    Each self-call passes its scope as one byte of calldata, and the
    frame records both calls' results. In `payment_then_execution`
    nothing else refuses the payment approval: no payer is set, the
    frame allows the scope, and the sender can afford `max_cost`. Had
    it succeeded, the sender would be bound as payer and the sponsor's
    later approval would be refused, invalidating the transaction.
    """
    first, second = (
        (Spec.APPROVE_EXECUTION, Spec.APPROVE_PAYMENT)
        if execution_first
        else (Spec.APPROVE_PAYMENT, Spec.APPROVE_EXECUTION)
    )
    record = (
        Op.MSTORE8(0, first)
        + record_call(SLOT_FIRST_CALL, CALL_SELF_ONE_BYTE)
        + Op.MSTORE8(0, second)
        + record_call(SLOT_SECOND_CALL, CALL_SELF_ONE_BYTE)
    )
    sender_code = Conditional(
        condition=Op.CALLDATASIZE,
        if_true=Op.APPROVE(0, 0, Op.SHR(248, Op.CALLDATALOAD(0))),
        if_false=record + Op.STOP,
    )
    sender = pre.deploy_contract(code=sender_code, balance=FUNDS)
    payer = pre.fund_eoa(amount=FUNDS)

    frames: List[FrameCase] = [
        default_frame(
            flags=Spec.APPROVE_EXECUTION_AND_PAYMENT,
            target=sender,
            gas_limit=FRAME_GAS,
            pin_gas=False,
            state_gas_used=record.state_cost(fork),
        ),
    ]
    if not execution_first:
        frames.append(verify_frame(flags=Spec.APPROVE_PAYMENT, target=payer))

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        nonce=1,
        payer=sender if execution_first else payer,
        frames=frames,
        # Both cases carry the same entries, so only the approval order
        # differs; `execution_then_payment` has no sponsor frame and
        # never reads entry 1.
        signatures=[PLACEHOLDER_ENTRY, canonical_entry(payer)],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(
                nonce=2,
                storage={
                    SLOT_FIRST_CALL: 2 if execution_first else 1,
                    SLOT_SECOND_CALL: 2,
                },
            ),
        },
    )


def test_second_payment_approval_refused(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    After the sender approved payment, a sponsor contract that can
    afford `max_cost` tries to approve payment too: its approval is
    refused, it keeps its balance, and the sender stays the payer.

    EIP-8141 §`APPROVE` Behavior, `APPROVE_PAYMENT`: "If `payer` was
    already set, revert the current call frame." The sponsor's balance
    covers `max_cost` and execution is approved, so the balance and
    ordering checks cannot be what refuses it.
    """
    sender = pre.fund_eoa()
    record = record_call(SLOT_FIRST_CALL, CALL_SELF)
    # The frame supplies calldata, the self-call none.
    sponsor_code = Conditional(
        condition=Op.CALLDATASIZE,
        if_true=record + Op.STOP,
        if_false=Op.APPROVE(0, 0, Spec.APPROVE_PAYMENT),
    )
    sponsor = pre.deploy_contract(code=sponsor_code, balance=FUNDS)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            default_frame(
                flags=Spec.APPROVE_PAYMENT,
                target=sponsor,
                data=Bytes(b"\x01"),
                gas_limit=FRAME_GAS,
                pin_gas=False,
                state_gas_used=record.state_cost(fork),
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            sponsor: Account(
                nonce=1, balance=FUNDS, storage={SLOT_FIRST_CALL: 1}
            ),
        },
    )


@pytest.mark.parametrize(
    "scope",
    [
        pytest.param(Spec.APPROVE_EXECUTION, id="execution_again"),
        pytest.param(
            Spec.APPROVE_EXECUTION_AND_PAYMENT,
            id="execution_and_payment_after_execution",
        ),
    ],
)
def test_execution_approval_refused_once_granted(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    scope: int,
) -> None:
    """
    After a `VERIFY` frame approved execution, a later frame of the
    sender tries to approve execution again, alone or together with
    payment: the approval is refused, and a sponsor approves payment.

    EIP-8141 §`APPROVE` Behavior: for `APPROVE_EXECUTION`, "If
    `sender_approved == true`, revert the current call frame."; for
    `APPROVE_EXECUTION_AND_PAYMENT`, "If `sender_approved` or `payer`
    was already set, revert the current call frame."

    The later frame allows the scope and the sender can afford
    `max_cost`, so only the existing approval refuses it. Had the
    combined approval succeeded, the sender would be the payer, the
    sponsor's approval would be refused, and the transaction would be
    invalid; the sender's nonce advances once, by the sponsor's
    approval.
    """
    record = record_call(SLOT_FIRST_CALL, CALL_SELF_ONE_BYTE)
    # The `VERIFY` frame supplies no calldata, the `DEFAULT` frame two
    # bytes, and its self-call one.
    sender_code = Conditional(
        condition=Op.CALLDATASIZE,
        if_true=Conditional(
            condition=Op.EQ(Op.CALLDATASIZE, 2),
            if_true=record + Op.STOP,
            if_false=Op.APPROVE(0, 0, scope),
        ),
        if_false=Op.APPROVE(0, 0, Spec.APPROVE_EXECUTION),
    )
    sender = pre.deploy_contract(code=sender_code, balance=FUNDS)
    payer = pre.fund_eoa(amount=FUNDS)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        nonce=1,
        payer=payer,
        frames=[
            verify_frame(flags=Spec.APPROVE_EXECUTION, pin_gas=False),
            default_frame(
                flags=scope,
                target=sender,
                data=Bytes(b"\x01\x01"),
                gas_limit=FRAME_GAS,
                pin_gas=False,
                state_gas_used=record.state_cost(fork),
            ),
            verify_frame(flags=Spec.APPROVE_PAYMENT, target=payer),
        ],
        signatures=[PLACEHOLDER_ENTRY, canonical_entry(payer)],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(
                nonce=2, balance=FUNDS, storage={SLOT_FIRST_CALL: 1}
            ),
        },
    )


@pytest.mark.parametrize(
    "granted",
    [
        pytest.param(True, id="granted_returns_memory"),
        pytest.param(False, id="scope_zero_refused"),
    ],
)
def test_approve_return_data(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    granted: bool,
) -> None:
    """
    A self-call writes a word to memory and runs `APPROVE` over it. A
    granted approval returns the word to the caller as return data. An
    approval with scope 0 is refused, and the frame then approves at
    its top level.

    EIP-8141 §`APPROVE` Instruction: "The `offset` and `length`
    operands designate a memory region that becomes the call frame's
    return data, following `RETURN` semantics." §`APPROVE` Behavior:
    "Ensure that `scope` is one of the caller's allowed scopes in
    `frame.flags`, otherwise revert. To check this, evaluate that
    `scope != 0` and [...]".

    The refused case pins only the call's failure and the untouched
    approval context: whether a refused `APPROVE` returns data is not
    specified, so its return data is not read.
    """
    inner = Op.MSTORE(0, RETURNED_WORD) + Op.APPROVE(
        0, 32, Spec.APPROVE_EXECUTION_AND_PAYMENT if granted else 0
    )
    record = record_call(SLOT_FIRST_CALL, CALL_SELF_ONE_BYTE)
    if granted:
        record += (
            Op.SSTORE(SLOT_RETURN_DATA_SIZE, Op.RETURNDATASIZE)
            + Op.RETURNDATACOPY(0, 0, 32)
            + Op.SSTORE(SLOT_RETURN_DATA, Op.MLOAD(0))
        )
    outer = record + (Op.STOP if granted else APPROVE_ALL)
    sender_code = Conditional(
        condition=Op.CALLDATASIZE, if_true=inner, if_false=outer
    )
    sender = pre.deploy_contract(code=sender_code, balance=FUNDS)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        nonce=1,
        frames=[
            default_frame(
                flags=Spec.APPROVE_EXECUTION_AND_PAYMENT,
                target=sender,
                gas_limit=FRAME_GAS,
                pin_gas=False,
                state_gas_used=record.state_cost(fork),
            ),
        ],
    )

    storage: Dict[int, int] = (
        {
            SLOT_FIRST_CALL: 2,
            SLOT_RETURN_DATA_SIZE: 32,
            SLOT_RETURN_DATA: RETURNED_WORD,
        }
        if granted
        else {SLOT_FIRST_CALL: 1}
    )
    state_test(
        pre=pre,
        tx=tx,
        post={sender: Account(nonce=2, storage=storage)},
    )


def test_code_after_approve_does_not_run(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    A frame's code approves, then writes storage: the write never
    runs, and the frame's receipt reports the entry access and the
    `APPROVE` and its operands alone.

    EIP-8141 §`APPROVE` Instruction: "The `APPROVE` instruction exits
    the current EVM call frame successfully". A `DEFAULT` frame is
    used so that the write, if reached, would succeed rather than halt
    on a static restriction.
    """
    sender_code = APPROVE_ALL + Op.SSTORE(SLOT_AFTER_APPROVE, 1) + Op.STOP
    sender = pre.deploy_contract(code=sender_code, balance=FUNDS)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        nonce=1,
        frames=[
            # The sender is warm from the start of the transaction.
            default_frame(
                flags=Spec.APPROVE_EXECUTION_AND_PAYMENT,
                target=sender,
                warm=True,
                code=APPROVE_ALL,
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={sender: Account(nonce=2, storage={})},
    )


@pytest.mark.parametrize(
    "offset,length",
    [
        pytest.param(0, 32, id="one_word"),
        pytest.param(0x100, 0x40, id="offset_region"),
        pytest.param(0, 0x4000, id="large_region"),
    ],
)
@pytest.mark.parametrize(
    "budget_delta",
    [
        pytest.param(0, id="exact"),
        pytest.param(-1, id="one_short", marks=pytest.mark.exception_test),
    ],
)
def test_approve_memory_expansion_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    offset: int,
    length: int,
    budget_delta: int,
) -> None:
    """
    A contract sender's `VERIFY` frame approves with a non-empty
    return-data region, budgeted exactly the entry access, the operand
    pushes and the region's memory expansion, and one gas less.

    EIP-8141 §`APPROVE` Gas: "`APPROVE` charges the memory expansion
    gas for the return-data region `[offset, offset + length)`, with no
    additional execution-gas base cost, matching `RETURN`." At the
    exact budget the approval succeeds and the receipt reports the
    whole budget; one gas short the frame halts out of gas, and a
    failed `VERIFY` frame makes the transaction invalid.
    """
    sender_code = Op.APPROVE(
        offset,
        length,
        Spec.APPROVE_EXECUTION_AND_PAYMENT,
        new_memory_size=offset + length,
    )
    sender = pre.deploy_contract(code=sender_code, balance=FUNDS)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        nonce=1,
        frames=[verify_frame(code=sender_code, gas_limit_delta=budget_delta)],
        error=(
            TransactionException.TYPE_6_INVALID_FRAME_EXECUTION
            if budget_delta
            else None
        ),
    )

    state_test(
        pre=pre,
        tx=tx,
        post={sender: Account(nonce=1 if budget_delta else 2)},
    )


@pytest.mark.parametrize(
    "mode,approves",
    [
        pytest.param(Spec.MODE_VERIFY, True, id="verify_frame"),
        pytest.param(
            Spec.MODE_DEFAULT,
            False,
            id="default_frame",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(
            Spec.MODE_SENDER,
            False,
            id="sender_frame",
            marks=pytest.mark.exception_test,
        ),
    ],
)
def test_default_code_approves_only_in_verify_frame(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    mode: int,
    approves: bool,
) -> None:
    """
    A codeless sponsor is the target of a frame flagged to approve
    payment, with its valid signature entry at index 1. In a `VERIFY`
    frame the default code approves payment; in a `DEFAULT` or
    `SENDER` frame it returns like empty code, so no frame sets a payer
    and the transaction is invalid.

    EIP-8141 §Default code: "If `mode` is `VERIFY`: [...] Call
    `APPROVE(allowed_scope)`." and "If `mode` is `SENDER` or
    `DEFAULT`: Return successfully as if calling empty code."
    §Behavior: "After executing all frames, verify that `payer` has
    been set [...]. If it is not, the whole transaction is invalid."

    The `verify_frame` case is the control: the same flags, target and
    signature entries bind the sponsor as payer.
    """
    sender = pre.fund_eoa()
    payer = pre.fund_eoa(amount=FUNDS)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        payer=payer,
        frames=[
            verify_frame(flags=Spec.APPROVE_EXECUTION),
            FrameCase(mode=mode, flags=Spec.APPROVE_PAYMENT, target=payer),
        ],
        signatures=sponsored_signatures(sender, payer),
        error=(
            None
            if approves
            else TransactionException.TYPE_6_INVALID_FRAME_EXECUTION
        ),
    )

    state_test(
        pre=pre,
        tx=tx,
        post={sender: Account(nonce=1 if approves else 0)},
    )


def test_max_cost_collected_at_payment_approval(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    A frame after a sponsor's payment approval reads the sponsor's
    balance: `max_cost` has already left it, before any settlement.

    EIP-8141 §`APPROVE` Behavior, `APPROVE_PAYMENT`: "Increment the
    sender's nonce, set `payer = resolved_target`, and collect the
    transaction's `max_cost` from `payer`." §Fee budget defines
    `max_cost = required_max_fee + max_priority_fee`, with
    `required_max_fee = max_gas * base_fee_per_gas` and
    `max_priority_fee = min(tx.fees.max_priority_fee_per_gas * max_gas,
    tx.fees.max_fee - required_max_fee)`.

    The default `max_fee` leaves room for the full tip, so `max_cost`
    is `max_gas` priced at the base fee plus the tip.
    """
    sender = pre.fund_eoa()
    payer = pre.fund_eoa(amount=FUNDS)
    probe_code = Op.SSTORE(SLOT_PAYER_BALANCE, Op.BALANCE(payer)) + Op.STOP
    probe = pre.deploy_contract(code=probe_code)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        payer=payer,
        max_priority_fee_per_gas=PRIORITY_FEE,
        frames=[
            verify_frame(flags=Spec.APPROVE_EXECUTION),
            verify_frame(flags=Spec.APPROVE_PAYMENT, target=payer),
            default_frame(
                target=probe,
                pin_gas=False,
                state_gas_used=probe_code.state_cost(fork),
            ),
        ],
        signatures=sponsored_signatures(sender, payer),
    )
    assert tx.frames is not None and tx.signatures is not None
    assert tx.max_fee is not None
    max_cost = fee_budget(
        fork,
        sender,
        tx.frames,
        tx.signatures,
        max_priority_fee_per_gas=PRIORITY_FEE,
        max_fee=int(tx.max_fee),
    ).max_cost

    state_test(
        env=Environment(base_fee_per_gas=BASE_FEE),
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            probe: Account(storage={SLOT_PAYER_BALANCE: FUNDS - max_cost}),
        },
    )


INNER_CALL_GAS = 50_000
"""Execution gas a sponsor forwards to its approving self-call."""

SLOT_CALL_GAS = 0x00
"""Storage slot recording the gas the approving self-call consumed."""

SLOT_SPONSOR_BALANCE = 0x00
"""Storage slot the balance probe records the sponsor's balance into."""


@pytest.mark.parametrize(
    "budget_delta",
    [
        pytest.param(0, id="exact"),
        pytest.param(-1, id="one_short"),
    ],
)
def test_sender_creation_shortfall_halts_payment_approval(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    budget_delta: int,
) -> None:
    """
    The sender does not exist yet. A sponsor contract approves payment
    from a self-call, with a state budget of exactly the new account's
    state gas for the sender, or one gas less.

    EIP-8141 §`APPROVE` Behavior, `APPROVE_PAYMENT`: "Immediately
    before incrementing the sender's nonce, if `tx.sender` does not
    exist [...], charge" the new account's state gas "from the current
    frame's `state_gas_left`. If the pool cannot cover the charge, halt
    the current call frame exceptionally without applying any approval
    effects."

    The sponsor measures its self-call and records the gas over a
    canary, a write that creates no state, so the sender's creation is
    the only state charge in the sponsor's frame.

    - `exact`: the self-call approves. It returns having spent only the
      instructions up to `APPROVE`, the sponsor's frame reports the
      sender's creation as its state gas, the receipt names the sponsor
      as payer, and a later frame reads the sponsor's balance less
      `max_cost`.
    - `one_short`: the self-call halts, consuming all the gas it was
      given, which a refusal (a revert) would return, and approves
      nothing. The sponsor keeps its balance and a second sponsor's
      approval succeeds, which it could not if the first had set the
      payer.
    """
    # No opcode makes this charge: `APPROVE` creates the sender, priced
    # as `NEW_ACCOUNT` (the state gas of one new account).
    new_account_gas = fork.gas_costs().NEW_ACCOUNT
    sender = pre.fund_eoa(amount=0)
    call = Op.CALL(gas=INNER_CALL_GAS, address=Op.ADDRESS, address_warm=True)
    measure = CodeGasMeasure(
        code=call, extra_stack_items=1, sstore_key=SLOT_CALL_GAS
    )
    approval = Op.APPROVE(0, 0, Spec.APPROVE_PAYMENT)
    # The frame supplies calldata, the self-call none.
    if_true = measure + Op.STOP
    sponsor_code = Conditional(
        condition=Op.CALLDATASIZE, if_true=if_true, if_false=approval
    )
    # The instructions the self-call runs: the untaken jump, then
    # `APPROVE`, which ends the call. `Conditional` places the branch
    # it skips to after the approval and the jump over the true branch.
    skip_true = Op.JUMP(Op.ADD(Op.PC, len(Op.JUMPDEST + if_true) + 3))
    approval_path = (
        Op.JUMPI(Op.ADD(Op.PC, len(approval + skip_true) + 3), Op.CALLDATASIZE)
        + approval
    )
    assert bytes(sponsor_code).startswith(bytes(approval_path))
    sponsor = pre.deploy_contract(
        code=sponsor_code, balance=FUNDS, storage={SLOT_CALL_GAS: CANARY}
    )
    if budget_delta == 0:
        approves = True
    elif budget_delta == -1:
        approves = False
    else:
        raise ValueError(f"unknown budget_delta: {budget_delta!r}")

    sponsor_frame = default_frame(
        flags=Spec.APPROVE_PAYMENT,
        target=sponsor,
        data=Bytes(b"\x01"),
        gas_limit=FRAME_GAS,
        state_gas_limit=new_account_gas + budget_delta,
        pin_gas=False,
        state_gas_used=new_account_gas if approves else 0,
    )
    post: Dict[Address, Account | None] = {sender: Account(nonce=1)}
    if approves:
        probe_code = (
            Op.SSTORE(SLOT_SPONSOR_BALANCE, Op.BALANCE(sponsor)) + Op.STOP
        )
        probe = pre.deploy_contract(code=probe_code)
        tx = FrameTransaction.build(
            fork=fork,
            sender=sender,
            payer=sponsor,
            max_priority_fee_per_gas=PRIORITY_FEE,
            frames=[
                verify_frame(flags=Spec.APPROVE_EXECUTION),
                sponsor_frame,
                default_frame(
                    target=probe,
                    pin_gas=False,
                    state_gas_used=probe_code.state_cost(fork),
                ),
            ],
            signatures=[canonical_entry(sender)],
        )
        assert tx.frames is not None and tx.signatures is not None
        assert tx.max_fee is not None
        max_cost = fee_budget(
            fork,
            sender,
            tx.frames,
            tx.signatures,
            max_priority_fee_per_gas=PRIORITY_FEE,
            max_fee=int(tx.max_fee),
        ).max_cost
        post[sponsor] = Account(
            nonce=1,
            storage={
                SLOT_CALL_GAS: call.gas_cost(fork)
                + approval_path.execution_cost(fork)
            },
        )
        post[probe] = Account(storage={SLOT_SPONSOR_BALANCE: FUNDS - max_cost})
    else:
        second_payer = pre.fund_eoa(amount=FUNDS)
        tx = FrameTransaction.build(
            fork=fork,
            sender=sender,
            payer=second_payer,
            frames=[
                verify_frame(flags=Spec.APPROVE_EXECUTION),
                sponsor_frame,
                verify_frame(
                    flags=Spec.APPROVE_PAYMENT,
                    target=second_payer,
                    state_gas_used=new_account_gas,
                ),
            ],
            signatures=sponsored_signatures(sender, second_payer),
        )
        post[sponsor] = Account(
            nonce=1,
            balance=FUNDS,
            storage={SLOT_CALL_GAS: call.gas_cost(fork) + INNER_CALL_GAS},
        )

    state_test(
        env=Environment(base_fee_per_gas=BASE_FEE), pre=pre, tx=tx, post=post
    )
