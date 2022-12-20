## Shanghai Network Upgrade Specification

### Included EIPs
Changes included in the Network Upgrade.

* [EIP-3540: EVM Object Format (EOF) v1](https://eips.ethereum.org/EIPS/eip-3540)
* [EIP-3651: Warm COINBASE](https://eips.ethereum.org/EIPS/eip-3651)
* [EIP-3670: EOF - Code Validation](https://eips.ethereum.org/EIPS/eip-3670)
* [EIP-3855: PUSH0 instruction](https://eips.ethereum.org/EIPS/eip-3855)
* [EIP-3860: Limit and meter initcode](https://eips.ethereum.org/EIPS/eip-3860)
* [EIP-4200: EOF - Static relative jumps](https://eips.ethereum.org/EIPS/eip-4200)
* [EIP-4750: EOF - Functions](https://eips.ethereum.org/EIPS/eip-4750)
* [EIP-4895: Beacon chain push withdrawals as operations](https://eips.ethereum.org/EIPS/eip-4895)
* [EIP-5450: EOF - Stack Validation](https://eips.ethereum.org/EIPS/eip-5450)

### Implementation Progresss

Implementation status of Included & CFI'd EIPs across participating clients.

| EIP            | [EIP-3540](https://eips.ethereum.org/EIPS/eip-3540)                   | [EIP-3651](https://eips.ethereum.org/EIPS/eip-3651)                   | [EIP-3670](https://eips.ethereum.org/EIPS/eip-3670)                   | [EIP-3855](https://eips.ethereum.org/EIPS/eip-3855)                   | [EIP-3860](https://eips.ethereum.org/EIPS/eip-3860)                   | [EIP-4200](https://eips.ethereum.org/EIPS/eip-4200)                 | [EIP-4750](https://eips.ethereum.org/EIPS/eip-4750)                 | [EIP-4895](https://eips.ethereum.org/EIPS/eip-4895)                                                                        | [EIP-5450](https://eips.ethereum.org/EIPS/eip-5450)                 |
|----------------|-----------------------------------------------------------------------|-----------------------------------------------------------------------|-----------------------------------------------------------------------|-----------------------------------------------------------------------|-----------------------------------------------------------------------|---------------------------------------------------------------------|---------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------|
| **Geth**       | [Not merged](https://github.com/ethereum/go-ethereum/pull/22958)      | [Merged](https://github.com/ethereum/go-ethereum/pull/25819)          | [Not merged](https://github.com/ethereum/go-ethereum/pull/26133)      | [Merged](https://github.com/ethereum/go-ethereum/pull/24039)          | [Not merged](https://github.com/ethereum/go-ethereum/pull/23847)      | [Not merged](https://github.com/ethereum/go-ethereum/pull/26133)    | [Not merged](https://github.com/ethereum/go-ethereum/pull/26133)    | [Not merged](https://github.com/ethereum/go-ethereum/pull/25838)                                                           | [Not merged](https://github.com/ethereum/go-ethereum/pull/26133)    |
| **Besu**       | [Merged](https://github.com/hyperledger/besu/pull/4644)               | [Merged](https://github.com/hyperledger/besu/pull/4620)               | [Merged](https://github.com/hyperledger/besu/pull/4644)               | [Merged](https://github.com/hyperledger/besu/pull/4660)               | [Merged](https://github.com/hyperledger/besu/pull/4726)               | [Merged](https://github.com/hyperledger/besu/pull/4760)         | [Merged](https://github.com/hyperledger/besu/pull/4781)         | [Not merged](https://github.com/hyperledger/besu/pull/4552)                                                                | [Not merged](https://github.com/hyperledger/besu/pull/4805)         |
| **Nethermind** | [Not merged](https://github.com/NethermindEth/nethermind/pull/4608)   | [Merged](https://github.com/NethermindEth/nethermind/pull/4594)       | [Not merged](https://github.com/NethermindEth/nethermind/pull/4609)   | [Merged](https://github.com/NethermindEth/nethermind/pull/4599)       | [Merged](https://github.com/NethermindEth/nethermind/pull/4740)       | [Not merged](https://github.com/NethermindEth/nethermind/pull/4864) | [Not merged](https://github.com/NethermindEth/nethermind/pull/4865) | [Not merged](https://github.com/NethermindEth/nethermind/pull/4731)                                                        | [Not merged](https://github.com/NethermindEth/nethermind/pull/4950) |
| **Erigon**     | [Not merged](https://github.com/ledgerwatch/erigon/pull/6382)         | [Merged](https://github.com/ledgerwatch/erigon/pull/5745)             | [Not merged](https://github.com/ledgerwatch/erigon/pull/6382)         | [Merged](https://github.com/ledgerwatch/erigon/pull/5256)             | [Merged](https://github.com/ledgerwatch/erigon/pull/5892)             | [Not merged](https://github.com/ledgerwatch/erigon/pull/6382)       | [Not merged](https://github.com/ledgerwatch/erigon/pull/6382)       | Partly merged ([1](https://github.com/ledgerwatch/erigon/pull/6009), [2](https://github.com/ledgerwatch/erigon/pull/6180)) | [Not merged](https://github.com/ledgerwatch/erigon/pull/6382)       |
| **EthereumJS** | [Merged](https://github.com/ethereumjs/ethereumjs-monorepo/pull/1719) | [Merged](https://github.com/ethereumjs/ethereumjs-monorepo/pull/1814) | [Merged](https://github.com/ethereumjs/ethereumjs-monorepo/pull/1743) | [Merged](https://github.com/ethereumjs/ethereumjs-monorepo/pull/1616) | [Merged](https://github.com/ethereumjs/ethereumjs-monorepo/pull/1619) | [Not merged](https://github.com/ethereumjs/ethereumjs-monorepo/pull/2446)                                                                 | [Not merged](https://github.com/ethereumjs/ethereumjs-monorepo/pull/2453)                                                  | [Merged](https://github.com/ethereumjs/ethereumjs-monorepo/pull/2353) | [Not merged](https://github.com/ethereumjs/ethereumjs-monorepo/pull/2453)

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
