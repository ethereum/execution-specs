"""
The Spurious Dragon fork is the second of two forks responding to a
denial-of-service attack on the Ethereum network. It tunes the prices of EVM
instructions, adds protection against replaying transaction on different
chains, limits the maximum size of contract code, and enables the removal of
empty accounts.

### Changes

- [EIP-155: Simple replay attack protection][EIP-155]
- [EIP-160: EXP cost increase][EIP-160]
- [EIP-161: State trie clearing (invariant-preserving alternative)][EIP-161]
- [EIP-170: Contract code size limit][EIP-170]

### Upgrade Schedule

| Network | Block        | Expected Date     | Fork Hash    |
| ------- | ------------ | ----------------- | ------------ |
| Mainnet | 2,675,000    | November 22, 2016 | `0x3edd5b10` |

### Releases

- [Geth 1.5.2]
- [Parity 1.4.4][p]
- [ruby-ethereum 0.11.0][rb]

[EIP-155]: https://eips.ethereum.org/EIPS/eip-155
[EIP-160]: https://eips.ethereum.org/EIPS/eip-160
[EIP-161]: https://eips.ethereum.org/EIPS/eip-161
[EIP-170]: https://eips.ethereum.org/EIPS/eip-170
[Geth 1.5.2]: https://github.com/ethereum/go-ethereum/releases/tag/v1.5.2
[p]: https://github.com/paritytech/parity/releases/tag/v1.4.4
[rb]: https://github.com/cryptape/ruby-ethereum/releases/tag/v0.11.0
"""

from ethereum.fork_criteria import ByBlockNumber

FORK_CRITERIA = ByBlockNumber(2675000)
