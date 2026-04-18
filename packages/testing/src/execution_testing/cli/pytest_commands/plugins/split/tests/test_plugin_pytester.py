"""Pytester-based integration tests for the grouped-split plugin."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

PLUGIN = "execution_testing.cli.pytest_commands.plugins.split.plugin"


def _synthetic_tests(pytester: pytest.Pytester) -> None:
    """
    Create a set of synthetic tests mirroring fill's nodeid shape.

    Two functions, two forks, two fixture formats, and one
    non-format parameter, producing nodeids like
    ``test_split_synth.py::test_alpha[fork_A-state_test-x_0]``. All
    variants of one ``(function, fork)`` share a grouping key under
    :func:`group_key`; different functions or different forks get
    different keys.
    """
    pytester.makepyfile(
        test_split_synth="""
        import pytest

        @pytest.mark.parametrize("fmt", ["state_test", "blockchain_test"])
        @pytest.mark.parametrize("x", ["0", "1"])
        @pytest.mark.parametrize("fork", ["fork_A", "fork_B"])
        def test_alpha(fork, fmt, x):
            pass

        @pytest.mark.parametrize("fmt", ["state_test", "blockchain_test"])
        @pytest.mark.parametrize("x", ["0", "1"])
        @pytest.mark.parametrize("fork", ["fork_A", "fork_B"])
        def test_beta(fork, fmt, x):
            pass

        def test_singleton():
            pass
        """
    )


def _write_durations(path: Path, items: dict[str, float]) -> None:
    """Write a synthetic ``.test_durations`` JSON file."""
    path.write_text(json.dumps(items))


def _collected_nodeids(result: pytest.RunResult) -> set[str]:
    """Return the set of ``test_split_synth``-prefixed nodeids."""
    return {
        line.strip()
        for line in result.stdout.lines
        if "::" in line and "test_split_synth" in line
    }


def test_partition_covers_every_item(pytester: pytest.Pytester) -> None:
    """Union of every group's selection equals the full collected set."""
    _synthetic_tests(pytester)
    durations_path = pytester.path / ".test_durations"
    _write_durations(durations_path, {})

    splits = 2
    seen: list[set[str]] = []
    for group in range(1, splits + 1):
        result = pytester.runpytest(
            "-p",
            PLUGIN,
            "--collect-only",
            "-q",
            "--grouped-split",
            f"--splits={splits}",
            f"--group={group}",
            f"--durations-path={durations_path}",
        )
        assert result.ret == 0
        seen.append(_collected_nodeids(result))

    union = set().union(*seen)
    intersection = seen[0].intersection(*seen[1:]) if seen else set()
    assert intersection == set()
    # 2 funcs * 2 forks * 2 params * 2 formats + 1 singleton = 17.
    assert len(union) == 17


def test_function_fork_items_stay_on_one_runner(
    pytester: pytest.Pytester,
) -> None:
    """Every item sharing a ``(function, fork)`` lands on one runner."""
    _synthetic_tests(pytester)
    durations_path = pytester.path / ".test_durations"
    _write_durations(durations_path, {})

    splits = 2
    runners: list[set[str]] = []
    for group in range(1, splits + 1):
        result = pytester.runpytest(
            "-p",
            PLUGIN,
            "--collect-only",
            "-q",
            "--grouped-split",
            f"--splits={splits}",
            f"--group={group}",
            f"--durations-path={durations_path}",
        )
        assert result.ret == 0
        runners.append(_collected_nodeids(result))

    for fn in ("test_alpha", "test_beta"):
        for fork in ("fork_A", "fork_B"):
            runner_idxs = {
                idx
                for idx, runner in enumerate(runners)
                for nid in runner
                if fn in nid and f"{fork}-" in nid
            }
            assert len(runner_idxs) == 1, (
                f"{fn} {fork} split across runners: {runner_idxs}"
            )


def test_pytest_split_plugin_unregistered_when_active(
    pytester: pytest.Pytester,
) -> None:
    """
    Upstream ``pytestsplitplugin`` is unregistered under
    ``--grouped-split``.
    """
    _synthetic_tests(pytester)
    durations_path = pytester.path / ".test_durations"
    _write_durations(durations_path, {})
    pytester.makeconftest(
        """
        def pytest_configure(config):
            active = config.pluginmanager.get_plugin("pytestsplitplugin")
            print(f"SPLIT_PLUGIN_REGISTERED={active is not None}")
        """
    )

    result = pytester.runpytest(
        "-p",
        PLUGIN,
        "--collect-only",
        "-s",
        "--grouped-split",
        "--splits=2",
        "--group=1",
        f"--durations-path={durations_path}",
    )
    assert result.ret == 0
    assert "SPLIT_PLUGIN_REGISTERED=False" in "\n".join(result.stdout.lines)


