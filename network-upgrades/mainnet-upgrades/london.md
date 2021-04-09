## London Network Upgrade Specification

### Included EIPs
Specifies changes included in the Network Upgrade.

  - [x] [EIP-1559: Fee market change for ETH 1.0 chain](https://eips.ethereum.org/EIPS/eip-1559)
  - [x] [EIP-3238: Difficulty Bomb Delay to Summer 2022](https://eips.ethereum.org/EIPS/eip-3238)


 ### Readiness Checklist

**List of outstanding items before deployment.**

Code merged into Participating Clients

|  **Client**  | EIP-1559 | EIP-3238 |
|--------------|:--------:|:--------:|
| Geth         |          |         |
| Besu         |          |         |
| Nethermind   |    x     |         |
| OpenEthereum |          |         |
| EthereumJS   |          |         |

 Tasks
- [ ] Client Integration Testing
  - [ ] Deploy a Client Integration Testnet
  - [ ] Integration Tests
  - [ ] Fuzz Testing
 - [ ] Select Fork Blocks
 - [ ] Deploy Clients
   - [ ]  Geth
   - [ ]  Besu
   - [ ]  Nethermind
   - [ ]  OpenEthereum
   - [ ]  EthereumJS
 - [ ] Pass Fork Blocks
