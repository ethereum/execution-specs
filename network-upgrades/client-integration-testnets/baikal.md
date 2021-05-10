# Client Integration Testnet Specification - Baikal

**Disclaimer: This is for testing basic infrastructure. It will be shut down. It is not for deploying dapps, nor does it guarantee that EIPs included will go into mainnet.**

The specification for the Baikal Client Integration Tesnet. Clients who wish to sync need to implement the following features into their client. It is for testing basic infrastructure and will be deprecated.

## Specification

**Name:** Baikal

**EthStats:** https://baikal.ethdevops.io/ 

**Faucet:** https://faucet.baikal.ethdevops.io/ 

**ID:** `Baikal`

**ChainId:** `1642` # The deepest point of Lake Baikal is 1642 meters. 

**NetworkId**: `1642`

**Genesis File: TBA**


**Bootnodes:**

```
enode://9e1096aa59862a6f164994cb5cb16f5124d6c992cdbf4535ff7dea43ea1512afe5448dca9df1b7ab0726129603f1a3336b631e4d7a1a44c94daddd03241587f9@3.9.20.133:30303
```

**Included EIPs:**
  - [x] [EIP-1559](https://eips.ethereum.org/EIPS/eip-1559) Commit Hash - [67d0d75f6393f6a109f2dc81cffc1e6541fb7aa3](https://github.com/ethereum/EIPs/commit/67d0d75f6393f6a109f2dc81cffc1e6541fb7aa3)
  - [x] [EIP-3198](https://eips.ethereum.org/EIPS/eip-3198) Commit Hash - [081db1a6614e523dd791691cff7016e32c369912](https://github.com/ethereum/EIPs/commit/081db1a6614e523dd791691cff7016e32c369912)
  - [x] [EIP-3529](https://eips.ethereum.org/EIPS/eip-3529) Commit Hash - [6079eba5d1344a6b68075f79c14d4b7caf13ef53](https://github.com/ethereum/EIPs/commit/6079eba5d1344a6b68075f79c14d4b7caf13ef53)
  - [x] [EIP-3541](https://github.com/ethereum/EIPs/pull/3541) Commit Hash - [82038271ee7981395db5f60b320b7ce76b1a677c](https://github.com/ethereum/EIPs/commit/82038271ee7981395db5f60b320b7ce76b1a677c)

## Client Consensus -> Implementation

| **Client**   | Repo                     | Signal |Merged | Syncing |
|--------------|--------------------------|--------|-------|---------|
| Besu         | [URL][besu-repo]         | x      | x     | x       |
| Geth         | [URL][geth-repo]         | x      | x     | x       |
| Nethermind   | [URL][nethermind-repo]   | x      |       |         |
| OpenEthereum | [URL][openethereum-repo] | x      |       |         |
| EthereumJS   | [URL][ethereumjs-repo]   | x      |       |         |
| TurboGeth    | [URL][turbogeth-repo]    | x      |       |         |


**Signal** -
Client intends to participate. *(You are on the bus)*

**Merge** -
Changes are implemented in the client and configurable for the network. *(You are ready to hit the gas and go)*

**Syncing**
Client syncs with the network

## Syncing Instructions:

For go-ethereum, either use [this branch](https://github.com/ethereum/go-ethereum/pull/22837) or this docker image: `holiman/geth-baikal:latest`. 

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).


[besu-repo]: https://github.com/hyperledger/besu
[geth-repo]: https://github.com/ethereum/go-ethereum
[nethermind-repo]: https://github.com/NethermindEth/nethermind
[openethereum-repo]: https://github.com/openethereum/openethereum
[ethereumjs-repo]: https://github.com/ethereumjs/ethereumjs-monorepo/tree/master/packages/client
[turbogeth-repo]: https://github.com/ledgerwatch/turbo-geth
