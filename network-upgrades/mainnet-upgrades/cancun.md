## Cancun Network Upgrade Specification

### Included EIPs
Changes included in the Network Upgrade.

* [EIP-1153: Transient storage opcodes](https://eips.ethereum.org/EIPS/eip-1153)
* [EIP-4844: Shard Blob Transactions](https://eips.ethereum.org/EIPS/eip-4844)
* [EIP-6475: SSZ Optional](https://eips.ethereum.org/EIPS/eip-6475)
* [EIP-6780: SELFDESTRUCT only in same transaction](https://eips.ethereum.org/EIPS/eip-6780)

### EIPs Considered for Inclusion
Changes [Considered for Inclusion](https://github.com/ethereum/execution-specs/tree/master/network-upgrades#definitions) as part of this upgrade, or potentially future ones. 

* [EIP-2537: Precompile for BLS12-381 curve operations](https://eips.ethereum.org/EIPS/eip-2537)
* [EIP-4788: Beacon block root in the EVM ](https://eips.ethereum.org/EIPS/eip-4788)
* [EIP-6493: SSZ Transaction Signature Scheme](https://eips.ethereum.org/EIPS/eip-6493)

### Implementation Progresss

Implementation status of Included EIPs across participating clients.

| EIP            | [EIP-1153](https://eips.ethereum.org/EIPS/eip-1153)                   | [EIP-4844](https://eips.ethereum.org/EIPS/eip-4844)                       | [EIP-6475](https://eips.ethereum.org/EIPS/eip-6475) | [EIP-6780](https://eips.ethereum.org/EIPS/eip-6780) |
|----------------|-----------------------------------------------------------------------|---------------------------------------------------------------------------|----------|----------|
| **Geth**       | [Merged](https://github.com/ethereum/go-ethereum/pull/26003)          | [Not merged](https://github.com/ethereum/go-ethereum/pull/26283)          |          | [Not merged](https://github.com/ethereum/go-ethereum/pull/27189)    |
| **Besu**       | [Merged](https://github.com/hyperledger/besu/pull/4118)               | [Not merged](https://github.com/hyperledger/besu/tree/eip-4844-interop)   |          | [Not merged](https://github.com/hyperledger/besu/pull/5430)         |
| **Nethermind** | [Merged](https://github.com/NethermindEth/nethermind/pull/4126)       | [Not merged](https://github.com/NethermindEth/nethermind/pull/4858)       |          | [Not merged](https://github.com/NethermindEth/nethermind/pull/4704) |
| **Erigon**     | [Merged](https://github.com/ledgerwatch/erigon/pull/7405)             |                                                                           |          |          |
| **EthereumJS** | [Merged](https://github.com/ethereumjs/ethereumjs-monorepo/pull/1860) | [Merged](https://github.com/ethereumjs/ethereumjs-monorepo/pull/2349)     |          |          |


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
