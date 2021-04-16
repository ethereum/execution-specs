# Eth1.0 Specifications

## Description

This repository contains various specification related to the Ethereum 1.0 chain, specifically the specifications for [network upgrades](/network-upgrades) and (soon) the [JSON RPC API](/json-rpc). 

## Ethereum Protocol Releases

| Version and Code Name | Block No. | Released | Incl EIPs | Specs | Impls |
|-----------------------|-----------|----------|-----------|-------|-------|
| Frontier | 1 | 07/30/2015 | | | [Geth v1.0.0](https://github.com/ethereum/go-ethereum/releases/tag/v1.0.0) |
| Frontier Thawing | 200000 | 09/07/2015 | | | [Geth v1.0.1.1](https://github.com/ethereum/go-ethereum/releases/tag/v1.0.1.1) |
| Homestead | 1150000 | 03/14/2016  | [EIP-2](https://eips.ethereum.org/EIPS/eip-2) <br/> [EIP-7](https://eips.ethereum.org/EIPS/eip-7) <br/> [EIP-8](https://eips.ethereum.org/EIPS/eip-8) | [HFM-606](https://eips.ethereum.org/EIPS/eip-606) | [Geth v1.3.4](https://github.com/ethereum/go-ethereum/releases/tag/v1.3.4) |
| DAO Wars | aborted | aborted |  |  | [Geth v1.4.8](https://github.com/ethereum/go-ethereum/releases/tag/v1.4.8) |
| DAO Fork | 1920000 | 07/20/2016 |  | [HFM-779](https://eips.ethereum.org/EIPS/eip-779) | [Geth v1.4.10](https://github.com/ethereum/go-ethereum/releases/tag/v1.4.10) |
| Tangerine Whistle | 2463000 | 10/18/2016 | [EIP-150](https://eips.ethereum.org/EIPS/eip-150) | [HFM-608](https://eips.ethereum.org/EIPS/eip-608) | [Geth v1.4.18](https://github.com/ethereum/go-ethereum/releases/tag/v1.4.18) |
| Spurious Dragon	 | 2675000 | 11/22/2016 | [EIP-155](https://eips.ethereum.org/EIPS/eip-155) <br/> [EIP-160](https://eips.ethereum.org/EIPS/eip-160) <br/> [EIP-161](https://eips.ethereum.org/EIPS/eip-161) <br/> [EIP-170](https://eips.ethereum.org/EIPS/eip-170) | [HFM-607](https://eips.ethereum.org/EIPS/eip-607) | [Geth v1.5.1](https://github.com/ethereum/go-ethereum/releases/tag/v1.5.1) |
| Byzantium | 4370000 | 10/16/2017	 | [EIP-100](https://eips.ethereum.org/EIPS/eip-100) <br/> [EIP-140](https://eips.ethereum.org/EIPS/eip-140) <br/>  [EIP-196](https://eips.ethereum.org/EIPS/eip-196) <br/> [EIP-197](https://eips.ethereum.org/EIPS/eip-197) <br/> [EIP-198](https://eips.ethereum.org/EIPS/eip-198) <br/> [EIP-211](https://eips.ethereum.org/EIPS/eip-211) <br/> [EIP-214](https://eips.ethereum.org/EIPS/eip-214) <br/> [EIP-649](https://eips.ethereum.org/EIPS/eip-649) <br/> [EIP-658](https://eips.ethereum.org/EIPS/eip-658) | [HFM-609](https://eips.ethereum.org/EIPS/eip-609) | [Geth v1.7.0](https://github.com/ethereum/go-ethereum/releases/tag/v1.7.0) |
| Constantinople | aborted | aborted | [EIP-145](https://eips.ethereum.org/EIPS/eip-145) <br/> [EIP-1014](https://eips.ethereum.org/EIPS/eip-1014) <br/> [EIP-1052](https://eips.ethereum.org/EIPS/eip-1052) <br/> [EIP-1234](https://eips.ethereum.org/EIPS/eip-1234) <br/> [EIP-1283](https://eips.ethereum.org/EIPS/eip-1283) | [HFM-1013](https://eips.ethereum.org/EIPS/eip-1013) | [Geth v1.8.20](https://github.com/ethereum/go-ethereum/releases/tag/v1.8.20) |
| St. Petersburg | 7280000 | 02/28/2019 | [EIP-145](https://eips.ethereum.org/EIPS/eip-145) <br/> [EIP-1014](https://eips.ethereum.org/EIPS/eip-1014) <br/> [EIP-1052](https://eips.ethereum.org/EIPS/eip-1052) <br/> [EIP-1234](https://eips.ethereum.org/EIPS/eip-1234) | [HFM-1716](https://github.com/ethereum/EIPs/pull/1716/) | [Geth v1.8.23](https://github.com/ethereum/go-ethereum/releases/tag/v1.8.23) |
| Istanbul | 9069000 | 12/07/2019 | [EIP-152](https://eips.ethereum.org/EIPS/eip-152) <br/> [EIP-1108](https://eips.ethereum.org/EIPS/eip-1108) <br/> [EIP-1344](https://eips.ethereum.org/EIPS/eip-1344) <br/> [EIP-1884](https://eips.ethereum.org/EIPS/eip-1884) <br/> [EIP-2028](https://eips.ethereum.org/EIPS/eip-2028) <br/> [EIP-2200](https://eips.ethereum.org/EIPS/eip-2200) | [HFM-1679](https://eips.ethereum.org/EIPS/eip-1679) | [Geth v1.9.7](https://github.com/ethereum/go-ethereum/releases/tag/v1.9.7)
| Muir Glacier | 9200000 | 01/02/2020 | [EIP-2384](https://eips.ethereum.org/EIPS/eip-2384) | [HFM-2387](https://eips.ethereum.org/EIPS/eip-2387) | [Geth v1.9.9](https://github.com/ethereum/go-ethereum/releases/tag/v1.9.9) |
| Berlin | 12244000 | 04/15/2021 | [EIP-2565](https://eips.ethereum.org/EIPS/eip-2565) <br/> [EIP-2929](https://eips.ethereum.org/EIPS/eip-2929) <br/> [EIP-2718](https://eips.ethereum.org/EIPS/eip-2718) <br/> [EIP-2930](https://eips.ethereum.org/EIPS/eip-2930) | ~[HFM-2070](https://eips.ethereum.org/EIPS/eip-2070)~ <br/> [Specification](https://github.com/ethereum/eth1.0-specs/blob/master/network-upgrades/mainnet-upgrades/berlin.md) | [Geth v1.10.1](https://github.com/ethereum/go-ethereum/releases/tag/v1.10.1) |


