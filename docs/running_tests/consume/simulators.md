# Consume Simulators

The `engine` and `rlp` simulators test clients by importing blocks through different interfaces. These simulators run within the Hive testing framework to provide containerized, isolated testing environments.

For your first run, start with [Hive setup](../hive/index.md), then choose how to run the simulators:

- **Run tests or reproduce a dashboard failure:** use [published images](#run-with-published-images) with `./hive --sim`. Hive runs both the simulator and clients in containers.
- **Run locally generated fixtures or debug interactively:** use [development mode](#debug-in-development-mode) with `./hive --dev`. Hive manages the clients while you run `uv run consume` from your local checkout.

## Run with published images

Start with [Run a Simulator from Images](../hive/images/tutorial.md) to run consume tests through Hive. Use the [tag guide](../hive/images/index.md#choose-a-tag) to select a mainnet release, a devnet or a nightly fill, and the [image reference](../hive/images/reference.md#simulators-and-their-test-content) to choose a simulator and fixture format.

For example, run the latest published mainnet release with:

```bash
./hive --sim consume-engine --client go-ethereum
```

Hive accepts the short simulator name. The image contains the fixtures and framework, so you do not need to install `consume` separately.

To reproduce a dashboard failure, match its simulator image, client version and configuration, and test selection. Follow [Reproduce a run exactly](../hive/images/how_to.md#reproduce-a-run-exactly) to pin the simulator image digest, and [Select a single test](../hive/common_options.md#exact-test-id-match) to filter the failing test. The default `latest` image may have changed since the dashboard run.

Once you can reproduce the failure, switch to development mode if you need to inspect Python state or edit the simulator. You can also [build images locally](../hive/images/how_to.md#build-the-images-from-a-local-checkout) to test changes in containers.

## Debug in development mode

Development mode lets you run against locally generated fixtures directly, without building or publishing an image. It also runs the simulator from your checkout, so edits take effect on the next run and you can use a Python debugger. Install the [testing tools](../../getting_started/installation.md) first, then follow [Hive development mode](../hive/dev_mode.md) for platform-specific setup.

On Linux, start Hive from its checkout and leave it running:

```bash
./hive --dev --client go-ethereum
```

In another terminal, from your execution-specs checkout, connect to Hive and run the simulator against fixtures you generated in `./fixtures`:

```bash
export HIVE_SIMULATOR=http://127.0.0.1:3000
uv run consume engine --input ./fixtures \
    --sim.limit ".*test_name.*" --pdb
```

Use the familiar Hive `--sim.limit` flag to select tests by regular expression. Replace `test_name` with the name of the test you are debugging; the surrounding `.*` matches the rest of its test ID. Regular pytest flags are also available: `-k test_name` is an alternative filter, and `--pdb` opens the debugger on failure. See [Useful Pytest Options](../useful_pytest_options.md) for more options.

Set `--input` to your local fixture directory, or use `--input tests@v20.0.2` to debug against a published release. See [Fixture Inputs](./cache.md#the-input-flag-to-specify-fixtures) for supported inputs. Simulator code comes from your checkout; the published image's `tag` no longer selects it.

### Command Syntax

```bash
uv run consume <engine|rlp> [OPTIONS]
```

### Further development references

- To install the `consume` command, see [Installation](../../getting_started/installation.md).
- Help [setting up](../hive/index.md) and [starting Hive in dev mode](../hive/dev_mode.md).
- For an explanation of how the `consume` simulators work, see the [Engine](../running.md#engine) and [RLP](../running.md#rlp) sections in [Running Tests](../running.md).
- Help for relevant options can be found in [Consume Cache and Fixture Inputs](./cache.md) and [Useful Pytest Options](../useful_pytest_options.md).

## Related: Block Building

A separate hive simulator [`build-block`](../running.md#block-building) is also fixture-driven but tests the client's **producer-side** path via the `testing_buildBlockV1` engine-API testing-namespace endpoint, rather than the consumer-side import path that the simulators above exercise.
