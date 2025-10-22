# Benchmark Test Cases

Benchmark tests aim to maximize the usage of a specific opcode, precompile, or operation within a transaction or block. They are located in the `./tests/benchmarks` folder and the available test cases are documented in [test case reference](../tests/benchmark/index.md).

To fill a benchmark test, in addition to the usual test flags, you must include the `-m benchmark` flag. This is necessary because benchmark tests are ignored by default; they must be manually selected via the `benchmark` pytest marker (="tag"). This marker is applied to all tests under `./tests/benchmark/` automatically by the framework.

**Note:** Benchmark tests are now only available starting from the `Prague` fork. Tests targeting earlier forks (`Cancun` or prior) are not supported in benchmark mode.

## Setting the Gas Limit for Benchmarking

To consume the full benchmark gas limit, use the `gas_benchmark_value` fixture as the gas limit:

```py
def test_benchmark(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    gas_benchmark_value: int
):
    ...
```

You can specify the block gas limit used in benchmark tests by setting the `--gas-benchmark-values` flag. This flag accepts a comma-separated list of values (in millions of gas), e.g. `--gas-benchmark-values 1,10,45,60`. This example would run the test 4 times, using a `gas_benchmark_value` of 1M, 10M, 45M, and 60M respectively.

Do not configure the transaction/block gas limit to `env.gas_limit`. When running in benchmark mode, the test framework sets this value to a very large number (e.g., `1_000_000_000_000`), this setup allows the framework to reuse a single genesis file for all specified gas limits. I.e., the example below is invalid:

```py
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

## Expected Gas Usage

In benchmark mode, the developer should set the expected gas consumption using the `expected_benchmark_gas_used` field. Benchmark tests do not need to consume the full gas limit, instead, you could calculate and specify the expected usage. If `expected_benchmark_gas_used` is not set, the test will fall back to using `gas_benchmark_value` as the expected value.

```py
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
