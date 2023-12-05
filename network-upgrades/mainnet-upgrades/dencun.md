---
eip: 7569
title: Hardfork Meta - Dencun
description: EIPs included in the Deneb/Cancun Ethereum network upgrade.
author: Tim Beiko (@timbeiko)
discussions-to: https://ethereum-magicians.org/t/dencun-hardfork-meta/16924
status: Draft
type: Meta
created: 2023-12-01
requires: 1153, 4788, 4844, 5656, 6780, 7044, 7045, 7514, 7516
---

## Abstract

This meta-EIP specifies the changes included in the Ethereum hardfork named Dencun.

### Full Specifications

#### Consensus Layer

EIPs 4788, 4844, 7044, 7045 and 7514 require changes to Ethereum's consensus layer. These are specified in the `deneb` folder of the `ethereum/consensus-specs` repository.

#### Execution Layer

EIPs 1153, 4788, 4844, 5656, 6780 and 7526 require changes to Ethereum's execution layer. The EIPs fully specify the changes.

### Activation

| Network Name     | Activation Epoch | Activation Timestamp |
|------------------|------------------|----------------------|
| Goerli           |                  |                      |
| Sepolia          |                  |                      |
| Holesky          |                  |                      |
| Mainnet          |                  |                      |

### Included EIPs

* [EIP-1153: Transient storage opcodes](https://eips.ethereum.org/EIPS/eip-1153)
* [EIP-4788: Beacon block root in the EVM ](https://eips.ethereum.org/EIPS/eip-4788)
* [EIP-4844: Shard Blob Transactions](https://eips.ethereum.org/EIPS/eip-4844)
* [EIP-5656: MCOPY - Memory copying instruction](https://eips.ethereum.org/EIPS/eip-5656)
* [EIP-6780: SELFDESTRUCT only in same transaction](https://eips.ethereum.org/EIPS/eip-6780)
* [EIP-7044: Perpetually Valid Signed Voluntary Exits](https://eips.ethereum.org/EIPS/eip-7044)
* [EIP-7045: Increase Max Attestation Inclusion Slot](https://eips.ethereum.org/EIPS/eip-7045)
* [EIP-7514: Add Max Epoch Churn Limit](https://eips.ethereum.org/EIPS/eip-7514)
* [EIP-7516: BLOBBASEFEE opcode](https://eips.ethereum.org/EIPS/eip-7516)

## References

1. [meta-EIP for Dencun](https://github.com/ethereum/EIPs/pull/8006/files)

## Copyright

Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).