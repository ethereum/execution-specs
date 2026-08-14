# Filling Tests at a Prompt

The execution-testing framework uses the [pytest framework](https://docs.pytest.org/en/latest/) for test case collection and execution. The `fill` command is essentially an alias for `pytest`, which uses several [custom pytest plugins](../library/pytest_plugins/index.md) to run transition tools against test cases and generate JSON fixtures.

!!! note "Options specific to execution-testing"
    The command-line options specific to filling tests can be listed via:

    ```console
    uv run fill --help
    ```

    See [Custom `fill` Command-Line Options](#custom-fill-command-line-options) for all options.

## Collection - Test Exploration

The test cases implemented in the `./tests` sub-directory can be listed in the console using:

```console
uv run fill --collect-only
```

and can be filtered (by test path, function and parameter substring):

```console
uv run fill --collect-only -k warm_coinbase
```

Docstrings are additionally displayed when ran verbosely:

```console
uv run fill --collect-only -k warm_coinbase -vv
```

## Execution

By default, test cases are filled for all forks already deployed to mainnet, but not for forks still under active development, i.e., as of time of writing, Q2 2023:

```console
uv run fill
```

will generate fixtures for test cases from Frontier to Shanghai.

To generate all the test fixtures defined in the `./tests/shanghai` sub-directory and write them to the `./fixtures-shanghai` directory, run `fill` in the top-level directory as:

```console
uv run fill ./tests/shanghai --output="fixtures-shanghai"
```

!!! note "Test case verification"
    Note, that the (limited set of) test `post` conditions are tested against the output of the `evm t8n` command during test generation.

To generate all the test fixtures in the `tests/shanghai/eip3651_warm_coinbase/test_warm_coinbase.py` module, for example, run:

```console
uv run fill tests/shanghai/eip3651_warm_coinbase/test_warm_coinbase.py
```

To generate specific test fixtures from a specific test function or even test function and parameter set, obtain the corresponding test ID using:

```console
uv run fill --collect-only -q -k test_warm_coinbase
```

This filters the tests by `test_warm_coinbase`. Then find the relevant test ID in the console output and provide it to fill, for example, for a test function:

```console
uv run fill tests/shanghai/eip3651_warm_coinbase/test_warm_coinbase.py::test_warm_coinbase_gas_usage
```

or, for a test function and specific parameter combination:

```console
uv run fill tests/shanghai/eip3651_warm_coinbase/test_warm_coinbase.py::test_warm_coinbase_gas_usage[fork_Paris-DELEGATECALL]
```

## Execution for Development Forks

!!! note ""
    By default, test cases are not filled for upcoming Ethereum forks so that they can be readily filled using the `evm` tool from the latest `geth` release.

    In order to fill test cases for an upcoming fork, ensure that the `evm` tool used supports that fork and features under test and use the `--until` or `--fork` flag.

    For example, as of Q2 2023, the current fork under active development is `Cancun`:
    ```console
    uv run fill --until Cancun
    ```

    See: [Filling Tests for Features under Development](./filling_tests_dev_fork.md).

## Generating All Fixture Formats

The `--generate-all-formats` flag enables generation of all fixture formats including the optimized `BlockchainEngineXFixture` in a single command:

```console
uv run fill --generate-all-formats tests/shanghai/
```

This flag automatically performs a two-phase execution:

1. **Phase 1**: Generates pre-allocation groups for optimization.
2. **Phase 2**: Generates all supported fixture formats (`StateFixture`, `BlockchainFixture`, `BlockchainEngineFixture`, `BlockchainEngineXFixture`, etc.).

!!! note "Tarball output requires explicit opt-in"
    Tarball output (`.tar.gz` files) does **not** imply `--generate-all-formats`. Pass the flag explicitly to include the pre-allocation group formats:
    ```console
    uv run fill --generate-all-formats --output=fixtures.tar.gz tests/shanghai/
    ```

## The Sync Block

By default the filler appends one framework-built empty block above every blockchain test's chain **in `blockchain_test_engine_x` fixtures only**, stored out-of-chain in the fixture's `syncPayload` field. `--no-sync-block` disables it:

```console
uv run fill --no-sync-block --generate-all-formats tests/cancun/
```

A consumer that makes a client download and execute a test's own blocks over devp2p needs the client to actually sync, and two facts about the protocol decide what such a consumer can guarantee: a client only starts a sync when the announced head's parent is unknown to it, and only blocks *below* the announced head must travel devp2p - the head's payload is always delivered through `engine_newPayload`, and whether a client also re-fetches it from a peer is an implementation choice. Appending the extra block satisfies both at once, for any chain the test declares:

```text
G → T₁ … Tₙ → S*
```

(`*` marks the block a sync-based consumer announces.) Every block the author wrote becomes an ancestor of that head, so a syncing client must fetch and execute all of them through its sync pipeline - by chain structure rather than by client courtesy.

This holds for chains whose head is intentionally invalid too. Nothing valid can be built on such a block, and the appended block does not try to be: it names the rejected block as its parent and is only a sync target. The client answers the announcement with `SYNCING`, fetches the rejected block from a peer, rejects it in its sync path, and then answers `INVALID` for the announced head with `latestValidHash` naming the last valid ancestor. Without the extra block the invalid block would be the announced head and would only ever arrive through the Engine API.

Because the appended block lives out-of-chain - the same representation [`consume sync`](../running_tests/running.md#sync)'s fixture format has always used - the fixture's `engineNewPayloads`, `lastblockhash` and post state keep describing exactly the chain the test author wrote: no shifted block numbers, no adjusted timestamps, no fee compensation, and byte-identical payloads to the same test's other fixture formats. Consumers that replay payloads through the Engine API can ignore the field entirely.

The block is real, built through the same machinery as every other block, and carries a per-test digest in its `extra_data` so that every announced head is a block the client has never seen - even across the byte-identical chains of two tests sharing a pre-allocation group.

Three kinds of chain get no appended block, and all of them fill as exactly the author's chain instead of being skipped, so no test ever leaves the fixture release (sync-based consumers skip chains that cannot sync at consume time):

- a chain asserting an `engine_api_error_code`, whose whole point is the client's answer to the announcement of one of its *own* payloads. A block announced above it would take that announcement away.
- a chain marked as unable to carry one. See [`no_sync_block_state_context`](../writing_tests/test_markers.md#pytestmarkno_sync_block_state_context) and [`no_sync_block_timestamp_headroom`](../writing_tests/test_markers.md#pytestmarkno_sync_block_timestamp_headroom).
- a chain whose head pins blob fields no child block can derive a fee context from. Only an intentionally invalid head can: every other header's blob fields are derived by the fork itself. Such a head either overflows the sum of excess blob gas and blob gas used, or (from Osaka on, where [EIP-7918](https://eips.ethereum.org/EIPS/eip-7918) makes a child's excess blob gas depend on its parent's blob gas price) names an excess blob gas whose price series would never terminate. No client can derive a child from such a header either - it rejects the head on the same arithmetic - and the bound depends on the fork's own blob math, so the filler decides this itself instead of requiring a marker.

Benchmark tests never carry the block - a framework block above the chain would distort their per-block measurements - so a combined fill needs no extra options.

## Debugging the `t8n` Command

The `--evm-dump-dir` flag can be used to dump the inputs and outputs of every call made to the `t8n` command for debugging purposes, see [Debugging Transition Tools](./debugging_t8n_tools.md).

## Watch Mode for Development

!!! tip "Development workflow"
    Use `--watch` or `--watcherfall` during test development to get immediate feedback on your changes without manually re-running the fill command.

### Standard Watch Mode (`--watch`)

This will:

1. Run the initial fill command.
2. Monitor all Python files in the `tests/` and `src/` directories for changes.
3. Automatically re-run the fill command when changes are detected.
4. Clear the screen and show which files changed.

```console
uv run fill tests/amsterdam/eip7928_block_level_access_lists/test_block_access_lists.py --clean --until Amsterdam --watch
✓ Fill completed

Watching for changes...

```

### Watcherfall Watch Mode (`--watcherfall`)

!!! info "Watcherfall mode"
    A verbose mode; like watch but the logs keep flowing - perfect when you want to see the full history of runs without clearing the terminal.

Same as `--watch` but without clearing the terminal between runs, so you can see the full output history:

```console
uv run fill tests/amsterdam/eip7928_block_level_access_lists/test_block_access_lists.py --clean --until Amsterdam --watcherfall
Starting watcherfall mode (verbose)...
✓ Fill completed

Watching for changes...

File changes detected, re-running...

✓ Fill completed

Watching for changes...

```

Exit either watch mode with Ctrl+C

## Other Useful Pytest Command-Line Options

```console
uv run fill -vv            # More verbose output
uv run fill -x             # Exit instantly on first error or failed test case
uv run fill --pdb -nauto   # Drop into the debugger upon error in a test case
uv run fill -s             # Print stdout from tests to the console during execution
```

## Custom `fill` Command-Line Options

To see all the options available to fill, including pytest and pytest plugin options, use `--pytest-help`.

To list the options that only specific to fill, use:

```console
uv run fill --help
```

For a complete, up-to-date list of all command-line options, see the [Fill Command-Line Options](filling_tests_command_line_options.md) page, which is automatically generated from the current `uv run fill --help` output.
