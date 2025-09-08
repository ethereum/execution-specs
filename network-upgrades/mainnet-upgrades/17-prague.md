## Prague Network Upgrade Specification

### Included EIPs
Execution layer changes included in the Network Upgrade.

* [EIP-2537: Precompile for BLS12-381 curve operations][2537]
* [EIP-2935: Serve historical block hashes from state][2935]
* [EIP-6110: Supply validator deposits on chain][6110]
* [EIP-7002: Execution layer triggerable withdrawals][7002]
* [EIP-7251: Increase the MAX\_EFFECTIVE\_BALANCE][7251]
* [EIP-7549: Move committee index outside Attestation][7549]
* [EIP-7623: Increase calldata cost][7623]
* [EIP-7685: General purpose execution layer requests][7685]
* [EIP-7691: Blob throughput increase][7691]
* [EIP-7840: Add blob schedule to EL config files][7840]
* [EIP-7702: Set Code for EOAs][7702]

### Implementation Progress

Implementation status of Included EIPs across participating clients.

|  **Client**    | [2537] | [2935] | [6110] | [7002] | [7251] | [7549] | [7623] | [7685] | [7691] | [7840] | [7702] |
|----------------|--------|--------|--------|--------|--------|--------|--------|--------|--------|--------|--------|
| **Geth**       |        |        |        |        |        |        |        |        |        |        |        |
| **Besu**       |        |        |        |        |        |        |        |        |        |        |        |
| **Nethermind** |        |        |        |        |        |        |        |        |        |        |        |
| **Reth**       |        |        |        |        |        |        |        |        |        |        |        |
| **Erigon**     |        |        |        |        |        |        |        |        |        |        |        |
| **EthereumJS** |        |        |        |        |        |        |        |        |        |        |        |

### Upgrade Schedule

| Network | Timestamp    | Date & Time (UTC)       | Fork Hash    | Beacon Chain Epoch |
|---------|--------------|-------------------------|--------------| ------------------ |
| Holesky | `1740434112` | 2025-02-24 21:55:12     |              | `115968`           |
| Sepolia | `1741159776` | 2025-03-05 07:29:36     |              | `222464`           |
| Hoodi   | `1742999832` | 2025-03-26 14:37:12     |              | `2048`             |
| Mainnet | `1746612311` | 2025-05-07 10:05:11     | `0xc376cf8b` | `364032`           |


### Readiness Checklist

**List of outstanding items before deployment.**

- [x] Client Integration Testing
  - [x] [Devnets](https://github.com/ethpandaops/pectra-testnet)
 - [x] Select Testnet Fork Blocks
 - [x] Select Mainnet Fork Block
 - [x] Release Mainnet Compatible Clients
   - [x]  Geth
   - [x]  Besu
   - [x]  Nethermind
   - [x]  Reth
   - [x]  Erigon
   - [x]  EthereumJS

[7702]: https://eips.ethereum.org/EIPS/eip-7702
[7691]: https://eips.ethereum.org/EIPS/eip-7691
[7623]: https://eips.ethereum.org/EIPS/eip-7623
[7840]: https://eips.ethereum.org/EIPS/eip-7840
[7251]: https://eips.ethereum.org/EIPS/eip-7251
[7002]: https://eips.ethereum.org/EIPS/eip-7002
[7685]: https://eips.ethereum.org/EIPS/eip-7685
[6110]: https://eips.ethereum.org/EIPS/eip-6110
[2537]: https://eips.ethereum.org/EIPS/eip-2537
[2935]: https://eips.ethereum.org/EIPS/eip-2935
[7549]: https://eips.ethereum.org/EIPS/eip-7549
