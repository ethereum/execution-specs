"""
Minimal conftest for osaka BAL tests.
"""

import pytest


def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line("markers", "bal: mark test as BAL-related")
    config.addinivalue_line("markers", "integration: mark test as integration test")