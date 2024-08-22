"""
Pytest utility functions used to write Ethereum tests.
"""

from typing import Any, Dict, List

import pytest
from _pytest.mark.structures import ParameterSet


class UnknownParameterInCasesError(Exception):
    """
    Exception raised when a test case contains parameters
    that are not present in the defaults.
    """

    def __init__(self) -> None:
        super().__init__("each case must only contain parameters present in defaults")


def extend_with_defaults(
    defaults: Dict[str, Any], cases: List[ParameterSet], **parametrize_kwargs: Any
) -> Dict[str, Any]:
    """
    Extends test cases with default parameter values.

    This utility function extends test case parameters by adding default values
    from the `defaults` dictionary to each case in the `cases` list. If a case
    already specifies a value for a parameter, its default is ignored.

    This function is particularly useful in scenarios where you want to define
    a common set of default values but allow individual test cases to override
    them as needed.

    The function returns a dictionary that can be directly unpacked and passed
    to the `@pytest.mark.parametrize` decorator.

    Args:
        defaults (Dict[str, Any]): A dictionary of default parameter names and
            their values. These values will be added to each case unless the case
            already defines a value for each parameter.
        cases (List[ParameterSet]): A list of `pytest.param` objects representing
            different test cases. Its first argument must be a dictionary defining
            parameter names and values.
        parametrize_kwargs (Any): Additional keyword arguments to be passed to
            `@pytest.mark.parametrize`. These arguments are not modified by this
            function and are passed through unchanged.

    Returns:
        Dict[str, Any]: A dictionary with the following structure:
            `argnames`: A list of parameter names.
            `argvalues`: A list of test cases with modified parameter values.
            `parametrize_kwargs`: Additional keyword arguments passed through unchanged.


    Example:
        ```python
        @pytest.mark.parametrize(**extend_with_defaults(
            defaults=dict(
                min_value=0,  # default minimum value is 0
                max_value=100,  # default maximum value is 100
                average=50,  # default average value is 50
            ),
            cases=[
                pytest.param(
                    dict(),  # use default values
                    id='default_case',
                ),
                pytest.param(
                    dict(min_value=10),  # override with min_value=10
                    id='min_value_10',
                ),
                pytest.param(
                    dict(max_value=200),  # override with max_value=200
                    id='max_value_200',
                ),
                pytest.param(
                    dict(min_value=-10, max_value=50),  # override both min_value
                    # and max_value
                    id='min_-10_max_50',
                ),
                pytest.param(
                    dict(min_value=20, max_value=80, average=50),  # all defaults
                    # are overridden
                    id="min_20_max_80_avg_50",
                ),
                pytest.param(
                    dict(min_value=100, max_value=0),  # invalid range
                    id='invalid_range',
                    marks=pytest.mark.xfail(reason='invalid range'),
                )
            ],
        ))
        def test_range(min_value, max_value, average):
            assert min_value <= max_value
            assert min_value <= average <= max_value
        ```

    The above test will execute with the following sets of parameters:

    ```python
    "default_case": {"min_value": 0, "max_value": 100, "average": 50}
    "min_value_10": {"min_value": 10, "max_value": 100, "average": 50}
    "max_value_200": {"min_value": 0, "max_value": 200, "average": 50}
    "min_-10_max_50": {"min_value": -10, "max_value": 50, "average": 50}
    "min_20_max_80_avg_50": {"min_value": 20, "max_value": 80, "average": 50}
    "invalid_range": {"min_value": 100, "max_value": 0, "average": 50}  # expected to fail
    ```

    Notes:
        - Each case in `cases` must contain exactly one value, which is a dictionary
          of parameter values.
        - The function performs an in-place update of the `cases` list, so the
          original `cases` list is modified.
    """
    for i, case in enumerate(cases):
        if not (len(case.values) == 1 and isinstance(case.values[0], dict)):
            raise ValueError(
                "each case must contain exactly one value; a dict of parameter values"
            )
        if set(case.values[0].keys()) - set(defaults.keys()):
            raise UnknownParameterInCasesError()
        # Overwrite values in defaults if the parameter is present in the test case values
        merged_params = {**defaults, **case.values[0]}  # type: ignore
        cases[i] = pytest.param(*merged_params.values(), id=case.id, marks=case.marks)

    return {"argnames": list(defaults), "argvalues": cases, **parametrize_kwargs}
