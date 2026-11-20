"""
Which spec functions a fork adds or changes, and the tests that target them.

A fork's spec package is a copy of its parent's, so the functions that are
new, or whose body differs from the parent's, are the ones the fork's EIPs
touched. The report lists them beside the tests that name them in a
`targets` marker, and so shows the ones no property checks yet.
"""

import ast
import inspect
import textwrap
from importlib import import_module
from types import FunctionType
from typing import Dict, List, Set

import pytest
from execution_testing.forks import Fork

from .forks import SPEC_PACKAGES, targets_of


def functions_of(fork: Fork) -> Dict[str, FunctionType]:
    """Return the public functions of a fork's spec package by their path."""
    spec = SPEC_PACKAGES[fork]
    functions = {}
    for info in spec.walk_packages():
        module = import_module(info.name)
        path = info.name.removeprefix(f"{spec.name}.")
        for name, value in vars(module).items():
            if name.startswith("_") or not inspect.isfunction(value):
                continue
            if value.__module__ == info.name:
                functions[f"{path}.{name}"] = value
    return functions


def _code(function: FunctionType) -> str:
    """Return a function's code without its docstring, to compare forks."""
    source = textwrap.dedent(inspect.getsource(function))
    definition = ast.parse(source).body[0]
    assert isinstance(definition, ast.FunctionDef)
    if ast.get_docstring(definition) is not None:
        definition.body = definition.body[1:]
    return ast.dump(definition)


def tests_by_target(
    items: List[pytest.Item], fork: Fork
) -> Dict[str, Set[str]]:
    """Return the tests that target each spec function on `fork`."""
    tests: Dict[str, Set[str]] = {}
    for item in items:
        callspec = getattr(item, "callspec", None)
        if callspec is None or callspec.params.get("fork") != fork:
            continue
        for name in targets_of(item, fork):
            tests.setdefault(name, set()).add(item.nodeid.split("[")[0])
    return tests


def report(fork: Fork, items: List[pytest.Item]) -> List[str]:
    """Return the lines of the report for `fork`."""
    forks = list(SPEC_PACKAGES)
    functions = functions_of(fork)
    before = forks.index(fork) - 1
    parent = functions_of(forks[before]) if before >= 0 else {}
    tests = tests_by_target(items, fork)

    rows = []
    for name, function in sorted(functions.items()):
        if name not in parent:
            status = "new"
        elif _code(function) != _code(parent[name]):
            status = "changed"
        else:
            continue
        rows.append((status, name, sorted(tests.get(name, []))))
    targeted = sum(1 for _, _, by in rows if by)
    width = max((len(name) for _, name, _ in rows), default=0)
    lines = [
        f"{fork.name()} adds or changes {len(rows)} spec functions, and "
        f"property tests target {targeted} of them.",
        "",
    ]
    for status, name, by in rows:
        names = ", ".join(test.split("::")[-1] for test in by)
        lines.append(f"{status:<8} {name:<{width}}  {names or '-'}")
    return lines
