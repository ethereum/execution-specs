# Transition Tool Support

The following transition tools are supported by the framework:

| Client | `t8n` Tool | Tracing Support |
| -------| ---------- | --------------- |
| [ethereum/evmone](https://github.com/ethereum/evmone) | `evmone t8n` | Yes |
| [ethereum/execution-specs](https://github.com/ethereum/execution-specs) | [`ethereum-spec-evm t8n`](https://github.com/ethereum/execution-specs/tree/e50432d044728f59a51ebf284f1fdf638b41aff4/packages/testing/src/execution_testing/evm_tools/t8n) | Yes |
| [ethereumjs](https://github.com/ethereumjs/ethereumjs-monorepo) | [`ethereumjs-t8ntool.sh`](https://github.com/ethereumjs/ethereumjs-monorepo/tree/master/packages/vm/test/t8n) | No |
| [ethereum/go-ethereum](https://github.com/ethereum/go-ethereum) | [`evm t8n`](https://github.com/ethereum/go-ethereum/tree/master/cmd/evm) | Yes |
| [besu-eth/besu](https://github.com/besu-eth/besu/tree/main/ethereum/evmtool) | [`evmtool t8n-server`](https://github.com/besu-eth/besu/tree/main/ethereum/evmtool) | Yes             |
| [status-im/nimbus-eth1](https://github.com/status-im/nimbus-eth1) | [`t8n`](https://github.com/status-im/nimbus-eth1/blob/master/tools/t8n/readme.md) | Yes |

## Fork transitions

Transition tests retain their fork configuration during filling. For example,
`BPO2ToAmsterdamAtTime15k` is passed in the existing `--state.fork` argument
(or the server request's `state.fork` field), together with the current and
parent block timestamps in the environment. EELS selects the execution rules
for each block and derives whether the block crosses the configured boundary.
No separate activation flag is required. External tools must support the
requested transition name and the fork's state changes.

An Amsterdam-only fixture starts with an Amsterdam genesis state; its first
executed block does not activate Amsterdam. A transition fixture instead runs
the EIP-8253 nonce update on the first block whose timestamp reaches or exceeds
the activation timestamp while its parent's timestamp is earlier.

EIP-8253 fixtures use the fixed Mainnet address list with synthetic account
states. Listed accounts are bumped even if their storage is empty or they are
absent. The framework does not impose Mainnet account-state restrictions on
custom prestates at those addresses or elsewhere.
