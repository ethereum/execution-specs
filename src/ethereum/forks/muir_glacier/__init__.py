"""
The Muir Glacier fork delays the difficulty bomb. There are no other changes
in this fork.

### Changes

- [EIP-2384: Muir Glacier Difficulty Bomb Delay][EIP-2384]

### Upgrade Schedule

| Network | Block        | Expected Date    | Fork Hash    |
| ------- | ------------ | ---------------- | ------------ |
| Ropsten |  7,117,117   |                  |              |
| Mainnet |  9,200,000   | January 2, 2020  | `0xe029e991` |

### Releases

- [Geth 1.9.9]
- [Parity 2.6.8-beta][p]
- [Besu 1.3.7]
- [Nethermind 1.2.6][n]
- [EthereumJS 4.1.2][js]
- [Aleth 1.8.0][a]
- [Trinity 0.1.0-alpha.34][t]

[EIP-2384]: https://eips.ethereum.org/EIPS/eip-2384
[Geth 1.9.9]: https://github.com/ethereum/go-ethereum/releases/tag/v1.9.9
[p]: https://github.com/paritytech/parity-ethereum/releases/tag/v2.6.8
[Besu 1.3.7]: https://github.com/hyperledger/besu/releases/tag/1.3.7
[n]: https://github.com/NethermindEth/nethermind/releases/tag/1.2.6
[js]: https://github.com/ethereumjs/ethereumjs-vm/releases/tag/v4.1.2
[a]: https://github.com/ethereum/aleth/releases/tag/v1.8.0
[t]: https://github.com/ethereum/trinity/releases/tag/v0.1.0-alpha.34
"""

from ethereum.fork_criteria import ByBlockNumber

FORK_CRITERIA = ByBlockNumber(9200000)
