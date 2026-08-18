"""
Warmth tests for
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

Each frame of a frame transaction starts warm with the transaction
sender, the coinbase, and the precompiles — but not its own target,
whose warm or cold access is charged at frame entry within the frame's
own gas. A successful frame commits everything it accessed to the warm
journal shared across frames; a reverting or halting frame discards
its accesses, so nothing it touched stays warm.

The tests observe warmth in two ways: by measuring the gas of a
`BALANCE` on a subject address inside a frame, and by pinning a
frame receipt's `gas_used` to the target access charged at frame
entry.
"""

from dataclasses import dataclass
from enum import Enum, auto, unique

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytecode,
    CodeGasMeasure,
    Environment,
    Fork,
    Frame,
    FrameReceipt,
    Op,
    StateTestFiller,
    Transaction,
    TransactionReceipt,
)

from .helpers import verify_frame
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

# EIP-8141 is slated for the fork after Amsterdam, so fixtures are
# labeled with the pseudo `Bogota` fork (Amsterdam + EIP-8141), even
# though the spec prototypes the EIP inside the Amsterdam fork module.
# Fill these tests with `--fork Bogota`.
pytestmark = pytest.mark.valid_from("Bogota")

SLOT_MEASURED_GAS = 0x00
"""Storage slot the probe contract writes the measured gas into."""

PROBE_FRAME_GAS = 500_000
"""Execution gas budget of the probe frames."""

PROBE_FRAME_STATE_GAS = 100_000
"""
State gas budget of the probe frames, covering the fresh storage slot
the measurement write creates.
"""

TOUCH_FRAME_GAS = 200_000
"""Gas limit of the frames that warm the subject address."""


@dataclass(frozen=True)
class AccessGasProbe:
    """
    A deployable gas probe and the expectations pinning its behavior.
    """

    code: Bytecode
    """Code measuring the gas of an account access."""

    frame_gas: int
    """Execution gas a frame running the probe uses."""

    frame_state_gas: int
    """State gas a frame running the probe uses: its measurement write."""

    post_account: Account
    """Post account pinning the measured access cost."""


def balance_probe(
    subject: Address, fork: Fork, warm: bool = False
) -> AccessGasProbe:
    """
    Build a probe measuring the gas of a `BALANCE` on `subject`.

    The measurement lands in storage slot `SLOT_MEASURED_GAS`, and the
    probe's post account expects the warm or cold access cost there,
    per `warm` — the access the probe is expected to perform. `warm`
    also tags the measured `BALANCE`'s metadata, so `frame_gas`
    reflects the frame's actual execution: the cold access for the
    probe contract itself — always a fresh, untouched frame target —
    charged at frame entry, plus the probe code's execution gas. The
    measurement write's state gas lands in `frame_state_gas`,
    mirroring the two dimensions of the frame's receipt.
    """
    access_gas = Op.BALANCE(address_warm=warm).gas_cost(fork)
    measured = Op.BALANCE(address=subject, address_warm=warm)
    code = CodeGasMeasure(
        code=measured,
        overhead_cost=measured.gas_cost(fork) - access_gas,
        extra_stack_items=1,
        sstore_key=SLOT_MEASURED_GAS,
    )
    return AccessGasProbe(
        code=code,
        frame_gas=fork.gas_costs().COLD_ACCOUNT_ACCESS
        + code.execution_cost(fork),
        frame_state_gas=code.state_cost(fork),
        post_account=Account(storage={SLOT_MEASURED_GAS: access_gas}),
    )


def probe_frame(probe: Address) -> Frame:
    """
    Return a `DEFAULT` frame calling the probe contract.
    """
    return Frame(
        mode=Spec.MODE_DEFAULT,
        target=probe,
        gas_limit=PROBE_FRAME_GAS,
        state_gas_limit=PROBE_FRAME_STATE_GAS,
    )


@unique
class Outcome(Enum):
    """How a frame's or a call's code ends."""

    SUCCESS = auto()
    REVERT = auto()
    HALT = auto()


