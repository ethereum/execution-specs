# Stateful Environment Stub Accounts Configuration

Stateful benchmarks require pre-deployed contracts and accounts. You can download a snapshot or use state-actor to generate the required state. This page documents the necessary stub accounts for each benchmark and provides an example state-actor configuration.

Key points:

- Receiver variants are named `receivers-<kebab-case>` (except `NON_EXISTING_ACCOUNT`, which has no entity)
- Exact addresses, keys, and derivation rules are in the full configuration
- Account counts scale to the target block gas limit (examples target 300M; adjust for your needs)

## General

Required by every run, regardless of which tests are selected.

| Entry | Configuration | Used By |
|-------|---------------|---------|
| `deterministic-deployment-proxy` | Arachnid CREATE2 factory at `0x4e59…956C` | All tests: derives `receivers-existing-contract-*` addresses; needed for EEST pre-alloc deploys. **Note:** Once EIP-7997 activates, verify that the factory code is already in genesis to avoid duplicate deployment. |
| `fill-stateful-seed` | EOA (private key `0x…01`, balance `1e28` wei) | All tests: funds accounts during `fill --stateful` |

## Test-specific

Only needed by the listed tests; omit when those tests are not run.

| Entry | Configuration | Tests |
| --- | --- | --- |
| `bloated-eoa-10gb` | `storage_pattern`: bloated storage to cover existing slots | `test_sload_bloated`, `test_sstore_bloated` (`existing_slots=True`) |
| `receivers-existing-eoa` | `sequential_eoas`: 1-wei EOAs, starting from `0x…1000` | `test_account_access`, `test_ether_transfers_onchain_receivers` (`EXISTING_EOA`) |
| `receivers-existing-contract-minimal` | `create2_deploys`: 1-byte STOP (`MinimalContractInitcode`) | `test_account_access`, `test_ether_transfers_onchain_receivers` (`EXISTING_CONTRACT_MINIMAL`) |
| `receivers-existing-contract-same-max` | `create2_deploys`: max-size identical copies | `test_account_access`, `test_ether_transfers_onchain_receivers` (`EXISTING_CONTRACT_SAME_MAX`) |
| `receivers-existing-contract-diff-max` | `create2_deploys`: max-size unique copies | `test_account_access`, `test_ether_transfers_onchain_receivers` (`EXISTING_CONTRACT_DIFF_MAX`); delegation target for `receivers-7702-delegated` |
| `receivers-existing-contract-jumpdest` | `create2_deploys`: JUMPDEST analysis | `test_account_access`, `test_ether_transfers_onchain_receivers` (`EXISTING_CONTRACT_JUMPDEST`) |
| `sender-pool` | `sequential_pkey_eoas`: 1-ETH EOAs with keys `SENDER_BASE_KEY + i`, funded on-chain so senders stay uncached | Benchmarks using `yield_distinct_sender` (e.g., `test_ether_transfers_onchain_receivers`) |
| `receivers-bittrex-contracts` | `create_preimage_deploys`: contracts at Bittrex controller CREATE addresses (nonces 2+) | `test_ether_transfers_onchain_receivers` (existing-contract receivers) |
| `receivers-7702-delegated` | `sequential_pkey_delegations`: EIP-7702 authorities (keys `DELEGATE_BASE_KEY + i`), delegating to `receivers-existing-contract-diff-max` | `test_ether_transfers_onchain_receivers` (delegated receivers) |

## Full configuration

An example state-actor configuration targeting a 300M block gas limit:

