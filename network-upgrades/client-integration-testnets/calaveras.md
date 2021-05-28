# Client Integration Testnet Specification - Calaveras

**Disclaimer: This is for testing basic infrastructure. It will be shut down. It is not for deploying dapps, nor does it guarantee that EIPs included will go into mainnet.**

The specification for the Calaveras Client Integration Tesnet. Clients who wish to sync need to implement the following features into their client. It is for testing basic infrastructure and will be deprecated.

## Specification

**Name:** Calaveras

**EthStats:** TBA

**Faucet:** TBA

**Explorer:** TBA

**ID:** `Calaveras`

**ChainId:** `123` # The Calaveras fault line extends over 123km.

**NetworkId**: `123`

**Genesis File:** TBA

**Bootnodes:** TBA

**Included EIPs:**
  - [x] [EIP-1559](https://eips.ethereum.org/EIPS/eip-1559) Commit Hash - [ee7053ead7fb730a3f9178e7c7ad9e1b8cf3ee6c](https://github.com/ethereum/EIPs/commit/ee7053ead7fb730a3f9178e7c7ad9e1b8cf3ee6c)
  - [x] [EIP-3198](https://eips.ethereum.org/EIPS/eip-3198) Commit Hash - [081db1a6614e523dd791691cff7016e32c369912](https://github.com/ethereum/EIPs/commit/081db1a6614e523dd791691cff7016e32c369912)
  - [x] [EIP-3529](https://eips.ethereum.org/EIPS/eip-3529) Commit Hash - [6079eba5d1344a6b68075f79c14d4b7caf13ef53](https://github.com/ethereum/EIPs/commit/6079eba5d1344a6b68075f79c14d4b7caf13ef53)
  - [x] [EIP-3541](https://eips.ethereum.org/EIPS/eip-3541) Commit Hash - [168245a87a5a21890cb909e1624135fff63dea71](https://github.com/ethereum/EIPs/commit/168245a87a5a21890cb909e1624135fff63dea71)

## Client Consensus -> Implementation

| **Client**   | Repo                     | Signal |Merged | Syncing |
|--------------|--------------------------|--------|-------|---------|
| Besu         | [URL][besu-repo]         | x      |       |         |
| Geth         | [URL][geth-repo]         | x      |       |         |
| Nethermind   | [URL][nethermind-repo]   | x      |       |         |
| OpenEthereum | [URL][openethereum-repo] | x      |       |         |
| EthereumJS   | [URL][ethereumjs-repo]   | x      |       |         |
| Erigon       | [URL][erigon-repo]       | x      |       |         |


**Signal** -
Client intends to participate. *(You are on the bus)*

**Merge** -
Changes are implemented in the client and configurable for the network. *(You are ready to hit the gas and go)*

**Syncing**
Client syncs with the network

## Syncing Instructions:

TBA.

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).

[besu-repo]: https://github.com/hyperledger/besu
[geth-repo]: https://github.com/ethereum/go-ethereum
[nethermind-repo]: https://github.com/NethermindEth/nethermind
[openethereum-repo]: https://github.com/openethereum/openethereum
[ethereumjs-repo]: https://github.com/ethereumjs/ethereumjs-monorepo/tree/master/packages/client
[erigon-repo]: https://github.com/ledgerwatch/erigon