def outcome_tail(outcome: Outcome) -> Bytecode:
    """
    Return the code ending a contract with the given outcome.
    """
    match outcome:
        case Outcome.SUCCESS:
            return Op.STOP
        case Outcome.REVERT:
            return Op.REVERT(0, 0)
        case Outcome.HALT:
            return Op.INVALID
    raise ValueError(f"unhandled outcome: {outcome}")


def test_sender_is_warm(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Measure a `BALANCE` of the transaction sender from a `DEFAULT`
    frame.

    The sender seeds the warm journal of every frame transaction, so
    the access is warm even though the frame involves the sender in no
    other way.
    """
    sender = pre.fund_eoa()
    probe = balance_probe(sender, fork, warm=True)
    probe_address = pre.deploy_contract(code=probe.code)

    tx = Transaction(
        sender=sender,
        frames=[
            verify_frame(),
            probe_frame(probe_address),
        ],
        expected_receipt=TransactionReceipt(
            payer=sender,
            frame_receipts=[
                FrameReceipt(status=Spec.STATUS_SUCCESS, gas_used=0),
                FrameReceipt(
                    status=Spec.STATUS_SUCCESS,
                    gas_used=probe.frame_gas,
                    state_gas_used=probe.frame_state_gas,
                ),
            ],
        ),
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            probe_address: probe.post_account,
        },
    )


def test_coinbase_is_warm(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Measure a `BALANCE` of the coinbase from a `DEFAULT` frame.

    The coinbase is warmed at the entry of every frame, so the access
    is warm.
    """
    sender = pre.fund_eoa()
    probe = balance_probe(env.fee_recipient, fork, warm=True)
    probe_address = pre.deploy_contract(code=probe.code)

    tx = Transaction(
        sender=sender,
        frames=[
            verify_frame(),
            probe_frame(probe_address),
        ],
        expected_receipt=TransactionReceipt(
            payer=sender,
            frame_receipts=[
                FrameReceipt(status=Spec.STATUS_SUCCESS, gas_used=0),
                FrameReceipt(
                    status=Spec.STATUS_SUCCESS,
                    gas_used=probe.frame_gas,
                    state_gas_used=probe.frame_state_gas,
                ),
            ],
        ),
    )

    state_test(
        env=env,
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            probe_address: probe.post_account,
        },
    )


