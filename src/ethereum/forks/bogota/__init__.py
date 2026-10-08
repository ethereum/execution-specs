"""
The Bogota fork ([EIP-8081]) is the development fork after Amsterdam. It
carries no protocol changes yet: EIPs targeting it are prototyped on their
own branches and land here once accepted.

### Changes

None yet.

### Releases

[EIP-8081]: https://eips.ethereum.org/EIPS/eip-8081
"""

# EIP branches leave this docstring as it is, so that a devnet can merge any
# set of them; an EIP adds its line under Changes when it lands on this branch.

from ethereum.fork_criteria import ForkCriteria, Unscheduled

FORK_CRITERIA: ForkCriteria = Unscheduled(order_index=4)
