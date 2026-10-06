"""
The Bogota fork ([EIP-8081]) is the development fork after Amsterdam. It
lowers the maximum per-block base fee change and updates the blob schedule
to accompany a shorter consensus-layer slot duration.

### Changes

- [EIP-8198: Quick Slots][EIP-8198]

### Releases

[EIP-8081]: https://eips.ethereum.org/EIPS/eip-8081
[EIP-8198]: https://eips.ethereum.org/EIPS/eip-8198
"""

from ethereum.fork_criteria import ForkCriteria, Unscheduled

FORK_CRITERIA: ForkCriteria = Unscheduled(order_index=4)
