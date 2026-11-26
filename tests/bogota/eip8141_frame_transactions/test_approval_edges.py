"""
`APPROVE` edge-case tests for
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

Each test isolates one check of §`APPROVE` Behavior. A refused
`APPROVE` reverts only its own call frame, so most tests reach it
through a self-call and store the call's result plus one: 2 for
success, 1 for a refusal, 0 if the call never ran.
"""

from typing import Dict, List

import pytest
from execution_testing import (
    EOA,
    Account,
    Alloc,
    Bytes,
    Case,
    CodeGasMeasure,
    Conditional,
    Environment,
    Fork,
    Frame,
    FrameSignature,
    GasFee,
    Op,
    Opcode,
    StateTestFiller,
    Switch,
    Transaction,
    TransactionException,
)

from .helpers import (
    APPROVE_ALL,
    BASE_FEE,
    PRIORITY_FEE,
    fee_budget,
)
from .signature_helpers import canonical_entry, signed_digest_entry
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")

FUNDS = 10**18
"""Balance of every approving account: far above any `max_cost` here."""

FRAME_GAS = 400_000
"""Execution gas budget of the frames whose code makes nested calls."""

PLACEHOLDER_ENTRY = FrameSignature(
    scheme=Spec.SCHEME_ARBITRARY, signature=Bytes(b"\x01")
)
"""
Entry 0 of a contract sender's sponsored transaction: only the payer's
entry 1 is read, and an `ARBITRARY` entry needs no validation.
"""


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
    Test that `APPROVE` checks only `ADDRESS`, not the call chain.

    A helper that calls back into the sender lets the sender approve. A
    helper that runs `APPROVE` itself is refused, as every other check
    passes, and the sender then approves at the frame's top level.
    """
    helper_code = (
        Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=Op.CALLER,
                args_offset=0,
                args_size=1,
                # gas accounting
                address_warm=True,
                new_memory_size=1,
            )
        )
        + Op.STOP
        if reentry
        else APPROVE_ALL
    )
    helper = pre.deploy_contract(code=helper_code, balance=FUNDS)
    record = Op.SSTORE(0, Op.ADD(1, Op.CALL(gas=Op.GAS, address=helper)))
    # The frame supplies no calldata; the helper's call back supplies
    # one byte.
    sender_code = Conditional(
        condition=Op.CALLDATASIZE,
        if_true=APPROVE_ALL,
        if_false=record + (Op.STOP if reentry else APPROVE_ALL),
    )
    sender = pre.deploy_contract(code=sender_code, balance=FUNDS)

    invocation = sender_code.branch(condition=False) + helper_code
    if reentry:
        invocation += sender_code.branch(condition=True)

    tx = Transaction(
        sender=sender,
        nonce=1,
        frames=[
            Frame.default(
                flags=Spec.APPROVE_EXECUTION_AND_PAYMENT,
                target=sender,
                # Each nested call forwards all but a 64th of the gas
                # left, so the budget carries both retentions.
                code=invocation,
                gas_limit_delta=invocation.execution_cost(fork) // 32,
                state_gas_used=record.state_cost(fork),
            ),
        ],
    ).resolve_frames(fork)

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(
                nonce=2,
                # 2: the helper's call succeeded; 1: it was refused.
                storage={0: 2 if reentry else 1},
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
    Test that a library's `APPROVE` succeeds through `DELEGATECALL` and
    `CALLCODE`, which keep the caller's `ADDRESS`, and is refused
    through `CALL` and `STATICCALL`, which reverts the `VERIFY` frame.
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

    invocation = sender_code.branch(condition=True) + APPROVE_ALL

    tx = Transaction(
        sender=sender,
        nonce=1,
        frames=[
            Frame.verify(
                # The call forwards all but a 64th of the gas left, so
                # the budget carries the retention.
                code=invocation,
                gas_limit_delta=invocation.execution_cost(fork) // 64,
            )
        ],
        error=(
            None
            if approves
            else TransactionException.TYPE_6_INVALID_FRAME_EXECUTION
        ),
    ).resolve_frames(fork)

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
    Test that payment cannot be approved before execution.

    One frame approves each scope in its own self-call. Execution first,
    both succeed; payment first, the payment approval is refused and a
    later sponsor frame pays instead.
    """
    first, second = (
        (Spec.APPROVE_EXECUTION, Spec.APPROVE_PAYMENT)
        if execution_first
        else (Spec.APPROVE_PAYMENT, Spec.APPROVE_EXECUTION)
    )
    call_self = Op.CALL(
        gas=Op.GAS,
        address=Op.ADDRESS,
        args_offset=0,
        args_size=1,
        # gas accounting
        address_warm=True,
    )
    record = (
        Op.MSTORE8(0, first, new_memory_size=1)
        + Op.SSTORE(0, Op.ADD(1, call_self))
        + Op.MSTORE8(0, second)
        + Op.SSTORE(1, Op.ADD(1, call_self))
    )
    sender_code = Conditional(
        condition=Op.CALLDATASIZE,
        if_true=Op.APPROVE(0, 0, Op.SHR(248, Op.CALLDATALOAD(0))),
        if_false=record + Op.STOP,
    )
    sender = pre.deploy_contract(code=sender_code, balance=FUNDS)
    payer = pre.fund_eoa(amount=FUNDS)

    invocation = (
        sender_code.branch(condition=False)
        + sender_code.branch(condition=True) * 2
    )

    frames: List[Frame] = [
        Frame.default(
            flags=Spec.APPROVE_EXECUTION_AND_PAYMENT,
            target=sender,
            # Each self-call forwards all but a 64th of the gas left, so
            # the budget carries the retention.
            code=invocation,
            gas_limit_delta=invocation.execution_cost(fork) // 64,
            state_gas_used=record.state_cost(fork),
        ),
    ]
    if not execution_first:
        frames.append(Frame.verify(flags=Spec.APPROVE_PAYMENT, target=payer))

    tx = Transaction(
        sender=sender,
        nonce=1,
        frames=frames,
        # Both cases carry the same entries, so only the approval order
        # differs; `execution_then_payment` has no sponsor frame and
        # never reads entry 1.
        signatures=[PLACEHOLDER_ENTRY, canonical_entry(payer)],
    ).resolve_frames(fork, payer=sender if execution_first else payer)

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(
                nonce=2,
                storage={0: 2 if execution_first else 1, 1: 2},
            ),
        },
    )


