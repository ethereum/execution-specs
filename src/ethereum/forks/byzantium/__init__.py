"""
The Byzantium fork ([EIP-609]) reduces the mining rewards, delays the
difficulty bomb, enables contracts to make non-state-changing calls to other
contracts, and adds cryptographic primitives for layer 2 scaling.

### Changes

- [EIP-100: Change difficulty adjustment to target mean block time including
  uncles][EIP-100]
- [EIP-140: REVERT instruction in the Ethereum Virtual Machine][EIP-140]
- [EIP-196: Precompiled contracts for addition and scalar multiplication on the
  elliptic curve alt_bn128][EIP-196]
- [EIP-197: Precompiled contracts for optimal ate pairing check on the elliptic
  curve alt_bn128][EIP-197]
- [EIP-198: Precompiled contract for bigint modular exponentiation][EIP-198]
- [EIP-211: New opcodes: RETURNDATASIZE and RETURNDATACOPY][EIP-211]
- [EIP-214: New opcode STATICCALL][EIP-214]
- [EIP-649: Difficulty Bomb Delay and Block Reward Reduction][EIP-649]
- [EIP-658: Embedding transaction status code in receipts][EIP-658]

### Upgrade Schedule

| Network | Block        | Expected Date    | Fork Hash    |
| ------- | ------------ | ---------------- | ------------ |
| Mainnet | 4,370,000    | October 16, 2017 | `0xa00bc324` |

### Releases

- [Harmony 2.1.0][h]
- [Geth 1.7.2]
- [Parity 1.7.6][p]

[EIP-100]: https://eips.ethereum.org/EIPS/eip-100
[EIP-140]: https://eips.ethereum.org/EIPS/eip-140
[EIP-196]: https://eips.ethereum.org/EIPS/eip-196
[EIP-197]: https://eips.ethereum.org/EIPS/eip-197
[EIP-198]: https://eips.ethereum.org/EIPS/eip-198
[EIP-211]: https://eips.ethereum.org/EIPS/eip-211
[EIP-214]: https://eips.ethereum.org/EIPS/eip-214
[EIP-609]: https://eips.ethereum.org/EIPS/eip-609
[EIP-649]: https://eips.ethereum.org/EIPS/eip-649
[EIP-658]: https://eips.ethereum.org/EIPS/eip-658
[h]: https://github.com/ether-camp/ethereum-harmony/releases/tag/v2.1b56
[Geth 1.7.2]: https://github.com/ethereum/go-ethereum/releases/tag/v1.7.2
[p]: https://github.com/paritytech/parity/releases/tag/v1.7.6
"""

from ethereum.fork_criteria import ByBlockNumber

FORK_CRITERIA = ByBlockNumber(4370000)
