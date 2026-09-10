"""Tests for EngineX consume argument processing."""

from types import SimpleNamespace

import pytest

from execution_testing.cli.pytest_commands.plugins.consume.simulators.enginex.conftest import (  # noqa: E501
    pytest_configure as configure_enginex,
)
from execution_testing.cli.pytest_commands.plugins.consume.simulators.enginex.conftest import (  # noqa: E501
    test_suite_description,
    test_suite_name,
)
from execution_testing.cli.pytest_commands.processors import (
    HiveEnvironmentProcessor,
)


def test_enginex_uses_session_scoped_hive_suite() -> None:
    """The session-wide result check must outlive every test module."""
    config = SimpleNamespace()

    configure_enginex(config)  # type: ignore[arg-type]

    assert config.assert_reported_test_count is True
    assert config.test_suite_scope == "session"
    assert test_suite_name._fixture_function_marker.scope == "session"
    assert test_suite_description._fixture_function_marker.scope == "session"


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
def test_enginex_parallelism_uses_loadgroup(
    monkeypatch: pytest.MonkeyPatch, parallelism_args: list[str]
) -> None:
    """EngineX must use xdist loadgroup for every supported -n spelling."""
    monkeypatch.delenv("HIVE_PARALLELISM", raising=False)

    args = HiveEnvironmentProcessor("enginex").process_args(
        [*parallelism_args]
    )

    assert "--dist" in args
    assert args[args.index("--dist") + 1] == "loadgroup"


@pytest.mark.parametrize(
    "dist_args",
    [
        ["--dist", "load"],
        ["--dist=load"],
    ],
)
def test_enginex_parallelism_overrides_non_loadgroup_dist(
    monkeypatch: pytest.MonkeyPatch, dist_args: list[str]
) -> None:
    """EngineX overrides incompatible xdist distribution modes."""
    monkeypatch.delenv("HIVE_PARALLELISM", raising=False)

    with pytest.warns(UserWarning, match="requires `--dist=loadgroup`"):
        args = HiveEnvironmentProcessor("enginex").process_args(
            ["-n=6", *dist_args]
        )

    assert "--dist=load" not in args
    if "--dist" in args:
        assert args[args.index("--dist") + 1] == "loadgroup"
    else:
        assert "--dist=loadgroup" in args


@pytest.mark.parametrize(
    "dist_args",
    [
        ["-d"],
        ["-d", "--dist=loadgroup"],
        ["--dist", "load", "-d"],
    ],
)
def test_enginex_strips_xdist_load_shorthand(
    monkeypatch: pytest.MonkeyPatch, dist_args: list[str]
) -> None:
    """
    EngineX removes xdist's `-d` shorthand for `--dist=load`.

    `-d` overrides any `--dist` value within pytest-xdist's cmdline
    hook, so overriding `--dist` alone is not enough.
    """
    monkeypatch.delenv("HIVE_PARALLELISM", raising=False)

    with pytest.warns(UserWarning, match="requires `--dist=loadgroup`"):
        args = HiveEnvironmentProcessor("enginex").process_args(
            ["-n=6", *dist_args]
        )

    assert "-d" not in args
    if "--dist" in args:
        assert args[args.index("--dist") + 1] == "loadgroup"
    else:
        assert "--dist=loadgroup" in args


def test_enginex_without_parallelism_still_sets_loadgroup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Loadgroup is set even without xdist args (inert without `-n`)."""
    monkeypatch.delenv("HIVE_PARALLELISM", raising=False)

    args = HiveEnvironmentProcessor("enginex").process_args([])

    assert args[args.index("--dist") + 1] == "loadgroup"


def test_consume_engine_parallelism_does_not_force_loadgroup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The loadgroup override is scoped to consume enginex."""
    monkeypatch.delenv("HIVE_PARALLELISM", raising=False)

    args = HiveEnvironmentProcessor("engine").process_args(["-n=6"])

    assert "--dist" not in args
    assert "--dist=loadgroup" not in args
