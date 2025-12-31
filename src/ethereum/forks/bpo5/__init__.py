"""
The fifth blob parameter only (BPO) fork, BPO5, includes only changes to the
blob fee schedule.

### Changes

- [EIP-7892: Blob Parameter Only Hardforks][EIP-7892]

### Upgrade Schedule

| Network | Timestamp    | Date & Time (UTC)       | Fork Hash    | Beacon Chain Epoch |
|---------|--------------|-------------------------|--------------|--------------------|
| Holesky | `          ` |                         | `          ` | `      `           |
| Sepolia | `          ` |                         | `          ` | `      `           |
| Hoodi   | `          ` |                         | `          ` |  `     `           |
| Mainnet | `          ` |                         | `          ` | `      `           |

[EIP-7892]: https://eips.ethereum.org/EIPS/eip-7892
"""  # noqa: E501

from ethereum.fork_criteria import ForkCriteria, Unscheduled

FORK_CRITERIA: ForkCriteria = Unscheduled(order_index=2)
