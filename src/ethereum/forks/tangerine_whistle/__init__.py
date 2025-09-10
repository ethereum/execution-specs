"""
The Tangerine Whistle fork ([EIP-608]) is the first of two forks responding to
a denial-of-service attack on the Ethereum network. It tunes the price of
various EVM instructions, and reduces the state size by removing a number of
empty accounts.

### Changes

  - [EIP-150: Gas cost changes for IO-heavy operations][EIP-150]

### Upgrade Schedule

| Network | Block      | Expected Date    | Fork Hash    |
| ------- | ---------- | ---------------- | ------------ |
| Mainnet | 2,463,000  | October 18, 2016 | `0x7a64da13` |

### Releases

- [EthereumJ 1.3.6]
- [Geth 1.4.18]
- [Parity 1.3.8][p]

[EIP-150]: https://eips.ethereum.org/EIPS/eip-150
[EIP-608]: https://eips.ethereum.org/EIPS/eip-608
[EthereumJ 1.3.6]: https://github.com/ethereum/ethereumj/releases/tag/1.3.6
[Geth 1.4.18]: https://github.com/ethereum/go-ethereum/releases/tag/v1.4.18
[p]: https://github.com/openethereum/parity-ethereum/releases/tag/v1.3.8
"""

from ethereum.fork_criteria import ByBlockNumber

FORK_CRITERIA = ByBlockNumber(2463000)
