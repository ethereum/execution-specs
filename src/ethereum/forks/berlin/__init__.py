"""
The Berlin fork adjusts the gas costs of the `ModExp` precompile and several
state access EVM instructions, introduces typed transaction envelopes along
with the first new transaction type—optional access lists.

### Changes

- [EIP-2565: ModExp Gas Cost][EIP-2565]
- [EIP-2929: Gas cost increases for state access opcodes][EIP-2929]
- [EIP-2718: Typed Transaction Envelope][EIP-2718]
- [EIP-2930: Optional access lists][EIP-2930]

### Upgrade Schedule

| Network | Block        | Expected Date    | Fork Hash    |
| ------- | ------------ | ---------------- | ------------ |
| Ropsten |  9,812,189   | March 10, 2021   |              |
| Goerli  |  4,460,644   | March 17, 2021   |              |
| Rinkeby |  8,290,928   | March 24, 2021   |              |
| Mainnet | 12,244,000   | April 14, 2021   | `0x0eb440f6` |

### Releases

- [Besu 21.1.2]
- [EthereumJS VM 5.2.0][js]
- [Geth 1.10.1]
- [Nethermind 1.10.58][n]
- [OpenEthereum 3.2.0][oe]

[EIP-2565]: https://eips.ethereum.org/EIPS/eip-2565
[EIP-2929]: https://eips.ethereum.org/EIPS/eip-2929
[EIP-2718]: https://eips.ethereum.org/EIPS/eip-2718
[EIP-2930]: https://eips.ethereum.org/EIPS/eip-2930
[Besu 21.1.2]: https://github.com/hyperledger/besu/releases/tag/21.1.2
[js]: https://github.com/ethereumjs/ethereumjs-monorepo/releases/tag/%40ethereumjs%2Fvm%405.2.0
[Geth 1.10.1]: https://github.com/ethereum/go-ethereum/releases/tag/v1.10.1
[n]: https://github.com/NethermindEth/nethermind/releases/tag/1.10.58
[oe]: https://github.com/openethereum/openethereum/releases/tag/v3.2.0
"""  # noqa: E501

from ethereum.fork_criteria import ByBlockNumber

FORK_CRITERIA = ByBlockNumber(12244000)
