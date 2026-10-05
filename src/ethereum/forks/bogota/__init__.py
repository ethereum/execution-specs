"""
The Bogota fork ([EIP-8081]) is the development fork after Amsterdam. It
introduces frame transactions.

### Changes

- [EIP-8141: Frame Transaction][EIP-8141]

### Releases

[EIP-8081]: https://eips.ethereum.org/EIPS/eip-8081
[EIP-8141]: https://eips.ethereum.org/EIPS/eip-8141
"""

from ethereum.fork_criteria import ForkCriteria, Unscheduled

FORK_CRITERIA: ForkCriteria = Unscheduled(order_index=4)
