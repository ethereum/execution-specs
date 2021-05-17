## London Network Upgrade Specification

### Included EIPs
Specifies changes included in the Network Upgrade.

  - [x] [EIP-1559: Fee market change for ETH 1.0 chain](https://eips.ethereum.org/EIPS/eip-1559)
  - [x] [EIP-3198: BASEFEE opcode](https://eips.ethereum.org/EIPS/eip-3198)
  - [x] [EIP-3554: Difficulty Bomb Delay to December 1st 2021](https://eips.ethereum.org/EIPS/eip-3554)
  - [x] [EIP-3529: Reduction in refunds](https://eips.ethereum.org/EIPS/eip-3529)
  - [x] [EIP-3541: Reject new contracts starting with the 0xEF byte](https://eips.ethereum.org/EIPS/eip-3541)


### Client Readiness Checklist
Code merged into Participating Clients

| EIP | [EIP-1559](https://eips.ethereum.org/EIPS/eip-1559) | [EIP-3198](https://eips.ethereum.org/EIPS/eip-3198) | [EIP-3554](https://eips.ethereum.org/EIPS/eip-3554) | [EIP-3529](https://eips.ethereum.org/EIPS/eip-3529) | [EIP-3541](https://eips.ethereum.org/EIPS/eip-3541) | 
|------------------|------|-------|--------|---------|-------|
| **Geth**         | [Not merged](https://github.com/ethereum/go-ethereum/pull/22837) | [Not merged](https://github.com/ethereum/go-ethereum/pull/22837) | [Merged](https://github.com/ethereum/go-ethereum/pull/22870) | [Merged](https://github.com/ethereum/go-ethereum/pull/22733) | [Merged](https://github.com/ethereum/go-ethereum/pull/22809)
| **OpenEthereum** | [Not merged](https://github.com/openethereum/openethereum/pull/393) | [Not merged](https://github.com/openethereum/openethereum/issues/394) | 
| **Besu**         | [Merged](https://github.com/hyperledger/besu/pulls?q=is%3Apr+1559) | [Merged](https://github.com/hyperledger/besu/pull/2123) | | [Merged](https://github.com/hyperledger/besu/pull/2238) | [Merged](https://github.com/hyperledger/besu/pull/2245)
| **Nethermind**   | [Merged](https://github.com/NethermindEth/nethermind/pull/3023) | [Merged](https://github.com/NethermindEth/nethermind/pull/2985)||[Merged](https://github.com/NethermindEth/nethermind/pull/3048) | [Not merged](https://github.com/NethermindEth/nethermind/pull/3059)
| **TurboGeth**    | [Merged](https://github.com/ledgerwatch/turbo-geth/pull/1704) | [Merged](https://github.com/ledgerwatch/turbo-geth/pull/1704) | | [Merged](https://github.com/ledgerwatch/turbo-geth/pull/1853)| [Merged](https://github.com/ledgerwatch/turbo-geth/pull/1853)
| **EthereumJS**   | [Not merged](https://github.com/ethereumjs/ethereumjs-monorepo/pull/1148) | [Not merged](https://github.com/ethereumjs/ethereumjs-monorepo/pull/1148) | [Merged](https://github.com/ethereumjs/ethereumjs-monorepo/pull/1245) | [Merged](https://github.com/ethereumjs/ethereumjs-monorepo/pull/1239) | [Merged](https://github.com/ethereumjs/ethereumjs-monorepo/pull/1240)

#### Client Teams Trackers

* Geth: https://github.com/ethereum/go-ethereum/issues/22736 
* OpenEthereum: https://github.com/openethereum/openethereum/issues/395 

#### Other Tasks
 
- [x] Client Integration Testing
  - [x] Deploy a Client Integration Testnet: [Aleut](https://github.com/ethereum/eth1.0-specs/blob/master/network-upgrades/client-integration-testnets/aleut.md)
  - [ ] Integration Tests: [WIP](https://hackmd.io/@SduYUIHbT6a6DHUpikAcFQ/BJP9arcB_/%2FuID06YEhSj2uFzEviDIaJQ)
  - [ ] Fuzz Testing
 - [ ] Select Fork Blocks
   - [ ] Ropsten: `10399301` (June 9, 2021)
   - [ ] Goerli:  `4979794` (June 16, 2021)
   - [ ] Rinkeby: `8813188` (June 23, 2021)
 - [ ] Deploy Clients
   - [ ]  Geth
   - [ ]  Besu
   - [ ]  Nethermind
   - [ ]  OpenEthereum
   - [ ]  EthereumJS
 - [ ] Pass Fork Blocks

### Ecosystem Readiness Checklist
Tooling, Libraries and other Infrastructure

If you know about a status update please add a PR to this document.

Legend for status updates:

- `-`: EIP not relevant / work not started
- 🛠️ : In progress
- ✅ : Ready

### Tools

| Name | [1559][eip-1559-link] | [3198][eip-3198-link] | Work | Dependencies | Status
|---|---|---|---|---|---|
| [Blocknative][blocknative-link]        | - | - |          | -      | - 
| [Hardhat][hardhat-link]        | - | - |          | EthereumJS      | - 
| [Truffle][truffle-link]        | - | - |          | ?               | - 
| [Remix][remix-link]            | - | - |          | EthereumJS, ?   | -
| [Waffle][waffle-link]          | - | - |          | Ganache, Ethers.js | -
| [Brownie][brownie-link]          | - | - |          | Ganache, ?      | -
| [OpenZeppelin][oz-link]        | - | - |          | ?               | -
| [Tenderly][tenderly-link]        | - | - |          | -      | - 
| [hardhat-deploy][hardhat-deploy-link]        | - | - |          | -      | - 
| [solidity-coverage][solidity-coverage-link]        | - | - |          | -      | - 
| [Typechain][typechain-link]        | - | - |          | -      | - 

[typechain-link]: https://github.com/ethereum-ts/TypeChain
[solidity-coverage-link]: https://github.com/sc-forks/solidity-coverage
[hardhat-deploy-link]: https://github.com/wighawag/hardhat-deploy
[blocknative-link]: https://github.com/blocknative
[hardhat-link]: https://github.com/nomiclabs/hardhat
[truffle-link]: https://github.com/trufflesuite/truffle
[remix-link]: https://github.com/ethereum/remix-project
[waffle-link]: https://github.com/EthWorks/Waffle
[brownie-link]: https://github.com/eth-brownie/brownie
[oz-link]: https://github.com/OpenZeppelin
[tenderly-link]: https://github.com/Tenderly

### Libraries

| Name | [1559][eip-1559-link] | [3198][eip-3198-link] | Work | Dependencies | Status
|---|---|---|---|---|---|
| [Web3.js][web3js-link]        | - | - |          | EthereumJS    | - 
| [Ethers.js][ethers-link]      | - | - |          | -             | - 
| [EthereumJS][ethereumjs-link] | 🛠️ | - | [URL][ethereumjs-work]   | -    | 🛠️ 
| [Web3.py][web3py-link]        | - | - |          | ?             | -
| [Web3j][web3j-link]           | - | - |          | ?             | -
| [Nethereum][nethereum-link]   | - | - |          | ?             | -

[web3js-link]: https://github.com/ChainSafe/web3.js
[ethers-link]: https://github.com/ethers-io/ethers.js
[ethereumjs-link]: https://github.com/ethereumjs/ethereumjs-monorepo
[ethereumjs-work]: https://github.com/ethereumjs/ethereumjs-monorepo/issues/1211
[web3py-link]: https://github.com/ethereum/web3.py
[web3j-link]: https://github.com/web3j/web3j
[nethereum-link]: https://github.com/Nethereum/Nethereum

### Infrastructure

Many of these projects may not update until much closer to the designated London block number.

| Name | [1559][eip-1559-link] | [3198][eip-3198-link] | Work | Dependencies | Status
|---|---|---|---|---|---|
| [Amazon Web Services][AWS-link]        | -    | -       |      | ?             | -
| [Infura][infura-link]        | -        | -       |      | ?             | -
| [POKT][pocket-link]        | -        | -       |      | Ethers, ?     | - 
| [Etherscan][etherscan-link] | -        | -       |      | ?           | -
| [MetaMask][metamask-link]   | -        | -       |      | EthereumJS, Ethers, Web3, ? | -
| [Ethernodes][ethernodes-link]   | -        | -       |      |  | -

[AWS-link]: https://aws.amazon.com/
[ethernodes-link]: https://www.ethernodes.org/
[infura-link]: https://github.com/INFURA
[pocket-link]: https://pokt.network/
[etherscan-link]: https://github.com/etherscan
[metamask-link]: https://github.com/MetaMask

[eip-1559-link]: https://eips.ethereum.org/EIPS/eip-1559
[eip-3198-link]: https://eips.ethereum.org/EIPS/eip-3198
