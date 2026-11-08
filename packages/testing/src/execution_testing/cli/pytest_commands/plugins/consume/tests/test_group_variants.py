"""Tests for running one fixture under several group variants."""

from typing import Any, Sequence

import pytest

from execution_testing.cli.pytest_commands.plugins.consume.simulators.helpers import (  # noqa: E501
    test_tracker,
)
from execution_testing.fixtures.consume import TestCaseBase
from execution_testing.forks import Amsterdam, Osaka

from .variant_generator import (
    PRE_HASH,
    engine_x_case,
    generate,
    groups,
    variants,
)

# The generator marks params with fork, format and variant marks that only
# a consume session registers.
pytestmark = pytest.mark.filterwarnings(
    "ignore::pytest.PytestUnknownMarkWarning"
)


def test_no_variants_keep_the_ids_and_groups() -> None:
    """
    A simulator that declares no variants gets one test per case, under
    the pre-hash and client key alone; a variant only extends the key.
    """
    (param,) = generate([engine_x_case("a", Osaka)])
    assert param.id == "a-geth"
    assert groups(param) == [f"{PRE_HASH}-geth"]
    assert variants(param) == []
    assert test_tracker.make_group_identifier(PRE_HASH, "geth") == (
        f"{PRE_HASH}-geth"
    )
    assert test_tracker.make_group_identifier(PRE_HASH, "geth", "served") == (
        f"{PRE_HASH}-geth-served"
    )


def test_each_variant_is_its_own_test_and_group() -> None:
    """
    Variants multiply a case into separately grouped tests, and a
    simulator can run a case under fewer variants on one client.
    """

    def group_variants(
        test_case: TestCaseBase, client_type: Any
    ) -> Sequence[str]:
        if test_case.fork is not Amsterdam:
            return ("",)
        if client_type.name == "nethermind":
            return ("withheld",)
        return ("withheld", "served")

    params = generate(
        [engine_x_case("a", Osaka), engine_x_case("b", Amsterdam)],
        clients=("geth", "nethermind"),
        group_variants=group_variants,
    )
    expected = [
        ("a-geth", f"{PRE_HASH}-geth", []),
        ("a-nethermind", f"{PRE_HASH}-nethermind", []),
        ("b-geth-withheld", f"{PRE_HASH}-geth-withheld", ["withheld"]),
        ("b-geth-served", f"{PRE_HASH}-geth-served", ["served"]),
        (
            "b-nethermind-withheld",
            f"{PRE_HASH}-nethermind-withheld",
            ["withheld"],
        ),
    ]
    assert [
        (param.id, *groups(param), variants(param)) for param in params
    ] == expected


@pytest.mark.parametrize("variant", ["", "served"])
def test_variant_round_trips_through_the_item(
    pytester: pytest.Pytester, variant: str
) -> None:
    """`group_variant_of` reads back the variant the generator marked."""
    pytester.makepyfile(
        f"""
        import pytest
        from execution_testing.forks import Amsterdam
        from {test_tracker.__name__} import group_variant_of
        from {generate.__module__} import engine_x_case, generate

        PARAMS = generate(
            [engine_x_case("a", Amsterdam)],
            group_variants=lambda test_case, client_type: ({variant!r},),
        )

        @pytest.mark.parametrize("test_case,client_type", PARAMS)
        def test_variant(request, test_case, client_type):
            assert group_variant_of(request.node) == {variant!r}
        """
    )
    result = pytester.runpytest("-p", "no:cacheprovider", "-W", "ignore")
    result.assert_outcomes(passed=1)
