"""
Ethereum Specification
^^^^^^^^^^^^^^^^^^^^^^

Core specifications for Ethereum clients.
"""
import sys
from typing import Any

__version__ = "0.1.0"

#
#  Ensure we can reach 1024 frames of recursion
#
EVM_RECURSION_LIMIT = 1024 * 12
sys.setrecursionlimit(max(EVM_RECURSION_LIMIT, sys.getrecursionlimit()))


def evm_trace(evm: Any, op: Any) -> None:
    """
    Placeholder for an evm trace function. The spec does not trace evm by
    default. EVM tracing will be injected if the user requests it.
    """
    pass
