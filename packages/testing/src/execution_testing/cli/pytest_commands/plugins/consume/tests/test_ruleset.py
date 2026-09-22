"""Check Hive rulesets for synthetic and historical blob schedules."""

import pytest

from execution_testing.forks import (
    AmsterdamToBPOIncreaseAtTime15k,
    BPO2ToBPO3AtTime15k,
    BPO3ToBPO4AtTime15k,
    BPODecrease,
    BPOIncrease,
    BPOIncreaseToBPODecreaseAtTime15k,
    Fork,
    TransitionFork,
)

from ..simulators.helpers.ruleset import ruleset_format


@pytest.mark.parametrize("fork", [BPOIncrease, BPODecrease])
def test_bpo_genesis_ruleset(fork: Fork) -> None:
    """Activate Amsterdam and each synthetic ancestor at genesis."""
    rules = ruleset_format(fork)
    assert rules["HIVE_AMSTERDAM_TIMESTAMP"] == 0
    assert rules["HIVE_BPO_INCREASE_TIMESTAMP"] == 0
    assert rules["HIVE_BPO_INCREASE_BLOB_TARGET"] == 21
    assert rules["HIVE_BPO_INCREASE_BLOB_MAX"] == 32
    assert rules["HIVE_BPO_INCREASE_BLOB_BASE_FEE_UPDATE_FRACTION"] == 20609697
    if fork is BPODecrease:
        assert rules["HIVE_BPO_DECREASE_TIMESTAMP"] == 0
        assert rules["HIVE_BPO_DECREASE_BLOB_TARGET"] == 14
        assert rules["HIVE_BPO_DECREASE_BLOB_MAX"] == 21
        assert (
            rules["HIVE_BPO_DECREASE_BLOB_BASE_FEE_UPDATE_FRACTION"]
            == 13739630
        )
    else:
        assert "HIVE_BPO_DECREASE_TIMESTAMP" not in rules
    assert not any(key.startswith("HIVE_AMSTERDAM_BLOB_") for key in rules)
    assert "HIVE_BPO3_TIMESTAMP" not in rules
    assert "HIVE_BPO4_TIMESTAMP" not in rules


@pytest.mark.parametrize(
    "fork,prefix,ancestor",
    [
        (AmsterdamToBPOIncreaseAtTime15k, "BPO_INCREASE", "AMSTERDAM"),
        (BPOIncreaseToBPODecreaseAtTime15k, "BPO_DECREASE", "BPO_INCREASE"),
        (BPO2ToBPO3AtTime15k, "BPO3", "BPO2"),
        (BPO3ToBPO4AtTime15k, "BPO4", "BPO3"),
    ],
)
def test_bpo_transition_ruleset(
    fork: TransitionFork, prefix: str, ancestor: str
) -> None:
    """Schedule only the destination at the transition timestamp."""
    rules = ruleset_format(fork)
    assert rules[f"HIVE_{ancestor}_TIMESTAMP"] == 0
    assert rules[f"HIVE_{prefix}_TIMESTAMP"] == 15_000
