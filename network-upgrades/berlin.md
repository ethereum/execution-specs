# Berlin Network Upgrade Specification

# Included EIPs
Specifies changes included in the Network Upgrade.

  - [x] [EIP-2565: ModExp Gas Cost](https://eips.ethereum.org/EIPS/eip-2565)
  - [x] [EIP-2315: Simple Subroutines for the EVM](https://eips.ethereum.org/EIPS/eip-2315)
  - [x] [EIP-2929: Gas cost increases for state access opcodes](https://eips.ethereum.org/EIPS/eip-2929)
  - [x] [EIP-2718: Typed Transaction Envelope](https://eips.ethereum.org/EIPS/eip-2718)
  - [x] [EIP-2930: Optional access lists](https://eips.ethereum.org/EIPS/eip-2930)

# Readiness Checklist

**List of outstanding items before deployment.**
 
Code merged into Participating Clients

|  **Client**  | EIP-2565 | EIP-2315 | EIP-2929 | EIP-2718 | EIP-2930  |
|--------------|:--------:|:--------:|:--------:|:--------:|:---------:|
| Geth         | ✔        | ✔        | ✔        | ✔        | ✔         |
| Besu         | ✔        | ✔        | ✔        | ✔        | ✔         |
| Nethermind   | ✔        | ✔        | ✔        | ✔        | ✔         |
| OpenEthereum | ✔        | ✔        | ✔        | ✔        | ✔         |
| EthereumJS   | ✔        | ✔        | ✔        |          |           |
 
 Tasks 
- [x] Client Integration Testing
  - [x] [Deploy Yolo-v3](https://github.com/ethereum/eth1.0-specs/blob/master/client-integration-testnets/YOLOv3.md)
  - [x] [Integration tests](https://github.com/ethereum/tests/releases/tag/v7.0.0)
  - [x] Fuzz Testing
 - [x] Select Fork Blocks
   - [x] Ropsten `9_812_189` (10 Mar 2021) [ethereum/ropsten#38](https://github.com/ethereum/ropsten/issues/38)
   - [x] Goerli `4_460_644` (17 Mar 2021) [goerli/testnet#75](https://github.com/goerli/testnet/pull/75)
   - [x] Rinkeby `8_290_928` (24 Mar 2021) [ethereum/pm#248](https://github.com/ethereum/pm/issues/248)
   - [x] ~~Kovan~~ (Will be handled by OpenEthereum at a later date)
   - [x] Mainnet `12_244_000` (14 Apr 2021) [ethereum/pm#248](https://github.com/ethereum/pm/issues/248)
 - [ ] Deploy Clients
   - [ ]  Geth
   - [ ]  Besu
   - [ ]  Nethermind
   - [ ]  OpenEthereum
   - [ ]  EthereumJS
 - [ ] Pass Fork Blocks
   - [ ] Ropsten `9_812_189` (10 Mar 2021) [ethereum/ropsten#38](https://github.com/ethereum/ropsten/issues/38)
   - [ ] Goerli `4_460_644` (17 Mar 2021) [goerli/testnet#75](https://github.com/goerli/testnet/pull/75)
   - [ ] Rinkeby `8_290_928` (24 Mar 2021) [ethereum/pm#248](https://github.com/ethereum/pm/issues/248)
   - [ ] ~~Kovan~~ (Will be handled by OpenEthereum at a later date)
   - [ ] Mainnet `12_244_000` (14 Apr 2021) [ethereum/pm#248](https://github.com/ethereum/pm/issues/248)
