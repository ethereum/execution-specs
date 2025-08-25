"""Test fork range descriptor parsing from string."""

import pytest

from ..forks.forks import Osaka, Prague
from ..helpers import ForkRangeDescriptor


@pytest.mark.parametrize(
    "fork_range_descriptor_string,expected_fork_range_descriptor",
    [
        (
            ">=Osaka",
            ForkRangeDescriptor(
                greater_equal=Osaka,
                less_than=None,
            ),
        ),
        (
            ">= Prague < Osaka",
            ForkRangeDescriptor(
                greater_equal=Prague,
                less_than=Osaka,
            ),
        ),
    ],
)
def test_parsing_fork_range_descriptor_from_string(
    fork_range_descriptor_string: str,
    expected_fork_range_descriptor: ForkRangeDescriptor,
):
    """Test multiple strings used as fork range descriptors in ethereum/tests."""
    assert (
        ForkRangeDescriptor.model_validate(fork_range_descriptor_string)
        == expected_fork_range_descriptor
    )
