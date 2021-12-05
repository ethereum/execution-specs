"""
Ethereum Specification
^^^^^^^^^^^^^^^^^^^^^^

Core specifications for Ethereum clients.
"""
import sys

__version__ = "0.1.0"

#
#  Ensure we can reach 1024 frames of recursion
#
EVM_RECURSION_LIMIT = 1024 * 12
sys.setrecursionlimit(max(EVM_RECURSION_LIMIT, sys.getrecursionlimit()))
