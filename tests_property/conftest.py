"""
Hypothesis profiles, the fork axis and the spec module fixtures.

The `ci` profile is the default and is derandomized, so a failure reproduces
from its printed blob. `dev` explores randomly and `long` runs a larger
budget by hand; select one with `--hypothesis-profile`.
"""

from functools import wraps
from inspect import isfunction
from types import ModuleType
from typing import Any, Callable, Generator, List, Optional, Set

import pytest
from execution_testing.forks import Fork
from hypothesis import HealthCheck, settings

from ethereum_spec_tools.forks import Hardfork

from .forks import (
    SPEC_PACKAGES,
    defines,
    forks_for,
    spec_module,
    targets_of,
)
from .targets_report import report

TARGETS_REPORT = pytest.StashKey[List[str]]()

# Spec code is slow and its timing varies between runs and interpreters, so
# no profile enforces a per-example deadline.
settings.register_profile(
    "dev",
    max_examples=200,
    deadline=None,
    print_blob=True,
)
# A quarter of the dev budget: the suite runs on every pull request, and the
# nightly workflow runs it at the dev profile. Without a database a local
# run does not replay failures it saved earlier, so it sees what CI sees.
settings.register_profile(
    "ci",
    parent=settings.get_profile("dev"),
    max_examples=50,
    derandomize=True,
    database=None,
)
settings.register_profile(
    "long",
    parent=settings.get_profile("dev"),
    max_examples=5000,
    suppress_health_check=[HealthCheck.too_slow],
)
settings.load_profile("ci")


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add the option that reports what a fork's properties target."""
    parser.addoption(
        "--spec-targets",
        metavar="FORK",
        help=(
            "List the spec functions FORK adds or changes and the tests "
            "that target them. Use with --collect-only."
        ),
    )


def pytest_configure(config: pytest.Config) -> None:
    """Register the suite's markers."""
    config.addinivalue_line(
        "markers", "requires(condition): run only on forks where it holds"
    )
    config.addinivalue_line(
        "markers", "targets(*names): the spec functions the test checks"
    )


def pytest_collection_modifyitems(
    config: pytest.Config, items: List[pytest.Item]
) -> None:
    """
    Deselect the forks a parameter's `requires` and `targets` markers rule
    out, and fail for a fork test that names nothing it checks in the spec.
    """

    def fork_of(item: pytest.Item) -> Optional[Fork]:
        params = getattr(item, "callspec", None)
        return params.params.get("fork") if params else None

    def applies(item: pytest.Item) -> bool:
        fork = fork_of(item)
        if fork is None:
            return True
        return all(
            marker.args[0](fork) for marker in item.iter_markers("requires")
        ) and all(
            defines(fork, name)
            for marker in item.iter_markers("targets")
            for name in marker.args
        )

    for item in items:
        for marker in item.iter_markers("targets"):
            for name in marker.args:
                if not any(defines(fork, name) for fork in SPEC_PACKAGES):
                    raise pytest.UsageError(
                        f"no fork defines {name}, for {item.nodeid}"
                    )
    dropped = [item for item in items if not applies(item)]
    if dropped:
        config.hook.pytest_deselected(items=dropped)
        items[:] = [item for item in items if applies(item)]
    for item in items:
        fork = fork_of(item)
        if fork is not None and not targets_of(item, fork):
            raise pytest.UsageError(f"{item.nodeid} has no `targets` marker")

    name = config.getoption("--spec-targets")
    if name is not None:
        by_name = {fork.name(): fork for fork in SPEC_PACKAGES}
        if name not in by_name:
            raise pytest.UsageError(f"--spec-targets: no fork named {name}")
        config.stash[TARGETS_REPORT] = report(by_name[name], items)


def pytest_terminal_summary(
    terminalreporter: Any, config: pytest.Config
) -> None:
    """Print the report `--spec-targets` asked for."""
    lines = config.stash.get(TARGETS_REPORT, None)
    if lines is not None:
        terminalreporter.section("spec targets")
        for line in lines:
            terminalreporter.write_line(line)


def _counting(
    function: Callable[..., Any], name: str, called: Set[str]
) -> Callable[..., Any]:
    """Return `function`, recording `name` in `called` when it runs."""

    @wraps(function)
    def counted(*args: Any, **kwargs: Any) -> Any:
        called.add(name)
        return function(*args, **kwargs)

    return counted


@pytest.hookimpl(wrapper=True)
def pytest_runtest_call(item: pytest.Item) -> Generator[None, None, None]:
    """Fail a test that never calls a spec function it targets."""
    callspec = getattr(item, "callspec", None)
    fork = callspec.params.get("fork") if callspec else None
    # A random run may not reach every function a model test targets, so
    # only the profile that draws the same inputs every time is held to it.
    if fork is None or not settings().derandomize:
        return (yield)
    called: Set[str] = set()
    names = []
    replaced = []
    for name in targets_of(item, fork):
        module_name, _, function_name = name.rpartition(".")
        module = spec_module(fork, module_name)
        function = getattr(module, function_name)
        if not isfunction(function):
            continue
        names.append(name)
        replaced.append((module, function_name, function))
        setattr(module, function_name, _counting(function, name, called))
    try:
        result = yield
    finally:
        for module, function_name, function in replaced:
            setattr(module, function_name, function)
    never_called = sorted(set(names) - called)
    assert not never_called, f"the test never called {never_called}"
    return result


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
