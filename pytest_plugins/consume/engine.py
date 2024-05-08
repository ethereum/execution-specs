"""
A hive simulator that executes blocks against clients using the `engine_newPayloadVX` method from
the Engine API, verifying the appropriate VALID/INVALID responses.

Implemented using the pytest framework as a pytest plugin.
"""

import pytest


@pytest.fixture(scope="session")
def test_suite_name() -> str:
    """
    The name of the hive test suite used in this simulator.
    """
    return "EEST Consume Blocks via Engine API"


@pytest.fixture(scope="session")
def test_suite_description() -> str:
    """
    The description of the hive test suite used in this simulator.
    """
    return "Execute blockchain tests by against clients using the `engine_newPayloadVX` method."
