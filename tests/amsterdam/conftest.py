"""
Minimal conftest for amsterdam BAL tests.
"""
from typing import Any


def pytest_configure(config: Any) -> None:
    """Configure custom markers."""
    config.addinivalue_line("markers", "bal: mark test as BAL-related")
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
