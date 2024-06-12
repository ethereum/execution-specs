"""
The DAO Fork is a response to a smart contract exploit known as the 2016 DAO
Attack where a vulnerable contract was drained of its ether. This fork recovers
the stolen funds into a new contract.
"""

from ethereum.fork_criteria import ByBlockNumber

FORK_CRITERIA = ByBlockNumber(1920000)
