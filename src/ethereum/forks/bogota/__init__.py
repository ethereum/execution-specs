"""
The Bogota fork includes the frame transaction, which decomposes a
transaction into a sequence of frames that validate the transaction,
approve gas payment, and execute user operations.

### Changes

- [EIP-8141: Frame Transaction][EIP-8141]

### Releases

[EIP-8141]: https://eips.ethereum.org/EIPS/eip-8141
"""

from ethereum.fork_criteria import ForkCriteria, Unscheduled

FORK_CRITERIA: ForkCriteria = Unscheduled(order_index=4)
