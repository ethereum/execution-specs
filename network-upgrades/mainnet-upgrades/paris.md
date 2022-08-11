## Paris Upgrade Specification

The Paris specification corresponds to the execution layers changes associated with Ethereum's transition to proof-of-stake, a.k.a. The Merge.

### Included EIPs
Specifies changes included in the network upgrade.

  - [x] [EIP-3675: Upgrade consensus to Proof-of-Stake](https://eips.ethereum.org/EIPS/eip-3675)
  - [x] [EIP-4399: Supplant DIFFICULTY opcode with PREVRANDAO](https://eips.ethereum.org/EIPS/eip-4399)

In addition to the EIPs listed above, an [EIP-2124](https://eips.ethereum.org/EIPS/eip-2124) `FORK_NEXT` value must be set for the Paris upgrade to allow nodes to disconnect stale peers. In typical upgrades, this happens on the fork block. Because Paris uses a [Terminal Total Difficulty](https://eips.ethereum.org/EIPS/eip-3675#total-difficulty-triggering-the-upgrade) instead of a block number to trigger the proof-of-work to proof-of-stake transition, this value must be set after the transition has completed. See the [FORK NEXT Upgrade](#fork-next-upgrade) section for more details. 


### Engine API

A new set of APIs is introduced as part of The Merge for the execution layer clients to communicate with the consensus layer. The specification for it is available [here](https://github.com/ethereum/execution-apis/tree/main/src/engine).

### Consensus Layer Specifications

This network upgrade requires changes to both Ethereum's execution and consensus layers. The consensus layer specifications for this upgrade are available [here](https://github.com/ethereum/consensus-specs/tree/dev/specs/bellatrix).

### Upgrade Schedule

#### Proof-of-Work to Proof-of-Stake Transition 

| Network | Terminal Total Difficulty | Expected Date | Fork Hash    |
|---------|------------|---------------|--------------|
| Ropsten | 50000000000000000 | June 8, 2022 | `0x7119B6B3` (unchanged from [London](https://github.com/ethereum/execution-specs/blob/master/network-upgrades/mainnet-upgrades/london.md)) |
| Sepolia | 17000000000000000 | July 6, 2022 | `0xfe3366e7` (unchanged from [Genesis](https://github.com/ethereum/go-ethereum/pull/23730)) |
| Goerli  | 10790000 | August 10, 2022 | `0xB8C6299D` (unchanged from [London](https://github.com/ethereum/execution-specs/blob/master/network-upgrades/mainnet-upgrades/london.md))  |
| Mainnet | 58750000000000000000000 | September 15, 2022 | TBD |

#### FORK NEXT Upgrade 

Once the proof-of-work to proof-of-stake transition has completed, an additional upgrade is required to add an [EIP-2124](https://eips.ethereum.org/EIPS/eip-2124) `FORK_NEXT` value to clients on the network in order to disconnect stale peers. 

| Network | Block Number / `FORK_NEXT` | Expected Date | Fork Hash |
|---------|------------|---------------|--------------|
| Ropsten | N/A | N/A | N/A | 
| Sepolia | 1735371 | August 17, 2022 | `0xb96cbd13` | 
| Goerli  | TBD | TBD | TBD | 
| Mainnet | TBD | TBD | TBD |  

Note that [Ropsten has been deprecated](https://blog.ethereum.org/2022/06/21/testnet-deprecation/) and will not be upgraded with a `FORK_NEXT` value. 

### Readiness Checklist

See https://github.com/ethereum/pm/blob/master/Merge/mainnet-readiness.md

### Client Integration Testnets

  - [Amphora](https://hackmd.io/@tvanepps/amphora-milestones)
  - Pithos
    - [Quickstart](https://github.com/parithosh/pithos-lighthouse-geth-quick-start)
    - [Configs](https://github.com/parithosh/consensus-deployment-ansible/blob/master/README.md)
    - [Explorer](https://pithos-explorer.ethdevops.io/)
  - [Kintsugi](https://kintsugi.themerge.dev/)
    - [devnet-0](https://github.com/parithosh/consensus-deployment-ansible/tree/master/merge-devnet-0)
    - [devnet-1](https://github.com/parithosh/consensus-deployment-ansible/tree/master/merge-devnet-1)
    - [devnet-2](https://github.com/parithosh/consensus-deployment-ansible/tree/master/merge-devnet-2)
    - [devnet-3](https://github.com/parithosh/consensus-deployment-ansible/tree/master/merge-devnet-3)
    - [devnet-4](https://github.com/parithosh/consensus-deployment-ansible/tree/master/merge-devnet-4)
    - [devnet-5](https://github.com/parithosh/consensus-deployment-ansible/tree/master/merge-devnet-5)
  - [Kiln](https://kiln.themerge.dev/)
  - [Goerli Shadow Fork 1](https://github.com/parithosh/consensus-deployment-ansible/tree/master/goerli-shadow-fork)
  - [Goerli Shadow Fork 2](https://github.com/parithosh/consensus-deployment-ansible/tree/master/goerli-shadow-fork-2)
  - [Goerli Shadow Fork 3](https://github.com/parithosh/consensus-deployment-ansible/tree/master/goerli-shadow-fork-3)
  - [Goerli Shadow Fork 4](https://github.com/parithosh/consensus-deployment-ansible/tree/master/goerli-shadow-fork-4)
  - [Mainnet Shadow Fork 1](https://github.com/parithosh/consensus-deployment-ansible/tree/master/mainnet-shadow-fork-1)
  - [Mainnet Shadow Fork 2](https://github.com/parithosh/consensus-deployment-ansible/tree/master/mainnet-shadow-fork-2)
  - [Mainnet Shadow Fork 3](https://github.com/parithosh/consensus-deployment-ansible/tree/master/mainnet-shadow-fork-3)
  - [Mainnet Shadow Fork 4](https://github.com/parithosh/consensus-deployment-ansible/tree/master/mainnet-shadow-fork-4)
  - [Mainnet Shadow Fork 5](https://github.com/parithosh/consensus-deployment-ansible/tree/master/mainnet-shadow-fork-5)
  - [Mainnet Shadow Fork 6](https://github.com/parithosh/consensus-deployment-ansible/tree/master/mainnet-shadow-fork-6)
  - [Mainnet Shadow Fork 7](https://github.com/parithosh/consensus-deployment-ansible/tree/master/mainnet-shadow-fork-7)
  - [Mainnet Shadow Fork 8](https://github.com/parithosh/consensus-deployment-ansible/tree/master/mainnet-shadow-fork-8)


### Client Releases

 - Ropsten:
    - [Besu](https://github.com/hyperledger/besu/releases/tag/22.4.2)
    - [Erigon](https://github.com/ledgerwatch/erigon/releases/tag/v2022.05.08)
    - [go-ethereum (geth)](https://github.com/ethereum/go-ethereum/releases/tag/v1.10.18)
    - [Nethermind](https://github.com/NethermindEth/nethermind/releases/tag/1.13.1)
- Sepolia
    - [Besu](https://github.com/hyperledger/besu/releases/tag/22.7.0-RC1)
    - [Erigon](https://github.com/ledgerwatch/erigon/releases/tag/v2022.07.01)
    - [go-ethereum (geth)](https://github.com/ethereum/go-ethereum/releases/tag/v1.10.21)
    - [Nethermind](https://github.com/NethermindEth/nethermind/releases/tag/1.13.4)
- Goerli
- Mainnet 
