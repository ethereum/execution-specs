## Shanghai Network Upgrade Specification

### Included EIPs
Specifies changes included in the Network Upgrade.

### EIPs Considered for Inclusion
Specifies changes potentially included in the Network Upgrade, pending successful deployment on Client Integration Testnets.

* [EIP-3540: EVM Object Format (EOF) v1](https://eips.ethereum.org/EIPS/eip-3540)
* [EIP-3670: EOF - Code Validation](https://eips.ethereum.org/EIPS/eip-3670)
* [EIP-3860: Limit and meter initcode](https://eips.ethereum.org/EIPS/eip-3860)

### Readiness Checklist

**List of outstanding items before deployment.**

Code merged into Participating Clients

|  **Client**  | TBA EIPs |
|--------------|:--------:|
| Geth         |          |
| Besu         |          |
| Nethermind   |          |
| OpenEthereum |          |
| EthereumJS   |          |

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
