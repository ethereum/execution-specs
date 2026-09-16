"""
The Amsterdam fork ([EIP-7773]) includes block-level access lists and the
deterministic ``CREATE2`` factory predeploy.

### Changes

- [EIP-2780: Resource-based intrinsic transaction gas][EIP-2780]
- [EIP-7708: ETH transfers emit a log][EIP-7708]
- [EIP-7778: Block Gas Accounting without Refunds][EIP-7778]
- [EIP-7843: SLOTNUM][EIP-7843]
- [EIP-7928: Block-Level Access Lists][EIP-7928]
- [EIP-7954: Increase Maximum Contract Size][EIP-7954]
- [EIP-7976: Increase calldata floor cost][EIP-7976]
- [EIP-7981: Increase Access List Cost][EIP-7981]
- [EIP-7997: Deterministic Factory Predeploy][EIP-7997]
- [EIP-8024: Stack Access Instructions][EIP-8024]
- [EIP-8037: State Creation Gas Cost Increase][EIP-8037]
- [EIP-8038: State Access Gas Cost Increase][EIP-8038]
- [EIP-8246: Remove SELFDESTRUCT balance burn][EIP-8246]
- [EIP-8253: Bump nonce of zero-nonce storage accounts][EIP-8253]
- [EIP-8282: Builder Execution Requests][EIP-8282]

### Releases

[EIP-7773]: https://eips.ethereum.org/EIPS/eip-7773
[EIP-2780]: https://eips.ethereum.org/EIPS/eip-2780
[EIP-7708]: https://eips.ethereum.org/EIPS/eip-7708
[EIP-7778]: https://eips.ethereum.org/EIPS/eip-7778
[EIP-7843]: https://eips.ethereum.org/EIPS/eip-7843
[EIP-7928]: https://eips.ethereum.org/EIPS/eip-7928
[EIP-7954]: https://eips.ethereum.org/EIPS/eip-7954
[EIP-7976]: https://eips.ethereum.org/EIPS/eip-7976
[EIP-7981]: https://eips.ethereum.org/EIPS/eip-7981
[EIP-7997]: https://eips.ethereum.org/EIPS/eip-7997
[EIP-8024]: https://eips.ethereum.org/EIPS/eip-8024
[EIP-8037]: https://eips.ethereum.org/EIPS/eip-8037
[EIP-8038]: https://eips.ethereum.org/EIPS/eip-8038
[EIP-8246]: https://eips.ethereum.org/EIPS/eip-8246
[EIP-8253]: https://eips.ethereum.org/EIPS/eip-8253
[EIP-8282]: https://eips.ethereum.org/EIPS/eip-8282
"""

from ethereum.fork_criteria import ForkCriteria, Unscheduled

FORK_CRITERIA: ForkCriteria = Unscheduled(order_index=3)
