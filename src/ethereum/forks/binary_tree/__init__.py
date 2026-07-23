"""
Experimental fork committing state through the [EIP-8297]
Partitioned Binary Tree instead of the Merkle Patricia Trie.

The fork is identical to Amsterdam except for its state commitment:
it uses the [`ethereum.state_pbt`] provider, whose state roots are
binary tree commitments over the embedded state, instead of
[`ethereum.state_mpt`]. There is no transition machinery; see the
[`ethereum.state_pbt`] module docstring for the simplifications it
makes relative to how the EIP would activate on mainnet.

[EIP-8297]: https://eips.ethereum.org/EIPS/eip-8297
[`ethereum.state_pbt`]: ref:ethereum.state_pbt
[`ethereum.state_mpt`]: ref:ethereum.state_mpt
"""

from ethereum.fork_criteria import ForkCriteria, Unscheduled

FORK_CRITERIA: ForkCriteria = Unscheduled(order_index=4)
