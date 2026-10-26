"""Helpers for EIP-8141 frame transaction tests."""

from enum import Enum, auto, unique
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
    SECP256K1_SIGNATURE_LENGTH,
    Address,
    Alloc,
    Bytecode,
    Bytes,
    Fork,
    Frame,
    FrameReceipt,
    FrameSignature,
    Op,
    Transaction,
    TransactionException,
    TransactionLog,
    TransactionReceipt,
    compute_create_address,
    create_op,
)
from execution_testing.base_types import HexNumber
from execution_testing.forks.forks.eips.bogota.eip_8141 import (
    EXPIRY_VERIFIER_BYTECODE,
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


EXPIRY_LENGTH_CHECK = (
    Op.PUSH1[Spec.EXPIRY_DATA_LENGTH]
    + Op.CALLDATASIZE
    + Op.EQ
    + Op.PUSH1[0x0A]
    + Op.JUMPI
)
"""The verifier's jump past its first `REVERT` on 8 bytes of calldata."""

EXPIRY_TIMESTAMP_CHECK = (
    Op.JUMPDEST
    + Op.PUSH0
    + Op.CALLDATALOAD
    + Op.PUSH1[0xC0]
    + Op.SHR
    + Op.TIMESTAMP
    + Op.GT
    + Op.PUSH1[0x16]
    + Op.JUMPI
)
"""The verifier's jump to its second `REVERT` once the expiry passed."""

EXPIRY_REJECT = Op.PUSH0 + Op.PUSH0 + Op.REVERT
"""The verifier's `REVERT`, reached when either check fails."""

EXPIRY_VERIFIER_CODE = (
    EXPIRY_LENGTH_CHECK
    + EXPIRY_REJECT
    + EXPIRY_TIMESTAMP_CHECK
    + Op.STOP
    + Op.JUMPDEST
    + EXPIRY_REJECT
)
"""The expiry verifier predeploy's code, as the EIP defines it."""
assert bytes(EXPIRY_VERIFIER_CODE) == EXPIRY_VERIFIER_BYTECODE

EXPIRY_VERIFIER_ACCEPTING_PATH = (
    EXPIRY_LENGTH_CHECK + EXPIRY_TIMESTAMP_CHECK + Op.STOP
)
"""The instructions the verifier runs accepting an unexpired timestamp."""

EXPIRY_VERIFIER_LENGTH_REJECTING_PATH = EXPIRY_LENGTH_CHECK + EXPIRY_REJECT
"""
The instructions the verifier runs when its calldata is not 8 bytes
long: the length check falls through to `REVERT`.
"""


def expiry_verifier_gas(fork: Fork) -> int:
    """
    Return the execution gas the verifier draws accepting its expiry.

    Its rejecting paths are never priced: a reverting `VERIFY` frame
    invalidates the whole transaction, which then reports no receipt.
    """
    return EXPIRY_VERIFIER_ACCEPTING_PATH.execution_cost(fork)


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


APPROVE_ALL = Op.APPROVE(0, 0, Spec.APPROVE_EXECUTION_AND_PAYMENT)
"""Approve execution and payment, returning no data."""

CURRENT_FRAME_INDEX = Op.TXPARAM(Spec.TXPARAM_CURRENT_FRAME_INDEX)
"""Push the executing frame's index, which keys per-frame records."""


def sponsored_signatures(sender: EOA, payer: EOA) -> List[FrameSignature]:
    """
    Return the signature entries of a sponsored transaction: the
    sender's canonical entry at index 0, which its default code reads to
    approve execution, and the payer's at index 1, which its default
    code reads to approve payment.
    """
    return [canonical_entry(sender), canonical_entry(payer)]


BASE_FEE = 7
"""Base fee of the block a fee budget case's transaction lands in."""

PRIORITY_FEE = 5
"""Tip per gas a fee budget case's transaction asks for when it tips."""


class FeeBudget(NamedTuple):
    """The amounts §Fee budget derives for a frame transaction."""

    max_gas: int
    """The gas limit in both dimensions, which the fee budget prices."""

    required_max_fee: int
    """`max_gas` at the base fee plus the blob gas at the blob base fee."""

    max_cost: int
    """
    `required_max_fee` plus the largest tip `max_fee` leaves room for:
    what the payer escrows when it approves payment.
    """


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
    Return the fee budget of a transaction `sender` sends with `frames`
    and `signatures` in a block at `BASE_FEE` and the blob base fee of
    `excess_blob_gas`.

    `signatures` defaults to the entries a transaction defaults to: the
    sender's canonical entry, or none for a contract sender. An unsigned
    entry over the canonical hash is priced at its signed length, since
    only the length of its raw bytes enters the cost, so the budget is
    known before the transaction is signed. `max_fee` defaults to one
    with room for the whole tip.
    """
    if signatures is None:
        signatures = (
            [canonical_entry(sender)]
            if isinstance(sender, EOA) and sender.key is not None
            else []
        )
    priced = [
        entry.model_copy(
            update={"signature": Bytes(bytes(SECP256K1_SIGNATURE_LENGTH))}
        )
        if entry.scheme == Spec.SCHEME_SECP256K1
        and len(entry.msg) == 0
        and len(entry.signature) == 0
        else entry
        for entry in signatures
    ]
    max_gas = fork.frame_transaction_intrinsic_cost_calculator()(
        frames=frames, signatures=priced, sender=sender
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


def storage_set_cost(fork: Fork) -> int:
    """
    Return the state gas of one fresh storage write,
    `STATE_BYTES_PER_STORAGE_SET * CPSB`.
    """
    return Op.SSTORE(0, 1).state_cost(fork)


def account_creation_cost(fork: Fork) -> int:
    """
    Return the state gas of one account creation,
    `STATE_BYTES_PER_NEW_ACCOUNT * CPSB`.
    """
    return fork.gas_costs().NEW_ACCOUNT


def clearing_refund(fork: Fork) -> int:
    """
    Return EIP-8038's `STORAGE_CLEAR_REFUND`: "added if the original
    value is non-zero, the current value is non-zero and the new value
    is zero", and subtracted when such a cleared slot is set non-zero
    again.
    """
    return fork.gas_costs().REFUND_STORAGE_CLEAR


def restoring_refund(fork: Fork) -> int:
    """
    Return EIP-8038's `STORAGE_WRITE`, "refunded if the new value equals
    the original value and differs from the current value": the write
    charge of a cold write less its cold access.
    """
    gas_costs = fork.gas_costs()
    return gas_costs.COLD_STORAGE_WRITE - gas_costs.COLD_STORAGE_ACCESS


CANARY = 0xDEAD
"""
Pre-state value of a recording slot, so overwriting it creates no state
and a slot left untouched, by a frame that halts or never reaches the
write, is distinguishable from a written one.
"""


def overwrite(slot: int, value: Bytecode) -> Bytecode:
    """Return a cold write of `value` over the canary in `slot`."""
    return Op.SSTORE(
        slot,
        value,
        key_warm=False,
        original_value=CANARY,
        current_value=CANARY,
        new_value=CANARY + 1,
    )


def record_pool(slot: int) -> Bytecode:
    """
    Return code recording the frame's remaining state gas pool, plus one
    so an empty pool is distinguishable from the canary, over the canary
    in `slot`.
    """
    return overwrite(slot, Op.ADD(1, Op.TXPARAM(Spec.TXPARAM_STATE_GAS_LEFT)))


FACTORY_NONCE = 1
"""Nonce of a contract deployed in the pre-state, which it creates at."""


def frame_data_copy(init_code: Bytecode) -> Bytecode:
    """
    Return code copying the frame data, which holds `init_code`, to
    memory offset zero.
    """
    size = len(init_code)
    return Op.CALLDATACOPY(
        0, 0, Op.CALLDATASIZE, data_size=size, new_memory_size=size
    )


def frame_data_create(
    create_opcode: Op, init_code: Bytecode, **metadata: Any
) -> Bytecode:
    """
    Return a `create_opcode` creation from the `init_code` that
    `frame_data_copy` placed in memory, with zero endowment and salt.

    Keyword arguments are passed on as the creation's gas metadata.
    """
    return create_op(
        create_opcode,
        size=Op.CALLDATASIZE,
        init_code_size=len(init_code),
        **metadata,
    )


def created_address(
    factory: Address, create_opcode: Op, init_code: Bytecode
) -> Address:
    """
    Return the address a pre-state factory's first `create_opcode`
    creation from `init_code` lands at.
    """
    return compute_create_address(
        address=factory,
        nonce=FACTORY_NONCE,
        salt=0,
        initcode=init_code,
        opcode=create_opcode,
    )


def padding_frame(
    pre: Alloc, padding: Bytecode, **overrides: Any
) -> FrameCase:
    """
    Return a `DEFAULT` frame running `padding`, then `STOP`, in a fresh
    contract: it spends execution gas and changes nothing, so the
    calldata floor stays unbound or a refund stays under its cap.
    """
    code = padding + Op.STOP
    return default_frame(
        target=pre.deploy_contract(code=code), code=code, **overrides
    )


def reserving_frame_tx(
    pre: Alloc,
    fork: Fork,
    *,
    execution_reservation: Optional[int] = None,
    state_reservation: int = 0,
    error: Optional[TransactionException] = None,
) -> Transaction:
    """
    Return a frame transaction reserving `execution_reservation` of a
    block's execution gas and `state_reservation` of its state gas.

    A fresh contract sender approving execution and payment sends it,
    with no signature entries and a single `VERIFY` frame without data,
    so the intrinsic cost is that of one bare frame and the frame's
    execution budget is the rest of the execution reservation. Without
    an execution reservation the frame is budgeted exactly what its
    approval spends.
    """
    sender = pre.deploy_contract(code=APPROVE_ALL, balance=10**18)
    if execution_reservation is None:
        gas_limit = fork.frame_entry_gas_calculator()(
            target_warm=True
        ) + APPROVE_ALL.execution_cost(fork)
    else:
        gas_limit = (
            execution_reservation
            - fork.frame_transaction_intrinsic_cost_calculator()(
                frames=1, return_cost_deducted_prior_execution=True
            )
        )
    return Transaction(
        sender=sender,
        nonce=1,
        frames=[
            verify_frame(
                gas_limit=gas_limit, state_gas_limit=state_reservation
            )
        ],
        error=error,
    )
