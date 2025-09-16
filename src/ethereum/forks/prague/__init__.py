"""
The Prague fork enables deploying code into externally owned accounts (EOAs)
via the [`SetCodeTransaction`][t], increases the blob throughput, increases the
cost of calldata-heavy transactions, introduces general execution layer
requests (and two request types: [consolidation][c], and [withdrawal][w]),
appends validator deposits to execution layer blocks, creates BLS12-381
precompiles, and exposes historical block hashes through [a system
contract][b].

### Changes

- [EIP-2537: Precompile for BLS12-381 curve operations][EIP-2537]
- [EIP-2935: Serve historical block hashes from state][EIP-2935]
- [EIP-6110: Supply validator deposits on chain][EIP-6110]
- [EIP-7002: Execution layer triggerable withdrawals][EIP-7002]
- [EIP-7251: Increase the MAX_EFFECTIVE_BALANCE][EIP-7251]
- [EIP-7549: Move committee index outside Attestation][EIP-7549]
- [EIP-7623: Increase calldata cost][EIP-7623]
- [EIP-7685: General purpose execution layer requests][EIP-7685]
- [EIP-7691: Blob throughput increase][EIP-7691]
- [EIP-7840: Add blob schedule to EL config files][EIP-7840]
- [EIP-7702: Set Code for EOAs][EIP-7702]

### Upgrade Schedule

| Network | Timestamp    | Date & Time (UTC)   | Fork Hash    | Beacon Chain Epoch |
| ------- | ------------ | ------------------- | ------------ | ------------------ |
| Holesky | `1740434112` | 2025-02-24 21:55:12 |              | 115,968            |
| Sepolia | `1741159776` | 2025-03-05 07:29:36 |              | 222,464            |
| Hoodi   | `1742999832` | 2025-03-26 14:37:12 |              |   2,048            |
| Mainnet | `1746612311` | 2025-05-07 10:05:11 | `0xc376cf8b` | 364,032            |

### Releases

[t]: ref:ethereum.forks.prague.transactions.SetCodeTransaction
[c]: ref:ethereum.forks.prague.requests.CONSOLIDATION_REQUEST_TYPE
[w]: ref:ethereum.forks.prague.requests.WITHDRAWAL_REQUEST_TYPE
[b]: ref:ethereum.forks.prague.fork.HISTORY_STORAGE_ADDRESS
[EIP-7702]: https://eips.ethereum.org/EIPS/eip-7702
[EIP-7691]: https://eips.ethereum.org/EIPS/eip-7691
[EIP-7623]: https://eips.ethereum.org/EIPS/eip-7623
[EIP-7840]: https://eips.ethereum.org/EIPS/eip-7840
[EIP-7251]: https://eips.ethereum.org/EIPS/eip-7251
[EIP-7002]: https://eips.ethereum.org/EIPS/eip-7002
[EIP-7685]: https://eips.ethereum.org/EIPS/eip-7685
[EIP-6110]: https://eips.ethereum.org/EIPS/eip-6110
[EIP-2537]: https://eips.ethereum.org/EIPS/eip-2537
[EIP-2935]: https://eips.ethereum.org/EIPS/eip-2935
[EIP-7549]: https://eips.ethereum.org/EIPS/eip-7549
"""  # noqa: E501

from ethereum.fork_criteria import ByTimestamp

FORK_CRITERIA = ByTimestamp(1746612311)
