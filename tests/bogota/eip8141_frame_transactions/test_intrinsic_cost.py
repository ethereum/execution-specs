"""
Intrinsic cost tests for
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

The intrinsic cost is a function of the transaction's fields alone: a
base cost, a cost per frame, the calldata cost of every frame's data
and every signature entry's bytes, a verification cost per entry, and a
value cost per frame that carries value to an explicit target other
than the sender, whether or not that frame later runs or succeeds.

Each test prices its transaction twice: through the framework's
calculator, which the pinned settlement uses, and through the EIP's own
formula written out below from the EIP's constants, so a framework that
drifts from the EIP shows as a failed assertion before anything is
filled.
"""

from typing import Dict, Iterable, List

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    Fork,
    Frame,
    FrameSignature,
    Op,
    StateTestFiller,
)

from .helpers import (
    FrameTransaction,
    Outcome,
    default_frame,
    sender_frame,
    verify_frame,
)
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")

# The EIP's constants (Constants and Gas Accounting), restated so the
# formula below does not borrow the framework's own.
FRAME_TX_INTRINSIC_COST = 12_000
FRAME_TX_PER_FRAME_COST = 475
TX_VALUE_COST = 6_000
STANDARD_TOKEN_COST = 4
SIGNATURE_GAS: Dict[int, int] = {
    Spec.SCHEME_SECP256K1: 2_800,
    Spec.SCHEME_P256: 6_700,
    Spec.SCHEME_ARBITRARY: 100,
}

PADDING = Op.JUMPDEST * 20_000
"""Execution that keeps the calldata floor from binding."""


def tokens_in(data: bytes) -> int:
    """EIP-8141 `tokens_in`: zero bytes count 1, non-zero bytes 4."""
    zero_bytes = data.count(0)
    return zero_bytes + (len(data) - zero_bytes) * 4


def floor_tokens_in(data: bytes) -> int:
    """EIP-8141 `floor_tokens_in`: every byte counts 4."""
    return len(data) * 4


def signature_bytes_tokens(signature: FrameSignature) -> int:
    """
    EIP-8141 `signature_bytes_tokens`: an empty-`msg` entry's signature
    bytes are priced as if all non-zero.
    """
    if len(signature.msg) == 0:
        return floor_tokens_in(bytes(signature.signature))
    return tokens_in(bytes(signature.signature))


def value_cost(frame: Frame, sender: Address) -> int:
    """EIP-8141 `value_cost`."""
    if frame.value > 0 and frame.target is not None and frame.target != sender:
        return TX_VALUE_COST
    return 0


def eip_intrinsic_gas(
    frames: Iterable[Frame],
    signatures: Iterable[FrameSignature],
    sender: Address,
) -> int:
    """EIP-8141 `frame_tx_intrinsic_gas`, term by term."""
    frames, signatures = list(frames), list(signatures)
    frame_data_cost = sum(
        STANDARD_TOKEN_COST * tokens_in(bytes(frame.data)) for frame in frames
    )
    signature_data_cost = sum(
        STANDARD_TOKEN_COST * tokens_in(bytes(signature.signer))
        + STANDARD_TOKEN_COST * tokens_in(bytes(signature.msg))
        + STANDARD_TOKEN_COST * signature_bytes_tokens(signature)
        for signature in signatures
    )
    signature_verification_cost = sum(
        SIGNATURE_GAS[int(signature.scheme)] for signature in signatures
    )
    value_transfer_cost = sum(value_cost(frame, sender) for frame in frames)
    return (
        FRAME_TX_INTRINSIC_COST
        + len(frames) * FRAME_TX_PER_FRAME_COST
        + frame_data_cost
        + signature_data_cost
        + signature_verification_cost
        + value_transfer_cost
    )


def assert_eip_intrinsic(
    fork: Fork, tx: FrameTransaction, sender: Address, expected: int
) -> None:
    """
    Check that the framework prices `tx`'s intrinsic cost as the EIP's
    formula does, and as the test expects.
    """
    assert tx.frames is not None and tx.signatures is not None
    framework = fork.frame_transaction_intrinsic_cost_calculator()(
        frames=tx.frames,
        signatures=tx.signatures,
        sender=sender,
        return_cost_deducted_prior_execution=True,
    )
    assert eip_intrinsic_gas(tx.frames, tx.signatures, sender) == framework
    assert framework == expected


def base_intrinsic(frame_count: int, signatures: List[FrameSignature]) -> int:
    """Return the intrinsic cost of dataless, valueless frames."""
    return eip_intrinsic_gas([Frame()] * frame_count, signatures, Address(0))


