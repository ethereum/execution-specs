"""
The Berlin fork adjusts the gas costs of the `ModExp` precompile and several
state access EVM instructions, introduces typed transaction envelopes along
with the first new transaction type—optional access lists.
"""

from ethereum.fork_criteria import ByBlockNumber

FORK_CRITERIA = ByBlockNumber(12244000)
