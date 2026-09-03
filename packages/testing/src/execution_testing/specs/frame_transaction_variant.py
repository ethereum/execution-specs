"""
Refill state tests with their transaction rewritten as an EIP-8141
frame transaction.

A legacy-shaped transaction — a plain call carrying ``to``, ``value``
and ``data`` — has a canonical frame-transaction equivalent: a
``VERIFY`` frame approving execution and payment against the sender's
default code, followed by a ``SENDER`` frame performing the original
call. Re-filling an existing test with that shape gives differential
coverage of the frame transaction plumbing while reusing each test's
own post-state assertions unchanged.

`FrameTransactionVariant` labels an existing fixture format as its
``frame_tx`` variant; `StateTest` fills the variant by passing itself
through `convert_to_frame_transaction_variant` first.
"""

from typing import TYPE_CHECKING, Any, Dict, List, Sequence, Set, Type

import pytest

from execution_testing.base_types import Account
from execution_testing.fixtures import BaseFixture, LabeledFixtureFormat
from execution_testing.fixtures.base import FixtureFillingPhase
from execution_testing.forks import Fork, TransitionFork
from execution_testing.test_types import Frame, Transaction
from execution_testing.test_types.block_types import DEFAULT_BLOCK_GAS_LIMIT

if TYPE_CHECKING:
    from .state import StateTest

FRAME_TRANSACTION_TYPE = 6
"""
Transaction type of the EIP-8141 frame transaction; its presence in a
fork's transaction types gates the ``frame_tx`` variant.
"""

VERIFY_FRAME_MODE = 1
"""Mode of a frame that runs before execution to grant approvals."""

SENDER_FRAME_MODE = 2
"""Mode of a frame executing as the transaction sender."""

APPROVE_EXECUTION_AND_PAYMENT = 0x3
"""Flags approving both the transaction's execution and its payment."""

FRAME_TRANSACTION_VARIANT = "frame_tx"
"""Variant name a spec type checks via ``fixture_format.is_variant``."""


def has_frame_transactions(fork: Fork | TransitionFork) -> bool:
    """
    Check whether the fork supports frame transactions.

    Transition forks carry no transaction types of their own and never
    receive the frame variant.
    """
    return (
        hasattr(fork, "tx_types") and FRAME_TRANSACTION_TYPE in fork.tx_types()
    )


FRAME_STATE_GAS_BUDGET_MAX = 104_000_000
"""
Upper bound on the ``SENDER`` frame's state gas budget.

Sized so the most storage-hungry conversion — depositing a
maximum-size contract's code, roughly 100M state gas — keeps
headroom under the default block gas limit; the state dimension is
exempt from the EIP-7825 cap.
"""

FRAME_INTRINSIC_HEADROOM = 150_000
"""
Execution gas reserved out of the EIP-7825 cap for everything beyond
the ``SENDER`` frame's budget and the calldata cost: the VERIFY
frame's budget and the base, per-frame, and signature intrinsic
charges.
"""

FRAME_VERIFY_TOTAL_GAS = 500_000
"""
The VERIFY frame's default budgets across both dimensions, counted
against the block gas limit when sizing the ``SENDER`` frame.
"""

FRAME_BUDGET_FLOOR = 1_000_000
"""
Minimum viable budget per dimension; an environment too small to
grant it cannot hold the rewritten transaction.
"""

FRAME_SKIP_CATEGORY = "frame-unconvertible"
"""
Terminal reporting category for frame variants that cannot be
generated; a conftest can group them into one summary block instead
of thousands of skip lines.
"""


def skip_frame_variant(reason: str) -> None:
    """
    Skip generating this frame variant, tagged for terminal reporting
    hooks keyed on `FRAME_SKIP_CATEGORY`.
    """
    pytest.skip(f"{FRAME_SKIP_CATEGORY}: {reason}")


def frame_budgets(
    fork: Fork, tx: Transaction, env_gas_limit: int
) -> tuple[int, int]:
    """
    Derive the ``SENDER`` frame's (execution, state) budgets for a
    rewritten transaction.

    The legacy tests leave the transaction gas limit unset and
    receive the implicit block-sized limit, so the frame analog gives
    execution everything the EIP-7825 cap allows after the calldata
    intrinsic, and state everything the block gas limit allows after
    that — the transaction's derived gas is its intrinsic cost plus
    every frame's budgets in both dimensions.
    """
    calldata_cost = fork.calldata_gas_calculator()(data=tx.data)
    cap = fork.transaction_gas_limit_cap()
    # Frame transactions postdate EIP-7825, so the fork always caps
    # the transaction gas limit.
    assert cap is not None, "fork with frame transactions has no gas cap"
    available = (
        env_gas_limit - calldata_cost - FRAME_VERIFY_TOTAL_GAS - 500_000
    )
    execution = min(
        cap - calldata_cost - FRAME_INTRINSIC_HEADROOM,
        available // 2,
    )
    state = min(FRAME_STATE_GAS_BUDGET_MAX, available - execution)
    if execution < FRAME_BUDGET_FLOOR or state < FRAME_BUDGET_FLOOR:
        skip_frame_variant("environment gas limit below the frame budgets")
    return execution, state


