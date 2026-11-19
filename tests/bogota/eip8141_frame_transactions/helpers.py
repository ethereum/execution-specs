"""Helpers for EIP-8141 frame transaction tests."""

from typing import (
    Any,
    Callable,
    Dict,
    List,
    NamedTuple,
    Optional,
    Self,
    Sequence,
)

from execution_testing import (
    EOA,
    Address,
    Fork,
    Frame,
    FrameSignature,
    Op,
    Transaction,
    TransactionReceipt,
)
from pydantic import Field

from .signature_helpers import canonical_entry
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


class FrameTransaction(Transaction):
    """Frame transaction whose settlement follows from its frames."""

    execution_gas: int = Field(0, exclude=True)
    """Pre-refund execution gas: the intrinsic cost plus every receipt."""

    state_gas: int = Field(0, exclude=True)
    """Attributed state gas, which no refund and no floor touches."""

    calldata_floor: int = Field(0, exclude=True)
    """The floor the execution dimension is held to."""

    effective_refund: int = Field(0, exclude=True)
    """The refund that survives the cap."""

    @classmethod
    def build(
        cls,
        *,
        fork: Fork,
        sender: EOA | Address,
        frames: List[Frame],
        payer: Optional[EOA | Address] = None,
        refund: int = 0,
        settle: bool = True,
        **overrides: Any,
    ) -> Self:
        """
        Return the frame transaction `frames` describes.

        `settle` drops the transaction total for a test that prices
        neither the refund nor the floor. A frame whose execution gas
        is unpinned leaves the total unpinned as well, since the total
        follows from every receipt. A transaction expected to be
        rejected carries no receipt expectation at all.
        """
        for case in frames:
            case.settle_budgets(fork)
        tx = cls(sender=sender, frames=frames, **overrides)
        assert tx.expected_receipt is None, (
            "the receipt follows from the frames, so it is never given"
        )
        if tx.error is not None:
            return tx

        # The intrinsic cost and the floor price the signature entries
        # before they are signed, from their signers' signature lengths.
        assert tx.frames is not None and tx.signatures is not None
        anchors: Dict[str, Any] = dict(
            frames=tx.frames,
            signatures=tx.signatures,
            sender=Address(sender),
        )

        receipts = [case.receipt(fork) for case in frames]
        intrinsic = fork.frame_transaction_intrinsic_cost_calculator()(
            return_cost_deducted_prior_execution=True, **anchors
        )
        tx.execution_gas = intrinsic + sum(
            int(receipt.gas_used or 0) for receipt in receipts
        )
        tx.state_gas = sum(
            int(receipt.state_gas_used or 0) for receipt in receipts
        )
        floor_calculator = fork.frame_transaction_data_floor_cost_calculator()
        tx.calldata_floor = floor_calculator(**anchors)
        tx.effective_refund = min(
            refund, tx.gas_before_refund // fork.max_refund_quotient()
        )

        settled = settle and all(
            receipt.gas_used is not None for receipt in receipts
        )
        tx.expected_receipt = TransactionReceipt(
            payer=payer if payer is not None else sender,
            cumulative_gas_used=tx.payer_gas_used() if settled else None,
            frame_receipts=receipts,
        )
        return tx

    @property
    def gas_before_refund(self) -> int:
        """Return the spent gas in both dimensions, before refunds."""
        return self.execution_gas + self.state_gas

    def floor_binds(self, *, after_refund: bool = True) -> bool:
        """Check whether the calldata floor sets the settled execution gas."""
        charged = self.execution_gas
        if after_refund:
            charged -= self.effective_refund
        return self.calldata_floor > charged

    def payer_gas_used(self) -> int:
        """Return the gas the payer is charged."""
        execution = max(
            self.execution_gas - self.effective_refund, self.calldata_floor
        )
        return execution + self.state_gas

    def block_gas_used(self) -> int:
        """Return the gas the block accounts for, before refunds."""
        return max(self.execution_gas, self.calldata_floor) + self.state_gas


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
    signatures: Optional[Sequence[FrameSignature]] = None,
    *,
    max_priority_fee_per_gas: int = 0,
    max_fee: Optional[int] = None,
    blob_count: int = 0,
    excess_blob_gas: int = 0,
) -> FeeBudget:
    """
    Return the fee budget of `sender`'s transaction with `frames` and
    `signatures` at `BASE_FEE`, pricing unsigned entries at their signer's
    signature length. `signatures` defaults to the sender's canonical
    entry (none for a contract sender), `max_fee` to room for the full
    tip. Pass settled frames, such as `tx.frames` after building.
    """
    if signatures is None:
        signatures = (
            [canonical_entry(sender)]
            if isinstance(sender, EOA) and sender.key is not None
            else []
        )
    max_gas = fork.frame_transaction_intrinsic_cost_calculator()(
        frames=frames, signatures=signatures, sender=sender
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
