"""
Tests for running one fixture under several client configurations.

A simulator sets `config.group_variants` to return, per test case, the
variants to run it under; each variant becomes its own test, with its
own client group, because a client that has imported a fixture's chain
cannot import it again.
"""

from pathlib import Path
from types import SimpleNamespace
from typing import Any, List, Sequence, cast

import pytest

# Imported as a module: a hook imported by name into a test module would
# be registered as that module's own `pytest_generate_tests`.
from execution_testing.cli.pytest_commands.plugins.consume import consume
from execution_testing.cli.pytest_commands.plugins.consume.simulators.helpers import (  # noqa: E501
    test_tracker,
)
from execution_testing.fixtures import BlockchainEngineXFixture
from execution_testing.fixtures.consume import TestCaseBase, TestCaseIndexFile
from execution_testing.forks import Amsterdam, Osaka
from execution_testing.test_types import AllocGroupHash

# The generator marks params with fork, format and variant marks that only
# a consume session registers.
pytestmark = pytest.mark.filterwarnings(
    "ignore::pytest.PytestUnknownMarkWarning"
)

HASH = "0x" + "11" * 32
PRE_HASH = AllocGroupHash("0x" + "22" * 8)


class _Metafunc:
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


def _case(test_id: str, fork: Any) -> TestCaseIndexFile:
    """Return an EngineX test case of `fork`."""
    return TestCaseIndexFile(
        id=test_id,
        fixture_hash=HASH,
        format=BlockchainEngineXFixture,
        fork=fork,
        pre_hash=PRE_HASH,
        json_path=Path(f"{test_id}.json"),
    )


def _generate(cases: List[TestCaseBase], **config: Any) -> List[Any]:
    """Run consume's generator over `cases` for one client."""
    metafunc = _Metafunc(
        SimpleNamespace(
            test_cases=cases,
            supported_fixture_formats=[BlockchainEngineXFixture],
            hive_execution_clients=[SimpleNamespace(name="geth")],
            **config,
        )
    )
    consume.pytest_generate_tests(cast(pytest.Metafunc, metafunc))
    return metafunc.params


def _groups(param: Any) -> List[str]:
    """Return the xdist group names a param is marked with."""
    return [
        mark.kwargs["name"]
        for mark in param.marks
        if mark.name == "xdist_group"
    ]


def _variants(param: Any) -> List[str]:
    """Return the group variants a param is marked with."""
    return [
        mark.args[0] for mark in param.marks if mark.name == "group_variant"
    ]


def test_identifier_without_variant_is_unchanged() -> None:
    """No variant keeps the established pre-hash and client key."""
    assert (
        test_tracker.make_group_identifier(PRE_HASH, "geth")
        == f"{PRE_HASH}-geth"
    )


def test_identifier_with_variant_is_distinct() -> None:
    """Each variant names its own group."""
    assert (
        test_tracker.make_group_identifier(PRE_HASH, "geth", "served")
        == f"{PRE_HASH}-geth-served"
    )


def test_no_variants_by_default() -> None:
    """A simulator that declares no variants gets one test per case."""
    (param,) = _generate([_case("a", Osaka)])
    assert param.id == "a-geth"
    assert _groups(param) == [f"{PRE_HASH}-geth"]
    assert _variants(param) == []


def test_each_variant_is_its_own_test_and_group() -> None:
    """Variants multiply the case into separately grouped tests."""

    def group_variants(test_case: TestCaseBase) -> Sequence[str]:
        return ("withheld", "served") if test_case.fork is Amsterdam else ("",)

    params = _generate(
        [_case("a", Osaka), _case("b", Amsterdam)],
        group_variants=group_variants,
    )
    assert [param.id for param in params] == [
        "a-geth",
        "b-geth-withheld",
        "b-geth-served",
    ]
    assert [_groups(param) for param in params] == [
        [f"{PRE_HASH}-geth"],
        [f"{PRE_HASH}-geth-withheld"],
        [f"{PRE_HASH}-geth-served"],
    ]
    assert [_variants(param) for param in params] == [
        [],
        ["withheld"],
        ["served"],
    ]


@pytest.mark.parametrize("variant", ["", "served"])
def test_variant_round_trips_through_the_item(
    pytester: pytest.Pytester, variant: str
) -> None:
    """`group_variant_of` reads back what the generator marked."""
    pytester.makepyfile(
        f"""
        import pytest
        from {test_tracker.__name__} import group_variant_of

        marks = [pytest.mark.group_variant({variant!r})] if {variant!r} else []

        @pytest.mark.parametrize("x", [pytest.param(1, marks=marks)])
        def test_variant(request, x):
            assert group_variant_of(request.node) == {variant!r}
        """
    )
    result = pytester.runpytest("-p", "no:cacheprovider", "-W", "ignore")
    result.assert_outcomes(passed=1)
