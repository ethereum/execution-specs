## Cancun Network Upgrade Specification

### Included EIPs
Changes included in the Network Upgrade.

* [EIP-4844: Shard Blob Transactions](https://eips.ethereum.org/EIPS/eip-4844)

### EIPs Considered for Inclusion
Changes [Considered for Inclusion](https://github.com/ethereum/execution-specs/tree/master/network-upgrades#definitions) as part of this upgrade, or potentially future ones. 

* [EIP-1153: Transient storage opcodes](https://eips.ethereum.org/EIPS/eip-1153)
* [EIP-2537: Precompile for BLS12-381 curve operations](https://eips.ethereum.org/EIPS/eip-2537)
* [EIP-5920: PAY Opcode](https://eips.ethereum.org/EIPS/eip-5920)

### Implementation Progresss

Implementation status of Included & CFI'd EIPs across participating clients.


| EIP            | [EIP-1153](https://eips.ethereum.org/EIPS/eip-1153)                   | [EIP-2537](https://eips.ethereum.org/EIPS/eip-2537)                  | [EIP-4844](https://eips.ethereum.org/EIPS/eip-4844)                       | [EIP-5920](https://eips.ethereum.org/EIPS/eip-5920) |
|----------------|-----------------------------------------------------------------------|----------------------------------------------------------------------|---------------------------------------------------------------------------|-|
| **Geth**       | [Merged](https://github.com/ethereum/go-ethereum/pull/26003)          | [Merged](https://github.com/ethereum/go-ethereum/pull/21018)         | [Not merged](https://github.com/ethereum/go-ethereum/pull/26283)          | |
| **Besu**       | [Not merged](https://github.com/hyperledger/besu/pull/4118)           | [Merged](https://github.com/hyperledger/besu/pull/964)               |                                                                           | |
| **Nethermind** | [Merged](https://github.com/NethermindEth/nethermind/pull/4126)       |                                                                      | [Not merged](https://github.com/NethermindEth/nethermind/pull/4858)       | |
| **Erigon**     | [Not merged](https://github.com/ledgerwatch/erigon/pull/6133)         |                                                                      |                                                                           | |
| **EthereumJS** | [Merged](https://github.com/ethereumjs/ethereumjs-monorepo/pull/1860) | [Merged](https://github.com/ethereumjs/ethereumjs-monorepo/pull/785) | [Not merged](https://github.com/ethereumjs/ethereumjs-monorepo/pull/2349) | |


### Readiness Checklist

**List of outstanding items before deployment.**

- [ ] Client Integration Testing
  - [ ] Deploy a Client Integration Testnet
  - [ ] Integration Tests
  - [ ] Fuzz Testing
 - [ ] Select Fork Blocks
 - [ ] Deploy Clients
   - [ ]  Geth
   - [ ]  Besu
   - [ ]  Nethermind
   - [ ]  OpenEthereum
   - [ ]  Erigon
   - [ ]  EthereumJS
 - [ ] Pass Fork Blocks
