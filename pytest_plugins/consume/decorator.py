"""Consume test function decorator used to mark properties of a test function."""

from ethereum_test_fixtures import FixtureFormat


def fixture_format(*formats: FixtureFormat):
    """Mark a test function as a test that consumes a specific fixture format."""

    def decorator(func):
        func.fixture_format = formats
        return func

    return decorator