@pytest.mark.parametrize(
    "outcome",
    [
        pytest.param(Outcome.SUCCESS, id="success_carries_target_warmth"),
        pytest.param(Outcome.REVERT, id="revert_discards_target_warmth"),
        pytest.param(Outcome.HALT, id="halt_discards_target_warmth"),
    ],
)
def test_frame_target_entry_charge(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    outcome: Outcome,
) -> None:
    """
    Charge a frame's target access at frame entry, within the frame's
    own gas.

    The target is not pre-warmed, so the first frame pays the cold
    account access — pinned by its receipt's `gas_used`. A second
    frame with the same target pays only the warm access if the first
    frame succeeded; a reverting frame discards the warmth it charged
    for, so the second frame pays the cold access again.

    A halting frame forfeits its whole gas limit regardless of the
    entry charge, which would leave the receipts blind if both frames
    halted, so the halt scenario gates the target on its call data:
    the first frame sends none and halts, the second sends one byte
    and executes cleanly — pinning a cold entry charge, because the
    halting frame discarded the target's warmth.
    """
    sender = pre.fund_eoa()

    cold_access = fork.gas_costs().COLD_ACCOUNT_ACCESS
    warm_access = fork.gas_costs().WARM_ACCESS

    match outcome:
        case Outcome.SUCCESS:
            target_code = outcome_tail(outcome)
            code_cost = target_code.gas_cost(fork)
            frame_data = [b"", b""]
            expected = [
                (Spec.STATUS_SUCCESS, cold_access + code_cost),
                (Spec.STATUS_SUCCESS, warm_access + code_cost),
            ]
        case Outcome.REVERT:
            target_code = outcome_tail(outcome)
            code_cost = target_code.gas_cost(fork)
            frame_data = [b"", b""]
            expected = [
                (Spec.STATUS_FAILURE, cold_access + code_cost),
                (Spec.STATUS_FAILURE, cold_access + code_cost),
            ]
        case Outcome.HALT:
            # Halt on empty call data, return cleanly otherwise: a
            # zero `CALLDATASIZE` falls through the `JUMPI` into
            # `INVALID`; non-empty data jumps to the `JUMPDEST` at
            # offset 5.
            target_code = (
                Op.JUMPI(5, Op.CALLDATASIZE)
                + Op.INVALID
                + Op.JUMPDEST
                + Op.STOP
            )
            # The whole listing's cost equals the executed path's:
            # the one skipped opcode, `INVALID`, costs nothing.
            code_cost = target_code.gas_cost(fork)
            frame_data = [b"", b"\x01"]
            expected = [
                # The halting frame forfeits its entire gas limit.
                (Spec.STATUS_FAILURE, TOUCH_FRAME_GAS),
                (Spec.STATUS_SUCCESS, cold_access + code_cost),
            ]
        case _:
            raise ValueError(f"unhandled outcome: {outcome}")

    target = pre.deploy_contract(code=target_code)
    tx = Transaction(
        sender=sender,
        frames=[
            verify_frame(),
            *[
                Frame(
                    mode=Spec.MODE_DEFAULT,
                    target=target,
                    gas_limit=TOUCH_FRAME_GAS,
                    data=data,
                )
                for data in frame_data
            ],
        ],
        expected_receipt=TransactionReceipt(
            payer=sender,
            frame_receipts=[
                FrameReceipt(status=Spec.STATUS_SUCCESS, gas_used=0),
                *[
                    FrameReceipt(status=status, gas_used=gas)
                    for status, gas in expected
                ],
            ],
        ),
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
        },
    )


@pytest.mark.parametrize(
    "outcome,carries",
    [
        pytest.param(Outcome.SUCCESS, True, id="success_carries"),
        pytest.param(Outcome.REVERT, False, id="revert_discards"),
        pytest.param(Outcome.HALT, False, id="halt_discards"),
    ],
)
def test_warmth_carry_to_next_frame(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    outcome: Outcome,
    carries: bool,
) -> None:
    """
    Warm an address in one frame and measure its access cost in the
    next.

    A successful frame commits its accesses to the warm journal shared
    across frames, so the next frame sees the address warm. A frame
    that reverts or halts discards them, and the next frame pays the
    cold access again.
    """
    sender = pre.fund_eoa()
    subject = pre.fund_eoa(amount=1)
    warmer_code = Op.POP(Op.BALANCE(subject)) + outcome_tail(outcome)
    warmer = pre.deploy_contract(code=warmer_code)
    probe = balance_probe(subject, fork, warm=carries)
    probe_address = pre.deploy_contract(code=probe.code)

    executed_gas = fork.gas_costs().COLD_ACCOUNT_ACCESS + warmer_code.gas_cost(
        fork
    )
    match outcome:
        case Outcome.SUCCESS:
            warmer_status = Spec.STATUS_SUCCESS
            warmer_gas = executed_gas
        case Outcome.REVERT:
            warmer_status = Spec.STATUS_FAILURE
            warmer_gas = executed_gas
        case Outcome.HALT:
            # A halting frame forfeits its entire gas limit.
            warmer_status = Spec.STATUS_FAILURE
            warmer_gas = TOUCH_FRAME_GAS
        case _:
            raise ValueError(f"unhandled outcome: {outcome}")
    tx = Transaction(
        sender=sender,
        frames=[
            verify_frame(),
            Frame(
                mode=Spec.MODE_DEFAULT,
                target=warmer,
                gas_limit=TOUCH_FRAME_GAS,
            ),
            probe_frame(probe_address),
        ],
        expected_receipt=TransactionReceipt(
            payer=sender,
            frame_receipts=[
                FrameReceipt(status=Spec.STATUS_SUCCESS, gas_used=0),
                FrameReceipt(status=warmer_status, gas_used=warmer_gas),
                FrameReceipt(
                    status=Spec.STATUS_SUCCESS,
                    gas_used=probe.frame_gas,
                    state_gas_used=probe.frame_state_gas,
                ),
            ],
        ),
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            probe_address: probe.post_account,
        },
    )


