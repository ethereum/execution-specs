"""
The Bogota fork ([EIP-8081]) is the development fork after Amsterdam. It
introduces fork-choice enforced inclusion lists.

### Changes

- [EIP-7805: Fork-choice enforced Inclusion Lists (FOCIL)][EIP-7805]

### Releases

[EIP-8081]: https://eips.ethereum.org/EIPS/eip-8081
[EIP-7805]: https://eips.ethereum.org/EIPS/eip-7805
"""

from ethereum.fork_criteria import ForkCriteria, Unscheduled

FORK_CRITERIA: ForkCriteria = Unscheduled(order_index=4)
