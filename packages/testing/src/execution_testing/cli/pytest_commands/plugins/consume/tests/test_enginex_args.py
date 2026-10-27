"""
Tests for the multi-test simulators' consume argument processing.

`consume enginex` and `consume wirex` reuse one client per group of
tests, so xdist must keep each group on one worker.
"""

import pytest

from execution_testing.cli.pytest_commands.processors import (
    HiveEnvironmentProcessor,
)

MULTI_TEST_SIMULATORS = ("enginex", "wirex")
"""The simulators that must distribute tests by xdist group."""


@pytest.mark.parametrize("simulator", MULTI_TEST_SIMULATORS)
@pytest.mark.parametrize(
    "parallelism_args",
    [
        ["-n", "6"],
        ["-n=6"],
        ["-n6"],
        ["--numprocesses", "6"],
        ["--numprocesses=6"],
    ],
)
def test_parallelism_uses_loadgroup(
    monkeypatch: pytest.MonkeyPatch,
    simulator: str,
    parallelism_args: list[str],
) -> None:
    """Loadgroup is used for every supported -n spelling."""
    monkeypatch.delenv("HIVE_PARALLELISM", raising=False)

    args = HiveEnvironmentProcessor(simulator).process_args(
        [*parallelism_args]
    )

    assert "--dist" in args
    assert args[args.index("--dist") + 1] == "loadgroup"


@pytest.mark.parametrize("simulator", MULTI_TEST_SIMULATORS)
@pytest.mark.parametrize(
    "dist_args",
    [
        ["--dist", "load"],
        ["--dist=load"],
    ],
)
def test_parallelism_overrides_non_loadgroup_dist(
    monkeypatch: pytest.MonkeyPatch, simulator: str, dist_args: list[str]
) -> None:
    """Incompatible xdist distribution modes are overridden."""
    monkeypatch.delenv("HIVE_PARALLELISM", raising=False)

    with pytest.warns(UserWarning, match="requires `--dist=loadgroup`"):
        args = HiveEnvironmentProcessor(simulator).process_args(
            ["-n=6", *dist_args]
        )

    assert "--dist=load" not in args
    if "--dist" in args:
        assert args[args.index("--dist") + 1] == "loadgroup"
    else:
        assert "--dist=loadgroup" in args


@pytest.mark.parametrize("simulator", MULTI_TEST_SIMULATORS)
@pytest.mark.parametrize(
    "dist_args",
    [
        ["-d"],
        ["-d", "--dist=loadgroup"],
        ["--dist", "load", "-d"],
    ],
)
def test_xdist_load_shorthand_is_stripped(
    monkeypatch: pytest.MonkeyPatch, simulator: str, dist_args: list[str]
) -> None:
    """
    The `-d` shorthand for `--dist=load` is removed.

    `-d` overrides any `--dist` value within pytest-xdist's cmdline
    hook, so overriding `--dist` alone is not enough.
    """
    monkeypatch.delenv("HIVE_PARALLELISM", raising=False)

    with pytest.warns(UserWarning, match="requires `--dist=loadgroup`"):
        args = HiveEnvironmentProcessor(simulator).process_args(
            ["-n=6", *dist_args]
        )

    assert "-d" not in args
    if "--dist" in args:
        assert args[args.index("--dist") + 1] == "loadgroup"
    else:
        assert "--dist=loadgroup" in args


@pytest.mark.parametrize("simulator", MULTI_TEST_SIMULATORS)
def test_without_parallelism_loadgroup_is_still_set(
    monkeypatch: pytest.MonkeyPatch, simulator: str
) -> None:
    """Loadgroup is set even without xdist args (inert without `-n`)."""
    monkeypatch.delenv("HIVE_PARALLELISM", raising=False)

    args = HiveEnvironmentProcessor(simulator).process_args([])

    assert args[args.index("--dist") + 1] == "loadgroup"


def test_consume_engine_parallelism_does_not_force_loadgroup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The loadgroup override is scoped to the multi-test simulators."""
    monkeypatch.delenv("HIVE_PARALLELISM", raising=False)

    args = HiveEnvironmentProcessor("engine").process_args(["-n=6"])

    assert "--dist" not in args
    assert "--dist=loadgroup" not in args
