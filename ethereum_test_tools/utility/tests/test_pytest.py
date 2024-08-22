"""
Tests for ethereum_test_tools.utility.pytest.
"""

import pytest

from ethereum_test_tools import extend_with_defaults
from ethereum_test_tools.utility.pytest import UnknownParameterInCasesError


# TODO: This is from the docstring in extend_with_defaults; should be tested automatically
@pytest.mark.parametrize(
    **extend_with_defaults(
        defaults=dict(
            min_value=0,  # default minimum value is 0
            max_value=100,  # default maximum value is 100
            average=50,  # default average value is 50
        ),
        cases=[
            pytest.param(
                dict(),  # use default values
                id="default_case",
            ),
            pytest.param(
                dict(min_value=10),  # override with min_value=10
                id="min_value_10",
            ),
            pytest.param(
                dict(max_value=200),  # override with max_value=200
                id="max_value_200",
            ),
            pytest.param(
                dict(min_value=-10, max_value=50),  # override both min_value
                # and max_value
                id="min_-10_max_50",
            ),
            pytest.param(
                dict(min_value=20, max_value=80, average=50),  # all defaults
                # are overridden
                id="min_20_max_80_avg_50",
            ),
            pytest.param(
                dict(min_value=100, max_value=0),  # invalid range
                id="invalid_range",
                marks=pytest.mark.xfail(reason="invalid range"),
            ),
        ],
    )
)
def test_range(min_value, max_value, average):  # noqa: D103
    assert min_value <= max_value
    assert min_value <= average <= max_value


@pytest.mark.parametrize(
    "defaults,cases,parametrize_kwargs,expected",
    [
        pytest.param(
            dict(min_value=0, max_value=100, average=50),
            [
                pytest.param(
                    dict(),
                    id="default_case",
                ),
                pytest.param(
                    dict(min_value=10),
                    id="min_value_10",
                ),
                pytest.param(
                    dict(max_value=200),
                    id="max_value_200",
                ),
                pytest.param(
                    dict(min_value=-10, max_value=50),
                    id="min_-10_max_50",
                ),
                pytest.param(
                    dict(min_value=20, max_value=80, average=50),
                    id="min_20_max_80_avg_50",
                ),
                pytest.param(
                    dict(min_value=100, max_value=0),
                    id="invalid_range",
                    marks=pytest.mark.xfail(reason="invalid range"),
                ),
            ],
            dict(),
            dict(
                argnames=["min_value", "max_value", "average"],
                argvalues=[
                    pytest.param(0, 100, 50, id="default_case"),
                    pytest.param(10, 100, 50, id="min_value_10"),
                    pytest.param(0, 200, 50, id="max_value_200"),
                    pytest.param(-10, 50, 50, id="min_-10_max_50"),
                    pytest.param(20, 80, 50, id="min_20_max_80_avg_50"),
                    pytest.param(
                        100,
                        0,
                        50,
                        id="invalid_range",
                        marks=pytest.mark.xfail(reason="invalid range"),
                    ),
                ],
            ),
            id="defaults_and_cases_empty_parametrize_kwargs",
        ),
        pytest.param(
            dict(min_value=0, max_value=100, average=50),
            [
                pytest.param(
                    dict(),
                    id="default_case",
                ),
                pytest.param(
                    dict(min_value=10),
                    id="min_value_10",
                ),
            ],
            dict(scope="session"),
            dict(
                argnames=["min_value", "max_value", "average"],
                argvalues=[
                    pytest.param(0, 100, 50, id="default_case"),
                    pytest.param(10, 100, 50, id="min_value_10"),
                ],
            ),
            id="defaults_and_cases_with_parametrize_kwargs",
        ),
    ],
)
def test_extend_with_defaults(defaults, cases, parametrize_kwargs, expected):  # noqa: D103
    result = extend_with_defaults(defaults, cases, **parametrize_kwargs)
    assert result["argnames"] == expected["argnames"]
    assert result["argvalues"] == expected["argvalues"]
    result.pop("argnames")
    result.pop("argvalues")
    assert result == parametrize_kwargs


def test_extend_with_defaults_raises_for_unknown_default():  # noqa: D103
    with pytest.raises(
        UnknownParameterInCasesError, match="only contain parameters present in defaults"
    ):
        extend_with_defaults(dict(a=0, b=1), [pytest.param(dict(c=2))])


@pytest.mark.parametrize(
    "defaults, cases",
    [
        pytest.param(
            dict(param_1="default1"),
            [pytest.param(dict(param_1="value1"), dict(param_2="value2"))],
            id="multiple_values",
        ),
        pytest.param(
            dict(param_1="default1"),
            [pytest.param("not_a_dict")],
            id="non_dict_value",
        ),
    ],
)
def test_extend_with_defaults_raises_value_error(defaults, cases):  # noqa: D103
    expected_message = "each case must contain exactly one value; a dict of parameter values"
    with pytest.raises(ValueError, match=expected_message):
        extend_with_defaults(defaults, cases)
