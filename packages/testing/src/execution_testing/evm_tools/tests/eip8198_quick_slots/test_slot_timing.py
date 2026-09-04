"""Tests that EIP-8198 duration changes are schedule-driven."""

import inspect
from dataclasses import replace

import pytest
from ethereum.crypto.hash import Hash32, keccak256
from ethereum.exceptions import InvalidBlock
from ethereum.forks.amsterdam import fork as amsterdam_fork
from ethereum.forks.amsterdam.blocks import Header
from ethereum.forks.amsterdam.fork import (
    EMPTY_OMMER_HASH,
    calculate_base_fee_per_gas,
    validate_header,
)
from ethereum.forks.amsterdam.fork_types import Bloom
from ethereum.forks.amsterdam.slot_timing import (
    BLOB_GAS_PER_BLOB,
    BlobScheduleParameters,
    SlotDurationEntry,
    calculate_blob_gas_price_for_slot,
    get_blob_schedule,
    get_max_blob_gas_per_block,
    get_slot_duration_ms,
    get_transition_durations,
    scale_blob_schedule,
    scale_transition_limit,
)
from ethereum.state import Address, Root
from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes, Bytes8, Bytes32
from ethereum_types.numeric import U64, U256, Uint

HEGOTA_EPOCH = U64(10)
FUTURE_TEST_EPOCH = U64(20)
SCHEDULE_12_10_6 = (
    SlotDurationEntry(HEGOTA_EPOCH, Uint(10000)),
    SlotDurationEntry(FUTURE_TEST_EPOCH, Uint(6000)),
)
ZERO_ROOT = Root(b"\x00" * 32)
ZERO_HASH = Hash32(b"\x00" * 32)


def _header(
    *,
    slot_number: U64,
    number: Uint,
    gas_limit: Uint,
    gas_used: Uint,
    base_fee_per_gas: Uint,
    timestamp: U256,
) -> Header:
    """Build a minimal Amsterdam header for duration-transition tests."""
    return Header(
        parent_hash=ZERO_HASH,
        ommers_hash=EMPTY_OMMER_HASH,
        coinbase=Address(b"\x00" * 20),
        state_root=ZERO_ROOT,
        transactions_root=ZERO_ROOT,
        receipt_root=ZERO_ROOT,
        bloom=Bloom(b"\x00" * 256),
        difficulty=Uint(0),
        number=number,
        gas_limit=gas_limit,
        gas_used=gas_used,
        timestamp=timestamp,
        extra_data=Bytes(b""),
        prev_randao=Bytes32(b"\x00" * 32),
        nonce=Bytes8(b"\x00" * 8),
        base_fee_per_gas=base_fee_per_gas,
        withdrawals_root=ZERO_ROOT,
        blob_gas_used=U64(0),
        excess_blob_gas=U64(0),
        parent_beacon_block_root=ZERO_ROOT,
        requests_hash=ZERO_HASH,
        block_access_list_hash=ZERO_HASH,
        slot_number=slot_number,
    )


def test_repeated_duration_changes_are_schedule_only() -> None:
    """A synthetic 10 -> 6 era uses the same lookup as 12 -> 10."""
    last_12s_slot = U64(HEGOTA_EPOCH * U64(32) - U64(1))
    first_10s_slot = U64(HEGOTA_EPOCH * U64(32))
    last_10s_slot = U64(FUTURE_TEST_EPOCH * U64(32) - U64(1))
    first_6s_slot = U64(FUTURE_TEST_EPOCH * U64(32))

    assert get_slot_duration_ms(last_12s_slot, SCHEDULE_12_10_6) == Uint(12000)
    assert get_slot_duration_ms(first_10s_slot, SCHEDULE_12_10_6) == Uint(
        10000
    )
    assert get_slot_duration_ms(last_10s_slot, SCHEDULE_12_10_6) == Uint(10000)
    assert get_slot_duration_ms(first_6s_slot, SCHEDULE_12_10_6) == Uint(6000)


def test_gas_limit_scales_once_at_each_duration_boundary() -> None:
    """Gas/sec is preserved at both 12 -> 10 and 10 -> 6 transitions."""
    first_10s_slot = U64(HEGOTA_EPOCH * U64(32))
    first_6s_slot = U64(FUTURE_TEST_EPOCH * U64(32))
    last_10s_payload_slot = U64(first_6s_slot - U64(7))

    old_ms, new_ms = get_transition_durations(
        None, first_10s_slot, SCHEDULE_12_10_6
    )
    gas_limit_10s = scale_transition_limit(Uint(72_000_000), old_ms, new_ms)
    assert (old_ms, new_ms) == (Uint(12000), Uint(10000))
    assert gas_limit_10s == Uint(60_000_000)

    old_ms, new_ms = get_transition_durations(
        last_10s_payload_slot,
        U64(first_6s_slot + U64(7)),
        SCHEDULE_12_10_6,
    )
    gas_limit_6s = scale_transition_limit(gas_limit_10s, old_ms, new_ms)
    assert (old_ms, new_ms) == (Uint(10000), Uint(6000))
    assert gas_limit_6s == Uint(36_000_000)

    old_ms, new_ms = get_transition_durations(
        U64(first_6s_slot + U64(7)),
        U64(first_6s_slot + U64(19)),
        SCHEDULE_12_10_6,
    )
    assert scale_transition_limit(gas_limit_6s, old_ms, new_ms) == gas_limit_6s


