"""
Slot-duration schedule helpers for EIP-8198.

The execution layer needs two distinct duration ratios:

* transition ratios compare the current execution payload's duration with
  its parent execution payload's duration and apply once at an era boundary;
* wall-clock response ratios compare the current duration with the
  pre-schedule base duration and apply to every block in the era.

Keeping these operations separate prevents a second slot-duration change
from accidentally reusing the one-off transition ratio as an ongoing rate.
"""

from dataclasses import dataclass
from typing import Final, Optional, Tuple, final

from ethereum_types.numeric import U64, Uint

from ethereum.utils.numeric import taylor_exponential

BASE_SLOT_DURATION_MS: Final[Uint] = Uint(12000)
"""Pre-schedule slot duration, in milliseconds."""

SLOTS_PER_EPOCH: Final[U64] = U64(32)
"""Number of slots per epoch; EIP-8198 does not change this value."""

BLOB_GAS_PER_BLOB: Final[U64] = U64(2**17)
BLOB_BASE_COST: Final[Uint] = Uint(2**13)
BLOB_MIN_GASPRICE: Final[Uint] = Uint(1)


@final
@dataclass(frozen=True)
class SlotDurationEntry:
    """One slot-duration schedule entry."""

    epoch: U64
    duration_ms: Uint


SlotDurationSchedule = Tuple[SlotDurationEntry, ...]


# The epoch-zero entry is an always-active initial Amsterdam duration when this
# fork package executes. Additional entries use consensus epoch numbers derived
# from Header.slot_number. A future duration change is therefore schedule data;
# protocol logic does not change.
SLOT_DURATION_SCHEDULE: Final[SlotDurationSchedule] = (
    SlotDurationEntry(U64(0), Uint(10000)),
)


@final
@dataclass(frozen=True)
class BlobScheduleParameters:
    """Blob parameters coupled to one slot-duration era."""

    maximum: U64
    target: U64
    update_fraction: Uint


BASE_BLOB_SCHEDULE: Final[BlobScheduleParameters] = BlobScheduleParameters(
    maximum=U64(21),
    target=U64(14),
    update_fraction=Uint(11_684_671),
)
"""Blob schedule in force before EIP-8198 activates."""


def validate_slot_duration_schedule(schedule: SlotDurationSchedule) -> None:
    """Validate ordering and duration constraints of a duration schedule."""
    previous_epoch: Optional[U64] = None
    for entry in schedule:
        if entry.duration_ms == 0 or entry.duration_ms % Uint(1000) != 0:
            raise ValueError("slot duration must be a positive whole second")
        if previous_epoch is not None and entry.epoch <= previous_epoch:
            raise ValueError(
                "slot duration epochs must be strictly increasing"
            )
        previous_epoch = entry.epoch


def get_slot_duration_ms(
    slot_number: U64,
    schedule: SlotDurationSchedule = SLOT_DURATION_SCHEDULE,
    base_duration_ms: Uint = BASE_SLOT_DURATION_MS,
    slots_per_epoch: U64 = SLOTS_PER_EPOCH,
) -> Uint:
    """Return the scheduled duration in effect for ``slot_number``."""
    validate_slot_duration_schedule(schedule)
    if base_duration_ms == 0 or slots_per_epoch == 0:
        raise ValueError("base duration and slots per epoch must be positive")

    epoch = slot_number // slots_per_epoch
    duration_ms = base_duration_ms
    for entry in schedule:
        if epoch < entry.epoch:
            break
        duration_ms = entry.duration_ms
    return duration_ms


