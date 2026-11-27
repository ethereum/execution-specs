# Benchmark Tests

The EELS benchmark serves as a centralized hub for benchmarking test cases, evaluating execution layer performance across a wide range of scenarios, including gas limit testing, zkEVM, Bloatnet, gas repricing and EIPs that introduce new opcodes, precompiles, transaction types, or more use cases.

All benchmark tests are maintained under the `./tests/benchmark` directory. The benchmark suite is further organized based on whether tests require a pre-configured, stateful environment.

## Directory Structure

The benchmark suite is organized as follows:

```text
tests/benchmark/
├── compute/
│   ├── instruction/        # Individual EVM opcodes
│   ├── precompile/         # EVM precompiles
│   └── scenario/           # Mix of operations, transaction types, etc.
└── stateful/               # Pre-configured state environments required
```

There are multiple files under `instruction/`, users can check each file's docstring to understand which opcodes are covered in the file.

Benchmark tests are not collected by `fill` and `execute remote`  by default, in order to run them, their path must explicitly be provided to these command:

```bash
fill -v tests/benchmark/
execute remote -v tests/benchmark
```

### Stateful Benchmarks

A subset of benchmark test cases run on top of stateful environments (such as bloatnet or mainnet-like setups), in order to analyze how state size, structure, and access patterns influence performance. These tests may (1) pre-deploy contracts (2) construct initial storage state (3) Interact with pre-deployed contracts via stub addresses.

These tests are located under `./tests/benchmark/stateful`.

### Compute Benchmarks

Other benchmark tests do not require any pre-state configuration. These benchmarks could be run even without pre-deployed contracts or initialized storage.

These tests are located under `./tests/benchmark/compute`.

**Note:** Benchmark tests are now only available starting from the `Prague` fork. Tests targeting earlier forks (`Cancun` or prior) are not supported in benchmark mode.

## Worst-Case Mode

In worst-case mode, users specify a target block gas limit.
By providing `--gas-benchmark-values N` (where N denotes the gas limit in millions), the benchmark construction process packs each block with as many instances as possible of the selected operation.

This mode is designed for gas limit testing, and gas repricing, where it enables:

- Evaluate execution-layer performance under extreme, worst-case conditions given certain operations.
- Identify bottlenecks that may only surface at high gas utilization levels

**Note:** Users may supply multiple values in a single invocation. For example, `--gas-benchmark-values 1,2,3` runs the test with 1M, 2M, and 3M block gas limits.

**Output layout with gas benchmark values:** When `--gas-benchmark-values` is provided and benchmark tests are filled, fixtures are written into per‑fork, per‑gas‑limit subdirectories under each format directory:

```text
<output>/
  blockchain_tests/
    for_osaka_at_0001M/...
    for_osaka_at_0002M/...
  blockchain_tests_engine/
    for_osaka_at_0001M/...
    for_osaka_at_0002M/...
  blockchain_tests_engine_x/
    pre_alloc/...
    for_osaka_at_0001M/...
    for_osaka_at_0002M/...
```

