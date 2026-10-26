"""Check Hive rulesets across fork transitions and blob schedules."""

from typing import List

import pytest
from _pytest.mark.structures import ParameterSet

from execution_testing.forks import (
    BPO_SCENARIOS,
    Amsterdam,
    AmsterdamToBogotaAtTime15k,
    Bogota,
    BPO2ToAmsterdamAtTime15k,
    BPO2ToBPO3AtTime15k,
    BPO3ToBPO4AtTime15k,
    Fork,
    TransitionFork,
    transition_fork_from_to,
)
from execution_testing.forks.forks.forks import first_free_bpo_slot

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


def bpo_scenario_transitions() -> List[ParameterSet]:
    """Return each transition into a BPO scenario with its ruleset names."""
    transitions = []
    for fork, scenarios in BPO_SCENARIOS.items():
        for scenario in scenarios:
            transition = transition_fork_from_to(fork, scenario)
            assert transition is not None
            transitions.append(
                pytest.param(
                    transition,
                    scenario.ruleset_name(),
                    fork.ruleset_name(),
                    id=transition.name(),
                )
            )
    return transitions


@pytest.mark.parametrize(
    "fork", list(BPO_SCENARIOS), ids=lambda fork: fork.name()
)
def test_bpo_scenario_genesis_ruleset(fork: Fork) -> None:
    """Activate each BPO scenario at genesis in the next client slot."""
    slot = first_free_bpo_slot(fork)
    prefix = f"HIVE_BPO{slot}"
    for scenario in BPO_SCENARIOS[fork]:
        assert scenario.ruleset_name() == f"BPO{slot}"
        rules = ruleset_format(scenario)
        assert rules[f"HIVE_{fork.ruleset_name()}_TIMESTAMP"] == 0
        assert rules[f"{prefix}_TIMESTAMP"] == 0
        assert (
            rules[f"{prefix}_BLOB_TARGET"] == scenario.target_blobs_per_block()
        )
        assert rules[f"{prefix}_BLOB_MAX"] == scenario.max_blobs_per_block()
        assert (
            rules[f"{prefix}_BLOB_BASE_FEE_UPDATE_FRACTION"]
            == scenario.blob_base_fee_update_fraction()
        )
        assert f"HIVE_BPO{slot + 1}_TIMESTAMP" not in rules
        assert not any(key.startswith("HIVE_AMSTERDAM_BLOB_") for key in rules)


@pytest.mark.parametrize(
    "fork,prefix,ancestor",
    [
        *bpo_scenario_transitions(),
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
