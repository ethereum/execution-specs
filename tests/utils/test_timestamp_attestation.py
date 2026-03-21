"""
Tests for proactive timestamp attestation utilities.
"""
from __future__ import annotations

import pytest

from ethereum.utils.timestamp_attestation import (
    AttestationHook,
    validate_transition_timestamp,
)


# ---------------------------------------------------------------------------
# Numeric threshold only (no hook)
# ---------------------------------------------------------------------------

def test_below_threshold_rejected() -> None:
    assert validate_transition_timestamp(999, 1000) is False


def test_at_threshold_accepted() -> None:
    assert validate_transition_timestamp(1000, 1000) is True


def test_above_threshold_accepted() -> None:
    assert validate_transition_timestamp(1001, 1000) is True


def test_no_hook_defaults_to_numeric_only() -> None:
    assert validate_transition_timestamp(5000, 5000, attestation_hook=None) is True


# ---------------------------------------------------------------------------
# With attestation hook
# ---------------------------------------------------------------------------

def test_hook_accept_passes() -> None:
    accept_all: AttestationHook = lambda ts: True
    assert validate_transition_timestamp(1000, 1000, attestation_hook=accept_all) is True


def test_hook_reject_blocks_even_if_numeric_ok() -> None:
    reject_all: AttestationHook = lambda ts: False
    assert validate_transition_timestamp(1000, 1000, attestation_hook=reject_all) is False


def test_hook_not_called_when_below_threshold() -> None:
    called: list[bool] = []

    def tracking_hook(ts: int) -> bool:
        called.append(True)
        return True

    result = validate_transition_timestamp(999, 1000, attestation_hook=tracking_hook)
    assert result is False
    assert called == [], "Hook must not be called when numeric threshold is not met"


def test_hook_receives_block_timestamp() -> None:
    received: list[int] = []

    def capture_hook(ts: int) -> bool:
        received.append(ts)
        return True

    validate_transition_timestamp(12345, 1000, attestation_hook=capture_hook)
    assert received == [12345]


def test_hook_drift_window_example() -> None:
    """
    Illustrates a realistic drift-checking hook.
    Validates that timestamps within a 4-second window pass,
    and timestamps outside it are rejected.
    """
    physical_time = 10000
    max_drift = 4

    def drift_hook(ts: int) -> bool:
        return abs(ts - physical_time) <= max_drift

    # Within tolerance
    assert validate_transition_timestamp(10003, 1000, attestation_hook=drift_hook) is True
    assert validate_transition_timestamp(9997, 1000, attestation_hook=drift_hook) is True

    # Outside tolerance
    assert validate_transition_timestamp(10005, 1000, attestation_hook=drift_hook) is False
    assert validate_transition_timestamp(9995, 1000, attestation_hook=drift_hook) is False
