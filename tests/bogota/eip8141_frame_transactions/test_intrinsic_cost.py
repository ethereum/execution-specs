"""
Intrinsic cost tests for
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

The intrinsic cost is a function of the transaction's fields alone: a
base cost, a cost per frame, the calldata cost of every frame's data
and every signature entry's bytes, a verification cost per entry, and a
value cost per frame that carries value to an explicit target other
than the sender, whether or not that frame later runs or succeeds.

Each test settles its transaction at the framework's intrinsic cost and
asserts, as the framework's difference with and without the term under
test, that the term contributes to it as the case requires.
"""

from typing import Any, List, Sequence, TypeVar

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    Fork,
    Frame,
    FrameSignature,
    GasConsumer,
    Op,
    StateTestFiller,
)

from .helpers import (
    FrameTransaction,
    Outcome,
    default_frame,
    padding_frame,
    sender_frame,
    verify_frame,
)
from .signature_helpers import canonical_entry
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")

PADDING_GAS = 20_000
"""Execution gas a padding frame burns to keep the floor from binding."""

ModelT = TypeVar("ModelT", Frame, FrameSignature)


def replaced(
    items: Sequence[ModelT], index: int, **update: Any
) -> List[ModelT]:
    """Return `items` with item `index` copied with `update` applied."""
    copies = list(items)
    copies[index] = items[index].model_copy(update=update)
    return copies


def intrinsic_cost(
    fork: Fork,
    frames: Sequence[Frame],
    signatures: Sequence[FrameSignature],
    sender: Address,
) -> int:
    """Return the framework's intrinsic cost of these transaction fields."""
    return fork.frame_transaction_intrinsic_cost_calculator()(
        frames=frames,
        signatures=signatures,
        sender=sender,
        return_cost_deducted_prior_execution=True,
    )


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

    Two frames carry as many non-zero and zero bytes, and execution
    padding keeps the calldata floor from binding, so the settled gas
    shows both frames' data cost. A client pricing only one frame's
    data, or every byte alike, settles a different amount.
    """
    sender = pre.fund_eoa()
    nonzero_data, zero_data = b"\x01" * 16, b"\x00" * 16
    padded = padding_frame(
        pre, GasConsumer(gas=PADDING_GAS, fork=fork), data=nonzero_data
    )
    plain = pre.deploy_contract(code=Op.STOP)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            padded,
            default_frame(target=plain, code=Op.STOP, data=zero_data),
        ],
    )
    assert tx.frames is not None and tx.signatures is not None
    frames, signatures = tx.frames, tx.signatures
    full = intrinsic_cost(fork, frames, signatures, sender)
    nonzero_data_cost = full - intrinsic_cost(
        fork, replaced(frames, 1, data=Bytes()), signatures, sender
    )
    zero_data_cost = full - intrinsic_cost(
        fork, replaced(frames, 2, data=Bytes()), signatures, sender
    )
    # The premises: both frames' data is charged, zero bytes less than
    # non-zero ones, and the floor does not bind.
    assert 0 < zero_data_cost < nonzero_data_cost
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
    padded = padding_frame(pre, GasConsumer(gas=PADDING_GAS, fork=fork))

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
            padded,
        ],
    )
    assert tx.frames is not None and tx.signatures is not None
    frames, signatures = tx.frames, tx.signatures
    full = intrinsic_cost(fork, frames, signatures, sender)
    valueless = list(frames)
    for index in range(1, 5):
        valueless = replaced(valueless, index, value=0)
    value_transfer_cost = full - intrinsic_cost(
        fork, valueless, signatures, sender
    )
    one_value_cost = full - intrinsic_cost(
        fork, replaced(frames, 1, value=0), signatures, sender
    )
    # The premises: the reverting frame's value is charged, the four
    # value frames are charged exactly two value costs, and the floor
    # does not bind.
    assert one_value_cost > 0
    assert value_transfer_cost == 2 * one_value_cost
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
    `signature_data_cost` pricing each entry's `signer`, `msg` and
    `signature` bytes.

    The transaction has a `VERIFY` frame and `frame_count - 1` empty
    `DEFAULT` frames, up to `MAX_FRAMES`, and besides the sender's entry
    `arbitrary_entries` `ARBITRARY` entries, each with an explicit `msg`
    and signature bytes holding zero and non-zero bytes. Its settled gas
    is the intrinsic cost plus the frames' entry accesses, with padding
    keeping the floor below it.
    """
    sender = pre.fund_eoa()
    padded = padding_frame(pre, GasConsumer(gas=PADDING_GAS, fork=fork))
    empty = pre.deploy_contract(code=Op.STOP)
    frames = [verify_frame(), padded]
    # Every later frame finds the empty contract warm.
    frames += [
        default_frame(target=empty, code=Op.STOP, warm=index > 0)
        for index in range(frame_count - 2)
    ]
    entries: List[FrameSignature] = [canonical_entry(sender)]
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
    assert tx.frames is not None and tx.signatures is not None
    signatures = tx.signatures
    full = intrinsic_cost(fork, tx.frames, signatures, sender)
    # The premise: a frame adds to the intrinsic cost even when empty.
    assert full > intrinsic_cost(fork, tx.frames[:-1], signatures, sender)
    for index in range(1, len(signatures)):
        without_entry = [
            entry for other, entry in enumerate(signatures) if other != index
        ]
        without_bytes = replaced(
            signatures, index, msg=Bytes(), signature=Bytes()
        )
        # The premise: each `ARBITRARY` entry is charged its
        # verification cost, and its bytes on top.
        assert (
            intrinsic_cost(fork, tx.frames, without_entry, sender)
            < intrinsic_cost(fork, tx.frames, without_bytes, sender)
            < full
        )
    assert not tx.floor_binds()

    state_test(pre=pre, tx=tx, post={sender: Account(nonce=1)})
