"""
The Istanbul fork ([EIP-1679]) makes changes to the gas costs of EVM
instructions and data, adds a cryptographic primitive, and introduces an
instruction to fetch the current chain identifier.

### Changes

- [EIP-152: Add BLAKE2 compression function `F` precompile][EIP-152]
- [EIP-1108: Reduce alt_bn128 precompile gas costs][EIP-1108]
- [EIP-1344: ChainID opcode][EIP-1344]
- [EIP-1884: Repricing for trie-size-dependent opcodes][EIP-1884]
- [EIP-2028: Transaction data gas cost reduction][EIP-2028]
- [EIP-2200: Structured Definitions for Net Gas Metering][EIP-2200]

### Upgrade Schedule

| Network | Block        | Expected Date    | Fork Hash    |
| ------- | ------------ | ---------------- | ------------ |
| Ropsten |  6,485,846   |                  |              |
| Goerli  |  1,561,651   |                  |              |
| Rinkeby |  5,435,345   |                  |              |
| Kovan   | 14,111,141   |                  |              |
| Mainnet |  9,069,000   | December 8, 2019 | `0x879d6e30` |

### Releases

- [Aleth 1.7.1][a]
- [Besu 1.3.6]
- [EthereumJS 4.0.2][js]
- [Geth 1.9.9]
- [Nethermind 1.2.3][n]
- [Parity 2.5.11-stable][p]
- [Trinity 0.1.0-alpha.31][t]

[EIP-1679]: https://eips.ethereum.org/EIPS/eip-1679
[EIP-152]: https://eips.ethereum.org/EIPS/eip-152
[EIP-1108]: https://eips.ethereum.org/EIPS/eip-1108
[EIP-1344]: https://eips.ethereum.org/EIPS/eip-1344
[EIP-1884]: https://eips.ethereum.org/EIPS/eip-1884
[EIP-2028]: https://eips.ethereum.org/EIPS/eip-2028
[EIP-2200]: https://eips.ethereum.org/EIPS/eip-2200
[a]: https://github.com/ethereum/aleth/releases/tag/v1.7.1
[Besu 1.3.6]: https://github.com/hyperledger/besu/releases/tag/1.3.6
[js]: https://github.com/ethereumjs/ethereumjs-blockchain/releases/tag/v4.0.2
[Geth 1.9.9]: https://github.com/ethereum/go-ethereum/releases/tag/v1.9.9
[n]: https://github.com/NethermindEth/nethermind/releases/tag/1.2.3
[p]: https://github.com/paritytech/parity-ethereum/releases/tag/v2.5.11
[t]: https://github.com/ethereum/trinity/releases/tag/v0.1.0-alpha.31
"""

from ethereum.fork_criteria import ByBlockNumber

FORK_CRITERIA = ByBlockNumber(9069000)
