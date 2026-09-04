"""
Corruption catalog for EIP-7928 Block Access Lists.

Derives Correctness and Completeness corruption cases from a valid
``BlockAccessListExpectation``. Each case bundles:

  - a stable ``id`` for pytest parametrization,
  - a ``modifier`` that, when applied to the real t8n-produced BAL at
    fill time, yields a corrupted variant,
  - the ``expected_exception`` the client must raise on that variant.

The catalog is pure: it never touches a real BAL and has no side
effects. Higher-level nibbles wire these cases into pytest.

## ID format

::

    <address>__<change>__<field>__<bai>           - nonce, balance, code
    <address>__<change>__storage__<slot>__<bai>   - storage_write
    <address>__<change>__storage_read__<slot>     - storage_read (no bai)
    <address>__missing                            - account-level missing

``<address>`` is ``str(address)`` — the canonical 0x-prefixed lowercase
hex form. ``<slot>`` is the slot key as 0x-prefixed lowercase hex.
Using the address directly makes IDs independent of dict iteration
order. ``<change>`` is ``wrong`` (Correctness) or ``missing``
(Completeness).

## Cases

- ``wrong``   — XOR-flip an existing value (Correctness).
- ``missing`` — drop an existing entry or whole account (Completeness).
"""

from typing import Callable, List, NamedTuple

from execution_testing.base_types import Address, ZeroPaddedHexNumber
from execution_testing.exceptions import BlockException

from .expectations import BalAccountExpectation, BlockAccessListExpectation
from .modifiers import (
    modify_balance,
    modify_code,
    modify_nonce,
    modify_storage,
    remove_accounts,
)
from .t8n import BlockAccessList

Modifier = Callable[[BlockAccessList], BlockAccessList]


class CorruptionCase(NamedTuple):
    """
    One corruption derived from a valid BAL expectation.

    Fields
    ------
    id
        Stable string for pytest parametrization. See module docstring
        for the naming convention.
    modifier
        Callable that, applied to the real t8n-produced BAL at fill
        time, yields the corrupted variant.
    expected_exception
        The ``BlockException`` the client must raise when verifying the
        corrupted block.
    """

    id: str
    modifier: Modifier
    expected_exception: BlockException


_INVALID_BAL = BlockException.INVALID_BLOCK_ACCESS_LIST
_FLIP_MASK = 0xFF


def _flip(value: int) -> int:
    """XOR-flip an integer to guarantee a distinct value."""
    return value ^ _FLIP_MASK


def _flip_bytes(value: bytes) -> bytes:
    r"""XOR-flip the first byte of a bytes value, or return ``\\xff``."""
    if not value:
        return b"\xff"
    return bytes([value[0] ^ 0xFF]) + value[1:]


def _remove_change_at(address: Address, field_name: str, bai: int) -> Modifier:
    """Drop one change in ``field_name`` at the given block_access_index."""

    def transform(bal: BlockAccessList) -> BlockAccessList:
        new_root = []
        for ac in bal.root:
            if ac.address == address:
                new_ac = ac.model_copy(deep=True)
                old = getattr(new_ac, field_name)
                setattr(
                    new_ac,
                    field_name,
                    [c for c in old if int(c.block_access_index) != bai],
                )
                new_root.append(new_ac)
            else:
                new_root.append(ac)
        return BlockAccessList(root=new_root)

    return transform


def _remove_slot_change_at(address: Address, slot: int, bai: int) -> Modifier:
    """Drop one slot change in ``storage_changes[slot]`` at ``bai``."""

    def transform(bal: BlockAccessList) -> BlockAccessList:
        new_root = []
        for ac in bal.root:
            if ac.address == address:
                new_ac = ac.model_copy(deep=True)
                for storage_slot in new_ac.storage_changes:
                    if int(storage_slot.slot) == slot:
                        storage_slot.slot_changes = [
                            c
                            for c in storage_slot.slot_changes
                            if int(c.block_access_index) != bai
                        ]
                        break
                new_root.append(new_ac)
            else:
                new_root.append(ac)
        return BlockAccessList(root=new_root)

    return transform


def _remove_storage_read_at(address: Address, slot: int) -> Modifier:
    """Drop a storage_read entry by slot key."""

    def transform(bal: BlockAccessList) -> BlockAccessList:
        new_root = []
        for ac in bal.root:
            if ac.address == address:
                new_ac = ac.model_copy(deep=True)
                new_ac.storage_reads = [
                    s for s in new_ac.storage_reads if int(s) != slot
                ]
                new_root.append(new_ac)
            else:
                new_root.append(ac)
        return BlockAccessList(root=new_root)

    return transform