@pytest.mark.parametrize(
    "sponsor_pays_first",
    [
        pytest.param(False, id="sender_paid_first"),
        pytest.param(True, id="sponsor_paid_first"),
    ],
)
def test_second_payment_approval_refused(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    sponsor_pays_first: bool,
) -> None:
    """
    Test that a sponsor's payment approval is refused once the sender,
    or an earlier sponsor, is the payer, although the sponsor can afford
    `max_cost`.
    """
    sender = pre.fund_eoa()
    record = Op.SSTORE(
        0,
        Op.ADD(1, Op.CALL(gas=Op.GAS, address=Op.ADDRESS, address_warm=True)),
    )
    # The frame supplies calldata, the self-call none.
    sponsor_code = Conditional(
        condition=Op.CALLDATASIZE,
        if_true=record + Op.STOP,
        if_false=Op.APPROVE(0, 0, Spec.APPROVE_PAYMENT),
    )
    sponsor = pre.deploy_contract(code=sponsor_code, balance=FUNDS)
    invocation = sponsor_code.branch(condition=True) + sponsor_code.branch(
        condition=False
    )
    sponsor_frame = Frame.default(
        flags=Spec.APPROVE_PAYMENT,
        target=sponsor,
        data=Bytes(b"\x01"),
        # The self-call forwards all but a 64th of the gas left, so the
        # budget carries the retention.
        code=invocation,
        gas_limit_delta=invocation.execution_cost(fork) // 64,
        state_gas_used=record.state_cost(fork),
    )

    signatures = [canonical_entry(sender)]
    if sponsor_pays_first:
        # A codeless sponsor approves through default code, which reads
        # the entry at index 1.
        first_payer = pre.fund_eoa(amount=FUNDS)
        signatures.append(canonical_entry(first_payer))
        frames = [
            Frame.verify(flags=Spec.APPROVE_EXECUTION),
            Frame.verify(flags=Spec.APPROVE_PAYMENT, target=first_payer),
            sponsor_frame,
        ]
    else:
        first_payer = sender
        frames = [Frame.verify(), sponsor_frame]

    tx = Transaction(
        sender=sender,
        frames=frames,
        signatures=signatures,
    ).resolve_frames(fork, payer=first_payer)

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            sponsor: Account(nonce=1, balance=FUNDS, storage={0: 1}),
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
    Test that execution cannot be approved again, alone or with
    payment, once a `VERIFY` frame approved it; a sponsor then pays.
    """
    call_self = Op.CALL(
        gas=Op.GAS,
        address=Op.ADDRESS,
        # gas accounting
        args_offset=0,
        args_size=1,
        address_warm=True,
        new_memory_size=1,
    )
    record = Op.SSTORE(0, Op.ADD(1, call_self))
    # The `VERIFY` frame supplies no calldata, the `DEFAULT` frame two
    # bytes, and its self-call one.
    sender_code = Switch(
        cases=[
            Case(condition=Op.EQ(Op.CALLDATASIZE, 2), action=record + Op.STOP),
            Case(condition=Op.CALLDATASIZE, action=Op.APPROVE(0, 0, scope)),
        ],
        default_action=Op.APPROVE(0, 0, Spec.APPROVE_EXECUTION),
    )
    sender = pre.deploy_contract(code=sender_code, balance=FUNDS)
    payer = pre.fund_eoa(amount=FUNDS)

    invocation = sender_code.branch(case=0) + sender_code.branch(case=1)

    tx = Transaction(
        sender=sender,
        nonce=1,
        frames=[
            Frame.verify(
                flags=Spec.APPROVE_EXECUTION,
                code=sender_code.branch(case=None),
            ),
            Frame.default(
                flags=scope,
                target=sender,
                data=Bytes(b"\x01\x01"),
                # The self-call forwards all but a 64th of the gas left,
                # so the budget carries the retention.
                code=invocation,
                gas_limit_delta=invocation.execution_cost(fork) // 64,
                state_gas_used=record.state_cost(fork),
            ),
            Frame.verify(flags=Spec.APPROVE_PAYMENT, target=payer),
        ],
        signatures=[PLACEHOLDER_ENTRY, canonical_entry(payer)],
    ).resolve_frames(fork, payer=payer)

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=2, balance=FUNDS, storage={0: 1}),
        },
    )


@pytest.mark.parametrize(
    "allowed,scope",
    [
        pytest.param(
            Spec.APPROVE_NONE,
            Spec.APPROVE_EXECUTION,
            id="execution_in_unflagged_frame",
        ),
        pytest.param(
            Spec.APPROVE_NONE,
            Spec.APPROVE_PAYMENT,
            id="payment_in_unflagged_frame",
        ),
        pytest.param(
            Spec.APPROVE_PAYMENT,
            Spec.APPROVE_EXECUTION,
            id="execution_in_payment_frame",
        ),
        pytest.param(
            Spec.APPROVE_EXECUTION,
            Spec.APPROVE_PAYMENT,
            id="payment_in_execution_frame",
        ),
        pytest.param(
            Spec.APPROVE_EXECUTION,
            Spec.APPROVE_EXECUTION_AND_PAYMENT,
            id="both_in_execution_frame",
        ),
        pytest.param(
            Spec.APPROVE_PAYMENT,
            Spec.APPROVE_EXECUTION_AND_PAYMENT,
            id="both_in_payment_frame",
        ),
    ],
)
def test_scope_beyond_frame_flags_refused(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    allowed: int,
    scope: int,
) -> None:
    """
    Test that a self-call asking for a scope outside the frame's flags
    is refused, with every other check passing, and later frames
    approve instead.
    """
    if scope == Spec.APPROVE_PAYMENT:
        # Approved by the first frame, so the ordering check passes.
        execution_first = True
        top_level_scope = Spec.APPROVE_EXECUTION
    elif scope in (
        Spec.APPROVE_EXECUTION,
        Spec.APPROVE_EXECUTION_AND_PAYMENT,
    ):
        execution_first = False
        top_level_scope = Spec.APPROVE_EXECUTION_AND_PAYMENT
    else:
        raise ValueError(f"unknown scope: {scope!r}")
    assert scope & ~allowed, "the scope must exceed the frame's flags"
    call_self = Op.CALL(
        gas=Op.GAS,
        address=Op.ADDRESS,
        args_offset=0,
        args_size=1,
        # gas accounting
        address_warm=True,
        new_memory_size=1,
    )
    record = Op.SSTORE(0, Op.ADD(1, call_self))
    # The `VERIFY` frames supply no calldata, the `DEFAULT` frame two
    # bytes, and its self-call one.
    sender_code = Switch(
        cases=[
            Case(condition=Op.EQ(Op.CALLDATASIZE, 2), action=record + Op.STOP),
            Case(condition=Op.CALLDATASIZE, action=Op.APPROVE(0, 0, scope)),
        ],
        default_action=Op.APPROVE(0, 0, top_level_scope),
    )
    sender = pre.deploy_contract(code=sender_code, balance=FUNDS)
    payer = pre.fund_eoa(amount=FUNDS)

    invocation = sender_code.branch(case=0) + sender_code.branch(case=1)
    verify_path = sender_code.branch(case=None)

    probe = Frame.default(
        flags=allowed,
        target=sender,
        data=Bytes(b"\x01\x01"),
        # The self-call forwards all but a 64th of the gas left, so the
        # budget carries the retention.
        code=invocation,
        gas_limit_delta=invocation.execution_cost(fork) // 64,
        state_gas_used=record.state_cost(fork),
    )
    frames: List[Frame]
    if execution_first:
        frames = [
            Frame.verify(flags=Spec.APPROVE_EXECUTION, code=verify_path),
            probe,
            Frame.verify(flags=Spec.APPROVE_PAYMENT, target=payer),
        ]
    else:
        frames = [probe, Frame.verify(code=verify_path)]

    tx = Transaction(
        sender=sender,
        nonce=1,
        frames=frames,
        signatures=[PLACEHOLDER_ENTRY, canonical_entry(payer)],
    ).resolve_frames(fork, payer=payer if execution_first else sender)

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=2, storage={0: 1}),
        },
    )


@pytest.mark.parametrize(
    "scopes,refused",
    [
        pytest.param(
            [Spec.APPROVE_EXECUTION, Spec.APPROVE_PAYMENT],
            False,
            id="execution_then_payment",
        ),
        # §APPROVE Behavior, `APPROVE_PAYMENT`: "If `sender_approved ==
        # false`, revert the current call frame."
        pytest.param(
            [Spec.APPROVE_PAYMENT, Spec.APPROVE_EXECUTION],
            True,
            id="payment_before_execution",
            marks=pytest.mark.exception_test,
        ),
        # §APPROVE Behavior, `APPROVE_PAYMENT`: "If `payer` was already
        # set, revert the current call frame." The second payer can
        # afford `max_cost`, so only the first approval refuses it.
        pytest.param(
            [Spec.APPROVE_EXECUTION_AND_PAYMENT, Spec.APPROVE_PAYMENT],
            True,
            id="second_payment_approval",
            marks=pytest.mark.exception_test,
        ),
        # §APPROVE Behavior, `APPROVE_EXECUTION`: "If `sender_approved ==
        # true`, revert the current call frame."
        pytest.param(
            [
                Spec.APPROVE_EXECUTION,
                Spec.APPROVE_EXECUTION,
                Spec.APPROVE_PAYMENT,
            ],
            True,
            id="second_execution_approval",
            marks=pytest.mark.exception_test,
        ),
        # §APPROVE Behavior, `APPROVE_EXECUTION_AND_PAYMENT`: "If
        # `sender_approved` or `payer` was already set, revert the
        # current call frame."
        pytest.param(
            [Spec.APPROVE_EXECUTION, Spec.APPROVE_EXECUTION_AND_PAYMENT],
            True,
            id="execution_and_payment_after_execution",
            marks=pytest.mark.exception_test,
        ),
    ],
)
def test_default_code_approval_refusals(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    scopes: List[int],
    refused: bool,
) -> None:
    """
    Test that default code `APPROVE` is subject to the ordering checks:
    a refused one reverts its `VERIFY` frame and invalidates the
    transaction. Payment-only frames target the payer, the others the
    sender.
    """
    sender = pre.fund_eoa()
    payer = pre.fund_eoa(amount=FUNDS)
    frames = [
        Frame.verify(flags=scope, target=payer)
        if scope == Spec.APPROVE_PAYMENT
        else Frame.verify(flags=scope)
        for scope in scopes
    ]
    signatures = [canonical_entry(sender)]
    if Spec.APPROVE_PAYMENT in scopes:
        # The payer's default code reads the entry at index 1.
        signatures.append(canonical_entry(payer))
    tx = Transaction(
        sender=sender,
        frames=frames,
        signatures=signatures,
        error=(
            TransactionException.TYPE_6_INVALID_FRAME_EXECUTION
            if refused
            else None
        ),
    ).resolve_frames(fork, payer=payer)

    post = {
        sender: Account(nonce=0 if refused else 1),
        payer: Account(
            nonce=0,
            balance_change=(
                0
                if refused
                else -GasFee(
                    tx, gas=tx.frame_settlement(fork).payer_gas_used()
                )
            ),
        ),
    }
    state_test(pre=pre, tx=tx, post=post)


@pytest.mark.exception_test
@pytest.mark.parametrize(
    "scope",
    [
        pytest.param(Spec.APPROVE_EXECUTION, id="execution"),
        pytest.param(Spec.APPROVE_PAYMENT, id="payment"),
        pytest.param(
            Spec.APPROVE_EXECUTION_AND_PAYMENT, id="execution_and_payment"
        ),
    ],
)
def test_default_code_refuses_explicit_digest_entry(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    scope: int,
) -> None:
    """
    Test that default code refuses an authorizing entry signed over an
    explicit digest rather than the canonical signature hash. The entry
    is a valid secp256k1 signature from the frame's target, so only its
    `msg` sets it apart from an authorizing one.
    """
    sender = pre.fund_eoa(amount=FUNDS)
    payer = pre.fund_eoa(amount=FUNDS)

    def digest_entry(account: EOA) -> FrameSignature:
        """Return an entry from `account` over an explicit digest."""
        assert account.key is not None
        return signed_digest_entry(account.key, signer=Bytes(account))

    sponsored = [
        Frame.verify(flags=Spec.APPROVE_EXECUTION),
        Frame.verify(flags=Spec.APPROVE_PAYMENT, target=payer),
    ]
    if scope == Spec.APPROVE_EXECUTION:
        # The sender's default code reads the entry at index 0.
        frames = sponsored
        signatures = [digest_entry(sender), canonical_entry(payer)]
    elif scope == Spec.APPROVE_PAYMENT:
        # The payer's default code reads the entry at index 1.
        frames = sponsored
        signatures = [canonical_entry(sender), digest_entry(payer)]
    elif scope == Spec.APPROVE_EXECUTION_AND_PAYMENT:
        frames = [Frame.verify()]
        signatures = [digest_entry(sender)]
    else:
        raise ValueError(f"unknown scope: {scope}")

    tx = Transaction(
        sender=sender,
        frames=frames,
        signatures=signatures,
        error=TransactionException.TYPE_6_INVALID_FRAME_EXECUTION,
    ).resolve_frames(fork, payer=payer if frames is sponsored else sender)

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=0, balance=FUNDS),
            payer: Account(nonce=0, balance=FUNDS),
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
    Test that a granted `APPROVE` returns its memory region to the
    caller as return data, and that scope 0 is refused. A refused
    call's return data is not read: the EIP leaves it unspecified.
    """
    inner = Op.MSTORE(0, 0xBEEF, new_memory_size=32) + Op.APPROVE(
        0,
        32,
        Spec.APPROVE_EXECUTION_AND_PAYMENT if granted else Spec.APPROVE_NONE,
    )
    call_self = Op.CALL(
        gas=Op.GAS,
        address=Op.ADDRESS,
        args_offset=0,
        args_size=1,
        # gas accounting
        address_warm=True,
        new_memory_size=1,
    )
    record = Op.SSTORE(0, Op.ADD(1, call_self))
    if granted:
        # Slot 1 records the return data size, slot 2 the returned word.
        record += (
            Op.SSTORE(1, Op.RETURNDATASIZE)
            + Op.RETURNDATACOPY(0, 0, 32, data_size=32)
            + Op.SSTORE(2, Op.MLOAD(0))
        )
    outer = record + (Op.STOP if granted else APPROVE_ALL)
    sender_code = Conditional(
        condition=Op.CALLDATASIZE, if_true=inner, if_false=outer
    )
    sender = pre.deploy_contract(code=sender_code, balance=FUNDS)

    invocation = sender_code.branch(condition=False) + sender_code.branch(
        condition=True
    )

    tx = Transaction(
        sender=sender,
        nonce=1,
        frames=[
            Frame.default(
                flags=Spec.APPROVE_EXECUTION_AND_PAYMENT,
                target=sender,
                # The self-call forwards all but a 64th of the gas left,
                # so the budget carries the retention.
                code=invocation,
                gas_limit_delta=invocation.execution_cost(fork) // 64,
                state_gas_used=record.state_cost(fork),
            ),
        ],
    ).resolve_frames(fork)

    storage: Dict[int, int] = {0: 2, 1: 32, 2: 0xBEEF} if granted else {0: 1}
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
    Test that `APPROVE` ends its call frame: the storage write after it
    never runs. A `DEFAULT` frame is used so the write would otherwise
    succeed.
    """
    # Slot 1 would only be written if code after `APPROVE` ran.
    sender_code = APPROVE_ALL + Op.SSTORE(1, 1) + Op.STOP
    sender = pre.deploy_contract(code=sender_code, balance=FUNDS)

    tx = Transaction(
        sender=sender,
        nonce=1,
        frames=[
            # The sender is warm from the start of the transaction.
            Frame.default(
                flags=Spec.APPROVE_EXECUTION_AND_PAYMENT,
                target=sender,
                warm=True,
                code=APPROVE_ALL,
            ),
        ],
    ).resolve_frames(fork)

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
    Test that `APPROVE` charges memory expansion for its return-data
    region and no base cost: the exact budget succeeds, one gas less
    halts the `VERIFY` frame and invalidates the transaction.
    """
    sender_code = Op.APPROVE(
        offset,
        length,
        Spec.APPROVE_EXECUTION_AND_PAYMENT,
        new_memory_size=offset + length,
    )
    sender = pre.deploy_contract(code=sender_code, balance=FUNDS)

    tx = Transaction(
        sender=sender,
        nonce=1,
        frames=[Frame.verify(code=sender_code, gas_limit_delta=budget_delta)],
        error=(
            TransactionException.TYPE_6_INVALID_FRAME_EXECUTION
            if budget_delta
            else None
        ),
    ).resolve_frames(fork)

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
    Test that a codeless payer's default code approves payment only in
    a `VERIFY` frame. In a `DEFAULT` or `SENDER` frame it returns like
    empty code, so no payer is set and the transaction is invalid.
    """
    sender = pre.fund_eoa()
    payer = pre.fund_eoa(amount=FUNDS)

    tx = Transaction(
        sender=sender,
        frames=[
            Frame.verify(flags=Spec.APPROVE_EXECUTION),
            Frame(mode=mode, flags=Spec.APPROVE_PAYMENT, target=payer),
        ],
        signatures=[canonical_entry(sender), canonical_entry(payer)],
        error=(
            None
            if approves
            else TransactionException.TYPE_6_INVALID_FRAME_EXECUTION
        ),
    ).resolve_frames(fork, payer=payer)

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
    Test that `max_cost`, the base fee plus the full tip on `max_gas`,
    leaves the payer when it approves payment: a later frame reads the
    reduced balance.
    """
    sender = pre.fund_eoa()
    payer = pre.fund_eoa(amount=FUNDS)
    # The payer's approving frame left it warm.
    probe_code = Op.SSTORE(0, Op.BALANCE(payer, address_warm=True)) + Op.STOP
    probe = pre.deploy_contract(code=probe_code)

    tx = Transaction(
        sender=sender,
        max_priority_fee_per_gas=PRIORITY_FEE,
        frames=[
            Frame.verify(flags=Spec.APPROVE_EXECUTION),
            Frame.verify(flags=Spec.APPROVE_PAYMENT, target=payer),
            Frame.default(
                target=probe,
                code=probe_code,
                state_gas_used=probe_code.state_cost(fork),
            ),
        ],
        signatures=[canonical_entry(sender), canonical_entry(payer)],
    ).resolve_frames(fork, payer=payer)
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
            sender: Account(nonce=1, balance_change=0),
            probe: Account(storage={0: FUNDS - max_cost}),
        },
    )


