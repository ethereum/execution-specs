# Consume Simulators

The `engine` and `rlp` simulators test clients by importing blocks through different interfaces. These simulators run within the Hive testing framework to provide containerized, isolated testing environments.

## Command Syntax

```bash
uv run consume <engine|rlp> [OPTIONS]
```

## Relevant Information

- To install the `consume` command, see [Installation](../../getting_started/installation.md).
- Help [setting up](../hive/index.md) and [starting Hive in dev mode](../hive/dev_mode.md).
- For an explanation of how the `consume` simulators work, see the [Engine](../running.md#engine) and [RLP](../running.md#rlp) sections in [Running Tests](../running.md).
- Help for relevant options can be found in [Consume Cache and Fixture Inputs](./cache.md) and [Useful Pytest Options](../useful_pytest_options.md).
