"""
The Amsterdam fork ([EIP-7607]) includes networking changes (peerDAS), increases
the gas cost while limiting the input size of the `MODEXP` precompile, limits
the maximum gas per transaction, raises the blob base fee to always be above
the execution cost, limits the RLP-encoded size of blocks, introduces a count
leading zeros (`CLZ`) instruction, and adds a new precompile supporting the
secp256r1 curve.

### Notices

- [EIP-7935: Set default gas limit to XX0M][EIP-7935]

### Changes

- [EIP-7594: PeerDAS - Peer Data Availability Sampling][EIP-7594]
- [EIP-7823: Set upper bounds for MODEXP][EIP-7823]
- [EIP-7825: Transaction Gas Limit Cap][EIP-7825]
- [EIP-7883: ModExp Gas Cost Increase][EIP-7883]
- [EIP-7918: Blob base fee bounded by execution cost][EIP-7918]
- [EIP-7934: RLP Execution Block Size Limit][EIP-7934]
- [EIP-7939: Count leading zeros (CLZ) opcode][EIP-7939]
- [EIP-7951: Precompile for secp256r1 Curve Support][EIP-7951]
- [EIP-7892: Blob Parameter Only Hardforks][EIP-7892]
- [EIP-7642: eth/69 - history expiry and simpler receipts][EIP-7642]
- [EIP-7910: eth_config JSON-RPC Method][EIP-7910]

### Upgrade Schedule

| Network | Timestamp    | Date & Time (UTC)       | Fork Hash    | Beacon Chain Epoch |
|---------|--------------|-------------------------|--------------| ------------------ |
| Holesky | `          ` |     -  -     :  :       | `0x        ` |                    |
| Sepolia | `          ` |     -  -     :  :       | `0x        ` |                    |
| Hoodi   | `          ` |     -  -     :  :       | `0x        ` |                    |
| Mainnet | `          ` |     -  -     :  :       | `0x        ` |                    |

### Releases

[EIP-7607]: https://eips.ethereum.org/EIPS/eip-7607
[EIP-7594]: https://eips.ethereum.org/EIPS/eip-7594
[EIP-7823]: https://eips.ethereum.org/EIPS/eip-7823
[EIP-7825]: https://eips.ethereum.org/EIPS/eip-7825
[EIP-7883]: https://eips.ethereum.org/EIPS/eip-7883
[EIP-7918]: https://eips.ethereum.org/EIPS/eip-7918
[EIP-7934]: https://eips.ethereum.org/EIPS/eip-7934
[EIP-7935]: https://eips.ethereum.org/EIPS/eip-7935
[EIP-7939]: https://eips.ethereum.org/EIPS/eip-7939
[EIP-7951]: https://eips.ethereum.org/EIPS/eip-7951
[EIP-7892]: https://eips.ethereum.org/EIPS/eip-7892
[EIP-7642]: https://eips.ethereum.org/EIPS/eip-7642
[EIP-7910]: https://eips.ethereum.org/EIPS/eip-7910
"""  # noqa: E501

from ethereum.fork_criteria import Unscheduled

FORK_CRITERIA = Unscheduled(order_index=1)
