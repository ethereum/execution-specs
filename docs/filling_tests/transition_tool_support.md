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

The filler resolves every block of a transition test to the fork whose rules apply to it and passes that fork's name in `--state.fork` (or the server request's `state.fork` field). External tools therefore see `BPO2` for the blocks before the boundary of `BPO2ToAmsterdamAtTime15k` and `Amsterdam` from the boundary on; they never see the transition name and cannot tell the fork block from a later one.

The in-process EELS t8n receives the transition fork itself and executes each block with the rules of the side it falls on. It mirrors the spec's `is_fork_block` with the transition schedule: the block activates its fork when the schedule places its parent, by number and `parentTimestamp`, on the other side of the boundary. The `ethereum-spec-evm t8n` command accepts the transition name directly, for example `--state.fork=BPO2ToAmsterdamAtTime15k`, and derives the same activation from the environment. No separate activation flag exists.

A fixture whose genesis is already in the fork has no fork block: a plain fork has no boundary, so nothing activates. Only a fixture that crosses the boundary runs the EIP-8253 nonce update, on the first block at or after the activation timestamp whose parent is before it.
