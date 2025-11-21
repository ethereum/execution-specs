"""
The Amsterdam fork ([EIP-7773]) includes block-level access lists.

### Changes

- [EIP-7928: Block-Level Access Lists][EIP-7928]

### Releases

[EIP-7928]: https://eips.ethereum.org/EIPS/eip-7928
"""  # noqa: E501

from ethereum.fork_criteria import ForkCriteria, Unscheduled

FORK_CRITERIA: ForkCriteria = Unscheduled(order_index=0)
