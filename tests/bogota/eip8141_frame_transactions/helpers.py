"""Helpers for EIP-8141 frame transaction tests."""

from enum import Enum, auto, unique
from typing import Any, Callable, Dict, List, Optional, Self

from execution_testing import (
    EOA,
    Address,
    Bytecode,
    Bytes,
    Fork,
    Frame,
    FrameReceipt,
    FrameSignature,
    Op,
    Transaction,
    TransactionLog,
    TransactionReceipt,
)
from execution_testing.base_types import HexNumber
from pydantic import Field

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


@unique
class Outcome(Enum):
    """How a frame ends, and therefore what its receipt reports."""

    SUCCESS = auto()
    REVERT = auto()
    HALT = auto()
    SKIPPED = auto()
    # Succeeded, then undone by its atomic batch.
    UNROLLED = auto()

    @property
    def status(self) -> int:
        """Return the status this outcome reports."""
        if self in (Outcome.SUCCESS, Outcome.UNROLLED):
            return Spec.STATUS_SUCCESS
        if self is Outcome.SKIPPED:
            return Spec.STATUS_SKIPPED
        return Spec.STATUS_FAILURE

    @property
    def keeps_state_gas(self) -> bool:
        """Check whether the frame's state changes survive."""
        return self is Outcome.SUCCESS


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


class FrameCase(Frame):
    """A frame carrying the facts its budget and receipt follow from."""

    # What the frame runs
    outcome: Outcome = Field(Outcome.SUCCESS, exclude=True)
    """How the frame ends."""

    code: Optional[Bytecode] = Field(None, exclude=True)
    """Code the frame's target runs, which prices it."""

    execution_gas: Optional[int] = Field(None, exclude=True)
    """Execution gas after entry, where `code` cannot price it."""

    # What it is budgeted
    gas_limit_delta: Optional[int] = Field(None, exclude=True)
    """Execution budget, relative to the gas the frame spends."""

    state_gas_limit_delta: Optional[int] = Field(None, exclude=True)
    """State budget, relative to the state gas the frame writes."""

    # What its target's entry access costs
    warm: bool = Field(False, exclude=True)
    """Whether the resolved target is warm."""

    delegated: bool = Field(False, exclude=True)
    """Whether the target carries an EIP-7702 designation."""

    delegation_warm: bool = Field(False, exclude=True)
    """Whether the designated address is warm."""

    # What its receipt reports
    pin_gas: bool = Field(True, exclude=True)
    """Whether the receipt's execution gas is pinned."""

    gas_used: Optional[int] = Field(None, exclude=True)
    """Execution gas the receipt reports."""

    state_gas_used: Optional[int] = Field(None, exclude=True)
    """State gas the receipt reports."""

    logs: Optional[List[TransactionLog]] = Field(None, exclude=True)
    """Logs the receipt reports."""

    def entry_gas(self, fork: Fork) -> int:
        """Return the access the frame is charged at entry."""
        return fork.frame_entry_gas_calculator()(
            target_warm=self.warm,
            delegated=self.delegated,
            delegation_warm=self.delegation_warm,
        )

    def code_gas(self, fork: Fork) -> int:
        """Return the execution gas the frame draws after entry."""
        if self.execution_gas is not None:
            return self.execution_gas
        if self.code is None:
            return 0
        return self.code.execution_cost(fork)

    def code_state_gas(self, fork: Fork) -> int:
        """Return the state gas the frame's code writes."""
        if self.code is None:
            return 0
        return self.code.state_cost(fork)

    def settle_budgets(self, fork: Fork) -> None:
        """Settle the budgets the frame declares as deltas on its cost."""
        if self.gas_limit_delta is not None:
            assert "gas_limit" not in self.model_fields_set, (
                "a frame declares its execution budget once"
            )
            self.gas_limit = HexNumber(
                self.entry_gas(fork)
                + self.code_gas(fork)
                + self.gas_limit_delta
            )
        if self.state_gas_limit_delta is not None:
            assert "state_gas_limit" not in self.model_fields_set, (
                "a frame declares its state budget once"
            )
            self.state_gas_limit = HexNumber(
                self.code_state_gas(fork) + self.state_gas_limit_delta
            )

    def receipt(self, fork: Fork) -> FrameReceipt:
        """Return the receipt the frame should report."""
        gas_used: Optional[int]
        match self.pin_gas, self.gas_used, self.outcome:
            case False, None, _:
                gas_used = None
            case True, int() as pinned, _:
                gas_used = pinned
            case True, None, Outcome.SKIPPED:
                gas_used = 0
            case True, None, Outcome.HALT:
                # A halting frame forfeits its entire execution budget.
                gas_used = int(self.gas_limit)
            case True, None, (
                Outcome.SUCCESS | Outcome.REVERT | Outcome.UNROLLED
            ):
                gas_used = self.entry_gas(fork) + self.code_gas(fork)
            case _:
                raise ValueError(
                    f"no receipt gas for pin_gas={self.pin_gas}, "
                    f"gas_used={self.gas_used}, outcome={self.outcome}"
                )

        state_gas_used = 0
        if self.state_gas_used is not None:
            state_gas_used = self.state_gas_used
        elif self.outcome.keeps_state_gas:
            state_gas_used = self.code_state_gas(fork)

        logs = self.logs
        if logs is None and self.outcome is not Outcome.SUCCESS:
            logs = []

        return FrameReceipt(
            status=self.outcome.status,
            gas_used=gas_used,
            state_gas_used=state_gas_used,
            logs=logs,
        )


