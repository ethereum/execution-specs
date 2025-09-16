"""
The Gray Glacier fork delays the difficulty bomb. There are no other changes
in this fork.

### Changes

- [EIP-5133: Delaying Difficulty Bomb to Mid September 2022][EIP-5133]

### Upgrade Schedule

| Network | Block      | Expected Date | Fork Hash    |
| ------- |----------- | ------------- | ------------ |
| Mainnet | 15,050,000 | June 29, 2022 | `0xf0afd0e3` |

### Releases

- [Besu 22.4.3]
- [Erigon 2022.06.03][e]
- [EthereumJS 5.9.3][js]
- [Geth 1.10.19]
- [Nethermind 1.13.3][n]


[EIP-5133]: https://eips.ethereum.org/EIPS/eip-5133
[Geth 1.10.19]: https://github.com/ethereum/go-ethereum/releases/tag/v1.10.19
[Besu 22.4.3]: https://github.com/hyperledger/besu/releases/tag/22.4.3
[e]: https://github.com/ledgerwatch/erigon/releases/tag/v2022.06.03
[js]: https://github.com/ethereumjs/ethereumjs-monorepo/releases/tag/@ethereumjs/vm@5.9.3
[n]: https://github.com/NethermindEth/nethermind/releases/tag/1.13.3
"""  # noqa: E501

from ethereum.fork_criteria import ByBlockNumber

FORK_CRITERIA = ByBlockNumber(15050000)
