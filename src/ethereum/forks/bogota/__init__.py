"""
The Bogota fork ([EIP-8081]) is the development fork after Amsterdam. EIPs
targeting it are prototyped on their own branches and land here once
accepted.

### Changes

- [EIP-7979: Call and Return Opcodes for the EVM][EIP-7979]
- [EIP-8337: Validated EVM Code][EIP-8337]

### Releases

[EIP-8081]: https://eips.ethereum.org/EIPS/eip-8081
[EIP-7979]: https://eips.ethereum.org/EIPS/eip-7979
[EIP-8337]: https://eips.ethereum.org/EIPS/eip-8337
"""

from ethereum.fork_criteria import ForkCriteria, Unscheduled

FORK_CRITERIA: ForkCriteria = Unscheduled(order_index=4)
