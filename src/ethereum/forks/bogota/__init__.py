"""
The Bogota fork ([EIP-8081]) is the development fork after Amsterdam. It
empties the logs bloom of blocks and receipts.

### Changes

- [EIP-7668: Remove bloom filters][EIP-7668]

### Releases

[EIP-8081]: https://eips.ethereum.org/EIPS/eip-8081
[EIP-7668]: https://eips.ethereum.org/EIPS/eip-7668
"""

from ethereum.fork_criteria import ForkCriteria, Unscheduled

FORK_CRITERIA: ForkCriteria = Unscheduled(order_index=4)
