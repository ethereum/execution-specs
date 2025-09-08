## Osaka Network Upgrade Specification

### Included EIPs
Execution layer changes included in the Network Upgrade.

* [EIP-7594: PeerDAS - Peer Data Availability Sampling][7594]
* [EIP-7823: Set upper bounds for MODEXP][7823]
* [EIP-7825: Transaction Gas Limit Cap][7825]
* [EIP-7883: ModExp Gas Cost Increase][7883]
* [EIP-7918: Blob base fee bounded by execution cost][7918]
* [EIP-7934: RLP Execution Block Size Limit][7934]
* [EIP-7935: Set default gas limit to XX0M][7935]
* [EIP-7939: Count leading zeros (CLZ) opcode][7939]
* [EIP-7951: Precompile for secp256r1 Curve Support][7951]
* [EIP-7892: Blob Parameter Only Hardforks][7892]
* [EIP-7642: eth/69 - history expiry and simpler receipts][7642]
* [EIP-7910: eth_config JSON-RPC Method][7910]

### Implementation Progress

Implementation status of Included EIPs across participating clients.

|  **Client**    | [7594] | [7823] | [7825] | [7883] | [7918] | [7934] | [7935] | [7939] | [7951] | [7892] | [7642] | [7910] |
|----------------|--------|--------|--------|--------|--------|--------|--------|--------|--------|--------|--------|--------|
| **Geth**       |        |        |        |        |        |        |        |        |        |        |        |        |
| **Besu**       |        |        |        |        |        |        |        |        |        |        |        |        |
| **Nethermind** |        |        |        |        |        |        |        |        |        |        |        |        |
| **Reth**       |        |        |        |        |        |        |        |        |        |        |        |        |
| **Erigon**     |        |        |        |        |        |        |        |        |        |        |        |        |
| **EthereumJS** |        |        |        |        |        |        |        |        |        |        |        |        |

### Upgrade Schedule

| Network | Timestamp    | Date & Time (UTC)       | Fork Hash    | Beacon Chain Epoch |
|---------|--------------|-------------------------|--------------| ------------------ |
| Holesky | `          ` |     -  -     :  :       | `0x        ` | `      `           |
| Sepolia | `          ` |     -  -     :  :       | `0x        ` | `      `           |
| Hoodi   | `          ` |     -  -     :  :       | `0x        ` | `      `           |
| Mainnet | `          ` |     -  -     :  :       | `0x        ` | `      `           |


### Readiness Checklist

**List of outstanding items before deployment.**

- [ ] Client Integration Testing
 - [ ] Select Testnet Fork Blocks
 - [ ] Select Mainnet Fork Block
 - [ ] Release Mainnet Compatible Clients
   - [ ]  Geth
   - [ ]  Besu
   - [ ]  Nethermind
   - [ ]  Reth
   - [ ]  Erigon
   - [ ]  EthereumJS

[7594]: https://eips.ethereum.org/EIPS/eip-7594
[7823]: https://eips.ethereum.org/EIPS/eip-7823
[7825]: https://eips.ethereum.org/EIPS/eip-7825
[7883]: https://eips.ethereum.org/EIPS/eip-7883
[7918]: https://eips.ethereum.org/EIPS/eip-7918
[7934]: https://eips.ethereum.org/EIPS/eip-7934
[7935]: https://eips.ethereum.org/EIPS/eip-7935
[7939]: https://eips.ethereum.org/EIPS/eip-7939
[7951]: https://eips.ethereum.org/EIPS/eip-7951
[7892]: https://eips.ethereum.org/EIPS/eip-7892
[7642]: https://eips.ethereum.org/EIPS/eip-7642
[7910]: https://eips.ethereum.org/EIPS/eip-7910