def test_summary_printed(pytester: pytest.Pytester) -> None:
    """The grouped-split summary appears in terminal output."""
    _synthetic_tests(pytester)
    durations_path = pytester.path / ".test_durations"
    _write_durations(durations_path, {})

    result = pytester.runpytest(
        "-p",
        PLUGIN,
        "--collect-only",
        "--grouped-split",
        "--splits=2",
        "--group=1",
        f"--durations-path={durations_path}",
    )
    assert result.ret == 0
    stdout = "\n".join(result.stdout.lines)
    assert "grouped-split" in stdout
    assert "runner 1/2" in stdout
    assert "(function, fork) keys" in stdout


def test_inactive_without_grouped_split_flag(
    pytester: pytest.Pytester,
) -> None:
    """Without ``--grouped-split`` the plugin is a no-op."""
    _synthetic_tests(pytester)
    result = pytester.runpytest("-p", PLUGIN, "--collect-only", "-q")
    assert result.ret == 0
    assert "grouped-split" not in "\n".join(result.stdout.lines)


def test_mode_labels_three_regimes(pytester: pytest.Pytester) -> None:
    """
    Plugin summary's ``mode:`` line reports the three operator-
    visible regimes: no durations, durations loaded but no match, and
    duration-aware.
    """
    _synthetic_tests(pytester)

    # Discover an actual collected nodeid so the "duration-aware"
    # case's key matches exactly — param ordering in multi-decorator
    # parametrize is implementation-defined, so hard-coding it is
    # brittle.
    collect_only = pytester.runpytest("-p", PLUGIN, "--collect-only", "-q")
    assert collect_only.ret == 0
    any_nodeid = next(
        line.strip()
        for line in collect_only.stdout.lines
        if "test_split_synth.py::test_alpha[" in line
    )

    missing_path = pytester.path / "missing.json"
    assert not missing_path.exists()
    bogus_path = pytester.path / "bogus.json"
    bogus_path.write_text('{"tests/unrelated.py::test_x[fork_Zzz]": 99.0}')
    matching_path = pytester.path / "matching.json"
    matching_path.write_text(json.dumps({any_nodeid: 5.0}))

    for path, expected in (
        (missing_path, "average-only (no durations"),
        (bogus_path, "average-only (1 durations loaded"),
        (matching_path, "duration-aware"),
    ):
        result = pytester.runpytest(
            "-p",
            PLUGIN,
            "--collect-only",
            "--grouped-split",
            "--splits=2",
            "--group=1",
            f"--durations-path={path}",
        )
        assert result.ret == 0
        stdout = "\n".join(result.stdout.lines)
        assert expected in stdout, (
            f"path={path.name}: expected {expected!r} in summary, got:"
            f"\n{stdout[-500:]}"
        )


def test_warning_annotation_on_key_mismatch(
    pytester: pytest.Pytester,
) -> None:
    """
    The ``::warning::`` annotation fires when durations are loaded
    but none match, so CI surfaces the silent-fallback regression.
    """
    _synthetic_tests(pytester)
    bogus_path = pytester.path / "bogus.json"
    bogus_path.write_text('{"tests/unrelated.py::test_x[fork_Zzz]": 99.0}')
    result = pytester.runpytest(
        "-p",
        PLUGIN,
        "--collect-only",
        "--grouped-split",
        "--splits=2",
        "--group=1",
        f"--durations-path={bogus_path}",
    )
    assert result.ret == 0
    combined = "\n".join(result.stdout.lines + result.stderr.lines)
    assert "::warning title=grouped-split durations mismatch::" in combined


def test_items_without_fork_param_become_singletons(
    pytester: pytest.Pytester,
) -> None:
    """Items whose nodeid carries no ``fork_*`` token are per-nodeid."""
    pytester.makepyfile(
        test_unmarked="""
        def test_a(): pass
        def test_b(): pass
        def test_c(): pass
        def test_d(): pass
        """
    )
    durations_path = pytester.path / ".test_durations"
    _write_durations(durations_path, {})

    splits = 2
    seen: list[set[str]] = []
    for group in range(1, splits + 1):
        result = pytester.runpytest(
            "-p",
            PLUGIN,
            "--collect-only",
            "-q",
            "--grouped-split",
            f"--splits={splits}",
            f"--group={group}",
            f"--durations-path={durations_path}",
        )
        assert result.ret == 0
        # Strip any rootdir-relative path prefix so the assertion is
        # robust to pytester sandboxes placed inside the outer pytest's
        # rootdir (e.g. under ``just test-tests --basetemp=.just/...``).
        seen.append(
            {
                line.strip().rsplit("/", 1)[-1]
                for line in result.stdout.lines
                if "test_unmarked.py::" in line
            }
        )

    assert all(len(s) > 0 for s in seen)
    assert set().union(*seen) == (
        {f"test_unmarked.py::test_{n}" for n in "abcd"}
    )
