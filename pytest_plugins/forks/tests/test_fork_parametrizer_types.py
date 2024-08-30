"""
Test the types used to parametrize forks.
"""

from typing import List

import pytest
from _pytest.mark.structures import ParameterSet

from ethereum_test_forks import Frontier

from ..forks import (
    ForkCovariantParameter,
    ForkParametrizer,
    MarkedValue,
    parameters_from_fork_parametrizer_list,
)


@pytest.mark.parametrize(
    "fork_parametrizers,expected_names,expected_parameter_sets",
    [
        pytest.param(
            [ForkParametrizer(fork=Frontier)],
            ["fork"],
            [pytest.param(Frontier)],
            id="only_fork",
        ),
        pytest.param(
            [
                ForkParametrizer(
                    fork=Frontier,
                    fork_covariant_parameters=[
                        ForkCovariantParameter(
                            names=["some_value"], values=[[MarkedValue(value=1)]]
                        )
                    ],
                )
            ],
            ["fork", "some_value"],
            [pytest.param(Frontier, 1)],
            id="fork_with_single_covariant_parameter",
        ),
        pytest.param(
            [
                ForkParametrizer(
                    fork=Frontier,
                    fork_covariant_parameters=[
                        ForkCovariantParameter(
                            names=["some_value"],
                            values=[[MarkedValue(value=1)], [MarkedValue(value=2)]],
                        )
                    ],
                )
            ],
            ["fork", "some_value"],
            [pytest.param(Frontier, 1), pytest.param(Frontier, 2)],
            id="fork_with_single_covariant_parameter_multiple_values",
        ),
        pytest.param(
            [
                ForkParametrizer(
                    fork=Frontier,
                    fork_covariant_parameters=[
                        ForkCovariantParameter(
                            names=["some_value"],
                            values=[
                                [MarkedValue(value=1, marks=[pytest.mark.some_mark])],
                                [MarkedValue(value=2)],
                            ],
                        )
                    ],
                )
            ],
            ["fork", "some_value"],
            [pytest.param(Frontier, 1, marks=[pytest.mark.some_mark]), pytest.param(Frontier, 2)],
            id="fork_with_single_covariant_parameter_multiple_values_one_mark",
        ),
        pytest.param(
            [
                ForkParametrizer(
                    fork=Frontier,
                    fork_covariant_parameters=[
                        ForkCovariantParameter(
                            names=["some_value"], values=[[MarkedValue(value=1)]]
                        ),
                        ForkCovariantParameter(
                            names=["another_value"], values=[[MarkedValue(value=2)]]
                        ),
                    ],
                )
            ],
            ["fork", "some_value", "another_value"],
            [pytest.param(Frontier, 1, 2)],
            id="fork_with_multiple_covariant_parameters",
        ),
        pytest.param(
            [
                ForkParametrizer(
                    fork=Frontier,
                    fork_covariant_parameters=[
                        ForkCovariantParameter(
                            names=["some_value"], values=[[MarkedValue(value=1)]]
                        ),
                        ForkCovariantParameter(
                            names=["another_value"],
                            values=[[MarkedValue(value=2)], [MarkedValue(value=3)]],
                        ),
                    ],
                )
            ],
            ["fork", "some_value", "another_value"],
            [pytest.param(Frontier, 1, 2), pytest.param(Frontier, 1, 3)],
            id="fork_with_multiple_covariant_parameters_multiple_values",
        ),
        pytest.param(
            [
                ForkParametrizer(
                    fork=Frontier,
                    fork_covariant_parameters=[
                        ForkCovariantParameter(
                            names=["some_value", "another_value"],
                            values=[
                                [MarkedValue(value=1), MarkedValue(value="a")],
                                [MarkedValue(value=2), MarkedValue(value="b")],
                            ],
                        )
                    ],
                )
            ],
            ["fork", "some_value", "another_value"],
            [pytest.param(Frontier, 1, "a"), pytest.param(Frontier, 2, "b")],
            id="fork_with_single_multi_value_covariant_parameter_multiple_values",
        ),
        pytest.param(
            [
                ForkParametrizer(
                    fork=Frontier,
                    fork_covariant_parameters=[
                        ForkCovariantParameter(
                            names=["some_value", "another_value"],
                            values=[
                                [MarkedValue(value=1), MarkedValue(value="a")],
                                [MarkedValue(value=2), MarkedValue(value="b")],
                            ],
                        ),
                        ForkCovariantParameter(
                            names=["yet_another_value", "last_value"],
                            values=[
                                [MarkedValue(value=3), MarkedValue(value="x")],
                                [MarkedValue(value=4), MarkedValue(value="y")],
                            ],
                        ),
                    ],
                )
            ],
            ["fork", "some_value", "another_value", "yet_another_value", "last_value"],
            [
                pytest.param(Frontier, 1, "a", 3, "x"),
                pytest.param(Frontier, 1, "a", 4, "y"),
                pytest.param(Frontier, 2, "b", 3, "x"),
                pytest.param(Frontier, 2, "b", 4, "y"),
            ],
            id="fork_with_multiple_multi_value_covariant_parameter_multiple_values",
        ),
        pytest.param(
            [
                ForkParametrizer(
                    fork=Frontier,
                    fork_covariant_parameters=[
                        ForkCovariantParameter(
                            names=["shared_value", "different_value_1"],
                            values=[
                                [MarkedValue(value=1), MarkedValue(value="a")],
                                [MarkedValue(value=2), MarkedValue(value="b")],
                            ],
                        ),
                        ForkCovariantParameter(
                            names=["shared_value", "different_value_2"],
                            values=[
                                [MarkedValue(value=1), MarkedValue(value="x")],
                                [MarkedValue(value=2), MarkedValue(value="y")],
                            ],
                        ),
                    ],
                )
            ],
            ["fork", "shared_value", "different_value_1", "different_value_2"],
            [
                pytest.param(Frontier, 1, "a", "x"),
                pytest.param(Frontier, 2, "b", "y"),
            ],
            id="fork_with_multiple_multi_value_covariant_parameter_shared_values",
        ),
    ],
)
def test_fork_parametrizer(
    fork_parametrizers: List[ForkParametrizer],
    expected_names: List[str],
    expected_parameter_sets: List[ParameterSet],
):
    """
    Test that the fork parametrizer correctly parametrizes tests based on the fork name.
    """
    parameter_names, values = parameters_from_fork_parametrizer_list(fork_parametrizers)
    assert parameter_names == expected_names
    assert len(values) == len(expected_parameter_sets)
    for i in range(len(values)):
        assert len(values[i].values) == len(expected_parameter_sets[i].values)
        for j in range(len(values[i].values)):
            assert values[i].values[j] == expected_parameter_sets[i].values[j]
        assert len(values[i].marks) == len(expected_parameter_sets[i].marks)
        for j in range(len(values[i].marks)):
            assert values[i].marks[j] == expected_parameter_sets[i].marks[j]  # type: ignore
