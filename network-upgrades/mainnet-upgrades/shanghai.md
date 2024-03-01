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
| Goerli  | `1678832736` | 3/14/2023, 10:25:36 PM	 |  `0xf9843abf` | 162304 
| Mainnet | `1681338455` | 4/12/2023, 10:27:35 PM |  `0xdce96c2d` | 194048 

### Implementation Progress

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
 - [x] Select Fork Timestamps
   - [x] Sepolia
   - [x] Goerli
   - [x] Mainnet 
 - [x] Deploy Clients
   - [x]  Geth [v1.11.5](https://github.com/ethereum/go-ethereum/releases/tag/v1.11.5)
   - [x]  Besu [v23.1.2](https://github.com/hyperledger/besu/releases/tag/23.1.2)
   - [x]  Nethermind [v1.17.3](https://github.com/NethermindEth/nethermind/releases/tag/1.17.3)
   - [x]  Erigon [v2.41.0](https://github.com/ledgerwatch/erigon/releases/tag/v2.41.0)
   - [x]  EthereumJS [vm v6.4.0](https://github.com/ethereumjs/ethereumjs-monorepo/releases/tag/%40ethereumjs%2Fvm%406.4.0)
 - [ ] Activate Fork
