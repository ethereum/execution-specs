"""
The Istanbul fork makes changes to the gas costs of EVM instructions and data,
adds a cryptographic primitive, and introduces an instruction to fetch the
current chain identifier.
"""

from ethereum.fork_criteria import ByBlockNumber

FORK_CRITERIA = ByBlockNumber(9069000)
