"""
The Bogota fork ([EIP-8081]) is the development fork after Amsterdam. It
carries no protocol changes yet: EIPs targeting it are prototyped on their
own branches and land here once accepted.

### Changes

None yet.

### Releases

[EIP-8081]: https://eips.ethereum.org/EIPS/eip-8081
"""

from ethereum.fork_criteria import ForkCriteria, Unscheduled

FORK_CRITERIA: ForkCriteria = Unscheduled(order_index=4)
