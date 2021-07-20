## London Network Upgrade Specification

### Included EIPs
Specifies changes included in the Network Upgrade.

  - [x] [EIP-1559: Fee market change for ETH 1.0 chain](https://eips.ethereum.org/EIPS/eip-1559) 
  - [x] [EIP-3198: BASEFEE opcode](https://eips.ethereum.org/EIPS/eip-3198) 
  - [x] [EIP-3529: Reduction in refunds](https://eips.ethereum.org/EIPS/eip-3529) 
  - [x] [EIP-3541: Reject new contracts starting with the 0xEF byte](https://eips.ethereum.org/EIPS/eip-3541) 
  - [x] [EIP-3554: Difficulty Bomb Delay to December 1st 2021](https://eips.ethereum.org/EIPS/eip-3554) 

### Upgrade Schedule

| Network | Block      | Expected Date | Fork Hash    |
|---------|------------|---------------|--------------|
| Ropsten | `10499401` | June 24, 2021 | `0x7119B6B3` |
| Goerli  | `5062605`  | June 30, 2021 | `0xB8C6299D` |
| Rinkeby | `8897988`  | July 7, 2021  | `0x8E29F2F3` |
| Kovan   | TBA        | TBA           | TBA          |
| Mainnet | `12965000` | August 4, 2021 | `0xB715077D` | 

### Client Readiness Checklist
Code merged into Participating Clients

| EIP | [EIP-1559](https://eips.ethereum.org/EIPS/eip-1559) | [EIP-3198](https://eips.ethereum.org/EIPS/eip-3198) | [EIP-3554](https://eips.ethereum.org/EIPS/eip-3554) | [EIP-3529](https://eips.ethereum.org/EIPS/eip-3529) | [EIP-3541](https://eips.ethereum.org/EIPS/eip-3541) | 
|------------------|------|-------|--------|---------|-------|
| **Geth**         | [Merged (Many PRs)](https://github.com/ethereum/go-ethereum/pull/22837) | [Merged](https://github.com/ethereum/go-ethereum/pull/22837) | [Merged](https://github.com/ethereum/go-ethereum/pull/22870) | [Merged](https://github.com/ethereum/go-ethereum/pull/22733) | [Merged](https://github.com/ethereum/go-ethereum/pull/22809)
| **OpenEthereum** | [Merged](https://github.com/openethereum/openethereum/pull/393) | [Merged](https://github.com/openethereum/openethereum/issues/393) | [Merged](https://github.com/openethereum/openethereum/pull/433) | [Merged](https://github.com/openethereum/openethereum/pull/406) | [Merged](https://github.com/openethereum/openethereum/pull/406) | [Merged](https://github.com/openethereum/openethereum/pull/422)
| **Besu**         | [Merged (Many PRs)](https://github.com/hyperledger/besu/pulls?q=is%3Apr+1559) | [Merged](https://github.com/hyperledger/besu/pull/2123) | [Merged](https://github.com/hyperledger/besu/pull/2289) | [Merged](https://github.com/hyperledger/besu/pull/2238) | [Merged](https://github.com/hyperledger/besu/pull/2245)
| **Nethermind**   | [Merged (Many PRs)](https://github.com/NethermindEth/nethermind/pull/3023) | [Merged](https://github.com/NethermindEth/nethermind/pull/2985)|[Merged](https://github.com/NethermindEth/nethermind/pull/3072)|[Merged](https://github.com/NethermindEth/nethermind/pull/3048) | [Merged](https://github.com/NethermindEth/nethermind/pull/3059)
| **Erigon**    | [Merged (Many PRs)](https://github.com/ledgerwatch/erigon/pull/1704) | [Merged](https://github.com/ledgerwatch/erigon/pull/1704) | [Merged](https://github.com/ledgerwatch/erigon/pull/1981) | [Merged](https://github.com/ledgerwatch/erigon/pull/1853)| [Merged](https://github.com/ledgerwatch/erigon/pull/1853)
| **EthereumJS**   | [Merged (Many PRs)](https://github.com/ethereumjs/ethereumjs-monorepo/pull/1148) | [Merged](https://github.com/ethereumjs/ethereumjs-monorepo/pull/1148) | [Merged](https://github.com/ethereumjs/ethereumjs-monorepo/pull/1245) | [Merged](https://github.com/ethereumjs/ethereumjs-monorepo/pull/1239) | [Merged](https://github.com/ethereumjs/ethereumjs-monorepo/pull/1240)

#### Client Teams Trackers

* Geth: https://github.com/ethereum/go-ethereum/issues/22736 
* OpenEthereum: https://github.com/openethereum/openethereum/issues/395 

### Client Integration Testnets 

  - [Aleut](https://github.com/ethereum/eth1.0-specs/blob/master/network-upgrades/client-integration-testnets/aleut.md)
  - [Baikal](https://github.com/ethereum/eth1.0-specs/blob/master/network-upgrades/client-integration-testnets/baikal.md)
  - [Calaveras](https://github.com/ethereum/eth1.0-specs/blob/master/network-upgrades/client-integration-testnets/calaveras.md)

### Client Releases 

 - [x] Testnets 
   - [x]  Geth [v1.10.4](https://github.com/ethereum/go-ethereum/releases/tag/v1.10.4)
   - [x]  Besu [v21.7.0-RC1](https://github.com/hyperledger/besu/releases/tag/21.7.0-RC1)
   - [x]  Nethermind [v1.10.73](https://github.com/NethermindEth/nethermind/releases/tag/1.10.73)
   - [x]  OpenEthereum [v3.3.0-rc2](https://github.com/openethereum/openethereum/releases/tag/v3.3.0-rc2)
   - [x]  Erigon [v2021.06.04-alpha](https://github.com/ledgerwatch/erigon/releases/tag/v2021.06.04)
   - [x]  EthereumJS [v5.4.1](https://github.com/ethereumjs/ethereumjs-monorepo/releases/tag/%40ethereumjs%2Fvm%405.4.1)
 - [x]  Mainnet 
   - [x]  Geth [v1.10.15](https://github.com/ethereum/go-ethereum/releases/tag/v1.10.5)
   - [x]  Besu [v21.7.1](https://github.com/hyperledger/besu/releases/tag/21.7.1)
   - [x]  Nethermind [v1.10.77](https://github.com/NethermindEth/nethermind/releases/tag/1.10.77)
   - [x]  OpenEthereum [v3.3.0-rc.4](https://github.com/openethereum/openethereum/releases/tag/v3.3.0-rc.4)
   - [x]  Erigon [v2021.07.03-alpha	](https://github.com/ledgerwatch/erigon/releases/tag/v2021.07.03)
   - [x]  EthereumJS [v5.5.0](https://github.com/ethereumjs/ethereumjs-monorepo/releases/tag/%40ethereumjs%2Fvm%405.5.0)
