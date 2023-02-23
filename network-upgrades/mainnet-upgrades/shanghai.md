## Shanghai Network Upgrade Specification

### Included EIPs
Changes included in the Network Upgrade.

* [EIP-3651: Warm COINBASE](https://eips.ethereum.org/EIPS/eip-3651)
* [EIP-3855: PUSH0 instruction](https://eips.ethereum.org/EIPS/eip-3855)
* [EIP-3860: Limit and meter initcode](https://eips.ethereum.org/EIPS/eip-3860)
* [EIP-4895: Beacon chain push withdrawals as operations](https://eips.ethereum.org/EIPS/eip-4895)
* [EIP-6049: Deprecate SELFDESTRUCT](https://eips.ethereum.org/EIPS/eip-6049)
    * **Note: EIP-6049 does not change the behavior of `SELFDESTRUCT` in and of itself, but formally announces client developers' intention of changing it in future upgrades. It is recommended that software which exposes the `SELFDESTRUCT` opcode to users warn them about an upcoming change in semantics.**

### Upgrade Schedule

| Network | Timestamp  | Date & Time (UTC)  | Fork Hash    | Beacon Chain Epoch |
|---------|------------|---------------|--------------| ---------- |
| Sepolia | `1677557088` | 2/28/2023, 4:04:48 AM | `0xf7f9bc08` | 56832 
| Goerli  | TBA | TBA |  TBA | TBA 
| Mainnet | TBA | TBA |  TBA | TBA 

### Implementation Progresss

Implementation status of Included & CFI'd EIPs across participating clients.

 EIP            | [EIP-3651](https://eips.ethereum.org/EIPS/eip-3651)                   | [EIP-3855](https://eips.ethereum.org/EIPS/eip-3855)                   | [EIP-3860](https://eips.ethereum.org/EIPS/eip-3860)                   | [EIP-4895](https://eips.ethereum.org/EIPS/eip-4895)                                                                        |
|----------------|-----------------------------------------------------------------------|-----------------------------------------------------------------------|-----------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------|
| **Geth**       | [Merged](https://github.com/ethereum/go-ethereum/pull/25819)          | [Merged](https://github.com/ethereum/go-ethereum/pull/24039)          | [Merged](https://github.com/ethereum/go-ethereum/pull/23847)      | [Merged](https://github.com/ethereum/go-ethereum/pull/26484)                                                           |
| **Besu**       | [Merged](https://github.com/hyperledger/besu/pull/4620)               | [Merged](https://github.com/hyperledger/besu/pull/4660)               | [Merged](https://github.com/hyperledger/besu/pull/4726)               | [Merged](https://github.com/hyperledger/besu/pull/4968)                                                                |
| **Nethermind** | [Merged](https://github.com/NethermindEth/nethermind/pull/4594)       | [Merged](https://github.com/NethermindEth/nethermind/pull/4599)       | [Merged](https://github.com/NethermindEth/nethermind/pull/4740)       | [Merged](https://github.com/NethermindEth/nethermind/pull/4731)                                                        |
| **Erigon**     | [Merged](https://github.com/ledgerwatch/erigon/pull/5745)             | [Merged](https://github.com/ledgerwatch/erigon/pull/5256)             | Merged ([1](https://github.com/ledgerwatch/erigon/pull/5892), [2](https://github.com/ledgerwatch/erigon/pull/6499))             | Merged ([1](https://github.com/ledgerwatch/erigon/pull/6009), [2](https://github.com/ledgerwatch/erigon/pull/6180), [3](https://github.com/ledgerwatch/erigon/pull/6496)) |
| **EthereumJS** | [Merged](https://github.com/ethereumjs/ethereumjs-monorepo/pull/1814) | [Merged](https://github.com/ethereumjs/ethereumjs-monorepo/pull/1616) | [Merged](https://github.com/ethereumjs/ethereumjs-monorepo/pull/1619) | [Merged](https://github.com/ethereumjs/ethereumjs-monorepo/pull/2353)                                                      |


### Readiness Checklist

**List of outstanding items before deployment.**

- [x] Client Integration Testing
  - [x] Deploy a Client Integration Testnet
  - [x] Integration Tests
  - [x] Fuzz Testing
 - [ ] Select Fork Timestamps
  - [x] Sepolia
  - [ ] Goerli
  - [ ] Mainnet 
 - [ ] Deploy Clients
   - [ ]  Geth
   - [ ]  Besu
   - [ ]  Nethermind
   - [ ]  OpenEthereum
   - [ ]  Erigon
   - [ ]  EthereumJS
 - [ ] Activate Fork
