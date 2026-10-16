"""Tests for Hive ruleset compatibility across fork transitions."""

import pytest

from execution_testing.forks import (
    Amsterdam,
    AmsterdamToBogotaAtTime15k,
    Bogota,
    BPO2ToAmsterdamAtTime15k,
    Fork,
    TransitionFork,
)

from ..simulators.helpers.ruleset import ruleset_format


@pytest.mark.parametrize(
    "fork,amsterdam_timestamp,bogota_timestamp",
    [
        (Amsterdam, 0, None),
        (BPO2ToAmsterdamAtTime15k, 15_000, None),
        (Bogota, 0, 0),
        (AmsterdamToBogotaAtTime15k, 0, 15_000),
    ],
)
def test_amsterdam_blob_compatibility(
    fork: Fork | TransitionFork,
    amsterdam_timestamp: int,
    bogota_timestamp: int | None,
) -> None:
    """Omit Amsterdam blob overrides while retaining fork activation times."""
    entries = ruleset_format(fork)

    assert entries["HIVE_AMSTERDAM_TIMESTAMP"] == amsterdam_timestamp
    assert entries.get("HIVE_BOGOTA_TIMESTAMP") == bogota_timestamp
    for suffix in ("TARGET", "MAX", "BASE_FEE_UPDATE_FRACTION"):
        assert f"HIVE_AMSTERDAM_BLOB_{suffix}" not in entries
        # Keep the inherited BPO schedule and any Bogota-specific settings.
        for prefix in ("HIVE_BPO2_BLOB_", "HIVE_BOGOTA_BLOB_"):
            key = prefix + suffix
            assert entries.get(key) == fork.ruleset().get(key)
