"""
The Shanghai fork brings staking withdrawals to the execution layer, adds a
push-zero EVM instruction, limits the maximum size of initialization
bytecode, and deprecates the self-destruct EVM instruction.
"""

from ethereum.fork_criteria import ByTimestamp

FORK_CRITERIA = ByTimestamp(1681338455)
