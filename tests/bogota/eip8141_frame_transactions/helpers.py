"""Helpers for EIP-8141 frame transaction tests."""

from typing import (
    Callable,
    NamedTuple,
    Optional,
    Sequence,
)

from execution_testing import (
    EOA,
    Address,
    Claim,
    Fork,
    Frame,
    Op,
)

from .claim_helpers import sender_claim
from .spec import Spec

MAX_FLOOR_PADDING = 1 << 16
"""Upper bound of the floor-binding padding search, far above any case."""


def floor_binding_padding(floor_binds: Callable[[int], bool]) -> int:
    """
    Return the fewest bytes of frame data for which `floor_binds` holds.

    With that padding the calldata floor binds by the smallest margin the
    data allows, and one byte less leaves it unbound, so a client that
    miscounts the charged data by a single byte charges the wrong side.
    """
    low, high = 0, MAX_FLOOR_PADDING
    assert not floor_binds(low) and floor_binds(high)
    while high - low > 1:
        middle = (low + high) // 2
        if floor_binds(middle):
            high = middle
        else:
            low = middle
    return high


def expiry_verifier_gas(fork: Fork) -> int:
    """
    Return the execution gas the verifier draws accepting its expiry.

    Its rejecting paths are never priced: a reverting `VERIFY` frame
    invalidates the whole transaction, which then reports no receipt.
    """
    accepting = (
        Op.PUSH1[0x08]
        + Op.CALLDATASIZE
        + Op.EQ
        + Op.PUSH1[0x0A]
        + Op.JUMPI
        + Op.JUMPDEST
        + Op.PUSH0
        + Op.CALLDATALOAD
        + Op.PUSH1[0xC0]
        + Op.SHR
        + Op.TIMESTAMP
        + Op.GT
        + Op.PUSH1[0x16]
        + Op.JUMPI
        + Op.STOP
    )
    return accepting.execution_cost(fork)


APPROVE_ALL = Op.APPROVE(0, 0, Spec.APPROVE_EXECUTION_AND_PAYMENT)
"""Approve execution and payment, returning no data."""

CALL_VALUE = 1
"""
Wei a test's `CALL` or `CALLCODE` sends along. An account the call must
be able to pay from is funded with exactly this much.
"""

CURRENT_FRAME_INDEX = Op.TXPARAM(Spec.TXPARAM_CURRENT_FRAME_INDEX)
"""Push the executing frame's index, which keys per-frame records."""

BASE_FEE = 7
"""Base fee of the block a fee-sensitive test's transaction lands in."""

PRIORITY_FEE = 5
"""Tip per gas a fee-sensitive test's transaction asks for when it tips."""


class FeeBudget(NamedTuple):
    """The amounts §Fee budget derives for a frame transaction."""

    max_gas: int
    """The gas limit in both dimensions, which the fee budget prices."""

    required_max_fee: int
    """`max_gas` at the base fee plus the blob gas at the blob base fee."""

    max_cost: int
    """`required_max_fee` plus the tip room: what the payer escrows."""


def fee_budget(
    fork: Fork,
    sender: EOA | Address,
    frames: Sequence[Frame],
    claims: Optional[Sequence[Claim]] = None,
    *,
    max_priority_fee_per_gas: int = 0,
    max_fee: Optional[int] = None,
    blob_count: int = 0,
    excess_blob_gas: int = 0,
) -> FeeBudget:
    """
    Return the fee budget of `sender`'s transaction with `frames` and
    `claims` at `BASE_FEE`. `claims` defaults to the sender's default
    claim (none for a contract sender), `max_fee` to room for the full
    tip. Pass resolved frames, such as `tx.frames` after
    `resolve_frames`.
    """
    if claims is None:
        claims = (
            [sender_claim(sender)]
            if isinstance(sender, EOA) and sender.key is not None
            else []
        )
    max_gas = fork.frame_transaction_intrinsic_cost_calculator()(
        frames=frames, claims=claims, sender=sender
    )
    blob_gas = blob_count * fork.blob_gas_per_blob()
    blob_base_fee = fork.blob_gas_price_calculator()(
        excess_blob_gas=excess_blob_gas
    )
    required_max_fee = max_gas * BASE_FEE + blob_gas * blob_base_fee
    full_tip = max_priority_fee_per_gas * max_gas
    if max_fee is None:
        max_fee = required_max_fee + full_tip
    max_cost = required_max_fee + min(full_tip, max_fee - required_max_fee)
    return FeeBudget(max_gas, required_max_fee, max_cost)
