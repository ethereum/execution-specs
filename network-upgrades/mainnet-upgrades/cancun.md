## Cancun Network Upgrade Specification

### Included EIPs
Execution layer changes included in the Network Upgrade.

* [EIP-1153: Transient storage opcodes](https://eips.ethereum.org/EIPS/eip-1153)
* [EIP-4788: Beacon block root in the EVM ](https://eips.ethereum.org/EIPS/eip-4788)
* [EIP-4844: Shard Blob Transactions](https://eips.ethereum.org/EIPS/eip-4844)
* [EIP-5656: MCOPY - Memory copying instruction](https://eips.ethereum.org/EIPS/eip-5656)
* [EIP-6780: SELFDESTRUCT only in same transaction](https://eips.ethereum.org/EIPS/eip-6780)
* [EIP-7516: BLOBBASEFEE opcode](https://eips.ethereum.org/EIPS/eip-7516)

### Implementation Progresss

Implementation status of Included EIPs across participating clients.

|                | [1153](https://eips.ethereum.org/EIPS/eip-1153) | [4788](https://eips.ethereum.org/EIPS/eip-4788) | [4844](https://eips.ethereum.org/EIPS/eip-4844) | [5656](https://eips.ethereum.org/EIPS/eip-5656) | [6780](https://eips.ethereum.org/EIPS/eip-6780) | [7516](https://eips.ethereum.org/EIPS/eip-7516) |
|----------------|-------------------------------------------------|-------------------------------------------------|-------------------------------------------------|-------------------------------------------------|-------------------------------------------------|-------------------------------------------------|
| **Geth**       | [Merged](https://github.com/ethereum/go-ethereum/pull/26003) + [Merged](https://github.com/ethereum/go-ethereum/pull/27663)| - | [Not merged](https://github.com/ethereum/go-ethereum/pull/26940) | [Merged](https://github.com/ethereum/go-ethereum/pull/26181) | [Not merged](https://github.com/ethereum/go-ethereum/pull/27189) | |
| **Besu**       | [Merged](https://github.com/hyperledger/besu/pull/4118) | - | [Merged]([https://github.com/hyperledger/besu/tree/eip-4844-interop](https://github.com/hyperledger/besu/pull/5724)) | [Merged](https://github.com/hyperledger/besu/pull/5493) | [Merged](https://github.com/hyperledger/besu/pull/4118) | |
| **Nethermind** | [Merged](https://github.com/NethermindEth/nethermind/pull/4126) | [Not merged](https://github.com/NethermindEth/nethermind/pull/5476) | [Not merged (many PRs)](https://github.com/NethermindEth/nethermind/pull/5671) | [Not merged](https://github.com/NethermindEth/nethermind/pull/5791) | [Not merged](https://github.com/NethermindEth/nethermind/pull/4704) | |
| **Erigon**     | [Merged](https://github.com/ledgerwatch/erigon/pull/7405) + [Merged](https://github.com/ledgerwatch/erigon/pull/7885) | [Merged (many PRs)](https://github.com/ledgerwatch/erigon/pulls?q=is%3Apr+4788) | [Merged (many PRs)](https://github.com/ledgerwatch/erigon/pulls?q=is%3Apr+4844) | [Merged](https://github.com/ledgerwatch/erigon/pull/7887) | [Merged](https://github.com/ledgerwatch/erigon/pull/7976) | [Merged](https://github.com/ledgerwatch/erigon/pull/8231) |
| **EthereumJS** | [Merged](https://github.com/ethereumjs/ethereumjs-monorepo/pull/1860) | [Merged](https://github.com/ethereumjs/ethereumjs-monorepo/pull/2810) | [Merged (many PRs)](https://github.com/ethereumjs/ethereumjs-monorepo/pulls?q=is%3Apr+4844) | [Merged](https://github.com/ethereumjs/ethereumjs-monorepo/pull/2808) | [Merged](https://github.com/ethereumjs/ethereumjs-monorepo/pull/2771) | |



### Readiness Checklist

**List of outstanding items before deployment.**

- [x] Client Integration Testing
  - [x] [Devnets](https://github.com/ethpandaops/dencun-testnet)
  - [x] [Testing suites](https://notes.ethereum.org/@ethpandaops/dencun-testing-overview)
 - [ ] Select Testnet Fork Blocks
 - [ ] Select Mainnet Fork Block
 - [ ] Release Mainnet Compatible Clients
   - [ ]  Geth
   - [ ]  Besu
   - [ ]  Nethermind
   - [ ]  OpenEthereum
   - [ ]  Erigon
   - [ ]  EthereumJS