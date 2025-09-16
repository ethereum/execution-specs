"""
The Arrow Glacier fork delays the difficulty bomb. There are no other changes
in this fork.

### Changes

- [EIP-4345: Difficulty Bomb Delay to June 2022][EIP-4345]

### Upgrade Schedule

| Network | Block        | Expected Date    | Fork Hash    |
| ------- | ------------ | ---------------- | ------------ |
| Mainnet | 13,773,000   | December 8, 2021 | `0x20c327fc` |

### Releases

- [Besu 21.10.0]
- [Erigon 2021.11.01-alpha][e]
- [EthereumJS VM 5.6.0][js]
- [Geth 1.10.12]
- [Nethermind 1.11.7][nm]

[EIP-4345]: https://eips.ethereum.org/EIPS/eip-4345
[Besu 21.10.0]: https://github.com/hyperledger/besu/releases/tag/21.10.0
[e]: https://github.com/ledgerwatch/erigon/releases/tag/v2021.11.01
[js]: https://github.com/ethereumjs/ethereumjs-monorepo/releases/tag/%40ethereumjs%2Fvm%405.6.0
[Geth 1.10.12]: https://github.com/ethereum/go-ethereum/releases/tag/v1.10.12
[nm]: https://github.com/NethermindEth/nethermind/releases/tag/1.11.7
"""  # noqa: E501

from ethereum.fork_criteria import ByBlockNumber

FORK_CRITERIA = ByBlockNumber(13773000)