def test_frame_data_cost_sums_over_frames(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Charge the calldata cost of every frame's data.

    EIP-8141 "Gas Accounting": "`frame_data_cost =
    sum(calldata_cost(frame.data) for frame in tx.frames)`", where
    `calldata_cost(data) = STANDARD_TOKEN_COST * tokens_in(data)` and
    `tokens_in` counts a zero byte once and a non-zero byte four times.

    Two frames carry 16 non-zero and 16 zero bytes, 64 and 16 tokens.
    The intrinsic cost includes `4 * (64 + 16)` for them, and execution
    padding keeps the calldata floor from binding, so the settled gas
    shows that cost. A client pricing only one frame's data, or every
    byte alike, settles a different amount.
    """
    sender = pre.fund_eoa()
    nonzero_data, zero_data = b"\x01" * 16, b"\x00" * 16
    padded_code = PADDING + Op.STOP
    padded = pre.deploy_contract(code=padded_code)
    plain = pre.deploy_contract(code=Op.STOP)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            default_frame(target=padded, code=padded_code, data=nonzero_data),
            default_frame(target=plain, code=Op.STOP, data=zero_data),
        ],
    )
    assert tx.signatures is not None
    expected = base_intrinsic(3, tx.signatures) + STANDARD_TOKEN_COST * (
        16 * 4 + 16
    )
    assert_eip_intrinsic(fork, tx, sender, expected)
    # The premise: the floor does not bind.
    assert not tx.floor_binds()

    state_test(pre=pre, tx=tx, post={sender: Account(nonce=1)})


def test_value_cost_counts_static_value_frames(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Charge `TX_VALUE_COST` once for each frame carrying value to an
    explicit target other than the sender, whether it runs or not.

    EIP-8141 "Gas Accounting": "`def value_cost(frame): if frame.value >
    0 and frame.target is not None and frame.target != tx.sender:
    return TX_VALUE_COST`" and "`value_transfer_cost =
    sum(value_cost(frame) for frame in tx.frames)`"; "The charge is
    static because `value` and `target` are transaction fields"
    (Rationale).

    Four `SENDER` frames each carry one wei. The first, flagged as an
    atomic batch, runs a reverting recipient and fails; the second, the
    batch's last frame, is skipped and never runs; the third has no
    target and the fourth names the sender, so neither is charged.
    The intrinsic cost includes exactly two value costs, for the failed
    and the skipped frames. A client charging per transfer actually
    made, or charging the sender-targeted frames, settles a different
    amount.
    """
    sender = pre.fund_eoa()
    reverter = pre.deploy_contract(code=Op.REVERT(0, 0))
    skipped = pre.fund_eoa(amount=1)
    padded_code = PADDING + Op.STOP
    padded = pre.deploy_contract(code=padded_code)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            sender_frame(
                flags=Spec.ATOMIC_BATCH_FLAG,
                target=reverter,
                value=1,
                code=Op.REVERT(0, 0),
                outcome=Outcome.REVERT,
            ),
            sender_frame(target=skipped, value=1, outcome=Outcome.SKIPPED),
            sender_frame(value=1),
            sender_frame(target=sender, value=1, warm=True),
            default_frame(target=padded, code=padded_code),
        ],
    )
    assert tx.signatures is not None
    expected = base_intrinsic(6, tx.signatures) + 2 * TX_VALUE_COST
    assert_eip_intrinsic(fork, tx, sender, expected)
    assert not tx.floor_binds()

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            reverter: Account(balance=0),
            skipped: Account(balance=1),
        },
    )


@pytest.mark.parametrize(
    "frame_count,arbitrary_entries",
    [
        pytest.param(2, 0, id="two_frames"),
        pytest.param(Spec.MAX_FRAMES, 0, id="max_frames"),
        pytest.param(2, 1, id="one_arbitrary_entry"),
        pytest.param(2, 3, id="three_arbitrary_entries"),
    ],
)
def test_intrinsic_cost_per_frame_and_entry(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    frame_count: int,
    arbitrary_entries: int,
) -> None:
    """
    Charge the base cost, the per-frame cost for every frame, and each
    signature entry's verification cost and bytes.

    EIP-8141 "Gas Accounting": "`frame_tx_intrinsic_gas =
    FRAME_TX_INTRINSIC_COST + len(tx.frames) * FRAME_TX_PER_FRAME_COST
    + frame_data_cost + signature_data_cost +
    signature_verification_cost + value_transfer_cost`", with
    `signature_gas` 100 for an `ARBITRARY` entry and
    `signature_data_cost` pricing each entry's `signer`, `msg` and
    `signature` bytes.

    The transaction has a `VERIFY` frame and `frame_count - 1` empty
    `DEFAULT` frames, up to the 64 frames allowed, and besides the
    sender's entry `arbitrary_entries` `ARBITRARY` entries, each with an
    explicit `msg` and signature bytes holding zero and non-zero bytes.
    Its settled gas is the intrinsic cost of the EIP's formula plus the
    frames' entry accesses, with padding keeping the floor below it.
    """
    sender = pre.fund_eoa()
    padded_code = PADDING + Op.STOP
    padded = pre.deploy_contract(code=padded_code)
    empty = pre.deploy_contract(code=Op.STOP)
    frames = [verify_frame(), default_frame(target=padded, code=padded_code)]
    # Every later frame finds the empty contract warm.
    frames += [
        default_frame(target=empty, code=Op.STOP, warm=index > 0)
        for index in range(frame_count - 2)
    ]
    entries: List[FrameSignature] = [
        FrameSignature(scheme=Spec.SCHEME_SECP256K1, signer=Bytes(sender))
    ]
    entries += [
        FrameSignature(
            scheme=Spec.SCHEME_ARBITRARY,
            msg=Bytes(bytes([index + 1]) * 32),
            signature=Bytes(b"\x00\x07" * (index + 1)),
        )
        for index in range(arbitrary_entries)
    ]

    tx = FrameTransaction.build(
        fork=fork, sender=sender, frames=frames, signatures=entries
    )
    assert tx.signatures is not None
    sender_entry, *arbitrary = tx.signatures
    expected = base_intrinsic(frame_count, [sender_entry]) + sum(
        SIGNATURE_GAS[Spec.SCHEME_ARBITRARY]
        + STANDARD_TOKEN_COST
        * (tokens_in(bytes(entry.msg)) + tokens_in(bytes(entry.signature)))
        for entry in arbitrary
    )
    assert_eip_intrinsic(fork, tx, sender, expected)
    assert not tx.floor_binds()

    state_test(pre=pre, tx=tx, post={sender: Account(nonce=1)})
