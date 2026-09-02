"""
Fill every state test a second time with its transaction rewritten
as an EIP-8141 frame transaction.

A legacy-shaped transaction — a plain call carrying ``to``, ``value``
and ``data`` — has a canonical frame-transaction equivalent: a
``VERIFY`` frame approving execution and payment against the sender's
default code, followed by a ``SENDER`` frame performing the original
call. Re-filling the existing tests with that shape gives differential
coverage of the frame transaction plumbing while reusing each test's
own post-state assertions unchanged.

The extra ``frame_tx`` variant is generated only for forks whose
transaction types include the frame transaction, so fills for earlier
forks are unaffected.
"""

from typing import Any, List

import pytest
from execution_testing import Account, Environment, Fork, Transaction

from .amsterdam.eip8141_frame_transactions.helpers import (
    sender_frame,
    verify_frame,
)

FRAME_TRANSACTION_TYPE = 6
"""
Transaction type of the EIP-8141 frame transaction; its presence in a
fork's transaction types gates the ``frame_tx`` variant.
"""


def has_frame_transactions(fork: Any) -> bool:
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


def transaction_shapes(fork: Fork) -> List[Any]:
    """
    Return the transaction shapes to fill at the given fork: always the
    test's own shape, plus the frame rewrite where the fork has
    frame transactions.
    """
    shapes: List[Any] = [pytest.param("non_frame", id="non_frame_tx")]
    if has_frame_transactions(fork):
        shapes.append(
            pytest.param(
                "frame",
                id="frame_tx",
                marks=[
                    pytest.mark.fixture_subfolder(level=1, prefix="frame_tx")
                ],
            )
        )
    return shapes


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """
    Parametrize every state test with a transaction shape.

    The parameter is only added when the fill session selects at least
    one fork with frame transactions, keeping earlier forks' test ids
    and fixtures byte-identical.
    """
    if "state_test" not in metafunc.fixturenames:
        return
    if "eip8141_frame_transactions" in str(metafunc.definition.path):
        # The frame transaction tests build their own frame
        # transactions; there is nothing to rewrite.
        return
    if "benchmark" in metafunc.definition.path.parts:
        # Benchmark tests measure gas and throughput of the legacy
        # shape; a frame variant would measure something else.
        return
    if any(
        marker.name in ("exception_test", "frame_tx_incompatible")
        for marker in metafunc.definition.iter_markers()
    ):
        return
    selected_forks = getattr(metafunc.config, "selected_fork_set", None)
    if not selected_forks or not any(
        has_frame_transactions(fork) for fork in selected_forks
    ):
        return
    metafunc.definition.add_marker(
        pytest.mark.parametrize_by_fork("tx_shape", transaction_shapes)
    )


FRAME_SKIP_CATEGORY = "frame-unconvertible"
"""
Terminal reporting category for frame variants that cannot be
generated; they carry no progress character and are summarized as one
grouped block instead of thousands of ``s`` markers.
"""


def skip_frame_variant(reason: str) -> None:
    """
    Skip generating this frame variant, tagged for the terminal
    reporting hooks below.
    """
    pytest.skip(f"{FRAME_SKIP_CATEGORY}: {reason}")


def pytest_report_teststatus(report: Any, config: pytest.Config) -> Any:
    """
    Report unconvertible frame variants under their own category with
    no progress character, keeping fill output free of skip noise.
    """
    if getattr(report, "skipped", False):
        longrepr = getattr(report, "longrepr", None)
        if isinstance(longrepr, tuple) and FRAME_SKIP_CATEGORY in longrepr[2]:
            return FRAME_SKIP_CATEGORY, "", FRAME_SKIP_CATEGORY.upper()
    return None


def pytest_terminal_summary(
    terminalreporter: Any, exitstatus: int, config: pytest.Config
) -> None:
    """
    Print one grouped breakdown of the frame variants that were not
    generated, in place of per-test skip lines.
    """
    reports = terminalreporter.stats.get(FRAME_SKIP_CATEGORY, [])
    if not reports:
        return
    reasons: dict[str, int] = {}
    for report in reports:
        reason = report.longrepr[2].split(f"{FRAME_SKIP_CATEGORY}: ")[-1]
        reasons[reason] = reasons.get(reason, 0) + 1
    terminalreporter.write_sep("-", "frame variants not generated")
    for reason, count in sorted(
        reasons.items(), key=lambda item: item[1], reverse=True
    ):
        terminalreporter.write_line(f"{count:>6}  {reason}")


RECEIPT_GAS_PINS = {"cumulative_gas_used", "gas_used"}
"""Receipt fields pinning gas usage, stripped for frame variants."""

HEADER_GAS_PINS = {"gas_used"}
"""Header fields pinning gas usage, stripped for frame variants."""


def without_gas_pins(pinned: Any, gas_fields: set[str]) -> Any:
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

    fee_fields: dict[str, Any] = {}
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

    blob_fields: dict[str, Any] = {}
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
            verify_frame(),
            sender_frame(
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


@pytest.fixture
def tx_shape() -> str:
    """Fill the original transaction shape when unparametrized."""
    return "non_frame"


@pytest.fixture
def state_test(state_test: Any, tx_shape: str, fork: Fork) -> Any:
    """
    Wrap the filler plugin's ``state_test`` fixture so the ``frame``
    shape rewrites the transaction before filling.

    The ``state_test`` parameter resolves to the plugin's fixture of
    the same name; the ``non_frame`` shape passes it through untouched.
    """
    if tx_shape == "non_frame":
        return state_test
    unmodified_filler = state_test

    def frame_filler(*args: Any, **kwargs: Any) -> Any:
        assert not args, "state_test must be called with keyword arguments"

        # A test's small block gas limit cannot hold the frame
        # budgets, and unlike the legacy one-dimensional gas pool the
        # two frame dimensions cannot spill into each other, so no
        # split of a small block satisfies every execution/state mix.
        # The block size is not what these tests assert: raise the
        # frame variant's block gas limit to the framework default so
        # every conversion gets the same generous budgets.
        default_gas_limit = int(Environment().gas_limit)
        env = kwargs.get("env")
        if env is not None and int(env.gas_limit) < default_gas_limit:
            env = env.model_copy(update={"gas_limit": default_gas_limit})
            kwargs["env"] = env
        env_gas_limit = int(
            env.gas_limit if env is not None else default_gas_limit
        )

        header_verify = kwargs.get("blockchain_test_header_verify")
        if header_verify is not None:
            kwargs["blockchain_test_header_verify"] = without_gas_pins(
                header_verify, HEADER_GAS_PINS
            )
        kwargs["tx"] = as_frame_transaction(
            kwargs["tx"],
            fork=fork,
            env_gas_limit=env_gas_limit,
            pre=kwargs.get("pre"),
        )

        # A pinned sender balance encodes the exact gas spent, which a
        # frame transaction cannot reproduce. Fail with the fix rather
        # than surfacing an opaque balance mismatch from the fill.
        post = kwargs.get("post")
        sender = kwargs["tx"].sender
        if post is not None and sender is not None:
            entry = post.get(sender) if hasattr(post, "get") else None
            if (
                isinstance(entry, Account)
                and "balance" in entry.model_fields_set
            ):
                pytest.fail(
                    "the sender's pinned post balance encodes the exact"
                    " gas spent, which a frame transaction cannot"
                    " reproduce; pin gas via"
                    " expected_receipt(cumulative_gas_used=...) instead",
                    pytrace=False,
                )

        return unmodified_filler(**kwargs)

    return frame_filler
