## Cancun Network Upgrade Specification

### Included EIPs
Changes included in the Network Upgrade.

* [EIP-1153: Transient storage opcodes](https://eips.ethereum.org/EIPS/eip-1153)
* [EIP-4788: Beacon block root in the EVM ](https://eips.ethereum.org/EIPS/eip-4788)
* [EIP-4844: Shard Blob Transactions](https://eips.ethereum.org/EIPS/eip-4844)
* [EIP-5656: MCOPY - Memory copying instruction](https://eips.ethereum.org/EIPS/eip-5656)
* [EIP-6780: SELFDESTRUCT only in same transaction](https://eips.ethereum.org/EIPS/eip-6780)

### Implementation Progresss

Implementation status of Included EIPs across participating clients.

|                | [1153](https://eips.ethereum.org/EIPS/eip-1153) | [4788](https://eips.ethereum.org/EIPS/eip-4788) | [4844](https://eips.ethereum.org/EIPS/eip-4844) | [5656](https://eips.ethereum.org/EIPS/eip-5656) | [6780](https://eips.ethereum.org/EIPS/eip-6780) |
|----------------|-------------------------------------------------|-------------------------------------------------|-------------------------------------------------|-------------------------------------------------|-------------------------------------------------|
| **Geth**       | [Merged](https://github.com/ethereum/go-ethereum/pull/26003) + [Merged](https://github.com/ethereum/go-ethereum/pull/27663)| - | [Not merged](https://github.com/ethereum/go-ethereum/pull/26940) | [Merged](https://github.com/ethereum/go-ethereum/pull/26181) | [Not merged](https://github.com/ethereum/go-ethereum/pull/27189) |
| **Besu**       | [Merged](https://github.com/hyperledger/besu/pull/4118) | - | [Not Merged](https://github.com/hyperledger/besu/tree/eip-4844-interop) | - | - |
| **Nethermind** | [Merged](https://github.com/NethermindEth/nethermind/pull/4126) | - | [Not merged](https://github.com/NethermindEth/nethermind/pull/5671) | - | - |
| **Erigon**     | [Merged](https://github.com/ledgerwatch/erigon/pull/7405) | - | [Merged (many PRs)](https://github.com/ledgerwatch/erigon/pulls?q=is%3Apr+4844) | - | - |
| **EthereumJS** | [Merged](https://github.com/ethereumjs/ethereumjs-monorepo/pull/1860) | - | [Merged (many PRs)](https://github.com/ethereumjs/ethereumjs-monorepo/pulls?q=is%3Apr+4844) | - | - |



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
