"""
The DAO Fork ([EIP-779]) is a response to a smart contract exploit known as the
2016 DAO Attack where a vulnerable contract was drained of its ether. This fork
recovers the stolen funds into a new contract.

### Changes

- Transfer ether from a [list of accounts][l] into the [Withdraw DAO][r]
  contract

### Upgrade Schedule

| Network | Block       | Expected Date | Fork Hash    |
| ------- | ----------- | ------------- | ------------ |
| Mainnet | 1,920,000   | July 20, 1026 | `0x91d1f948` |

### Releases

- [Geth 1.4.10]

[l]: ref:ethereum.forks.dao_fork.dao.DAO_ACCOUNTS
[r]: ref:ethereum.forks.dao_fork.dao.DAO_RECOVERY
[EIP-779]: https://eips.ethereum.org/EIPS/eip-779
[Geth 1.4.10]: https://github.com/ethereum/go-ethereum/releases/tag/v1.4.10
"""

from ethereum.fork_criteria import ByBlockNumber

FORK_CRITERIA = ByBlockNumber(1920000)
