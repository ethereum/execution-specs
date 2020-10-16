
# Client Integration Testnet Specification - YOLOv3


**Disclaimer: This is for testing basic infrastructure. It will be nuked. It is not for deploying dapps, nor does it define what will go into mainnet. For information on network upgrades, please follow the relevant meta EIPs and ongoing discussion on Ethereum/pm.**


The specification for Ephemeral Testnet Yolo. Clients who wish to sync need to implement the following features into their client. It is for testing basic infrastructure and will be nuked.

## Specification 

Name: Yolo
ID: `YOLO-v3`

  - [x] EIP 2537 Commit Hash - [5edff4ae6ff62c7e0bbfad624fc3d0ba7dc84392](https://github.com/ethereum/EIPs/commit/5edff4ae6ff62c7e0bbfad624fc3d0ba7dc84392)
  - [x] EIP 2315 Commit Hash - [e8accf22cdc5562d6982c560080c6cd6b7f94867](https://github.com/ethereum/EIPs/commit/e8accf22cdc5562d6982c560080c6cd6b7f94867)
  - [x] EIP 2929
  - [x] EIP 2718
  - [x] EIP 2930

*[ ] Proposed - [x] Consensus to include.*
## Timeline

 - Deployed: 
 
## Client Consensus -> Implementation 

YOLO-v3
| **Client**   | Signal | Spec | Merged | Syncing |
|--------------|--------|------|--------|---------|
| Besu         | x      | x    |        |         |
| EthereumJS   |        |      |        |         |
| Geth         | x      | x    |        |         |
| Nethermind   | x      | x    |        |         |
| OpenEthereum |        |      |        |         |
| Trinity      |        |      |        |         |

**Signal** -
Client intends to participate. *(You are on the bus)*

**Spec** -
Client is satisfied with the proposed specification. *(You agree with the direction)*

**Merge** -
Changes are implemented in the client and configurable for YOLO. *(You are ready to hit the gas and go)*

**Syncing**
Client syncs with the network

## Copyright
Copyright and related rights waived via [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
