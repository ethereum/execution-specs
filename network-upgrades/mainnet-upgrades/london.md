## London Network Upgrade Specification

### Included EIPs
Specifies changes included in the Network Upgrade.

  - [x] [EIP-1559: Fee market change for ETH 1.0 chain](https://eips.ethereum.org/EIPS/eip-1559)
  - [x] [EIP-3198: BASEFEE opcode](https://eips.ethereum.org/EIPS/eip-3198)
  - [x] [EIP-3238: Difficulty Bomb Delay to Summer 2022](https://eips.ethereum.org/EIPS/eip-3238)


### Client Readiness Checklist
Code merged into Participating Clients

| EIP | Geth | OpenEthereum | Besu | Nethermind | TurboGeth | EthereumJS | 
|-----|------|-------|--------|------------|--------|------------|
| [EIP-1559: Fee market change for ETH 1.0 chain](https://eips.ethereum.org/EIPS/eip-1559)| [Not merged](https://github.com/ethereum/EIPs/pull/2129) |  |[This & others](https://github.com/hyperledger/besu/pull/1867) | [Not merged](https://github.com/NethermindEth/nethermind/pull/3023) 
| [EIP-3198: BASEFEE opcode](https://eips.ethereum.org/EIPS/eip-3198) | [Not merged](https://github.com/ethereum/EIPs/pull/2129) | | | [This & others](https://github.com/NethermindEth/nethermind/pull/2985)
| [EIP-3238: Difficulty Bomb Delay to Q2/2022](https://eips.ethereum.org/EIPS/eip-3238) |

#### Client Teams Trackers

* Geth: https://github.com/ethereum/go-ethereum/issues/22736 

#### Other Tasks
 
- [x] Client Integration Testing
  - [x] Deploy a Client Integration Testnet: [Aleut](https://github.com/ethereum/eth1.0-specs/blob/master/network-upgrades/client-integration-testnets/aleut.md)
  - [ ] Integration Tests: [WIP](https://hackmd.io/@SduYUIHbT6a6DHUpikAcFQ/BJP9arcB_/%2FuID06YEhSj2uFzEviDIaJQ)
  - [ ] Fuzz Testing
 - [ ] Select Fork Blocks
 - [ ] Deploy Clients
   - [ ]  Geth
   - [ ]  Besu
   - [ ]  Nethermind
   - [ ]  OpenEthereum
   - [ ]  EthereumJS
 - [ ] Pass Fork Blocks
