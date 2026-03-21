"""
Proactive timestamp attestation for fork transition validation.

Provides an optional hook mechanism that allows callers to validate that a
block timestamp corresponds to real physical time — not just that it is
numerically >= the configured transition threshold — before a fork transition
is applied.

This is the enforcement-layer complement to after-the-fact timestamp anomaly
detection tools (e.g. Roughtime). Where those tools identify drift after
finalization, the hook here operates before the transition is committed.

See: https://eips.ethereum.org/EIPS/eip-1482 (15-second drift tolerance)
"""

from __future__ import annotations

from typing import Callable, Optional

from ethereum_types.numeric import U256

AttestationHook = Callable[[int], bool]
"""
A callable that receives a block timestamp (Unix seconds, as int) and
returns True if the timestamp is considered valid by an external source,
or False if it should be rejected.

The hook is called **before** the fork transition is applied. A return
value of False causes the block to be treated as invalid under the
transition logic of any caller that supplies the hook.

Implementations should:
- Be deterministic for the same input timestamp.
- Not introduce blocking network I/O in the hot path (use cached values).
- Fail open (return True) if the external source is unreachable, unless
  the caller explicitly requires fail-closed behaviour.
"""


def validate_transition_timestamp(
    block_timestamp: int,
    transition_ts: int,
    attestation_hook: Optional[AttestationHook] = None,
) -> bool:
    """
    Return True if block_timestamp clears both the numeric threshold and,
    when provided, the external attestation check.

    Parameters
    ----------
    block_timestamp:
        The Unix timestamp (seconds) from the block header.
    transition_ts:
        The minimum timestamp at which the fork activates.
    attestation_hook:
        Optional callable conforming to AttestationHook. When None, only
        the numeric comparison is performed (existing behaviour unchanged).

    Returns
    -------
    bool
        False if block_timestamp < transition_ts.
        False if attestation_hook is provided and returns False.
        True otherwise.
    """
    if block_timestamp < transition_ts:
        return False
    if attestation_hook is not None:
        return attestation_hook(block_timestamp)
    return True
