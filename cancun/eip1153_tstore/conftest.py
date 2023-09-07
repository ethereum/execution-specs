"""
Pytest plugin local to EIP-1153 tests.
"""
from typing import List

import pytest


@pytest.fixture(autouse=True)
def eips(eip_enabled: bool = True) -> List[int]:
    """
    Returns a list of EIPs to enable in the client t8n tool.
    """
    return [1153] if eip_enabled else []
