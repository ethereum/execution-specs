"""
Test that an environment sheds the fields a fork's header lacks.
"""

import pytest

from execution_testing.forks import Amsterdam, Fork, Istanbul, Paris

from ..block_types import Environment

PINNED = Environment(
    prev_randao=0x20000,
    base_fee_per_gas=10,
    excess_blob_gas=0,
    slot_number=7,
)


@pytest.mark.parametrize(
    "fork,dropped",
    [
        pytest.param(
            Istanbul,
            {
                "currentRandom",
                "currentBaseFee",
                "currentExcessBlobGas",
                "slotNumber",
            },
            id="istanbul",
        ),
        pytest.param(
            Paris,
            {"currentExcessBlobGas", "slotNumber"},
            id="paris",
        ),
        pytest.param(Amsterdam, set(), id="amsterdam"),
    ],
)
def test_without_fork_ignored_fields(fork: Fork, dropped: set) -> None:
    """Pinned fields the fork's header lacks must not serialize."""
    env = PINNED.set_fork_requirements(fork).without_fork_ignored_fields(fork)
    keys = env.model_dump(mode="json", by_alias=True, exclude_none=True).keys()
    assert dropped.isdisjoint(keys)
    kept = {
        "currentRandom",
        "currentBaseFee",
        "currentExcessBlobGas",
        "slotNumber",
    } - dropped
    assert kept <= keys