def get_transition_durations(
    parent_slot_number: Optional[U64],
    current_slot_number: U64,
    schedule: SlotDurationSchedule = SLOT_DURATION_SCHEDULE,
    base_duration_ms: Uint = BASE_SLOT_DURATION_MS,
) -> Tuple[Uint, Uint]:
    """
    Return parent/current execution-payload durations.

    ``None`` represents the legacy parent at the first EIP-8198 execution
    payload. Future transitions use the parent execution payload's actual
    slot, so missed slots and withheld payloads cannot suppress the change.
    """
    new_duration_ms = get_slot_duration_ms(
        current_slot_number, schedule, base_duration_ms
    )
    if parent_slot_number is None:
        old_duration_ms = base_duration_ms
    else:
        old_duration_ms = get_slot_duration_ms(
            parent_slot_number, schedule, base_duration_ms
        )
    return old_duration_ms, new_duration_ms


def scale_transition_limit(
    value: Uint, old_duration_ms: Uint, new_duration_ms: Uint
) -> Uint:
    """Scale a per-block capacity once when the duration era changes."""
    if old_duration_ms == 0 or new_duration_ms == 0:
        raise ValueError("slot durations must be positive")
    if old_duration_ms == new_duration_ms:
        return value
    return Uint(value * new_duration_ms // old_duration_ms)


def scale_blob_schedule(
    previous: BlobScheduleParameters,
    old_duration_ms: Uint,
    new_duration_ms: Uint,
) -> BlobScheduleParameters:
    """
    Derive blob parameters for the next duration era.

    Maximum blob count truncates down, target blob count rounds to nearest,
    and the update fraction preserves maximum sustained blob-fee response
    per unit of wall-clock time.
    """
    if old_duration_ms == 0 or new_duration_ms == 0:
        raise ValueError("slot durations must be positive")
    if previous.maximum <= previous.target:
        raise ValueError("blob maximum must exceed blob target")

    maximum = U64(Uint(previous.maximum) * new_duration_ms // old_duration_ms)
    target = U64(
        (Uint(previous.target) * new_duration_ms + old_duration_ms // Uint(2))
        // old_duration_ms
    )
    if maximum <= target:
        raise ValueError("scaled blob maximum must exceed scaled target")

    old_headroom = Uint(previous.maximum - previous.target)
    new_headroom = Uint(maximum - target)
    update_fraction = Uint(
        previous.update_fraction
        * new_headroom
        * old_duration_ms
        // (old_headroom * new_duration_ms)
    )
    return BlobScheduleParameters(maximum, target, update_fraction)


def get_blob_schedule(
    slot_number: U64,
    schedule: SlotDurationSchedule = SLOT_DURATION_SCHEDULE,
    base_duration_ms: Uint = BASE_SLOT_DURATION_MS,
    base_blob_schedule: BlobScheduleParameters = BASE_BLOB_SCHEDULE,
) -> BlobScheduleParameters:
    """Return blob parameters derived through every active duration era."""
    validate_slot_duration_schedule(schedule)
    current_epoch = slot_number // SLOTS_PER_EPOCH
    duration_ms = base_duration_ms
    blob_schedule = base_blob_schedule

    for entry in schedule:
        if current_epoch < entry.epoch:
            break
        if entry.duration_ms != duration_ms:
            blob_schedule = scale_blob_schedule(
                blob_schedule, duration_ms, entry.duration_ms
            )
            duration_ms = entry.duration_ms

    return blob_schedule


def get_max_blob_gas_per_block(
    slot_number: U64,
    schedule: SlotDurationSchedule = SLOT_DURATION_SCHEDULE,
) -> U64:
    """Return blob gas capacity for the active duration era."""
    return BLOB_GAS_PER_BLOB * get_blob_schedule(slot_number, schedule).maximum


def calculate_blob_gas_price_for_slot(
    excess_blob_gas: U64,
    slot_number: U64,
    schedule: SlotDurationSchedule = SLOT_DURATION_SCHEDULE,
) -> Uint:
    """Calculate the blob gas price using the current duration era."""
    blob_schedule = get_blob_schedule(slot_number, schedule)
    return taylor_exponential(
        BLOB_MIN_GASPRICE,
        Uint(excess_blob_gas),
        blob_schedule.update_fraction,
    )
