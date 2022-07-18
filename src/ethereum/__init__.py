"""
Ethereum Specification
^^^^^^^^^^^^^^^^^^^^^^
Seeing as internet connections have been vastly expanding across the
world, spreading information has become as cheap as ever. Bitcoin, for
example, has demonstrated the possibility of creating a decentralized,
trade system that is accessible around the world. Namecoin is another
system that built off of Bitcoin's currency structure to create other
simple technological applications.

Ethereum's goal is to create a cryptographically secure system in which
any and all types of transaction-based concepts can be built. It provides
an exceptionally accessible and decentralized system to build software
and execute transactions.

This package contains a reference implementation, written as simply as
possible, to aid in defining the behavior of Ethereum clients.
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
    autoapi_noshow
    Placeholder for an evm trace function. The spec does not trace evm by
    default. EVM tracing will be injected if the user requests it.
    """
    pass
