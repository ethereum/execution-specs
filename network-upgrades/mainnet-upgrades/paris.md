## Paris Upgrade Specification

The Paris specification corresponds to the execution layers changes associated with Ethereum's transition to proof-of-stake, a.k.a. The Merge.

### Included EIPs
Specifies changes included in the network upgrade.

  - [x] [EIP-3675: Upgrade consensus to Proof-of-Stake](https://eips.ethereum.org/EIPS/eip-3675)
  - [x] [EIP-4399: Supplant DIFFICULTY opcode with RANDOM](https://eips.ethereum.org/EIPS/eip-4399)

### Engine API

A new set of APIs is introduced as part of The Merge for the execution layer clients to communicate with the consensus layer. The specification for it is available [here](https://github.com/ethereum/execution-apis/tree/main/src/engine).

### Consensus Layer Specifications

This network upgrade requires changes to both Ethereum's execution and consensus layers. The consensus layer specifications for this upgrade are available [here](https://github.com/ethereum/consensus-specs/tree/dev/specs/bellatrix).

### Upgrade Schedule

| Network | Terminal Total Difficulty (`TTD`) | Expected Date | Fork Hash    |
|---------|------------|---------------|--------------|
| Ropsten | `43531756765713534` | June 8, 2022 | TBD |
| Goerli  | TBD | TBD | TBD |
| Sepolia | TBD | TBD | TBD |
| Mainnet | TBD | TBD | TBD |

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
  - [Kiln](https://kiln.themerge.dev/)
  - [Goerli Shadow Fork 1](https://github.com/parithosh/consensus-deployment-ansible/tree/master/goerli-shadow-fork)
  - [Goerli Shadow Fork 2](https://github.com/parithosh/consensus-deployment-ansible/tree/master/goerli-shadow-fork-2)
  - [Goerli Shadow Fork 3](https://github.com/parithosh/consensus-deployment-ansible/tree/master/goerli-shadow-fork-3)
  - [Goerli Shadow Fork 4](https://github.com/parithosh/consensus-deployment-ansible/tree/master/goerli-shadow-fork-4)
  - [Mainnet Shadow Fork 1](https://github.com/parithosh/consensus-deployment-ansible/tree/master/mainnet-shadow-fork-1)
  - [Mainnet Shadow Fork 2](https://github.com/parithosh/consensus-deployment-ansible/tree/master/mainnet-shadow-fork-2)
  - [Mainnet Shadow Fork 3](https://github.com/parithosh/consensus-deployment-ansible/tree/master/mainnet-shadow-fork-3)
  - [Mainnet Shadow Fork 4](https://github.com/parithosh/consensus-deployment-ansible/tree/master/mainnet-shadow-fork-4)


### Client Releases

 - TBA
