"""
The forks the property suite runs on, taken from the testing framework.

Every framework fork is tested against its spec package, so a new fork is
covered as soon as both sides define it. A test names the spec functions it
checks with `targets` and runs on the forks that define them. A test that
also needs a feature states it with `requires`, which asks the framework's
fork rather than naming forks.
"""

from functools import cache
from importlib import import_module
from inspect import isclass, isfunction
from types import ModuleType
from typing import Callable, Dict, List, Sequence

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


def targets(
    *names: str, where_present: Sequence[str] = ()
) -> pytest.MarkDecorator:
    """
    Name what a test checks in the spec, as paths inside a fork's package:
    its functions, or a type for a test about the type itself.

    The test runs on the forks that define every one of `names`. It also
    checks each function in `where_present` on the forks that have it, for
    a test that reaches a function only some of its forks define. The
    marker also goes on a parameter that checks a function of its own.
    """
    return pytest.mark.targets.with_args(
        *names, where_present=tuple(where_present)
    )


def spec_module(fork: Fork, path: str) -> ModuleType:
    """Return a module of the spec package of `fork`."""
    return import_module(f"{SPEC_PACKAGES[fork].name}.{path}")


@cache
def defines(fork: Fork, name: str) -> bool:
    """
    Return whether the spec package of `fork` defines `name` at that path.
    A function or class that the module only imports does not count.
    """
    path, _, attribute = name.rpartition(".")
    try:
        module = spec_module(fork, path)
    except ModuleNotFoundError:
        return False
    found = getattr(module, attribute, None)
    if isfunction(found) or isclass(found):
        return found.__module__ == module.__name__
    return found is not None


def targets_of(item: pytest.Item, fork: Fork) -> List[str]:
    """Return the spec functions a test checks on `fork`."""
    names: List[str] = []
    for marker in item.iter_markers("targets"):
        names += marker.args
        names += [
            name
            for name in marker.kwargs["where_present"]
            if defines(fork, name)
        ]
    return names


def _check_stays_defined(item: pytest.Item, name: str) -> None:
    """
    Fail if a later fork lacks a function an earlier fork defines, so that
    a rename fails collection and does not drop the later fork from the
    test.
    """
    defining = [fork for fork in SPEC_PACKAGES if defines(fork, name)]
    if not defining:
        raise ValueError(f"no fork defines {name}, for {item.nodeid}")
    later = list(SPEC_PACKAGES)[list(SPEC_PACKAGES).index(defining[0]) :]
    missing = [fork.name() for fork in later if fork not in defining]
    if missing:
        raise ValueError(
            f"{name} is defined from {defining[0].name()} but missing from "
            f"{', '.join(missing)}, for {item.nodeid}"
        )


def forks_for(item: pytest.Function) -> List[Fork]:
    """
    Return the forks a test runs on, from its `targets` and `requires`
    markers, and fail if no fork qualifies.
    """
    required = [
        name for marker in item.iter_markers("targets") for name in marker.args
    ]
    for name in required:
        _check_stays_defined(item, name)
    conditions = [marker.args[0] for marker in item.iter_markers("requires")]
    forks = [
        fork
        for fork in SPEC_PACKAGES
        if all(defines(fork, name) for name in required)
        and all(condition(fork) for condition in conditions)
    ]
    if not forks:
        raise ValueError(f"no fork meets the requirements of {item.nodeid}")
    return forks
