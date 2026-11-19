"""
Hypothesis profiles, the fork axis and the spec module fixtures.

The `ci` profile is the default and is derandomized, so a failure reproduces
from its printed blob. `dev` explores randomly and `long` runs a larger
budget by hand; select one with `--hypothesis-profile`.
"""

from types import ModuleType
from typing import List

import pytest
from execution_testing.forks import Fork
from hypothesis import HealthCheck, settings

from ethereum_spec_tools.forks import Hardfork

from .forks import SPEC_PACKAGES, forks_for

# Spec code is slow and its timing varies between runs and interpreters, so
# no profile enforces a per-example deadline.
settings.register_profile(
    "dev",
    max_examples=200,
    deadline=None,
    print_blob=True,
)
# A quarter of the dev budget: the suite runs on every pull request, and the
# nightly workflow runs it at the dev profile.
settings.register_profile(
    "ci",
    parent=settings.get_profile("dev"),
    max_examples=50,
    derandomize=True,
)
settings.register_profile(
    "long",
    parent=settings.get_profile("dev"),
    max_examples=5000,
    suppress_health_check=[HealthCheck.too_slow],
)
settings.load_profile("ci")


def pytest_configure(config: pytest.Config) -> None:
    """Register the suite's markers."""
    config.addinivalue_line(
        "markers", "requires(condition): run only on forks where it holds"
    )
    config.addinivalue_line(
        "markers",
        "spec_unit: a model test of a spec data structure, run nightly",
    )


def pytest_collection_modifyitems(
    config: pytest.Config, items: List[pytest.Item]
) -> None:
    """Deselect the forks a parameter's `requires` marker rules out."""

    def applies(item: pytest.Item) -> bool:
        params = getattr(item, "callspec", None)
        if params is None or "fork" not in params.params:
            return True
        fork = params.params["fork"]
        return all(
            marker.args[0](fork) for marker in item.iter_markers("requires")
        )

    dropped = [item for item in items if not applies(item)]
    if dropped:
        config.hook.pytest_deselected(items=dropped)
        items[:] = [item for item in items if applies(item)]


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Run every test that uses `fork` once per fork it applies to."""
    if "fork" not in metafunc.fixturenames:
        return
    forks = forks_for(metafunc.definition)
    metafunc.parametrize(
        "fork", forks, ids=[fork.name() for fork in forks], scope="session"
    )


@pytest.fixture(scope="session")
def spec(fork: Fork) -> Hardfork:
    """Return the spec package of the fork under test."""
    spec = SPEC_PACKAGES[fork]
    # The block validation module pulls in the whole fork, and a dependency
    # raises the recursion limit on import, which Hypothesis warns about if
    # it happens during a test.
    spec.module("fork")
    return spec


@pytest.fixture(scope="session")
def gas(spec: Hardfork) -> ModuleType:
    """Return the gas module of the fork under test."""
    return spec.module("vm.gas")


@pytest.fixture(scope="session")
def transactions(spec: Hardfork) -> ModuleType:
    """Return the transactions module of the fork under test."""
    return spec.module("transactions")


@pytest.fixture(scope="session")
def blocks(spec: Hardfork) -> ModuleType:
    """Return the blocks module of the fork under test."""
    return spec.module("blocks")


@pytest.fixture(scope="session")
def tracker(spec: Hardfork) -> ModuleType:
    """Return the state tracker module of the fork under test."""
    return spec.module("state_tracker")


@pytest.fixture(scope="session")
def bal(spec: Hardfork) -> ModuleType:
    """Return the block access list module of the fork under test."""
    return spec.module("block_access_lists")