def test_validate_header_handles_missed_payloads_at_second_boundary() -> None:
    """
    Validate the production header path across a synthetic 10 -> 6 change.

    The parent execution payload is seven slots before the boundary and the
    child payload is seven slots after it. The duration transition must still
    scale the gas limit exactly once, even though no payload exists at the
    scheduled boundary slot.
    """
    first_6s_slot = U64(FUTURE_TEST_EPOCH * U64(32))
    parent = _header(
        slot_number=U64(first_6s_slot - U64(7)),
        number=Uint(100),
        gas_limit=Uint(60_000_000),
        gas_used=Uint(30_000_000),
        base_fee_per_gas=Uint(960),
        timestamp=U256(1_000_000),
    )
    transition = _header(
        slot_number=U64(first_6s_slot + U64(7)),
        number=Uint(101),
        gas_limit=Uint(36_000_000),
        gas_used=Uint(18_000_000),
        base_fee_per_gas=Uint(960),
        timestamp=U256(1_000_006),
    )
    transition = replace(
        transition,
        parent_hash=keccak256(rlp.encode(parent)),
    )

    validate_header(parent, transition, SCHEDULE_12_10_6)

    unscaled = replace(transition, gas_limit=Uint(60_000_000))
    with pytest.raises(InvalidBlock):
        validate_header(parent, unscaled, SCHEDULE_12_10_6)

    ordinary_6s = _header(
        slot_number=U64(first_6s_slot + U64(19)),
        number=Uint(102),
        gas_limit=Uint(36_000_000),
        gas_used=Uint(18_000_000),
        base_fee_per_gas=Uint(960),
        timestamp=U256(1_000_012),
    )
    ordinary_6s = replace(
        ordinary_6s,
        parent_hash=keccak256(rlp.encode(transition)),
    )
    validate_header(transition, ordinary_6s, SCHEDULE_12_10_6)


def test_production_base_fee_path_supports_second_era() -> None:
    """Amsterdam's real base-fee calculator remains wall-clock invariant."""
    common = dict(
        block_gas_limit=Uint(60_000_000),
        parent_gas_limit=Uint(60_000_000),
        parent_gas_used=Uint(60_000_000),
        parent_base_fee_per_gas=Uint(960),
        gas_limit_reference=Uint(60_000_000),
    )

    fee_10s = calculate_base_fee_per_gas(
        **common,
        slot_duration_ms=Uint(10000),
    )
    fee_6s = calculate_base_fee_per_gas(
        **common,
        slot_duration_ms=Uint(6000),
    )

    assert fee_10s == Uint(1060)
    assert fee_6s == Uint(1020)


def test_blob_schedule_derives_repeated_eras_from_same_transition() -> None:
    """Blob throughput and fee response derive through 12 -> 10 -> 6."""
    blob_12s = BlobScheduleParameters(
        maximum=U64(21),
        target=U64(14),
        update_fraction=Uint(11_684_671),
    )

    blob_10s = scale_blob_schedule(blob_12s, Uint(12000), Uint(10000))
    assert blob_10s == BlobScheduleParameters(
        maximum=U64(17),
        target=U64(12),
        update_fraction=Uint(10_015_432),
    )

    blob_6s = scale_blob_schedule(blob_10s, Uint(10000), Uint(6000))
    assert blob_6s == BlobScheduleParameters(
        maximum=U64(10),
        target=U64(7),
        update_fraction=Uint(10_015_432),
    )


def test_production_blob_paths_follow_same_schedule() -> None:
    """Capacity and blob-fee inputs both follow the synthetic 6s era."""
    first_10s_slot = U64(HEGOTA_EPOCH * U64(32))
    first_6s_slot = U64(FUTURE_TEST_EPOCH * U64(32))

    blob_10s = get_blob_schedule(first_10s_slot, SCHEDULE_12_10_6)
    blob_6s = get_blob_schedule(first_6s_slot, SCHEDULE_12_10_6)
    assert blob_10s.maximum == U64(17)
    assert blob_6s.maximum == U64(10)
    assert blob_10s.target == U64(12)
    assert blob_6s.target == U64(7)
    # For this exact 10s -> 6s ratio the derived update fraction is unchanged.
    # That is valid: the reduced per-block headroom and shorter cadence cancel.
    assert blob_6s.update_fraction == blob_10s.update_fraction

    assert get_max_blob_gas_per_block(
        first_10s_slot, SCHEDULE_12_10_6
    ) == BLOB_GAS_PER_BLOB * U64(17)
    assert get_max_blob_gas_per_block(
        first_6s_slot, SCHEDULE_12_10_6
    ) == BLOB_GAS_PER_BLOB * U64(10)

    excess = U64(20_000_000)
    fee_10s = calculate_blob_gas_price_for_slot(
        excess, first_10s_slot, SCHEDULE_12_10_6
    )
    fee_6s = calculate_blob_gas_price_for_slot(
        excess, first_6s_slot, SCHEDULE_12_10_6
    )
    assert fee_10s == Uint(7)
    assert fee_6s == Uint(7)


def test_amsterdam_has_no_12_to_10_transition_special_case() -> None:
    """The production header path contains no previous-duration constant."""
    source = inspect.getsource(amsterdam_fork)
    assert "PREVIOUS_SLOT_DURATION_MS" not in source
    assert "SLOT_DURATION_MS = Uint(10000)" not in source
    assert "get_transition_durations" in source
    assert "scale_transition_limit" in source
