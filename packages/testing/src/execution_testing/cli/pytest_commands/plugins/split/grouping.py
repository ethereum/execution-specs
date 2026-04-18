"""
Split-group key extraction for ``--grouped-split``.

The grouping key maps every parametrization of one test function
under one fork to a single runner. The key format mirrors fill's
output-file layout (one file per ``(fork, function)`` pair), so plain
file copies can fan in the per-runner outputs without content
collisions.

This module encodes only the correctness invariant -- which items
must stay together. The performance question of how to distribute
groups across runners is handled by :mod:`.scheduling`.
"""

from __future__ import annotations

from _pytest.nodes import Item

from execution_testing.cli.pytest_commands.plugins.split.durations import (
    strip_xdist_suffix,
)

_FORK_PARAM = "parametrized_fork"


def group_key(item: Item) -> str:
    """
    Return the ``(function_path, fork)`` split-group key for *item*.

    Every parametrization of one test function under one fork maps
    to the same key and therefore lands on the same runner, keeping
    each per-test-function fixture file under its fork subdir
    runner-owned.

    The fork is read from the authoritative source when available --
    ``item.callspec.params["parametrized_fork"]`` set by the forks
    plugin -- so a parametrize value that happens to start with
    ``fork_`` cannot be mistaken for the real fork. Items without a
    callspec (unparametrized functions, doctests, or unit-test stubs)
    fall back to a nodeid-based ``fork_*`` token scan. Items with no
    fork anywhere form singleton groups keyed by the bare nodeid.
    """
    nodeid = strip_xdist_suffix(item.nodeid)
    path = nodeid.partition("[")[0]

    callspec = getattr(item, "callspec", None)
    if callspec is not None:
        params = getattr(callspec, "params", None) or {}
        fork = params.get(_FORK_PARAM)
        if fork is not None:
            return f"{path}|fork={fork}"

    if "[" not in nodeid:
        return nodeid
    _, _, bracketed = nodeid.partition("[")
    for token in bracketed.rstrip("]").split("-"):
        if token.startswith("fork_"):
            return f"{path}|fork={token[len('fork_') :]}"
    return path
