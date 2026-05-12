"""
The Amsterdam fork ([EIP-7773]) includes block-level access lists and the
partial header hash that the consensus layer (Gloas) cross-checks against.

### Changes

- [EIP-7928: Block-Level Access Lists][EIP-7928]
- [EIP-8237: Partial Header Hash][EIP-8237]

### Releases

[EIP-7773]: https://eips.ethereum.org/EIPS/eip-7773
[EIP-7928]: https://eips.ethereum.org/EIPS/eip-7928
[EIP-8237]: https://eips.ethereum.org/EIPS/eip-8237
"""

from ethereum.fork_criteria import ForkCriteria, Unscheduled

FORK_CRITERIA: ForkCriteria = Unscheduled(order_index=3)
