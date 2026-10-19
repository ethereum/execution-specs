"""
The Bogota fork ([EIP-8081]) is the development fork after Amsterdam. EIPs
targeting it are prototyped on their own branches and land here once
accepted.

### Changes

- [EIP-8298: SETCODEFROM Code Reuse Instruction][EIP-8298]

### Releases

[EIP-8081]: https://eips.ethereum.org/EIPS/eip-8081
[EIP-8298]: https://eips.ethereum.org/EIPS/eip-8298
"""

from ethereum.fork_criteria import ForkCriteria, Unscheduled

FORK_CRITERIA: ForkCriteria = Unscheduled(order_index=4)