RECEIPT_GAS_PINS = {"cumulative_gas_used", "gas_used"}
"""Receipt fields pinning gas usage, stripped for frame variants."""

HEADER_GAS_PINS = {"gas_used"}
"""Header fields pinning gas usage, stripped for frame variants."""


def without_gas_pins(pinned: Any, gas_fields: Set[str]) -> Any:
    """
    Return a copy of a pinned model without its gas-usage pins, or
    ``None`` when nothing else was pinned.

    Frame transactions have different intrinsic and per-frame costs,
    so a pinned gas value can never match; the remaining pins — logs,
    status, non-gas header fields — carry over unchanged, and the
    fixture's post-state root still captures gas indirectly through
    the sender and coinbase balances.
    """
    kept = {
        field: getattr(pinned, field)
        for field in pinned.model_fields_set
        if field not in gas_fields
    }
    if not kept:
        return None
    return type(pinned)(**kept)


def as_frame_transaction(
    tx: Transaction,
    fork: Fork,
    env_gas_limit: int,
    pre: Any = None,
) -> Transaction:
    """
    Rewrite a legacy-shaped transaction as its canonical frame
    transaction equivalent, skipping the test when the transaction
    carries a feature a frame transaction cannot express.

    The rewrite builds a fresh ``Transaction`` rather than copying:
    a model copy round-trips through serialization and loses the
    sender's private key, which the frame signature derivation needs.
    """
    if int(tx.ty) == FRAME_TRANSACTION_TYPE:
        skip_frame_variant("the transaction is already a frame transaction")
    if int(tx.ty) not in (0, 2, 3):
        skip_frame_variant(
            f"type-{int(tx.ty)} features have no frame equivalent"
        )
    if tx.to is None:
        skip_frame_variant("frame transactions cannot create contracts")
    if tx.access_list:
        skip_frame_variant("frame transactions carry no access list")
    if "gas_limit" in tx.model_fields_set:
        skip_frame_variant(
            "an explicit gas limit does not map to frame budgets"
        )
    if tx.error is not None:
        skip_frame_variant("transaction-validity errors do not carry over")
    if tx.sender is None or tx.sender.key is None:
        skip_frame_variant("frame signatures need the sender's key")
    if "state_gas_reservoir" in tx.model_fields_set:
        skip_frame_variant("frame budgets replace the state gas reservoir")
    if pre is not None:
        sender_account = pre[tx.sender] if tx.sender in pre else None
        if sender_account is not None and sender_account.code:
            # A delegated sender's VERIFY frame dispatches the
            # delegation's code instead of the protocol default code,
            # so the canonical wrapper never grants approval.
            skip_frame_variant("delegated senders approve via their own code")

    fee_fields: Dict[str, Any] = {}
    if tx.gas_price is not None:
        # A legacy gas price — the default included, which differs
        # from the default 1559 fee caps — maps exactly onto the
        # 1559-style fee fields: with both caps at the gas price, the
        # effective gas price equals it for any base fee the
        # transaction can pay.
        fee_fields = dict(
            max_fee_per_gas=tx.gas_price,
            max_priority_fee_per_gas=tx.gas_price,
        )
    elif int(tx.ty) in (2, 3):
        fee_fields = dict(
            max_fee_per_gas=tx.max_fee_per_gas,
            max_priority_fee_per_gas=tx.max_priority_fee_per_gas,
        )

    blob_fields: Dict[str, Any] = {}
    if int(tx.ty) == 3:
        # Frame transactions carry blobs natively: the versioned
        # hashes and blob fee cap transfer field-for-field.
        blob_fields = dict(
            blob_versioned_hashes=tx.blob_versioned_hashes,
            max_fee_per_blob_gas=tx.max_fee_per_blob_gas,
        )

    expected_receipt = None
    if tx.expected_receipt is not None:
        expected_receipt = without_gas_pins(
            tx.expected_receipt, RECEIPT_GAS_PINS
        )

    execution_budget, state_budget = frame_budgets(fork, tx, env_gas_limit)

    return Transaction(
        sender=tx.sender,
        nonce=tx.nonce,
        expected_receipt=expected_receipt,
        frames=[
            Frame(
                mode=VERIFY_FRAME_MODE,
                flags=APPROVE_EXECUTION_AND_PAYMENT,
            ),
            Frame(
                mode=SENDER_FRAME_MODE,
                target=tx.to,
                value=tx.value,
                data=tx.data,
                gas_limit=execution_budget,
                state_gas_limit=state_budget,
            ),
        ],
        **fee_fields,
        **blob_fields,
    )


