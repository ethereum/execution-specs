"""
Tests for TemporalHarness — deterministic timestamp injection utility.

These tests verify the harness itself, not any fork-specific logic.
All existing tests are unaffected: TemporalHarness is never imported
unless explicitly instantiated.
"""

from __future__ import annotations

import pytest

from ethereum.utils.temporal_harness import TemporalHarness, TimestampDriftError

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

PINNED_MS = 1_700_000_000_000  # fixed reference: 2023-11-14 ~22:13 UTC
PINNED_S = PINNED_MS // 1_000


# ---------------------------------------------------------------------------
# Basic drift validation
# ---------------------------------------------------------------------------


def test_within_drift_passes() -> None:
    """Block timestamp 5 s ahead of source is within EIP-1482 tolerance."""
    harness = TemporalHarness(time_source=lambda: PINNED_MS)
    harness.validate(block_timestamp_s=PINNED_S + 5)


def test_exact_drift_boundary_passes() -> None:
    """Block timestamp exactly at the 15 s boundary must pass."""
    harness = TemporalHarness(time_source=lambda: PINNED_MS)
    harness.validate(block_timestamp_s=PINNED_S + 15)


def test_exceeds_drift_raises() -> None:
    """Block timestamp 20 s ahead of source exceeds EIP-1482 limit."""
    harness = TemporalHarness(time_source=lambda: PINNED_MS)
    with pytest.raises(TimestampDriftError):
        harness.validate(block_timestamp_s=PINNED_S + 20)


def test_block_behind_source_raises() -> None:
    """Block timestamp 20 s behind source also exceeds the limit."""
    harness = TemporalHarness(time_source=lambda: PINNED_MS)
    with pytest.raises(TimestampDriftError):
        harness.validate(block_timestamp_s=PINNED_S - 20)


def test_custom_max_drift() -> None:
    """Custom max_drift_ms overrides the EIP-1482 default."""
    harness = TemporalHarness(
        time_source=lambda: PINNED_MS,
        max_drift_ms=5_000,
    )
    # 3 s drift — within custom 5 s window
    harness.validate(block_timestamp_s=PINNED_S + 3)
    # 6 s drift — exceeds custom 5 s window
    with pytest.raises(TimestampDriftError):
        harness.validate(block_timestamp_s=PINNED_S + 6)


# ---------------------------------------------------------------------------
# Attestation hook
# ---------------------------------------------------------------------------


def test_attestation_hook_invoked() -> None:
    """Attestation hook is called with (block_ms, source_ms) before check."""
    log: list[tuple[int, int]] = []

    harness = TemporalHarness(
        time_source=lambda: PINNED_MS,
        attestation_hook=lambda block_ms, src_ms: log.append(
            (block_ms, src_ms)
        ),
    )

    harness.validate(block_timestamp_s=PINNED_S + 3)

    assert len(log) == 1
    block_ms_recorded, src_ms_recorded = log[0]
    assert block_ms_recorded == (PINNED_S + 3) * 1_000
    assert src_ms_recorded == PINNED_MS


def test_attestation_hook_invoked_before_raise() -> None:
    """Hook fires even when drift is out of bounds."""
    log: list[tuple[int, int]] = []

    harness = TemporalHarness(
        time_source=lambda: PINNED_MS,
        attestation_hook=lambda block_ms, src_ms: log.append(
            (block_ms, src_ms)
        ),
    )

    with pytest.raises(TimestampDriftError):
        harness.validate(block_timestamp_s=PINNED_S + 30)

    assert len(log) == 1


# ---------------------------------------------------------------------------
# Default time source (smoke test — does not assert exact value)
# ---------------------------------------------------------------------------


def test_default_time_source_returns_int() -> None:
    """Default time_source returns a positive integer (ms since epoch)."""
    harness = TemporalHarness()
    result = harness.time_source()
    assert isinstance(result, int)
    assert result > 0
