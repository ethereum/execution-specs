"""Fork rules for consume hive simulators."""

from typing import Dict

from execution_testing.forks import (
    ALL_FORKS_WITH_TRANSITIONS,
    Amsterdam,
    Fork,
    London,
    TangerineWhistle,
    TransitionFork,
)


def ruleset_format(fork: Fork | TransitionFork) -> Dict[str, int]:
    """Format the ruleset for backwards compatibility."""
    default_values: Dict[str, int] = dict.fromkeys(
        London.ruleset().keys(), 2000
    )
    if fork < TangerineWhistle:
        # Only a network that has not passed Tangerine Whistle can still
        # see the DAO fork: a client refuses a DAO fork scheduled after
        # an active Tangerine Whistle (as Hive's own rulesets do).
        default_values["HIVE_FORK_DAO_BLOCK"] = 2000
    if fork > London:
        default_values["HIVE_TERMINAL_TOTAL_DIFFICULTY"] = 0
    entries = default_values | fork.ruleset()
    if fork >= Amsterdam:
        entries.pop("HIVE_AMSTERDAM_BLOB_BASE_FEE_UPDATE_FRACTION")
        entries.pop("HIVE_AMSTERDAM_BLOB_MAX")
        entries.pop("HIVE_AMSTERDAM_BLOB_TARGET")
    return entries


ruleset = {f: ruleset_format(f) for f in ALL_FORKS_WITH_TRANSITIONS}
