"""
The London fork overhauls the transaction fee market, changes gas refunds,
reserves a contract prefix for future use, and delays the difficulty bomb.

### Changes

- [EIP-1559: Fee market change for ETH 1.0 chain][EIP-1559]
- [EIP-3198: BASEFEE opcode][EIP-3198]
- [EIP-3529: Reduction in refunds][EIP-3529]
- [EIP-3541: Reject new contract code starting with the 0xEF byte][EIP-3541]
- [EIP-3554: Difficulty Bomb Delay to December 2021][EIP-3554]

### Upgrade Schedule

| Network | Block        | Expected Date    | Fork Hash    |
| ------- | ------------ | ---------------- | ------------ |
| Ropsten | 10,499,401   |   June 24, 2021  | `0x7119b6b3` |
| Goerli  |  5,062,605   |   June 30, 2021  | `0xb8c6299d` |
| Rinkeby |  9,987,988   |    July 7, 2021  | `0x8e29f2f3` |
| Mainnet | 12,965,000   |  August 5, 2021  | `0x0eb440f6` |
| Kovan   | 26,741,100   | August 12, 2021  |              |


### Releases

- [Besu 21.7.2]
- [Erigon 2021.07.04-alpha][e]
- [EthereumJS 5.5.0][js]
- [Geth 1.10.6]
- [Nethermind 1.10.79][n]
- [OpenEthereum 3.3.0-rc.4][oe]

[EIP-1559]: https://eips.ethereum.org/EIPS/eip-1559
[EIP-3198]: https://eips.ethereum.org/EIPS/eip-3198
[EIP-3529]: https://eips.ethereum.org/EIPS/eip-3529
[EIP-3541]: https://eips.ethereum.org/EIPS/eip-3541
[EIP-3554]: https://eips.ethereum.org/EIPS/eip-3554
[Besu 21.7.2]: https://github.com/hyperledger/besu/releases/tag/21.7.2
[e]: https://github.com/ledgerwatch/erigon/releases/tag/v2021.07.04
[js]: https://github.com/ethereumjs/ethereumjs-monorepo/releases/tag/%40ethereumjs%2Fvm%405.5.0
[Geth 1.10.6]: https://github.com/ethereum/go-ethereum/releases/tag/v1.10.6
[n]: https://github.com/NethermindEth/nethermind/releases/tag/1.10.79
[oe]: https://github.com/openethereum/openethereum/releases/tag/v3.3.0-rc.4
"""  # noqa: E501

from ethereum.fork_criteria import ByBlockNumber

FORK_CRITERIA = ByBlockNumber(12965000)
