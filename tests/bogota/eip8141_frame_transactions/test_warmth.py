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
`BALANCE` on a subject address inside a frame, and by declaring a
frame's target warm or cold, which the frame receipt's `gas_used`
then pins.
"""

from dataclasses import dataclass
from typing import Any

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytecode,
    Bytes,
    CodeGasMeasure,
    Environment,
    Fork,
    FrameSignature,
    Op,
    StateTestFiller,
)

from .helpers import (
    FrameCase,
    FrameTransaction,
    Outcome,
    default_frame,
    verify_frame,
)
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

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
    """A deployable gas probe and the post account pinning its result."""

    code: Bytecode
    """Code measuring the gas of an account access."""

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
    also tags the measured `BALANCE`'s metadata, so the probe's code
    prices the frame's actual execution.
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
        post_account=Account(storage={SLOT_MEASURED_GAS: access_gas}),
    )


def probe_frame(target: Address, probe: AccessGasProbe) -> FrameCase:
    """
    Return a `DEFAULT` frame calling the probe contract.

    The probe is always a fresh, untouched frame target, so its entry
    access is cold.
    """
    return default_frame(
        target=target,
        code=probe.code,
        gas_limit=PROBE_FRAME_GAS,
        state_gas_limit=PROBE_FRAME_STATE_GAS,
    )


def outcome_tail(outcome: Outcome) -> Bytecode:
    """Return the code ending a contract with the given outcome."""
    match outcome:
        case Outcome.SUCCESS:
            return Op.STOP
        case Outcome.REVERT:
            return Op.REVERT(0, 0)
        case Outcome.HALT:
            return Op.INVALID
        case _:
            raise ValueError(f"no code ends a frame as {outcome}")


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

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            probe_frame(probe_address, probe),
        ],
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

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            probe_frame(probe_address, probe),
        ],
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

    if outcome is Outcome.HALT:
        # Halt on empty call data, return cleanly otherwise: a zero
        # `CALLDATASIZE` falls through the `JUMPI` into `INVALID`;
        # non-empty data jumps to the `JUMPDEST` at offset 5.
        target_code = (
            Op.JUMPI(5, Op.CALLDATASIZE) + Op.INVALID + Op.JUMPDEST + Op.STOP
        )
    else:
        target_code = outcome_tail(outcome)
    target = pre.deploy_contract(code=target_code)

    def touch(**facts: Any) -> FrameCase:
        return default_frame(
            target=target,
            code=target_code,
            gas_limit=TOUCH_FRAME_GAS,
            **facts,
        )

    match outcome:
        case Outcome.SUCCESS:
            # The first frame's success leaves the target warm.
            touches = [touch(), touch(warm=True)]
        case Outcome.REVERT:
            # The revert discards the warmth it charged for.
            touches = [touch(outcome=outcome), touch(outcome=outcome)]
        case Outcome.HALT:
            touches = [touch(outcome=outcome, data=b""), touch(data=b"\x01")]
        case _:
            raise ValueError(f"unhandled outcome: {outcome}")

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[verify_frame(), *touches],
    )

    state_test(pre=pre, tx=tx, post={sender: Account(nonce=1)})


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

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            default_frame(
                target=warmer,
                code=warmer_code,
                gas_limit=TOUCH_FRAME_GAS,
                outcome=outcome,
            ),
            probe_frame(probe_address, probe),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            probe_address: probe.post_account,
        },
    )


def test_payer_warm_after_default_code_payment_approval(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Measure a `BALANCE` of the payer in the frame after a sponsored
    payment approval through the payer's protocol default code.

    The payer needs no warming rule of its own: it is the resolved
    target of the frame that approves payment, so that frame charges
    the payer's access at entry — a cold one, the transaction having
    touched the sponsor nowhere else — and commits the warmth to the
    journal shared across frames when it succeeds.
    """
    sender = pre.fund_eoa()
    payer = pre.fund_eoa()
    probe = balance_probe(payer, fork, warm=True)
    probe_address = pre.deploy_contract(code=probe.code)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        payer=payer,
        frames=[
            verify_frame(flags=Spec.APPROVE_EXECUTION),
            verify_frame(flags=Spec.APPROVE_PAYMENT, target=payer),
            probe_frame(probe_address, probe),
        ],
        signatures=[
            FrameSignature(scheme=Spec.SCHEME_SECP256K1, signer=Bytes(sender)),
            FrameSignature(
                scheme=Spec.SCHEME_SECP256K1,
                signer=Bytes(payer),
                secret_key=payer.key,
            ),
        ],
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
    "mode,origin_warm",
    [
        pytest.param(Spec.MODE_DEFAULT, False, id="default_frame_origin_cold"),
        pytest.param(Spec.MODE_VERIFY, False, id="verify_frame_origin_cold"),
        pytest.param(Spec.MODE_SENDER, True, id="sender_frame_origin_warm"),
    ],
)
def test_origin_warmth_by_frame_mode(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    mode: int,
    origin_warm: bool,
) -> None:
    """
    Access the balance of `ORIGIN` in each frame mode, pinning its
    warm or cold cost through the frame receipt's gas.

    The frame entry point is not pre-warmed, so the access is cold in
    `DEFAULT` and `VERIFY` frames, where `ORIGIN` is the entry point.
    In a `SENDER` frame `ORIGIN` is the transaction sender, which
    seeds the warm journal. The receipt pins the gas — rather than a
    stored measurement — so the probe stays free of state writes and
    runs unchanged in a `VERIFY` frame.
    """
    sender = pre.fund_eoa()
    code = Op.POP(Op.BALANCE(Op.ORIGIN, address_warm=origin_warm)) + Op.STOP
    prober = pre.deploy_contract(code=code)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            FrameCase(
                target=prober,
                mode=mode,
                code=code,
                gas_limit=TOUCH_FRAME_GAS,
            ),
        ],
    )

    state_test(pre=pre, tx=tx, post={sender: Account(nonce=1)})


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

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            default_frame(
                target=outer,
                gas_limit=TOUCH_FRAME_GAS,
                outcome=frame_outcome,
                execution_gas=(
                    outer_code.execution_cost(fork)
                    + child_code.execution_cost(fork)
                ),
                # A halting child consumes all the gas forwarded to it,
                # an amount the 63/64 retention rule sets rather than
                # the code under test.
                pin_gas=child_outcome is not Outcome.HALT,
            ),
            probe_frame(probe_address, probe),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            probe_address: probe.post_account,
        },
    )
