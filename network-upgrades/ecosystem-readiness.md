# Ecosystem Readiness Checklist
Tooling, Libraries and other Infrastructure

See the [1559 Cheatsheet for Implementers](https://hackmd.io/4YVYKxxvRZGDto7aq7rVkg?view) for the latest resources to help you along.

If you know about a status update please add a PR to this document or post on the latest [update issue](https://github.com/ethereum/eth1.0-specs/issues/198) for aggregated inclusion on a weekly basis.

## London Hardfork

For a list of included EIPs see the [specification](./mainnet-upgrades/london.md) document.

Tracking: `active`
⭕ - Not Started
🛠️ - In Progress
✅ - Complete

### Developer Tools

| Name | Description | Dependencies | Work | EIPs | Release | Status
|---|---|---|---|---|---|---|
| [Hardhat][hardhat-link] | Framework | EthereumJS, Ethers | [URL][hardhat-work] | All | | 🛠️ 
| [Truffle][truffle-link] | Framework | EthereumJS, Web3.js, Ethers |  | All | | ⭕
| [DappTools][dapptools-link] | Framework | - | [URL][dapptools-work] | All |  | 🛠️ 
| [Remix][remix-link] | IDE | EthereumJS, Web3.js, Ethers |  | All |  | 🛠️
| [Waffle][waffle-link] | Framework | Ganache, Ethers.js, Typechain |  | All | | 🛠️
| [Brownie][brownie-link] | Framework | Web3.py |  | All | | ⭕
| [OpenZeppelin][oz-link] | Smart Contract Security | Hardhat |  | ? | | 🛠️
| [Tenderly][tenderly-link] | Contract Monitoring | Hardhat |  | 1559 | | 🛠️
| [hardhat-deploy][hardhat-deploy-link] | Contract Deployment | Hardhat, Ethers |  | ? | | ⭕
| [solidity-coverage][solidity-coverage-link] | Contract Testing | Hardhat, Solidity |  | ? | | ⭕
| [Typechain][typechain-link] | Language Tool | Ethers, Truffle, Hardhat, Web3.js, Solidity |  | ? | | ⭕
| [Solidity][solidity-link] | Language | - | [URL][solidity-work] | 3198 |  | 🛠️ 

[hardhat-link]: https://github.com/nomiclabs/hardhat
[hardhat-work]: https://github.com/nomiclabs/hardhat/projects/8
[truffle-link]: https://github.com/trufflesuite/truffle
[dapptools-link]: https://github.com/dapphub/dapptools
[remix-link]: https://github.com/ethereum/remix-project
[waffle-link]: https://github.com/EthWorks/Waffle
[brownie-link]: https://github.com/eth-brownie/brownie
[oz-link]: https://github.com/OpenZeppelin
[tenderly-link]: https://github.com/Tenderly
[hardhat-deploy-link]: https://github.com/wighawag/hardhat-deploy
[solidity-coverage-link]: https://github.com/sc-forks/solidity-coverage
[typechain-link]: https://github.com/ethereum-ts/TypeChain
[solidity-link]: http://soliditylang.eth
[solidity-work]: https://github.com/ethereum/solidity/issues/11390
[dapptools-work]:https://github.com/dapphub/dapptools/pull/688


### Libraries

| Name | Description | Dependencies | Work | EIPs | Release | Status
|---|---|---|---|---|---|---|
| [Web3.js][web3js-link] | Network API (JavaScript) | EthereumJS |  |1559 |  |🛠️
| [Ethers.js][ethers-link] | Network API (JavaScript) |  | [URL][ethers-work] |1559 |[v5.4.1][ethers-release]  |✅ 
| [EthereumJS][ethereumjs-link] | Libraries |  | [URL][ethereumjs-work] | All | [URL][ethereumjs-release] |✅
| [Web3.py][web3py-link] | Network API (Python) |  | [URL][web3py-work] |1559 | [v5.21.0][web3py-release] |✅
| [Web3j][web3j-link] | Network API (Java) |  | [URL][web3j-work] |1559 |  |🛠️ 
| [Nethereum][nethereum-link] | Network API (.Net) |  |  |1559 |  |🛠️
| [KEthereum][kethereum-link] | Network API (Kotlin) | | [URL][kethereum-work] |1559 |[URL][kethereum-release]  |✅


[web3js-link]: https://github.com/ChainSafe/web3.js
[ethers-link]: https://github.com/ethers-io/ethers.js
[ethers-work]: https://github.com/ethers-io/ethers.js/issues/1610
[ethers-release]: https://github.com/ethers-io/ethers.js/releases/tag/v5.4.1
[ethereumjs-link]: https://github.com/ethereumjs/ethereumjs-monorepo
[ethereumjs-work]: https://github.com/ethereumjs/ethereumjs-monorepo/issues/1211
[ethereumjs-release]: https://github.com/ethereumjs/ethereumjs-monorepo/pull/1263
[web3py-link]: https://github.com/ethereum/web3.py
[web3py-work]: https://github.com/ethereum/web3.py/issues/1835
[web3py-release]: https://web3py.readthedocs.io/en/latest/releases.html#v5-21-0-2021-07-12
[web3j-link]: https://github.com/web3j/web3j
[web3j-work]: https://github.com/web3j/web3j/pull/1417
[nethereum-link]: https://github.com/Nethereum/Nethereum
[kethereum-link]: https://github.com/komputing/KEthereum
[kethereum-work]: https://github.com/komputing/KEthereum/issues/101
[kethereum-release]: https://github.com/komputing/KEthereum/commit/8c1386853301e792f798d148677812c04ff0e434

### Infrastructure

Many of these projects may not update until much closer to the designated London block number.

| Name | Description | Dependencies | Work | EIPs | Release | Status
|---|---|---|---|---|---|---|
| [Amazon Web Services][AWS-link] | Managed Blockchain |  |  | All |  |⭕
| [Blocknative][blocknative-link] | Mempool Explorer |  |  | 1559 |  |⭕
| [Infura][infura-link] | Ethereum APIs |  |  | 1559 |  |✅
| [POKT][pocket-link] | Request API |  |  | 1559 |  |⭕ 
| [Etherscan][etherscan-link] | Block Explorer |  |  | 1559 |  |⭕
| [MetaMask][metamask-link] | Browser Extension | EthereumJS, Ethers, Web3, ? | [URL][metamask-work] | 1559 |  |🛠️ 
| [Ethernodes][ethernodes-link] | Node Explorer | Eth 1.0 Clients |  | ? |  |⭕ 
| [TREZOR][trezor-link] | Hardware Wallet |  | [URL][trezor-work] | 1559 |  |🛠️ 
| [WallETH][walleth-link] | Wallet | KEthereum | [URL][walleth-work] | 1559 |  |🛠️  

[AWS-link]: https://aws.amazon.com/managed-blockchain/
[blocknative-link]: https://github.com/blocknative
[infura-link]: https://github.com/INFURA
[pocket-link]: https://pokt.network/
[etherscan-link]: https://github.com/etherscan
[metamask-link]: https://github.com/MetaMask
[metamask-work]: https://github.com/MetaMask/metamask-mobile/issues/2571
[ethernodes-link]: https://www.ethernodes.org/
[trezor-link]: https://trezor.io
[trezor-work]: https://github.com/trezor/trezor-firmware/issues/1604
[walleth-link]: https://walleth.org
[walleth-work]: https://github.com/walleth/walleth/issues/523

