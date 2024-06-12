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
| **Geth**       | [Merged](https://github.com/ethereum/go-ethereum/pull/26003) + [Merged](https://github.com/ethereum/go-ethereum/pull/27663)| - | [Merged](https://github.com/ethereum/go-ethereum/pull/26940) | [Merged](https://github.com/ethereum/go-ethereum/pull/26181) | [Not merged](https://github.com/ethereum/go-ethereum/pull/27189) | |
| **Besu**       | [Merged](https://github.com/hyperledger/besu/pull/4118) | - | [Merged]([https://github.com/hyperledger/besu/tree/eip-4844-interop](https://github.com/hyperledger/besu/pull/5724)) | [Merged](https://github.com/hyperledger/besu/pull/5493) | [Merged](https://github.com/hyperledger/besu/pull/4118) | |
| **Nethermind** | [Merged](https://github.com/NethermindEth/nethermind/pull/4126) | [Merged](https://github.com/NethermindEth/nethermind/pull/6009) | [Merged (many PRs)](https://github.com/NethermindEth/nethermind/issues?q=is%3Aclosed+label%3Aeip-4844) | [Merged](https://github.com/NethermindEth/nethermind/pull/5791) | [Merged](https://github.com/NethermindEth/nethermind/pull/4704) | [Merged](https://github.com/NethermindEth/nethermind/pull/6096) |
| **Erigon**     | [Merged](https://github.com/ledgerwatch/erigon/pull/7405) + [Merged](https://github.com/ledgerwatch/erigon/pull/7885) | [Merged (many PRs)](https://github.com/ledgerwatch/erigon/pulls?q=is%3Apr+4788) | [Merged (many PRs)](https://github.com/ledgerwatch/erigon/pulls?q=is%3Apr+4844) | [Merged](https://github.com/ledgerwatch/erigon/pull/7887) | [Merged](https://github.com/ledgerwatch/erigon/pull/7976) | [Merged](https://github.com/ledgerwatch/erigon/pull/8231) |
| **EthereumJS** | [Merged](https://github.com/ethereumjs/ethereumjs-monorepo/pull/1860) | [Merged](https://github.com/ethereumjs/ethereumjs-monorepo/pull/2810) | [Merged (many PRs)](https://github.com/ethereumjs/ethereumjs-monorepo/pulls?q=is%3Apr+4844) | [Merged](https://github.com/ethereumjs/ethereumjs-monorepo/pull/2808) | [Merged](https://github.com/ethereumjs/ethereumjs-monorepo/pull/2771) | |

### Upgrade Schedule

| Network | Timestamp    | Date & Time (UTC)       | Fork Hash    | Beacon Chain Epoch |
|---------|--------------|-------------------------|--------------| ------------------ |
| Goerli  | `1705473120` | 2024-01-17 06:32:00     | `0x70cc14e2` | 231680 
| Sepolia | `1706655072` | 2024-01-30 22:51:12     | `0x88cf81d9` | 132608 
| Holesky | `1707305664` | 2024-02-07 11:34:24     | `0x9b192ad0` | 29696 
| Mainnet | `1710338135` | 2024-03-13 13:55:35     | `0x9f3d2254` | 269568 


### Readiness Checklist

**List of outstanding items before deployment.**

- [x] Client Integration Testing
  - [x] [Devnets](https://github.com/ethpandaops/dencun-testnet)
  - [x] [Testing suites](https://notes.ethereum.org/@ethpandaops/dencun-testing-overview)
 - [x] Select Testnet Fork Blocks
 - [x] Select Mainnet Fork Block
 - [ ] Release Mainnet Compatible Clients
   - [ ]  Geth
   - [ ]  Besu
   - [ ]  Nethermind
   - [ ]  OpenEthereum
   - [ ]  Erigon
   - [ ]  EthereumJS
