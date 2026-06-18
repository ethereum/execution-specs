"""
The Amsterdam fork ([EIP-7773]) includes block-level access lists and the
deterministic ``CREATE2`` factory predeploy.

### Changes

- [EIP-7928: Block-Level Access Lists][EIP-7928]
- [EIP-7954: Increase Maximum Contract Size][EIP-7954]
- [EIP-7997: Deterministic Factory Predeploy][EIP-7997]
- [EIP-8246: Remove SELFDESTRUCT balance burn][EIP-8246]

### Releases

[EIP-7773]: https://eips.ethereum.org/EIPS/eip-7773
[EIP-7928]: https://eips.ethereum.org/EIPS/eip-7928
[EIP-7954]: https://eips.ethereum.org/EIPS/eip-7954
[EIP-7997]: https://eips.ethereum.org/EIPS/eip-7997
[EIP-8246]: https://eips.ethereum.org/EIPS/eip-8246
"""

from ethereum.fork_criteria import ForkCriteria, Unscheduled

FORK_CRITERIA: ForkCriteria = Unscheduled(order_index=3)
