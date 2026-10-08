"""Helpers for EIP-8272 recent root tests."""

from typing import Any, Dict, Sequence

from execution_testing import Fork, Frame, Op

from ..eip8141_frame_transactions.spec import Spec as FrameSpec
from .spec import Spec

WRITE_STATE_GAS = 200_000
"""
State gas budget of a frame publishing a root: a fresh recent root entry
is one storage set, with headroom.
"""

VALIDATION_FIXED_GAS = 119
"""
Execution gas of the validation operation outside the tuple loop: the
value check, the calldata length dispatch and the three length checks,
reading the current slot and the loop offset, and the first tuple's
memory expansion to the four words its entry preimage occupies.
"""

VALIDATION_TUPLE_GAS = 296
"""
Execution gas of one tuple's successful path through the validation
loop, excluding its storage read: decoding the slot, the two slot
checks, hashing the entry preimage and the storage key preimage, the
comparison and the loop step. Measured against `RECENT_ROOT_CODE` and
confirmed by counting its assembly; re-derive both constants if the
canonical code changes.
"""


def validation_gas(
    fork: Fork, *, tuples: int, cold_keys: int, target_warm: bool = False
) -> int:
    """
    Return the execution gas a recent root verifier frame reports for
    `tuples` references of which `cold_keys` read distinct storage keys
    for the first time in the transaction.

    The frame charges its target's access at entry, then the contract's
    fixed cost, its per-tuple cost, and one warm or cold storage read
    per tuple.
    """
    warm_keys = tuples - cold_keys
    return (
        fork.frame_entry_gas_calculator()(target_warm=target_warm)
        + VALIDATION_FIXED_GAS
        + tuples * VALIDATION_TUPLE_GAS
        + cold_keys
        * Op.SLOAD.with_metadata(key_warm=False).execution_cost(fork)
        + warm_keys
        * Op.SLOAD.with_metadata(key_warm=True).execution_cost(fork)
    )


def recent_root_frame(
    references: Sequence[bytes] | bytes, **overrides: Any
) -> Frame:
    """
    Return a recent root verifier frame: a `VERIFY` frame targeting the
    recent root contract with no flags, no value, no state gas and the
    concatenated validation tuples as data.

    Keyword arguments override the corresponding frame fields, for
    variants that differ from the canonical frame in a single field.
    """
    data = (
        bytes(references)
        if isinstance(references, (bytes, bytearray))
        else b"".join(references)
    )
    kwargs: Dict[str, Any] = dict(
        mode=FrameSpec.MODE_VERIFY,
        flags=FrameSpec.APPROVE_NONE,
        target=Spec.RECENT_ROOT_ADDRESS,
        state_gas_limit=0,
        data=data,
    )
    kwargs.update(overrides)
    return Frame(**kwargs)


def write_frame(salt: bytes, root: bytes, **overrides: Any) -> Frame:
    """
    Return a `SENDER` frame publishing `root` under `salt` for the
    transaction sender: it calls the recent root contract with the 64-byte
    write encoding and a state gas budget covering the entry's creation.

    Keyword arguments override the corresponding frame fields.
    """
    kwargs: Dict[str, Any] = dict(
        mode=FrameSpec.MODE_SENDER,
        target=Spec.RECENT_ROOT_ADDRESS,
        state_gas_limit=WRITE_STATE_GAS,
        data=bytes(salt) + bytes(root),
    )
    kwargs.update(overrides)
    return Frame(**kwargs)