def test_max_cost_collected_within_approving_frame(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test that `max_cost` leaves the payer within the approving frame: a
    self-call approves payment and returns, then its caller reads the
    reduced balance.
    """
    call_self = Op.CALL(
        gas=Op.GAS,
        address=Op.ADDRESS,
        args_offset=0,
        args_size=1,
        # gas accounting
        address_warm=True,
        new_memory_size=1,
    )
    # Slot 0 records the self-call's result plus one, slot 1 the balance
    # its caller reads after it returns.
    record = Op.SSTORE(0, Op.ADD(1, call_self)) + Op.SSTORE(1, Op.SELFBALANCE)
    # The frame supplies no calldata, the self-call one byte.
    sender_code = Conditional(
        condition=Op.CALLDATASIZE,
        if_true=APPROVE_ALL,
        if_false=record + Op.STOP,
    )
    sender = pre.deploy_contract(code=sender_code, balance=FUNDS)

    invocation = sender_code.branch(condition=False) + sender_code.branch(
        condition=True
    )

    tx = Transaction(
        sender=sender,
        nonce=1,
        max_priority_fee_per_gas=PRIORITY_FEE,
        frames=[
            Frame.default(
                flags=Spec.APPROVE_EXECUTION_AND_PAYMENT,
                target=sender,
                # The self-call forwards all but a 64th of the gas left,
                # so the budget carries the retention.
                code=invocation,
                gas_limit_delta=invocation.execution_cost(fork) // 64,
                state_gas_used=record.state_cost(fork),
            ),
        ],
    ).resolve_frames(fork)
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
            sender: Account(nonce=2, storage={0: 2, 1: FUNDS - max_cost}),
        },
    )


def test_sender_creation_shortfall_halts_payment_approval(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test the new-account charge for an absent sender when a sponsor
    approves payment: one gas short of it, the sponsor's self-call halts
    without approving; with exactly that state budget, a second
    sponsor's approval succeeds.
    """
    # No opcode makes this charge: `APPROVE` creates the sender, priced
    # as `NEW_ACCOUNT` (the state gas of one new account).
    new_account_gas = fork.gas_costs().NEW_ACCOUNT
    sender = pre.fund_eoa(amount=0)
    # Execution gas the sponsor forwards to its approving self-call,
    # whose consumed gas it records in slot 0.
    inner_call_gas = 50_000
    call = Op.CALL(gas=inner_call_gas, address=Op.ADDRESS, address_warm=True)
    measure = CodeGasMeasure(code=call, extra_stack_items=1, sstore_key=0)
    # The frame supplies calldata, the self-call none.
    sponsor_code = Conditional(
        condition=Op.CALLDATASIZE,
        if_true=measure + Op.STOP,
        if_false=Op.APPROVE(0, 0, Spec.APPROVE_PAYMENT),
    )
    # The sponsor records the self-call's gas over a canary, a write that
    # creates no state, so the sender's creation is the only state charge
    # in the sponsor's frame.
    sponsor = pre.deploy_contract(
        code=sponsor_code, balance=FUNDS, storage={0: 0xDEAD}
    )
    second_payer = pre.fund_eoa(amount=FUNDS)

    tx = Transaction(
        sender=sender,
        frames=[
            Frame.verify(flags=Spec.APPROVE_EXECUTION),
            # One gas short of the creation: the self-call halts and
            # approves nothing, so the frame reports no state gas.
            Frame.default(
                flags=Spec.APPROVE_PAYMENT,
                target=sponsor,
                data=Bytes(b"\x01"),
                gas_limit=FRAME_GAS,
                state_gas_limit=new_account_gas - 1,
                pin_gas=False,
                state_gas_used=0,
            ),
            # Exactly the creation: the approval succeeds, which it could
            # not had the sponsor set the payer, and reports the creation
            # as its state gas.
            Frame.verify(
                flags=Spec.APPROVE_PAYMENT,
                target=second_payer,
                state_gas_limit=new_account_gas,
                state_gas_used=new_account_gas,
            ),
        ],
        signatures=[canonical_entry(sender), canonical_entry(second_payer)],
    ).resolve_frames(fork, payer=second_payer)

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            # The self-call halts, consuming all the gas it was given (a
            # revert would return it), and the sponsor keeps its balance.
            sponsor: Account(
                nonce=1,
                balance=FUNDS,
                storage={0: call.gas_cost(fork) + inner_call_gas},
            ),
        },
    )
