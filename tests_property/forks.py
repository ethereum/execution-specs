"""
The forks the property suite runs on, taken from the testing framework.

Every framework fork is tested against its spec package, so a new fork is
covered as soon as both sides define it. A test that needs a feature states
it with `requires`, which asks the framework's fork rather than naming forks.
"""

from typing import Callable, Dict, List

import pytest
from execution_testing.forks import (
    BPO_SCENARIOS,
    Constantinople,
    ConstantinopleFix,
    Fork,
    get_forks,
)

from ethereum_spec_tools.forks import Hardfork
from ethereum_spec_tools.utils import resolve_fork

# A BPO scenario fork reuses its parent's spec package with a patched blob
# schedule, so its parent covers that package.
SCENARIO_FORKS = {
    scenario for scenarios in BPO_SCENARIOS.values() for scenario in scenarios
}

# A blob-parameter-only fork that is not scheduled has a test-only schedule
# in the framework, and its spec package is a placeholder that `fill` clones
# with that schedule.
PLACEHOLDER_FORKS = [
    fork
    for fork in get_forks()
    if fork.bpo_fork()
    and not fork.is_deployed()
    and fork not in SCENARIO_FORKS
]


def _spec_packages() -> Dict[Fork, Hardfork]:
    packages: Dict[Fork, Hardfork] = {}
    for fork in get_forks():
        if fork in PLACEHOLDER_FORKS or fork in SCENARIO_FORKS:
            continue
        spec = resolve_fork(fork.transition_tool_name())
        for other, other_spec in list(packages.items()):
            if other_spec.short_name != spec.short_name:
                continue
            # The spec folds Constantinople and its fix into one package;
            # test it against the fix, the fork mainnet ran.
            if (other, fork) != (Constantinople, ConstantinopleFix):
                raise ValueError(f"{other} and {fork} share {spec.name}")
            del packages[other]
        packages[fork] = spec
    return packages


SPEC_PACKAGES = _spec_packages()
"""The spec package of each framework fork under test."""


def requires(condition: Callable[[Fork], object]) -> pytest.MarkDecorator:
    """Run a test only on the forks where `condition` holds."""
    return pytest.mark.requires.with_args(condition)


def forks_for(item: pytest.Function) -> List[Fork]:
    """
    Return the forks a test runs on, from its `requires` markers, and fail
    if no fork qualifies.
    """
    conditions = [marker.args[0] for marker in item.iter_markers("requires")]
    forks = [
        fork
        for fork in SPEC_PACKAGES
        if all(condition(fork) for condition in conditions)
    ]
    if not forks:
        raise ValueError(f"no fork meets the requirements of {item.nodeid}")
    return forks
