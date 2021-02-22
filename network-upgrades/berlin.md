

## Berlin Network Upgrade Specification

Name: Berlin
Fork Block: TBD

### Included EIPs
Specifies changes included in the Network Upgrade.

  - [x] [EIP-2565: ModExp Gas Cost](https://eips.ethereum.org/EIPS/eip-2565)
  - [x] [EIP-2315: Simple Subroutines for the EVM](https://eips.ethereum.org/EIPS/eip-2315)
  - [x] [EIP-2929: Gas cost increases for state access opcodes](https://eips.ethereum.org/EIPS/eip-2929)
  - [x] [EIP-2718: Typed Transaction Envelope](https://eips.ethereum.org/EIPS/eip-2718)
  - [x] [EIP-2930: Optional access lists](https://eips.ethereum.org/EIPS/eip-2930)


 ### Readiness Checklist
 
**List of outstanding items before deployment.**
 
Code merged into Participating Clients

|  **Client**  | EIP-2565 | EIP-2315 | EIP-2929 | EIP-2718 | EIP-2930  |
|--------------|:--------:|:--------:|:--------:|:--------:|:---------:|
| Geth         | ✔        | ✔        | ✔        | ✔        | ✔         |
| Besu         | ✔        | ✔        | ✔        | ✔        | ✔         |
| Nethermind   | ✔        | ✔        | ✔        | ✔        | ✔         |
| OpenEthereum | ✔        | ✔        | ✔        | ✔        | ✔         |
 
 Tasks 
 - [x] [Deploy Yolo-v3](https://github.com/ethereum/eth1.0-specs/blob/master/client-integration-testnets/YOLOv3.md)
 - [ ] Green Light from security teams
   - [ ] Client Integration
   - [ ] Fuzz Testing
 - [x] Propose Fork Block for testnets
   - [x] Goerli `4_460_644` [goerli/testnet#75](https://github.com/goerli/testnet/pull/75)
   - [x] Ropsten `9_812_189` [ethereum/ropsten#38](https://github.com/ethereum/ropsten/issues/38)
   - [x] Rinkeby `8_290_928` [ethereum/pm#248](https://github.com/ethereum/pm/issues/248)
   - [ ] ~~Kovan~~
 - [x] Propose Mainnet fork block `12_244_000` [ethereum/pm#248](https://github.com/ethereum/pm/issues/248)
 - [ ] Finalise Testnet and Mainnet fork blocks.
 - [ ] Deploy Clients
 - [ ] Pass fork block on Mainnet.
