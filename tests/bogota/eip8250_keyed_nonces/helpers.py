"""Helpers for EIP-8250 keyed nonce tests."""

from typing import Sequence

from ethereum_rlp import rlp
from ethereum_types.numeric import U256
from execution_testing import Account, Alloc, Fork, Op, Transaction

from .spec import Spec, keyed_nonce_slot

NONCE_KEY = 0xBEEF
"""A nonce key selecting a keyed domain."""

OTHER_KEY = 0xCAFE
"""A second nonce key, disjoint from `NONCE_KEY`."""


def keyed_nonce_first_use(fork: Fork) -> int:
    """
    Return the state gas of a keyed nonce slot's first use, which the
    EIP prices as one storage slot creation.
    """
    return Op.SSTORE(original_value=0, new_value=1).state_cost(fork)


def nonce_field_calldata(nonce_keys: Sequence[int], nonce_seq: int) -> bytes:
    """
    Return the encoding of the nonce fields the EIP prices as transaction
    data. A keyed single-use sequence is encoded and signed but exempt
    from data pricing.
    """
    priced_sequence = (
        b""
        if nonce_keys and nonce_seq == Spec.MAX_NONCE_SEQ
        else rlp.encode(U256(nonce_seq))
    )
    return rlp.encode([U256(key) for key in nonce_keys]) + priced_sequence


def keyed_nonce_access_cost(fork: Fork, nonce_keys: Sequence[int]) -> int:
    """
    Return the EIP's `keyed_nonce_access_cost`, which prices each key as
    an `SSTORE` changing a cold slot. The empty key set pays nothing.
    """
    per_key = Op.SSTORE(key_warm=False, original_value=1, new_value=2)
    return len(nonce_keys) * per_key.execution_cost(fork)


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
    frame_gas = fork.frame_entry_gas_calculator()(target_warm=True)
    execution_used = intrinsic + len(tx.frames) * frame_gas
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
