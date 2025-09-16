"""
The Shanghai fork brings staking withdrawals to the execution layer, adds a
push-zero EVM instruction, limits the maximum size of initialization
bytecode, and deprecates the self-destruct EVM instruction.

### Notices

- [EIP-6049: Deprecate SELFDESTRUCT][EIP-6049]

### Changes

- [EIP-3651: Warm COINBASE][EIP-3651]
- [EIP-3855: PUSH0 instruction][EIP-3855]
- [EIP-3860: Limit and meter initcode][EIP-3860]
- [EIP-4895: Beacon chain push withdrawals as operations][EIP-4895]

### Upgrade Schedule

| Network | Timestamp    | Date & Time (UTC)   | Fork Hash    | Beacon Chain Epoch |
| ------- | ------------ | ------------------- | ------------ | ------------------ |
| Sepolia | `1677557088` | 2023-02-28 04:04:48 | `0xf7f9bc08` |  56,832            |
| Goerli  | `1678832736` | 2023-03-14 22:25:36 | `0xf9843abf` | 162,304            |
| Mainnet | `1681338455` | 2023-04-12 22:27:35 | `0xdce96c2d` | 194,048            |


### Releases

- [Besu 23.1.2]
- [Geth 1.11.5]
- [Erigon 2.41.0][e]
- [EthereumJS 6.4.0][js]
- [Nethermind 1.17.3][n]

[EIP-3651]: https://eips.ethereum.org/EIPS/eip-3651
[EIP-3855]: https://eips.ethereum.org/EIPS/eip-3855
[EIP-3860]: https://eips.ethereum.org/EIPS/eip-3860
[EIP-4895]: https://eips.ethereum.org/EIPS/eip-4895
[Geth 1.11.5]: https://github.com/ethereum/go-ethereum/releases/tag/v1.11.5
[Besu 23.1.2]: https://github.com/hyperledger/besu/releases/tag/23.1.2
[n]: https://github.com/NethermindEth/nethermind/releases/tag/1.17.3
[e]: https://github.com/ledgerwatch/erigon/releases/tag/v2.41.0
[js]: https://github.com/ethereumjs/ethereumjs-monorepo/releases/tag/%40ethereumjs%2Fvm%406.4.0
"""  # noqa: E501

from ethereum.fork_criteria import ByTimestamp

FORK_CRITERIA = ByTimestamp(1681338455)
