"""Helpers for pytest plugins."""

from typing import Any, Dict, Tuple, Type

import pytest
from _pytest.mark.structures import ParameterSet

from ethereum_test_execution import ExecuteFormat, LabeledExecuteFormat
from ethereum_test_fixtures import FixtureFormat, LabeledFixtureFormat
from ethereum_test_tools import BaseTest


def labeled_format_parameter_set(
    format_with_or_without_label: LabeledExecuteFormat
    | LabeledFixtureFormat
    | ExecuteFormat
    | FixtureFormat,
) -> ParameterSet:
    """
    Return a parameter set from a fixture/execute format and parses a label if there's
    any.

    The label will be used in the test id and also will be added as a marker to the
    generated test case when filling/executing the test.
    """
    if isinstance(format_with_or_without_label, LabeledExecuteFormat) or isinstance(
        format_with_or_without_label, LabeledFixtureFormat
    ):
        return pytest.param(
            format_with_or_without_label.format,
            id=format_with_or_without_label.label,
            marks=[
                getattr(
                    pytest.mark,
                    format_with_or_without_label.format_name.lower(),
                ),
                getattr(
                    pytest.mark,
                    format_with_or_without_label.label.lower(),
                ),
            ],
        )
    else:
        return pytest.param(
            format_with_or_without_label,
            id=format_with_or_without_label.format_name.lower(),
            marks=[
                getattr(
                    pytest.mark,
                    format_with_or_without_label.format_name.lower(),
                )
            ],
        )


def get_spec_format_for_item(
    params: Dict[str, Any],
) -> Tuple[Type[BaseTest], Any]:
    """Return the spec type and execute format for the given test item."""
    for spec_type in BaseTest.spec_types.values():
        if spec_type.pytest_parameter_name() in params:
            return spec_type, params[spec_type.pytest_parameter_name()]
    raise ValueError("No spec type format found in the test item.")