def convert_to_frame_transaction_variant(test: "StateTest") -> "StateTest":
    """
    Return a copy of a state test with its transaction rewritten as a
    frame transaction, skipping the test when the transaction carries
    a feature a frame transaction cannot express.

    Along with the transaction rewrite, the copy raises a small block
    gas limit to the framework default and strips the test's gas-usage
    pins, neither of which can carry over to the frame shape.
    """
    update: Dict[str, Any] = {}

    # A test's small block gas limit cannot hold the frame budgets,
    # and unlike the legacy one-dimensional gas pool the two frame
    # dimensions cannot spill into each other, so no split of a small
    # block satisfies every execution/state mix. The block size is not
    # what these tests assert: raise the variant's block gas limit to
    # the framework default so every conversion gets the same generous
    # budgets.
    env = test.env
    if int(env.gas_limit) < DEFAULT_BLOCK_GAS_LIMIT:
        env = env.model_copy(update={"gas_limit": DEFAULT_BLOCK_GAS_LIMIT})
        update["env"] = env

    if test.blockchain_test_header_verify is not None:
        update["blockchain_test_header_verify"] = without_gas_pins(
            test.blockchain_test_header_verify, HEADER_GAS_PINS
        )

    # The variant never fills at a transition fork, so this names the
    # concrete fork whose gas schedule sizes the frame budgets.
    fork = test.fork.fork_at(
        block_number=test.env.number, timestamp=test.env.timestamp
    )
    tx = as_frame_transaction(
        test.tx,
        fork=fork,
        env_gas_limit=int(env.gas_limit),
        pre=test.pre,
    )
    update["tx"] = tx

    # A pinned sender balance encodes the exact gas spent, which a
    # frame transaction cannot reproduce. Fail with the fix rather
    # than surfacing an opaque balance mismatch from the fill.
    sender = tx.sender
    post_entry = (
        test.post[sender]
        if sender is not None and sender in test.post
        else None
    )
    if (
        isinstance(post_entry, Account)
        and "balance" in post_entry.model_fields_set
    ):
        pytest.fail(
            "the sender's pinned post balance encodes the exact gas"
            " spent, which a frame transaction cannot reproduce; pin"
            " gas via expected_receipt(cumulative_gas_used=...)"
            " instead",
            pytrace=False,
        )

    return test.model_copy(update=update)


class FrameTransactionVariant(LabeledFixtureFormat):
    """
    Label a fixture format as its ``frame_tx`` variant: the same
    fixture refilled with the test's transaction rewritten as a frame
    transaction.

    The variant fills only at forks whose transaction types include
    the frame transaction, and never for exception tests or tests
    marked ``frame_tx_incompatible``, whose oracles depend on the
    transaction type.
    """

    def __init__(
        self,
        fixture_format: "Type[BaseFixture] | LabeledFixtureFormat",
    ) -> None:
        """
        Label the wrapped format's id with a ``_frame_tx`` suffix.

        The variant asks the transition tool for a different
        transaction than the wrapped format, so it derives its own
        cache key from the wrapped format's rather than sharing it.
        """
        format_id = (
            fixture_format.format_id()
            if isinstance(fixture_format, LabeledFixtureFormat)
            else fixture_format.format_name
        )
        wrapped_cache_key = fixture_format.transition_tool_cache_key
        super().__init__(
            fixture_format,
            f"{format_id}_frame_tx",
            f"A {format_id} refilled with the test's transaction"
            " rewritten as a frame transaction",
            transition_tool_cache_key=(
                f"{wrapped_cache_key}_frame_tx" if wrapped_cache_key else ""
            ),
            variant=FRAME_TRANSACTION_VARIANT,
        )

    def supports_fork(self, fork: Fork | TransitionFork) -> bool:
        """
        Fill the variant only at forks with frame transactions, on top
        of whatever the wrapped format requires of the fork.
        """
        return has_frame_transactions(fork) and super().supports_fork(fork)

    def discard_fixture_format_by_marks(
        self,
        fork: Fork | TransitionFork,
        markers: List[pytest.Mark],
    ) -> bool:
        """
        Discard the variant for tests whose oracle depends on the
        transaction type: exception tests assert the original shape's
        validity, and ``frame_tx_incompatible`` marks the rest.
        """
        if any(
            marker.name in ("exception_test", "frame_tx_incompatible")
            for marker in markers
        ):
            return True
        return super().discard_fixture_format_by_marks(fork, markers)


def frame_transaction_variants(
    fixture_formats: Sequence["Type[BaseFixture] | LabeledFixtureFormat"],
) -> List[LabeledFixtureFormat]:
    """
    Return the ``frame_tx`` variant of every plain-fill format.

    Formats filled through pre-allocation grouping or state snapshots
    derive their genesis before the variant's rewrite runs, so only
    formats of the plain fill phase get a variant.
    """
    return [
        FrameTransactionVariant(fixture_format)
        for fixture_format in fixture_formats
        if FixtureFillingPhase.FILL in fixture_format.format_phases
    ]
