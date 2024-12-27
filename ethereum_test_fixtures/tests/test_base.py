"""Test cases for the ethereum_test_fixtures.base module."""

from ..base import BaseFixture


def test_json_dict():
    """Test that the json_dict property does not include the info field."""
    fixture = BaseFixture()
    assert "_info" not in fixture.json_dict, "json_dict should exclude the 'info' field"