def default_frame(**overrides: Any) -> FrameCase:
    """Return a `DEFAULT` frame executing the frame entry point."""
    mode = overrides.setdefault("mode", Spec.MODE_DEFAULT)
    assert mode == Spec.MODE_DEFAULT, f"not a DEFAULT frame: mode {mode}"
    return FrameCase(**overrides)


def sender_frame(**overrides: Any) -> FrameCase:
    """Return a `SENDER` frame executing as the transaction sender."""
    mode = overrides.setdefault("mode", Spec.MODE_SENDER)
    assert mode == Spec.MODE_SENDER, f"not a SENDER frame: mode {mode}"
    # An empty target resolves to the sender, which frames start warm with.
    overrides.setdefault("warm", overrides.get("target") is None)
    return FrameCase(**overrides)


def verify_frame(**overrides: Any) -> FrameCase:
    """Return a `VERIFY` frame approving execution and payment."""
    mode = overrides.setdefault("mode", Spec.MODE_VERIFY)
    assert mode == Spec.MODE_VERIFY, f"not a VERIFY frame: mode {mode}"
    overrides.setdefault("flags", Spec.APPROVE_EXECUTION_AND_PAYMENT)
    # An empty target resolves to the sender, which frames start warm with.
    overrides.setdefault("warm", overrides.get("target") is None)
    return FrameCase(**overrides)


def expiry_frame(**overrides: Any) -> FrameCase:
    """Return a `VERIFY` frame targeting the expiry verifier predeploy."""
    mode = overrides.setdefault("mode", Spec.MODE_VERIFY)
    assert mode == Spec.MODE_VERIFY, f"not a VERIFY frame: mode {mode}"
    overrides.setdefault("flags", Spec.APPROVE_NONE)
    overrides.setdefault("target", Spec.EXPIRY_VERIFIER)
    # Such a frame is only valid with a zero state gas budget, and never
    # expires at the maximum timestamp.
    overrides.setdefault("state_gas_limit", 0)
    overrides.setdefault(
        "data", (2**64 - 1).to_bytes(Spec.EXPIRY_DATA_LENGTH, "big")
    )
    return FrameCase(**overrides)


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
        frames: List[FrameCase],
        payer: Optional[EOA] = None,
        signatures: Optional[List[FrameSignature]] = None,
        sender_scheme: Optional[int] = None,
        payer_scheme: Optional[int] = None,
        refund: int = 0,
        settle: bool = True,
        **overrides: Any,
    ) -> Self:
        """
        Return the frame transaction `frames` describes.

        A `payer` sponsors the transaction's gas, which settles its
        signature entries: the sender's names it without carrying
        signature material, which the transaction's own signature
        supplies, and the sponsor's is signed with the sponsor's own
        key, with `sender_scheme` and `payer_scheme` picking the
        schemes those entries carry. A test pinning malformed entries
        declares `signatures` itself instead, and then declares no
        scheme, since a given list settles every entry.

        `settle` drops the transaction total for a test that prices
        neither the refund nor the floor. A frame whose execution gas
        is unpinned leaves the total unpinned as well, since the total
        follows from every receipt. A transaction expected to be
        rejected carries no receipt expectation at all.
        """
        for case in frames:
            case.settle_budgets(fork)
        if signatures is None and payer is not None:
            if sender_scheme is None:
                sender_scheme = Spec.SCHEME_SECP256K1
            if payer_scheme is None:
                payer_scheme = Spec.SCHEME_SECP256K1
            signatures = [
                FrameSignature(scheme=sender_scheme, signer=Bytes(sender)),
                FrameSignature(
                    scheme=payer_scheme,
                    signer=Bytes(payer),
                    secret_key=payer.key,
                ),
            ]
        else:
            assert sender_scheme is None and payer_scheme is None, (
                "a transaction declares its signature entries once"
            )
        tx = cls(
            sender=sender, frames=frames, signatures=signatures, **overrides
        )
        assert tx.expected_receipt is None, (
            "the receipt follows from the frames, so it is never given"
        )
        if tx.error is not None:
            return tx

        # The intrinsic cost and the floor both charge for the signature
        # entries, which only exist once the transaction is signed.
        tx.sign()
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
