"""
The Homestead fork increases the gas cost of creating contracts, restricts the
range of valid ECDSA signatures for transactions (but not precompiles), tweaks
the behavior of contract creation with insufficient gas, delays the
difficulty bomb, and adds an improved delegate call EVM instruction.

### Changes

- [EIP-2: Homestead Hard-fork Changes][EIP-2]
- [EIP-7: DELEGATECALL][EIP-7]
- [EIP-8: devp2p Forward Compatibility Requirements for Homestead][EIP-8]

### Upgrade Schedule

| Network | Block        | Expected Date    | Fork Hash    |
| ------- | ------------ | ---------------- | ------------ |
| Morden  |    494,000   |                  |              |
| Mainnet |  1,150,000   |  March 14, 2016  | `0x97c2c34c` |

### Releases

- [CPP Ethereum 1.2.0][cpp]
- [Geth 1.3.5]

[EIP-2]: https://eips.ethereum.org/EIPS/eip-2
[EIP-7]: https://eips.ethereum.org/EIPS/eip-7
[EIP-8]: https://eips.ethereum.org/EIPS/eip-8
[cpp]: https://github.com/ethereum/webthree-umbrella/releases/tag/v1.2.0
[Geth 1.3.5]: https://github.com/ethereum/go-ethereum/releases/tag/v1.3.5
"""

from ethereum.fork_criteria import ByBlockNumber

FORK_CRITERIA = ByBlockNumber(1150000)
