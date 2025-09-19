"""
The Paris fork transitions Ethereum from a proof-of-work consensus model to a
proof-of-stake one. This fork is often referred to as "The Merge" because it
marks the integration of the [consensus layer] with the execution layer
(defined in this project).

### Changes

- [EIP-3675: Upgrade consensus to Proof-of-Stake][EIP-3675]
- [EIP-4399: Supplant DIFFICULTY opcode with PREVRANDAO][EIP-4399]

### Upgrade Schedule

| Network | Terminal Total Difficulty      | Expected Date      | Fork Hash    |
| ------- | ------------------------------ | ------------------ | ------------ |
| Ropsten | 50,000,000,000,000,000         | June 8, 2022       | `0x7119B6B3` |
| Sepolia | 17,000,000,000,000,000         | July 6, 2022       | `0xfe3366e7` |
| Goerli  | 10,790,000                     | August 10, 2022    | `0xB8C6299D` |
| Mainnet | 58,750,000,000,000,000,000,000 | September 15, 2022 | `0xf0afd0e3` |

### Releases

- [Besu 22.7.2]
- [Erigon 2022.09.01][e]
- [Geth 1.10.23]
- [Nethermind 1.14.1][nm]

[consensus layer]: https://github.com/ethereum/consensus-specs
[EIP-3675]: https://eips.ethereum.org/EIPS/eip-3675
[EIP-4399]: https://eips.ethereum.org/EIPS/eip-4399
[Besu 22.7.2]: https://github.com/hyperledger/besu/releases/tag/22.7.2
[e]: https://github.com/ledgerwatch/erigon/releases/tag/v2022.09.01
[Geth 1.10.23]: https://github.com/ethereum/go-ethereum/releases/tag/v1.10.23
[nm]: https://github.com/NethermindEth/nethermind/releases/tag/1.14.1
"""  # noqa: E501

from ethereum.fork_criteria import ByBlockNumber

# The actual trigger for the Paris hardfork was The Merge occurring when
# total difficulty (the sum of the all block difficulties) reached the
# Terminal Total Difficulty value (58750000000000000000000 on Mainnet). The
# Merge is now a historical event.
FORK_CRITERIA = ByBlockNumber(15537394)
