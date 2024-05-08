"""
A hive simulator that executes test fixtures in the blockchain test format
against clients by providing them a genesis state and RLP-encoded blocks
that they consume upon start-up.

Implemented using the pytest framework as a pytest plugin.
"""
import pytest


@pytest.fixture(scope="session")
def test_suite_name() -> str:
    """
    The name of the hive test suite used in this simulator.
    """
    return "EEST Consume Blocks via RLP"


@pytest.fixture(scope="session")
def test_suite_description() -> str:
    """
    The description of the hive test suite used in this simulator.
    """
    return "Execute blockchain tests by providing RLP-encoded blocks to a client upon start-up."
