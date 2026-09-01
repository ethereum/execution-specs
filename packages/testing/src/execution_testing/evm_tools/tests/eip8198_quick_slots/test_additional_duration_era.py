"""Extra synthetic era proving EIP-8198 logic is duration-agnostic."""

from ethereum.forks.amsterdam.slot_timing import (
    BlobScheduleParameters,
    SlotDurationEntry,
    get_blob_schedule,
    get_slot_duration_ms,
    get_transition_durations,
    scale_transition_limit,
)
from ethereum_types.numeric import U64, Uint

HEGOTA_EPOCH = U64(10)
MID_TEST_EPOCH = U64(15)
FUTURE_TEST_EPOCH = U64(20)
SLOTS_PER_EPOCH = U64(32)

SCHEDULE_12_10_8_6 = (
    SlotDurationEntry(HEGOTA_EPOCH, Uint(10000)),
    SlotDurationEntry(MID_TEST_EPOCH, Uint(8000)),
    SlotDurationEntry(FUTURE_TEST_EPOCH, Uint(6000)),
)


def test_additional_8s_era_is_schedule_data_only() -> None:
    """A 10 -> 8 -> 6 sequence uses the same duration lookup path."""
    first_10s_slot = U64(HEGOTA_EPOCH * SLOTS_PER_EPOCH)
    first_8s_slot = U64(MID_TEST_EPOCH * SLOTS_PER_EPOCH)
    first_6s_slot = U64(FUTURE_TEST_EPOCH * SLOTS_PER_EPOCH)

    assert get_slot_duration_ms(
        U64(first_10s_slot - U64(1)), SCHEDULE_12_10_8_6
    ) == Uint(12000)
    assert get_slot_duration_ms(first_10s_slot, SCHEDULE_12_10_8_6) == Uint(
        10000
    )
    assert get_slot_duration_ms(first_8s_slot, SCHEDULE_12_10_8_6) == Uint(
        8000
    )
    assert get_slot_duration_ms(first_6s_slot, SCHEDULE_12_10_8_6) == Uint(
        6000
    )


def test_capacity_scaling_composes_through_8s_era() -> None:
    """Gas/sec remains constant through 12 -> 10 -> 8 -> 6."""
    first_10s_slot = U64(HEGOTA_EPOCH * SLOTS_PER_EPOCH)
    first_8s_slot = U64(MID_TEST_EPOCH * SLOTS_PER_EPOCH)
    first_6s_slot = U64(FUTURE_TEST_EPOCH * SLOTS_PER_EPOCH)

    old_ms, new_ms = get_transition_durations(
        None, first_10s_slot, SCHEDULE_12_10_8_6
    )
    gas_10s = scale_transition_limit(Uint(72_000_000), old_ms, new_ms)
    assert (old_ms, new_ms, gas_10s) == (
        Uint(12000),
        Uint(10000),
        Uint(60_000_000),
    )

    old_ms, new_ms = get_transition_durations(
        U64(first_8s_slot - U64(7)),
        U64(first_8s_slot + U64(7)),
        SCHEDULE_12_10_8_6,
    )
    gas_8s = scale_transition_limit(gas_10s, old_ms, new_ms)
    assert (old_ms, new_ms, gas_8s) == (
        Uint(10000),
        Uint(8000),
        Uint(48_000_000),
    )

    old_ms, new_ms = get_transition_durations(
        U64(first_6s_slot - U64(7)),
        U64(first_6s_slot + U64(7)),
        SCHEDULE_12_10_8_6,
    )
    gas_6s = scale_transition_limit(gas_8s, old_ms, new_ms)
    assert (old_ms, new_ms, gas_6s) == (
        Uint(8000),
        Uint(6000),
        Uint(36_000_000),
    )


def test_blob_schedule_composes_through_8s_era() -> None:
    """Derive blob parameters through the added era without a new branch."""
    first_8s_slot = U64(MID_TEST_EPOCH * SLOTS_PER_EPOCH)
    first_6s_slot = U64(FUTURE_TEST_EPOCH * SLOTS_PER_EPOCH)

    blob_8s = get_blob_schedule(first_8s_slot, SCHEDULE_12_10_8_6)
    blob_6s = get_blob_schedule(first_6s_slot, SCHEDULE_12_10_8_6)

    assert blob_8s == BlobScheduleParameters(
        maximum=U64(13),
        target=U64(10),
        update_fraction=Uint(7_511_574),
    )
    assert blob_6s == BlobScheduleParameters(
        maximum=U64(9),
        target=U64(8),
        update_fraction=Uint(3_338_477),
    )