The subdirectory name follows the pattern `for_{fork}_at_{gas}M` (see [Fixture Output Directory Structure](../running_tests/releases.md#fixture-output-directory-structure) for details). Non-benchmark (consensus) fixtures use `for_{fork}` without the gas limit suffix.

## Developing Benchmarks

Before writing benchmark-specific tests, please refer to the [general documentation](./writing_a_new_test.md) for the fundamentals of writing tests in the EELS framework.

### Environment Variables

#### Accessing the Block Gas Limit

When using `--gas-benchmark-values`, do not read the block gas limit from `env.gas_limit`. Instead, tests consume the injected `gas_benchmark_value` parameter, which reflects the current benchmark iteration block gas limit value.

```python
def test_benchmark(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    gas_benchmark_value: int
):
    ...
```

For example, running the test with `--gas-benchmark-values 1,10,45,60`. will execute the test 4 times, passing `gas_benchmark_value` as 1M, 10M, 45M, and 60M respectively.

Never configure the transaction / block gas limit to `env.gas_limit`. When running in benchmark mode, the test framework sets this value to a very large number (e.g., `1_000_000_000_000`), this setup allows the framework to reuse a single genesis file for all specified gas limits. I.e., the example below should be avoided:

```python
def test_benchmark(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    env: Environment
):
    ...
    tx = Transaction(
        to=opcode_address,
        gas_limit=env.gas_limit, # Do not set the gas_limit manually.
        sender=pre.fund_eoa(),
    )
    ...
```

#### Referencing Transaction Gas Limit

Since the Osaka fork, EIP-7825 introduces a transaction gas limit cap (approximately 16M). Instead of hardcoding this value in the test, use `fork.transaction_gas_limit_cap()` for a cleaner, fork-aware approach.

This helper fixture could simplify the logic of determine the transaction gas limit cap, it returns the value if available, otherwise falls back to the block gas limit:

```python
@pytest.fixture
def tx_gas_limit(fork: Fork, gas_benchmark_value: int) -> int:
    """Return the transaction gas limit cap, or block gas limit if not available."""
    return fork.transaction_gas_limit_cap() or gas_benchmark_value
```

Example usage: import `tx_gas_limit` to calculate how many transactions fit in the block:

```python
def test_benchmark(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    gas_benchmark_value: int,
    tx_gas_limit: int
):
    ...
    num_of_full_tx_num = gas_benchmark_value // tx_gas_limit
    gas_for_last_tx = gas_benchmark_value % tx_gas_limit
    ...
```

#### Specifying Execution Semantics

When constructing benchmark tests with multiple transactions or blocks, identify which transaction is the actual benchmark transaction becomes difficult. `TestPhaseManager` is used to label transactions as either setup or execution phases.

```python
def test_complex_benchmark(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
) -> None:
    # Setup phase
    with TestPhaseManager.setup():
        setup_tx = Transaction(...)

    # Execution phase
    with TestPhaseManager.execution():
        exec_tx = Transaction(...)

    benchmark_test(
        blocks=[Block(txs=[setup_tx]), Block(txs=[exec_tx])],
        expected_benchmark_gas_used=...,
    )
```

Import `TestPhaseManager` and use it to annotate each transaction or block with its corresponding phase. During analysis, filters transactions by metadata, excluding setup transactions and measuring only the actual benchmark transaction.

### BenchmarkTest Wrapper

Within the EELS framework, tests can be written using existing fixtures such as `BlockchainTest` and `StateTest`. However, for benchmark scenarios, we strongly recommend using the `BenchmarkTest` wrapper, which encapsulates repetitive logic commonly required in benchmark test construction.

Note that `BenchmarkTest` is a wrapper, not a new fixture type. It does not introduce a new fixture format, and therefore clients do not need to add special support for it. Internally, `BenchmarkTest` accepts user-provided parameters and converts them into the corresponding `BlockchainTest` representation.

#### Mode 1: Using Custom Blocks

This mode is suitable for complex scenarios that require multiple transactions, where each transaction's logic is completely different.

```python
def test_complex_benchmark(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
) -> None:
    ...
    exec_tx_1 = Transaction(...)
    exec_tx_2 = Transaction(...)
    attack_block = Block(txs=[exec_tx_1, exec_tx_2])
    ...
    benchmark_test(
        blocks=[attack_block],
    )
```

#### Mode 2: Using a Single Transaction

Users may also provide a single transaction directly. In this mode, the wrapper automatically generates multiple transactions to fully utilize the target block gas limit.

For example, assume 60M block gas limit, and 16M transaction gas limit cap, the wrapper will construct 3 transactions with 16M gas limit and the final transaction with 12M gas limit

```python
def test_simple_benchmark(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    gas_benchmark_value: int,
) -> None:
    contract_address = pre.deploy_contract(code=Op.PUSH1(1) + Op.STOP)
    benchmark_test(
        tx=Transaction(
            to=contract_address,
            gas_limit=gas_benchmark_value,
            sender=pre.fund_eoa(),
        ),
    )
```

#### Mode 3: Using a Code Generator (Recommended)

This mode allows users to provide a code generator that emits execution payloads dynamically. It is the recommended approach for most benchmark use cases, as it offers the greatest flexibility and reuse.

Currently, EELS provides two built-in code generators, `JumpLoopGenerator` and `ExtCallGenerator`. Both generators accept the following components to construct the benchmark contracts:

- `setup`: Code executed once before the attack loop
- `attack_block`: The core operation to be benchmarked
- `cleanup`: Optional cleanup logic executed after benchmarking

In addition, users may customize transaction and contract construction via:

- `tx_kwargs`: Transaction-level parameters (e.g., calldata, blob fields)
- `code_padding_opcode`: If specified, the contract bytecode will be padded with the given opcode up to the maximum contract size

##### JumpLoopGenerator

`JumpLoopGenerator` maximizes the number of `attack_block` repetitions within a single contract by looping via `JUMP`. The benchmark construction repeats the `attack_block` as many times as possible.

```python
target_contract = (
    setup
    + JUMPDEST
    + attack_block
    + ...
    + attack_block
    + cleanup
    + JUMP(len(setup))
)
```

This generator is suitable when the benchmarked operation does **not** grow the EVM stack unboundedly, or when stack growth is explicitly managed (e.g., by pairing stack-producing opcodes with `POP`).

##### ExtCallGenerator

`ExtCallGenerator` constructs two contracts: (1) a target contract, which contains the benchmarked logic and (2) a loop contract, which repeatedly calls into the target contract

In this design, The `attack_block` inside the target contract is repeated 1024 times, corresponding to the EVM maximum stack size. And the loop contract repeatedly invokes the target contract to amplify execution via `STATICCALL`.

The contract structures are as follows:

Target contract:

```python
target_contract = (
    setup
    + attack_block
    + (repeat another 1022 times)
    + attack_block
    + cleanup  # usually empty
)
```

Loop contract:

```python
attack_block = pop(staticcall(addr=target_contract, argsize=CALLDATASIZE))

loop_contract = (
    CALLDATACOPY(size=CALLDATASIZE)
    + JUMPDEST
    + attack_block
    + ...
    + attack_block
    + cleanup
    + JUMP(len(setup))
)
```

`CALLDATACOPY` is required in loop contract since some target operation requires access to calldata, while the calldata is supplied in the transaction object. As a result, the loop contract must explicitly forward the calldata to the target contract. The calldata is first copied from transaction to the memory via `CALLDATACOPY` and pass to the target contract via `STATICCALL`.

##### Choosing Between Generators

`ExtCallGenerator` is particularly useful when benchmarking stack-growing opcodes (i.e., opcodes that push values onto the stack).

For example:

- When benchmarking `CALLDATASIZE` using `JumpLoopGenerator`, the `attack_block` must be written as `POP(CALLDATASIZE)` to avoid stack overflow
- With `ExtCallGenerator`, this restriction does not apply, as target contract execution naturally stops at the maximum stack size

Based on experimental results, `ExtCallGenerator` is often more optimized than `JumpLoopGenerator`, as it requires fewer glue opcodes in the benchmarked execution path.

**Note:** Users must provide exactly one parameter, either `tx`, `block` or `code_generator` to `BenchmarkTest`, more than one of these inputs simultaneously is not allowed.

## Validating Benchmarks

### Setting Expected Gas Usage

In benchmark mode, set the expected gas consumption using the `expected_benchmark_gas_used` field, if the test do not need to consume the full gas limit. Developer could calculate and specify the expected usage. If `expected_benchmark_gas_used` is not available, the setting will fall back to using `gas_benchmark_value` as the expected value.

```python
@pytest.mark.valid_from("Prague")
def test_empty_block(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
):
    """Test running an empty block as a baseline for fixed proving costs."""
    blockchain_test(
        pre=pre,
        post={},
        blocks=[Block(txs=[])],
        expected_benchmark_gas_used=0,
    )
```

This is a safety check to make sure the benchmark works as expected. For example, if a test uses the `JUMP` instruction but the jump destination is invalid, each transaction will stop early. That means it won't use as much gas as we expected.

This check helps catch such issues. As a result, the post-storage comparison method via `SSTORE` is no longer needed, thereby reducing the additional storage cost.

However, in cases where it is difficult to determine the total gas usage, or if an alternative verification method is used, developers may set `skip_gas_used_validation` to `True` to disable the gas usage check.

### Setting Target Operation

Specify which opcode to target using the `target_opcode` parameter. When `expected_opcode_count` is also set, the benchmark compares the executed count of `target_opcode` against it and fails on a deviation above 5%.

Opcode counts are recorded in a fixture's `_info.metadata` only for benchmark tests (tests under `tests/benchmark`, tests using `benchmark_test`, or any test filled with gas benchmark values). Pass `--count-opcodes` to `fill` to record them for every test.

```python
def test_jumpdests(
    benchmark_test: BenchmarkTestFiller,
) -> None:
    """Benchmark JUMPDEST instruction."""
    benchmark_test(
        target_opcode=Op.JUMPDEST,
        code_generator=JumpLoopGenerator(attack_block=Op.JUMPDEST),
    )
```

**Note:** This verification currently only works in `fill` mode, not in `execute-remote` mode.
