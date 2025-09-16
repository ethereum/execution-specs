"""
The Cancun fork ([EIP-7569]) introduces transient storage, exposes beacon chain
roots, introduces a new blob-carrying transaction type, adds a memory copying
instruction, limits self-destruct to only work for contracts created in the
same transaction, and adds an instruction to read the blob base fee.

### Changes

- [EIP-1153: Transient storage opcodes][EIP-1153]
- [EIP-4788: Beacon block root in the EVM][EIP-4788]
- [EIP-4844: Shard Blob Transactions][EIP-4844]
- [EIP-5656: MCOPY - Memory copying instruction][EIP-5656]
- [EIP-6780: SELFDESTRUCT only in same transaction][EIP-6780]
- [EIP-7516: BLOBBASEFEE instruction][EIP-7516]

### Upgrade Schedule

| Network | Timestamp    | Date & Time (UTC)   | Fork Hash    | Beacon Chain Epoch |
| ------- | ------------ | ------------------- | ------------ | ------------------ |
| Goerli  | `1705473120` | 2024-01-17 06:32:00 | `0x70cc14e2` | 231,680            |
| Sepolia | `1706655072` | 2024-01-30 22:51:12 | `0x88cf81d9` | 132,608            |
| Holesky | `1707305664` | 2024-02-07 11:34:24 | `0x9b192ad0` |  29,696            |
| Mainnet | `1710338135` | 2024-03-13 13:55:35 | `0x9f3d2254` | 269,568            |

### Releases

- [Besu 24.1.2]
- [Erigon 2.58.1][e]
- [Geth 1.13.13]
- [Nethermind 1.25.4][n]
- [Reth 0.1.0-alpha.19][r]

[EIP-7569]: https://eips.ethereum.org/EIPS/eip-7569
[EIP-1153]: https://eips.ethereum.org/EIPS/eip-1153
[EIP-4788]: https://eips.ethereum.org/EIPS/eip-4788
[EIP-4844]: https://eips.ethereum.org/EIPS/eip-4844
[EIP-5656]: https://eips.ethereum.org/EIPS/eip-5656
[EIP-6780]: https://eips.ethereum.org/EIPS/eip-6780
[EIP-7516]: https://eips.ethereum.org/EIPS/eip-7516
[Besu 24.1.2]: https://github.com/hyperledger/besu/releases/tag/24.1.2
[e]: https://github.com/ledgerwatch/erigon/releases/tag/v2.58.1
[Geth 1.13.13]: https://github.com/ethereum/go-ethereum/releases/tag/v1.13.13
[n]: https://github.com/NethermindEth/nethermind/releases/tag/1.25.4
[r]: https://github.com/paradigmxyz/reth/releases/tag/v0.1.0-alpha.19
"""  # noqa: E501

from ethereum.fork_criteria import ByTimestamp

FORK_CRITERIA = ByTimestamp(1710338135)
