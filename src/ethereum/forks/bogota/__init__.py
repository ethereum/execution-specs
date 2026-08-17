"""
The Bogota development fork collects candidate changes for the fork
after Amsterdam.

### Changes

- [EIP-4758: Deactivate SELFDESTRUCT][EIP-4758]

[EIP-4758]: https://eips.ethereum.org/EIPS/eip-4758
"""

from ethereum.fork_criteria import ForkCriteria, Unscheduled

FORK_CRITERIA: ForkCriteria = Unscheduled(order_index=4)
