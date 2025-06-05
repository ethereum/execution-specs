---
eip: 1679
title: "Hardfork Meta: Istanbul"
author: Alex Beregszaszi (@axic), Afri Schoedon (@5chdn)
discussions-to: https://ethereum-magicians.org/t/hardfork-meta-istanbul-discussion/3207
type: Meta
status: Final
created: 2019-01-04
requires: 152, 1108, 1344, 1716, 1884, 2028, 2200
legacy link: https://eips.ethereum.org/EIPS/eip-1679
---

## Abstract

This meta-EIP specifies the changes included in the Ethereum hardfork named Istanbul.

## Specification

- Codename: Istanbul

### Activation
  - `Block >= 9,069,000` on the Ethereum mainnet
  - `Block >= 6,485,846` on the Ropsten testnet
  - `Block >= 14,111,141` on the Kovan testnet
  - `Block >= 5,435,345` on the Rinkeby testnet
  - `Block >= 1,561,651` on the Görli testnet

### Included EIPs
  - [EIP-152](https://eips.ethereum.org/EIPS/eip-152): Add Blake2 compression function `F` precompile
  - [EIP-1108](https://eips.ethereum.org/EIPS/eip-1108): Reduce alt_bn128 precompile gas costs
  - [EIP-1344](https://eips.ethereum.org/EIPS/eip-1344): Add ChainID opcode
  - [EIP-1884](https://eips.ethereum.org/EIPS/eip-1884): Repricing for trie-size-dependent opcodes
  - [EIP-2028](https://eips.ethereum.org/EIPS/eip-2028): Calldata gas cost reduction
  - [EIP-2200](https://eips.ethereum.org/EIPS/eip-2200): Rebalance net-metered SSTORE gas cost with consideration of SLOAD gas cost change

## References

1. Included EIPs were finalized in [All Core Devs Call #68](https://github.com/ethereum/pm/blob/master/AllCoreDevs-EL-Meetings/Meeting%2068.md)
2. https://medium.com/ethereum-cat-herders/istanbul-testnets-are-coming-53973bcea7df

## Copyright

Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
