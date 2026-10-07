"""Helpers for EIP-8250 keyed nonce tests."""

from typing import Sequence

from execution_testing import Account, Alloc, Fork, Op, Transaction

from ..eip8141_frame_transactions.helpers import default_code_frame_gas
from .spec import Spec, keyed_nonce_slot

NONCE_KEY = 0xBEEF
"""A non-zero nonce key selecting a keyed domain."""

OTHER_KEY = 0xCAFE
"""A second non-zero nonce key, disjoint from `NONCE_KEY`."""


def keyed_nonce_first_use(fork: Fork) -> int:
    """
    Return the state gas of a keyed nonce slot's first use, which the
    EIP prices as one storage slot creation.
    """
    return Op.SSTORE(original_value=0, new_value=1).state_cost(fork)


def nonce_fields(tx: Transaction) -> tuple[Sequence[int], int]:
    """Return the transaction's nonce keys and sequence as integers."""
    assert tx.nonce_keys is not None
    return [int(key) for key in tx.nonce_keys], int(tx.nonce)


def verify_only_tx_gas_used(
    fork: Fork, tx: Transaction, first_uses: int
) -> int:
    """
    Return the gas used by a transaction of default-code `VERIFY` frames
    resolving to its sender, with `first_uses` keyed slots created.
    """
    tx.sign()
    assert tx.frames is not None and tx.signatures is not None
    nonce_keys, nonce_seq = nonce_fields(tx)
    intrinsic = fork.frame_transaction_intrinsic_cost_calculator()(
        frames=tx.frames,
        signatures=tx.signatures,
        sender=tx.sender,
        nonce_keys=nonce_keys,
        nonce_seq=nonce_seq,
        return_cost_deducted_prior_execution=True,
    )
    floor = fork.frame_transaction_data_floor_cost_calculator()(
        frames=tx.frames,
        signatures=tx.signatures,
        sender=tx.sender,
        nonce_keys=nonce_keys,
        nonce_seq=nonce_seq,
    )
    execution_used = intrinsic + len(tx.frames) * default_code_frame_gas(
        fork, target_warm=True
    )
    state_used = first_uses * keyed_nonce_first_use(fork)
    return max(execution_used, floor) + state_used


def nonce_manager_with_slots(pre: Alloc, slots: dict[int, int]) -> None:
    """
    Seed the nonce manager's storage in the pre-state, keeping its
    deployed code and nonce. The test must be `pre_alloc_mutable`.
    """
    pre[Spec.NONCE_MANAGER] = Account(
        nonce=Spec.NONCE_MANAGER_NONCE,
        code=Spec.NONCE_MANAGER_CODE,
        storage=slots,
    )


def used_key_slots(
    sender: Account | bytes, keys_to_seq: dict[int, int]
) -> dict[int, int]:
    """Return the nonce manager slots holding `sender`'s key sequences."""
    return {
        keyed_nonce_slot(sender, key): seq  # type: ignore[arg-type]
        for key, seq in keys_to_seq.items()
    }
