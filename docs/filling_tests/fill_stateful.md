# Filling Stateful Benchmark Fixtures

The `fill-stateful` command produces `BlockchainEngineStatefulFixture` JSON for benchmark tests by driving block construction on a live EL client via `testing_buildBlockV1` against a pre-loaded network snapshot. The fixtures are replayed by [`benchmarkoor`](https://github.com/ethpandaops/benchmarkoor) against the same snapshot on any EL client. This replaces the gas-benchmarks MITMProxy approach.

!!! note "When to use `fill-stateful`"
    Use the standard `fill` for t8n-based fixture generation. Use `fill-stateful` to run benchmarks in a stateful environment (e.g., perfnet, Kurtosis, or other snapshots) to observe how state size affects performance. Any test can be run using this command, but some benchmarks – like the ones under `tests/benchmark/stateful/` – only produce meaningful results in such environments.

`fill-stateful` does not manage datadirs — it expects the target client to already be running with the snapshot mounted. Snapshot management (overlayfs / ZFS / copy) is `benchmarkoor`'s responsibility on the replay side.

## Prerequisites

The target client must expose:

- `testing` (`testing_buildBlockV1`) — block construction with explicit transaction ordering.
- `engine` — `engine_newPayloadVX`, `engine_forkchoiceUpdatedVX`.
- `eth`, `debug` — chain queries and `debug_setHead` (or `debug_resetHead` on clients like Nethermind that lack `debug_setHead`) for between-test rewind. `--extract-opcode-count` additionally needs `debug_traceBlockByHash` with JS tracer support.
- `web3` (optional) — `web3_clientVersion` is recorded into the fixture's `_info.filling-transition-tool` for traceability.

The production-ready filler is `ethpandaops/geth:master`.

## End-to-end flow

### 1. Bootstrap a snapshot

For local development, a kurtosis enclave produces a synthetic snapshot:

```yaml
# /tmp/fillst-kurtosis-args.yaml
participants:
  - el_type: geth
    el_image: ethpandaops/geth:master
    el_extra_params:
      - "--http.api=admin,debug,eth,miner,net,txpool,web3,testing,engine"
      - "--miner.gaslimit=1000000000000"
    cl_type: lodestar
network_params:
  preset: minimal
  genesis_delay: 30
  fulu_fork_epoch: 0
  gas_limit: 1000000000000
ethereum_genesis_generator_params:
  image: "ethpandaops/ethereum-genesis-generator:5.3.5"
```

```bash
kurtosis run --enclave fillst /path/to/ethereum-package \
    --args-file /tmp/fillst-kurtosis-args.yaml
```

Drain a few blocks, stop CL then EL cleanly, extract the datadir + genesis bundle:

```bash
docker stop -t 30 vc-1-geth-lodestar--... cl-1-lodestar-geth--...
docker stop -t 60 el-1-geth-lodestar--...
docker cp el-1-geth-lodestar--...:/data/geth/execution-data /tmp/multi-snap/geth/
rm -f /tmp/multi-snap/geth/execution-data/geth/{LOCK,nodes/LOCK,chaindata/LOCK}
kurtosis files download fillst el_cl_genesis_data /tmp/multi-snap/genesis
kurtosis files download fillst jwt_file /tmp/fillst-out/jwt
```

For production benchmarking, use a perfnet / bloatnet snapshot instead.

### 2. Start a standalone client on a copy of the snapshot

Keep the original snapshot pristine so `benchmarkoor` can reuse it on the replay side:

```bash
cp -a /tmp/multi-snap/geth/execution-data /tmp/multi-snap/geth-fillcopy

docker run -d --name geth-fillcopy \
  -p 18545:8545 -p 18551:8551 \
  -v /tmp/multi-snap/geth-fillcopy:/datadir \
  -v /tmp/multi-snap/genesis:/genesis:ro \
  -v /tmp/fillst-out/jwt:/jwt:ro \
  ethpandaops/geth:master \
  --datadir=/datadir --override.genesis=/genesis/genesis.json \
  --http --http.addr=0.0.0.0 --http.port=8545 \
  --http.api=admin,debug,eth,miner,net,txpool,web3,testing,engine \
  --authrpc.port=8551 --authrpc.addr=0.0.0.0 \
  --authrpc.jwtsecret=/jwt/jwtsecret \
  --syncmode=full --gcmode=archive \
  --miner.gaslimit=1000000000000 \
  --nodiscover --maxpeers=0
```

### 3. Fill

```bash
uv run fill-stateful \
    --clean \
    --rpc-endpoint=http://127.0.0.1:18545 \
    --engine-endpoint=http://127.0.0.1:18551 \
    --engine-jwt-secret-file=/tmp/fillst-out/jwt/jwtsecret \
    --fork=Osaka \
    --output=/tmp/fillst-out/fixtures \
    --snapshot-block=0x<32-byte-hash> \
    --gas-benchmark-values=10,30 \
    tests/benchmark/stateful/bloatnet/test_transient_storage.py
```

### 4. Replay

Point `benchmarkoor`'s `datadirs.geth.source_dir` at the pristine snapshot (`/tmp/multi-snap/geth/execution-data`) — never at the fillcopy — and `tests.source.eest_fixtures.local_fixtures_dir` at the fill output. See the [benchmarkoor docs](https://github.com/ethpandaops/benchmarkoor) for the full config shape.

## CLI options

Required:

- `--engine-jwt-secret-file PATH` — JWT secret for engine API auth.
- `--fork NAME` — fork to fill against, e.g. `Osaka`.

Optional:

- `--rpc-endpoint URL` — default `http://localhost:8545`.
- `--engine-endpoint URL` — derived from `--rpc-endpoint` with port `8551`.
- `--chain-id INT` — auto-detected from the client.
- `--snapshot-block HASH_OR_NUMBER` — anchor to a specific block; accepts a 32-byte hash (recommended) or an integer block number (hex `0x...` or decimal). Defaults to the client's `latest`, recorded by hash.
- `--rpc-seed-key 0x<64hex>` — pin the seed account for reproducible fills. When omitted, a random key is generated and funded via CL withdrawal each session.
- `--address-stubs PATH` — JSON map of label → on-chain address (and optional pkey). Required by stub-dependent tests; see [Stub-dependent tests](#stub-dependent-tests) below.
- `--max-gas-per-test INT` — overrides the fork's `transaction_gas_limit_cap()` (EIP-7825).
- `--gas-benchmark-values 10,30,...` — gas budgets in millions to parametrize against.
- `--default-{gas-price,max-fee-per-gas,max-priority-fee-per-gas,max-fee-per-blob-gas}` — pin per-session fees; defaults bump live-query values by `1.5×`.
- `--output PATH` — default `./fixtures`.
- `--clean` — wipe the output dir before filling.
- `--extract-opcode-count` — after building each block, trace it via `debug_traceBlockByHash` (a JS opcode-counting tracer) and record per-opcode execution counts (execution-phase blocks only) in the fixture's `_info.metadata.opcode_count`, matching what the standard `fill` benchmark path emits. When a benchmark test declares a target opcode count (`fixed_opcode_count`/`expected_opcode_count`), the live-client count is verified against it and the fill fails on >5% divergence. Requires the `debug` namespace with JS tracer support. Adds a full re-execution trace per block, so it is slow and opt-in.

## Output layout

```text
<output>/
└── blockchain_tests_stateful_engine/
    ├── pre_run/
    │   └── <start_block_hash>.json # session bootstrap (factory deploy + seed funding)
    └── for_<fork>_at_<gas>M/
        └── <test_path>/
            └── <test>.json         # per-test setup + execution payloads
```

Each `pre_run/<start_block_hash>.json` (a `StatefulPreRunFixture`) is replayed once per `benchmarkoor` run. Per-test fixtures (`BlockchainEngineStatefulFixture`) reference their setup file by hash: a fixture with `startBlockHash = 0xabc...` is preceded by `pre_run/0xabc....json`. Each per-test fixture carries `snapshotBlockNumber`/`Hash`, `startBlockNumber`/`Hash`, `setupEngineNewPayloads`, `engineNewPayloads`, plus a `benchmarkGasUsed` field and the EL build in `_info.filling-transition-tool`. With `--extract-opcode-count`, it also carries `_info.metadata.opcode_count` (per-opcode execution counts across the execution-phase blocks). The hash-based filename leaves room for multiple pre-run files (e.g. different setup variants off one snapshot) without coordinating names.

!!! warning "Snapshot anchoring"
    `--snapshot-block` accepts a hash on purpose. Anchoring to `latest` works against a quiescent client, but a live reorg between session start and fixture write would silently re-anchor the fixture to a different block. The hash form rejects that.

!!! warning "State pollution across fills"
    Re-running `fill-stateful` against the same datadir progresses the chain past previous fills. Always start from a fresh copy of the snapshot.

!!! note "Single-worker"
    `fill-stateful` forces `-n 0` — pytest-xdist is not used; the chain advances sequentially.

## Stub-dependent tests

Some stateful tests (e.g. `test_single_opcode.py`, `test_multi_opcode.py`) target on-chain accounts the snapshot already contains. They reach them two ways:

- `@pytest.mark.stub_parametrize("name", "prefix_")` — parametrize values pulled from `--address-stubs` matching `prefix_`.
- `pre.deploy_contract(stub="<label>", ...)` — direct runtime lookup.

Without a matching `--address-stubs` entry, both paths fail loudly: the marker path with `FAILED ... MISSING_STUBS` carrying the missing prefix; the runtime path with `ValueError("Stub '<label>' not found...")`. Stock pytest's silent skip on empty parametrize is overridden — running a bloatnet test with no stubs is a misconfiguration, not a valid outcome.

Stubs must point at addresses already on the live client; fill-stateful validates each at session start. The kurtosis devnet recipe above does **not** include them — use a bloatnet / perfnet snapshot (or a custom snapshot generator) for these tests.

## Architecture

`fill-stateful` reuses fill's standard spec loop and swaps the *backend*. Two
backends now exist behind a common protocol; the rest of fill is unchanged.

```text
                 BlockchainTest.generate_block_data
                              │
                ┌─────────────┴──────────────┐
                ▼                            ▼
       TransitionTool                  ClientBackend
       (t8n CLI / server)         (testing_buildBlockV1 on a live EL)
            ▼                            ▼
       make_fixture /               make_stateful_fixture
       make_hive_fixture                  ▼
            ▼                  BlockchainEngineStatefulFixture
       BlockchainFixture /                + StatefulPreRunFixture
       BlockchainEngineFixture
```

Both backends satisfy `FillerBackend` (`client_clis/filler_backend.py`). `ClientBackend.evaluate(...)` returns a `TransitionToolOutput` with an `EnginePayloadMetadata` attached (`GetPayloadResponse` + engine API versions); the spec receives it as `TestingBuildBlock(BuiltBlock)` and forwards the payload verbatim — no header rebuild, no side-channel capture.

### Plugins and shared code

| Module | Role |
|---|---|
| `cli/pytest_commands/fill_stateful.py` | CLI entry — `fill-stateful` Click command. |
| `plugins/fill_stateful/fill_stateful.py` | Session pre-run + `t8n`/`session_t8n` overrides; CLI options. |
| `plugins/shared/live_client_flags.py` | Live-client flags + fee fixtures factored out of `execute/execute.py`. |
| `plugins/execute/pre_alloc.py` | Reused `Alloc`; `pending_transactions()` drains the queue without sending. |
| `plugins/execute/rpc/chain_builder_eth_rpc.py` | `fund_via_withdrawals` + `build_block_with_transactions` — return `EnginePayloadMetadata`. |
| `client_clis/client_backend.py` | `ClientBackend`: builds via `testing_buildBlockV1`, advances via `engine_newPayload` + `forkchoiceUpdated` (SYNCING-retry). |
| `specs/blockchain.py` | `make_stateful_fixture`, `payload_metadata_to_fixture`, `Block.phase`, `_split_blocks_by_phase`, `TestingBuildBlock`. |

### Flags introduced

| Flag | Where | Purpose |
|---|---|---|
| `--snapshot-block` | `fill-stateful` | Anchor by 32-byte hash (reorg-safe) or block number; defaults to `latest`. |
| `--rpc-seed-key` | `fill-stateful` | Pin the seed EOA; otherwise generated + funded via CL withdrawal. |
| `--default-gas-price`, `--default-max-fee-per-gas`, `--default-max-priority-fee-per-gas`, `--default-max-fee-per-blob-gas` | `shared/live_client_flags` | Pin per-session fees; defaults bump a one-shot live query by `1.5x`. |
| `--max-gas-per-test`, `--max-tx-per-batch`, `--transaction-gas-limit`, ... | `shared/live_client_flags` | Generic live-client knobs reused across commands. |

### Fill flow

1. **Session pre-run** (`_session_pre_run`, autouse session fixture):
    1. Resolve `--snapshot-block` → record `(number, hash)` on the backend.
    2. Fund the seed EOA via CL withdrawal (`ChainBuilderEthRPC.fund_via_withdrawals`).
    3. Deploy the deterministic factory if missing (`contracts.deploy_deterministic_factory_contract`).
    4. Capture `latest` as the `start_block` anchor on the backend.
    5. Write `pre_run/<start_block_hash>.json` (a `StatefulPreRunFixture`).
2. **Per-test fill** (`make_stateful_fixture`):
    1. Materialise `pre.fund_eoa` / `pre.deploy_contract` queue into a synthetic setup block prepended to `self.blocks`.
    2. `_split_blocks_by_phase` splits any mixed-phase blocks (e.g. EIP-7702 SETUP + benchmark TEST).
    3. For each block, `ClientBackend.evaluate` builds + finalises it; payload partitioned by `Block.phase` into `setupEngineNewPayloads` vs `engineNewPayloads`.
    4. Write `<test>.json` (a `BlockchainEngineStatefulFixture`).
3. **Per-test reset** (`_reset_chain_between_tests`): `debug_setHead(start_block.number)` — or `debug_resetHead(start_block.hash)` on clients without `debug_setHead`, e.g. Nethermind — re-fetch `latest`, abort if hash drifted.

### Fixture types

| Type | One per | Carries |
|---|---|---|
| `StatefulPreRunFixture` | session | `snapshot/start` anchors, `engineNewPayloads` (the withdrawal + factory deploy blocks). |
| `BlockchainEngineStatefulFixture` | test | `snapshot/start` anchors, `setupEngineNewPayloads`, `engineNewPayloads`, `benchmarkGasUsed`, `_info.filling-transition-tool` (EL build string). |
| `FixtureEngineNewPayload` | block | `params` (`engine_newPayloadVX` args), `newPayloadVersion`, `forkchoiceUpdatedVersion`, `phase` (`SETUP`/`EXECUTION`/`None`). |

### What's captured in each payload

The client's `GetPayloadResponse` is recorded **verbatim**. Rebuilding from `FixtureHeader` would diverge on client-picked fields (e.g. `gas_limit`) and break `engine_newPayload` hash validation on replay.

### Replay (benchmarkoor)

```text
pristine snapshot ───copy──▶ datadir ───▶ geth ───▶ benchmarkoor
                                                       │
                                                       ├── replay pre_run/<startBlockHash>.json
                                                       │   for each fixture's startBlockHash
                                                       │   (1 client, 1 time per hash per run)
                                                       │
                                                       └── for each test fixture:
                                                            ├── replay setupEngineNewPayloads
                                                            ├── replay engineNewPayloads (timed)
                                                            ├── debug_setHead/resetHead → start_block
                                                            └── re-fetch latest, verify hash
```

Sanity check: each fixture's `benchmarkGasUsed` (recorded at fill) should equal benchmarkoor's measured `gas_used_total` for that test.
