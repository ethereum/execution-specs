"""Run consume's real test generator outside a pytest session."""

from pathlib import Path
from types import SimpleNamespace
from typing import Any, List, Sequence, cast

import pytest

# Imported as a module: a hook imported by name into a test module would
# be registered as that module's own `pytest_generate_tests`.
from execution_testing.cli.pytest_commands.plugins.consume import consume
from execution_testing.fixtures import BlockchainEngineXFixture
from execution_testing.fixtures.consume import TestCaseBase, TestCaseIndexFile
from execution_testing.test_types import AllocGroupHash

HASH = "0x" + "11" * 32
PRE_HASH = AllocGroupHash("0x" + "22" * 8)


class Metafunc:
    """The slice of `pytest.Metafunc` that consume's generator uses."""

    def __init__(self, config: Any) -> None:
        """Hold `config` and capture what gets parametrized."""
        self.config = config
        self.fixturenames = ["test_case", "client_type"]
        self.params: List[Any] = []

    def parametrize(self, argnames: str, params: List[Any]) -> None:
        """Capture the parametrization instead of applying it."""
        del argnames
        self.params = params


def engine_x_case(test_id: str, fork: Any) -> TestCaseIndexFile:
    """Return an EngineX test case of `fork` in the `PRE_HASH` group."""
    return TestCaseIndexFile(
        id=test_id,
        fixture_hash=HASH,
        format=BlockchainEngineXFixture,
        fork=fork,
        pre_hash=PRE_HASH,
        json_path=Path(f"{test_id}.json"),
    )


def generate(
    cases: List[TestCaseBase],
    clients: Sequence[str] = ("geth",),
    **config: Any,
) -> List[Any]:
    """Run consume's generator over `cases` for `clients`."""
    metafunc = Metafunc(
        SimpleNamespace(
            test_cases=cases,
            supported_fixture_formats=[BlockchainEngineXFixture],
            hive_execution_clients=[
                SimpleNamespace(name=name) for name in clients
            ],
            **config,
        )
    )
    consume.pytest_generate_tests(cast(pytest.Metafunc, metafunc))
    return metafunc.params


def groups(param: Any) -> List[str]:
    """Return the xdist group names a param is marked with."""
    return [
        mark.kwargs["name"]
        for mark in param.marks
        if mark.name == "xdist_group"
    ]


def variants(param: Any) -> List[str]:
    """Return the group variants a param is marked with."""
    return [
        mark.args[0] for mark in param.marks if mark.name == "group_variant"
    ]
