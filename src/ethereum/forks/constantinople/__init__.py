"""
The Constantinople fork reduces mining rewards, delays the difficulty bomb,
and introduces new EVM instructions for logical shifts, counterfactual
contract deployment, and computing bytecode hashes.

Note that, on certain testnets, this fork is divided in two: Constantinople
followed by Petersburg. On these testnets, Constantinople contains an
additional change, [EIP-1283], which was reverted in Petersburg. Because
EIP-1283 was never present on mainnet, this specification omits the whole
awkward situation and presents only a single fork without EIP-1283.

### Changes

- [EIP-145: Bitwise shifting instructions in EVM][EIP-145]
- [EIP-1014: Skinny CREATE2][EIP-1014]
- [EIP-1052: EXTCODEHASH opcode][EIP-1052]
- [EIP-1234: Constantinople Difficulty Bomb Delay and Block Reward
  Adjustment][EIP-1234]

### Upgrade Schedule

| Network | Block      | Expected Date     | Fork Hash    |
| ------- |----------- | ----------------- | ------------ |
| Mainnet |  7,280,000 | February 28, 2019 | `0x668db0af` |

### Releases

- [EthereumJS 2.6.0][js]
- [Geth 1.8.23]
- [Harmony 2.3b74][h]
- [Nethermind 0.9.4][n]
- [Pantheon 0.9.1][pan]
- [Parity 2.2.10-stable][p]
- [Trinity 0.1.0-alpha.23][t]

[EIP-1283]: https://eips.ethereum.org/EIPS/eip-1283
[EIP-145]: https://eips.ethereum.org/EIPS/eip-145
[EIP-1014]: https://eips.ethereum.org/EIPS/eip-1014
[EIP-1052]: https://eips.ethereum.org/EIPS/eip-1052
[EIP-1234]: https://eips.ethereum.org/EIPS/eip-1234
[js]: https://github.com/ethereumjs/ethereumjs-vm/releases/tag/v2.6.0
[Geth 1.8.23]: https://github.com/ethereum/go-ethereum/releases/tag/v1.8.23
[h]: https://github.com/ether-camp/ethereum-harmony/releases/tag/v2.3b74
[n]: https://github.com/NethermindEth/nethermind/releases/tag/v0.9.4
[pan]: https://github.com/PegaSysEng/pantheon/releases/tag/0.9.1
[t]: https://github.com/ethereum/trinity/releases/tag/v0.1.0-alpha.23
"""  # noqa: E501

from ethereum.fork_criteria import ByBlockNumber

FORK_CRITERIA = ByBlockNumber(7280000)