```yaml
entities:
  # Arachnid CREATE2 factory (required by create2_deploys and EEST fill).
  - kind: contract
    template: create2_factory
    name: deterministic-deployment-proxy
    address: 0x4e59b44847b379578588920cA78FbF26c0B4956C
  # Seed EOA for fill-stateful funding (private key 0x…01).
  - kind: eoa
    name: fill-stateful-seed
    address: 0x7e5f4552091a69125d5dfcb7b8c2659029395bdf
    balance: "10000000000000000000000000000"
    nonce: 0
  # Bloated storage account (test_sload_bloated / test_sstore_bloated with existing_slots=True).
  - kind: contract
    name: bloated-eoa-10gb
    template: storage_pattern
    address: 0x87a6314da5ac8832f6e7a176c8fb133b19f5be04
    nonce: 1
    balance: "1000000000000000000"
    parameters:
      final: 150000
  # Sequential EOAs for EXISTING_EOA account mode
  - kind: contract
    name: receivers-existing-eoa
    template: sequential_eoas
    address: 0x0000000000000000000000000000000000001000
    parameters:
      count: 150000
      balance: "1"
  # CREATE2 contract receivers for different code patterns. Initcodes are deterministic;
  # addresses derive from salt + code_pattern via the CREATE2 factory.
  - kind: contract
    name: receivers-existing-contract-minimal
    template: create2_deploys
    parameters:
      initcode: "0x60016000f3"
      runtime: "0x00"
      salt_count: 100000
  - kind: contract
    name: receivers-existing-contract-same-max
    template: create2_deploys
    parameters:
      code_pattern: max_same_pre_amsterdam
      salt_count: 100000 # (all byte-identical)
  - kind: contract
    name: receivers-existing-contract-diff-max
    template: create2_deploys
    parameters:
      code_pattern: max_diff_pre_amsterdam
      salt_count: 100000 # (all byte-unique, ADDRESS-embedded)
  - kind: contract
    name: receivers-existing-contract-jumpdest
    template: create2_deploys
    parameters:
      code_pattern: unique_jumpdest_pre_amsterdam
      salt_count: 100000 # (JUMPDEST-heavy)
  # Sender pool for bloatnet benchmarks (test_ether_transfers_onchain_receivers).
  # Senders derived as EOA(key=SENDER_BASE_KEY + i) and pre-funded.
  - kind: contract
    name: sender-pool
    template: sequential_pkey_eoas
    parameters:
      start_pkey: "0xe1e1d3457c4e69b29cba0f7e1f92ce080d4db56d221bed913b09b2753bd97c7a"
      count: 150000
      balance: "1000000000000000000"
  # Bittrex controller CREATE-derived contracts.
  # Sender is Bittrex, nonces 2+ produce the contract chain.
  - kind: contract
    name: receivers-bittrex-contracts
    template: create_preimage_deploys
    parameters:
      sender: "0xA3C1E324CA1CE40DB73ED6026C4A177F099B5770"
      start_nonce: 2
      count: 100000
      runtime: "0x606060405236156100495763ffffffff7c01000000000000000000000000000000000000000000000000000000006000350416636ea056a98114610052578063c0ee0b8a14610092575b6100505b5b565b005b341561005a57fe5b61007e73ffffffffffffffffffffffffffffffffffffffff60043516602435610104565b604080519115158252519081900360200190f35b341561009a57fe5b604080516020600460443581810135601f810184900484028501840190955284845261005094823573ffffffffffffffffffffffffffffffffffffffff169460248035956064949293919092019181908401838280828437509496506101ef95505050505050565b005b6000805460408051602090810184905281517f3c18d31800000000000000000000000000000000000000000000000000000000815273ffffffffffffffffffffffffffffffffffffffff878116600483015292519290931692633c18d318926024808301939282900301818787803b151561017b57fe5b6102c65a03f1151561018957fe5b5050506040518051905073ffffffffffffffffffffffffffffffffffffffff1660003660006040516020015260405180838380828437820191505092505050602060405180830381856102c65a03f415156101e057fe5b50506040515190505b92915050565b5b5050505600a165627a7a723058204cdd69fdcf3cf6cbee9677fe380fa5f044048aa9e060ec5619a21ca5a5bd4cd10029"
      storage_init:
        "0x0": "0xa3c1e324ca1ce40db73ed6026c4a177f099b5770"
  # EIP-7702 delegated authorities
  # Authority i (key=DELEGATE_BASE_KEY + i) delegates to max_diff receiver i.
  - kind: contract
    name: receivers-7702-delegated
    template: sequential_pkey_delegations
    parameters:
      start_pkey: "0x959a83d905ff1fab43bf72c3e87020e4c77fd4bde0e5eeb48e5edbf74a9ec64e"
      code_pattern: max_diff_pre_amsterdam
      count: 100000
      balance: "1000000000000000000"
```
