"""
The second blob parameter only (BPO) fork, BPO2 ([EIP-8135]), includes only
changes to the blob fee schedule.

### Changes

- [EIP-7892: Blob Parameter Only Hardforks][EIP-7892]

### Upgrade Schedule

| Network | Timestamp    | Date & Time (UTC)       | Fork Hash    | Beacon Chain Epoch |
|---------|--------------|-------------------------|--------------|--------------------|
| Holesky | `1760389824` | 2025-10-13 21:10:24     | `0x9bc6cb31` | `167936`           |
| Sepolia | `1761607008` | 2025-10-27 23:16:48     | `0x268956b6` | `275712`           |
| Hoodi   | `1762955544` | 2025-11-12 13:52:24     | `0x23aa1351` |  `54016`           |
| Mainnet | `1767747671` | 2026-01-07 01:01:11     | `0x07c9462e` | `419072`           |

[EIP-8135]: https://eips.ethereum.org/EIPS/eip-8135
[EIP-7892]: https://eips.ethereum.org/EIPS/eip-7892
"""  # noqa: E501

from ethereum.fork_criteria import ByTimestamp, ForkCriteria

FORK_CRITERIA: ForkCriteria = ByTimestamp(1767747671)
