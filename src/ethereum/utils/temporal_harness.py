"""
Temporal Harness for Timestamp Injection in Tests.

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Optional test infrastructure for injecting and validating external time
sources in execution-spec timestamp tests.

Follows the opt-in pattern established by ``TransitionConfig`` (#2449):
existing tests are completely unaffected unless a ``TemporalHarness``
instance is explicitly constructed and passed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class TemporalHarness:
    """
    Optional harness for injecting and validating external time sources
    in execution-specs timestamp tests.

    Follows the TransitionConfig opt-in pattern (#2449).
    All fields have safe defaults — existing tests are unaffected unless
    a TemporalHarness instance is explicitly passed.

    Parameters
    ----------
    time_source :
        A zero-argument callable returning the current time in milliseconds
        (Unix epoch, integer). Defaults to system time via ``time.time_ns``.
        Can be replaced with any deterministic mock, NTP client, or
        GPS-synchronized time source for test isolation.
    max_drift_ms :
        Maximum acceptable drift in milliseconds between the block timestamp
        and the value returned by ``time_source``.
        Default: 15000 ms (15 seconds), per EIP-1482.
    attestation_hook :
        Optional callable invoked before drift validation.
        Receives ``(block_timestamp_ms: int, source_timestamp_ms: int)
        -> None``. Intended for integration with external attestation
        systems (e.g., satellite time verification). No-op when ``None``.
    """

    time_source: Callable[[], int] = field(
        default_factory=lambda: (
            lambda: __import__("time").time_ns() // 1_000_000
        )
    )
    max_drift_ms: int = 15_000  # EIP-1482: ±15 seconds
    attestation_hook: Optional[Callable[[int, int], None]] = None

    def validate(self, block_timestamp_s: int) -> None:
        """
        Validate that ``block_timestamp_s`` does not exceed ``max_drift_ms``
        relative to the injected time source.

        Parameters
        ----------
        block_timestamp_s :
            Block timestamp in seconds, as stored on-chain.

        Raises
        ------
        TimestampDriftError
            If the absolute drift exceeds ``max_drift_ms``.
        """
        source_ms = self.time_source()
        block_ms = block_timestamp_s * 1_000
        drift_ms = abs(source_ms - block_ms)

        if self.attestation_hook is not None:
            self.attestation_hook(block_ms, source_ms)

        if drift_ms > self.max_drift_ms:
            raise TimestampDriftError(
                f"block.timestamp drift {drift_ms} ms exceeds "
                f"EIP-1482 limit of {self.max_drift_ms} ms "
                f"(block={block_ms} ms, source={source_ms} ms)"
            )


class TimestampDriftError(Exception):
    """Raised when block.timestamp drift exceeds the configured threshold."""

    pass
