# Client Integration Testnet Specification - Aleut

**Disclaimer: This network will soon be shut down in favor of [Baikal](/baikal.md).**

The specification for the Aleut Client Integration Tesnet. Clients who wish to sync need to implement the following features into their client. It is for testing basic infrastructure and will be deprecated.

## Specification

**Name:** Baikal

**ID:** `Baikal`

**ChainId:** `1642` # The deepest point of Lake Baikal is 1642 meters. 

**Genesis File: TBA**


**Static Nodes: TBA**

**Included EIPs:**
  - [x] [EIP-1559](https://eips.ethereum.org/EIPS/eip-1559) Commit Hash - [79f4fe6cbe0d323dfac7412270c6e8cf33e62af3](https://github.com/ethereum/EIPs/commit/79f4fe6cbe0d323dfac7412270c6e8cf33e62af3)
  - [x] [EIP-3198](https://eips.ethereum.org/EIPS/eip-3198) Commit Hash - [081db1a6614e523dd791691cff7016e32c369912](https://github.com/ethereum/EIPs/commit/081db1a6614e523dd791691cff7016e32c369912)
  - [x] [EIP-3529](https://eips.ethereum.org/EIPS/eip-3529) Commit Hash - [6079eba5d1344a6b68075f79c14d4b7caf13ef53](https://github.com/ethereum/EIPs/commit/6079eba5d1344a6b68075f79c14d4b7caf13ef53)
  - [x] [EIP-3541](https://github.com/ethereum/EIPs/pull/3541) Commit Hash - TBA

## Client Consensus -> Implementation

| **Client**   | Repo                     | Signal |Merged | Syncing |
|--------------|--------------------------|--------|-------|---------|
| Besu         | [URL][besu-repo]         | x      |       |         |
| Geth         | [URL][geth-repo]         | x      |       |         |
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

TBA

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).


[besu-repo]: https://github.com/hyperledger/besu
[geth-repo]: https://github.com/ethereum/go-ethereum
[nethermind-repo]: https://github.com/NethermindEth/nethermind
[openethereum-repo]: https://github.com/openethereum/openethereum
[ethereumjs-repo]: https://github.com/ethereumjs/ethereumjs-monorepo/tree/master/packages/client
[turbogeth-repo]: https://github.com/ledgerwatch/turbo-geth
