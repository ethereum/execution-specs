"""
The Bogota fork ([EIP-8081]) is the development fork after Amsterdam. EIPs
targeting it are prototyped on their own branches and land here once
accepted.

### Changes

- [EIP-3298: Remove storage-clear refund and refund cap][EIP-3298]

### Releases

[EIP-8081]: https://eips.ethereum.org/EIPS/eip-8081
[EIP-3298]: https://eips.ethereum.org/EIPS/eip-3298
"""

from ethereum.fork_criteria import ForkCriteria, Unscheduled

FORK_CRITERIA: ForkCriteria = Unscheduled(order_index=4)
