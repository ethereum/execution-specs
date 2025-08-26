"""
The Constantinople fork reduces mining rewards, delays the difficulty bomb,
and introduces new EVM instructions for logical shifts, counterfactual
contract deployment, and computing bytecode hashes.
"""

from ethereum.fork_criteria import ByBlockNumber

FORK_CRITERIA = ByBlockNumber(7280000)
