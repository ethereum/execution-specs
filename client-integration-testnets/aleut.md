# Client Integration Testnet Specification - Aleut

**Disclaimer: This is for testing basic infrastructure. It will be nuked. It is not for deploying dapps, nor does it guarantee that EIPs included will go into mainnet.**

The specification for the Aleut Client Integration Tesnet. Clients who wish to sync need to implement the following features into their client. It is for testing basic infrastructure and will be deprecated.

## Specification

Name: Aleut
ID: `Aleut`

  - [x] [EIP-1559](https://eips.ethereum.org/EIPS/eip-1559) Commit Hash - [79f4fe6cbe0d323dfac7412270c6e8cf33e62af3](https://github.com/ethereum/EIPs/commit/79f4fe6cbe0d323dfac7412270c6e8cf33e62af3)
  - [x] [EIP-3198](https://eips.ethereum.org/EIPS/eip-3198) Commit Hash - [081db1a6614e523dd791691cff7016e32c369912](https://github.com/ethereum/EIPs/commit/081db1a6614e523dd791691cff7016e32c369912) 

## Client Consensus -> Implementation 

| **Client**   | Repo                     | Signal | Spec | Merged | Syncing |
|--------------|--------------------------|--------|------|--------|---------|
| Besu         | [URL][besu-repo]         | x      | x    |        |         |
| Geth         | [URL][geth-repo]         | x      | x    |        |         |
| Nethermind   | [URL][nethermind-repo]   | x      | x    |        |         |
| OpenEthereum | [URL][openethereum-repo] | x      | x    |        |         |
| EthereumJS   | [URL][ethereumjs-repo]   | x      | x    |        |         |
| TurboGeth    | [URL][turbogeth-repo]    | x      | x    |        |         |


**Signal** -
Client intends to participate. *(You are on the bus)*

**Spec** -
Client is satisfied with the proposed specification. *(You agree with the direction)*

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