@pytest.mark.parametrize(
    "child_outcome,frame_outcome,carries",
    [
        pytest.param(
            Outcome.SUCCESS,
            Outcome.SUCCESS,
            True,
            id="child_and_frame_succeed",
        ),
        pytest.param(
            Outcome.REVERT, Outcome.SUCCESS, False, id="child_reverts"
        ),
        pytest.param(Outcome.HALT, Outcome.SUCCESS, False, id="child_halts"),
        pytest.param(
            Outcome.SUCCESS, Outcome.REVERT, False, id="frame_reverts"
        ),
        pytest.param(Outcome.SUCCESS, Outcome.HALT, False, id="frame_halts"),
    ],
)
def test_warmth_from_inner_call(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    child_outcome: Outcome,
    frame_outcome: Outcome,
    carries: bool,
) -> None:
    """
    Warm an address at call depth 1 inside a frame and measure its
    access cost in the next frame.

    The child call's accesses surface into the frame's top-level EVM
    only when the child returns successfully, and reach the warm
    journal shared across frames only when the frame itself succeeds
    as well. Either the child or the frame reverting or halting
    discards the access, and the next frame pays the cold cost.
    """
    sender = pre.fund_eoa()
    subject = pre.fund_eoa(amount=1)
    child_code = Op.POP(Op.BALANCE(subject)) + outcome_tail(child_outcome)
    child = pre.deploy_contract(code=child_code)
    outer_code = Op.POP(Op.CALL(Op.GAS, child, 0, 0, 0, 0, 0)) + outcome_tail(
        frame_outcome
    )
    outer = pre.deploy_contract(code=outer_code)
    probe = balance_probe(subject, fork, warm=carries)
    probe_address = pre.deploy_contract(code=probe.code)

    outer_gas: int | None
    match child_outcome, frame_outcome:
        case (_, Outcome.HALT):
            # A halting frame forfeits its entire gas limit.
            outer_gas = TOUCH_FRAME_GAS
        case (Outcome.HALT, _):
            # The halting child consumes all the gas forwarded to it,
            # an amount set by the 63/64 retention rule rather than by
            # the code under test, so the frame's gas is not pinned.
            outer_gas = None
        case (
            Outcome.SUCCESS | Outcome.REVERT,
            Outcome.SUCCESS | Outcome.REVERT,
        ):
            outer_gas = (
                fork.gas_costs().COLD_ACCOUNT_ACCESS
                + outer_code.gas_cost(fork)
                + child_code.gas_cost(fork)
            )
        case _:
            raise ValueError(
                f"unhandled outcomes: {child_outcome}, {frame_outcome}"
            )

    outer_status = (
        Spec.STATUS_SUCCESS
        if frame_outcome is Outcome.SUCCESS
        else Spec.STATUS_FAILURE
    )
    tx = Transaction(
        sender=sender,
        frames=[
            verify_frame(),
            Frame(
                mode=Spec.MODE_DEFAULT,
                target=outer,
                gas_limit=TOUCH_FRAME_GAS,
            ),
            probe_frame(probe_address),
        ],
        expected_receipt=TransactionReceipt(
            payer=sender,
            frame_receipts=[
                FrameReceipt(status=Spec.STATUS_SUCCESS, gas_used=0),
                FrameReceipt(status=outer_status, gas_used=outer_gas),
                FrameReceipt(
                    status=Spec.STATUS_SUCCESS,
                    gas_used=probe.frame_gas,
                    state_gas_used=probe.frame_state_gas,
                ),
            ],
        ),
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            probe_address: probe.post_account,
        },
    )