def _replace_storage_read_slot(
    address: Address, old_slot: int, new_slot: int
) -> Modifier:
    """Replace a storage_read's slot key with a flipped value."""

    def transform(bal: BlockAccessList) -> BlockAccessList:
        new_root = []
        for ac in bal.root:
            if ac.address == address:
                new_ac = ac.model_copy(deep=True)
                reads = list(new_ac.storage_reads)
                for i, s in enumerate(reads):
                    if int(s) == old_slot:
                        reads[i] = ZeroPaddedHexNumber(new_slot)
                        break
                new_ac.storage_reads = reads
                new_root.append(new_ac)
            else:
                new_root.append(ac)
        return BlockAccessList(root=new_root)

    return transform


def _account_cases(
    address: Address, account_exp: BalAccountExpectation
) -> List[CorruptionCase]:
    """Emit Correctness + Completeness cases for one account."""
    cases: List[CorruptionCase] = []
    addr = str(address)

    for nc in account_exp.nonce_changes:
        bai = int(nc.block_access_index)
        cases.append(
            CorruptionCase(
                id=f"{addr}__wrong__nonce__{bai}",
                modifier=modify_nonce(address, bai, _flip(int(nc.post_nonce))),
                expected_exception=_INVALID_BAL,
            )
        )
        cases.append(
            CorruptionCase(
                id=f"{addr}__missing__nonce__{bai}",
                modifier=_remove_change_at(address, "nonce_changes", bai),
                expected_exception=_INVALID_BAL,
            )
        )

    for bc in account_exp.balance_changes:
        bai = int(bc.block_access_index)
        cases.append(
            CorruptionCase(
                id=f"{addr}__wrong__balance__{bai}",
                modifier=modify_balance(
                    address, bai, _flip(int(bc.post_balance))
                ),
                expected_exception=_INVALID_BAL,
            )
        )
        cases.append(
            CorruptionCase(
                id=f"{addr}__missing__balance__{bai}",
                modifier=_remove_change_at(address, "balance_changes", bai),
                expected_exception=_INVALID_BAL,
            )
        )

    for cc in account_exp.code_changes:
        bai = int(cc.block_access_index)
        cases.append(
            CorruptionCase(
                id=f"{addr}__wrong__code__{bai}",
                modifier=modify_code(
                    address, bai, _flip_bytes(bytes(cc.new_code))
                ),
                expected_exception=_INVALID_BAL,
            )
        )
        cases.append(
            CorruptionCase(
                id=f"{addr}__missing__code__{bai}",
                modifier=_remove_change_at(address, "code_changes", bai),
                expected_exception=_INVALID_BAL,
            )
        )

    for ss in account_exp.storage_changes:
        slot = int(ss.slot)
        for sc in ss.slot_changes:
            bai = int(sc.block_access_index)
            cases.append(
                CorruptionCase(
                    id=f"{addr}__wrong__storage__{slot:#x}__{bai}",
                    modifier=modify_storage(
                        address, bai, slot, _flip(int(sc.post_value))
                    ),
                    expected_exception=_INVALID_BAL,
                )
            )
            cases.append(
                CorruptionCase(
                    id=f"{addr}__missing__storage__{slot:#x}__{bai}",
                    modifier=_remove_slot_change_at(address, slot, bai),
                    expected_exception=_INVALID_BAL,
                )
            )

    for sr in account_exp.storage_reads:
        slot = int.from_bytes(bytes(sr), "big")
        cases.append(
            CorruptionCase(
                id=f"{addr}__wrong__storage_read__{slot:#x}",
                modifier=_replace_storage_read_slot(
                    address, slot, _flip(slot)
                ),
                expected_exception=_INVALID_BAL,
            )
        )
        cases.append(
            CorruptionCase(
                id=f"{addr}__missing__storage_read__{slot:#x}",
                modifier=_remove_storage_read_at(address, slot),
                expected_exception=_INVALID_BAL,
            )
        )

    cases.append(
        CorruptionCase(
            id=f"{addr}__missing",
            modifier=remove_accounts(address),
            expected_exception=_INVALID_BAL,
        )
    )

    return cases


def enumerate_corruptions(
    expectation: BlockAccessListExpectation,
) -> List[CorruptionCase]:
    """
    Return every Correctness and Completeness case derivable from
    ``expectation``.

    See the module docstring for the ID format and the cases emitted.
    """
    cases: List[CorruptionCase] = []
    for address, account_exp in expectation.account_expectations.items():
        if account_exp is None:
            continue
        cases.extend(_account_cases(address, account_exp))
    return cases
