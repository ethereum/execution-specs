"""
Consume test function decorator used to mark properties of a test function.
"""

from ethereum_test_fixtures import FixtureFormats


def fixture_format(*formats: FixtureFormats):
    """
    Mark a test function as a test that consumes a specific fixture format.
    """

    def decorator(func):
        func.fixture_formats = formats
        return func

    return decorator
