# Consensus Tests

The consensus tests in `./tests/` verify that Ethereum execution clients implement the protocol correctly and agree on the resulting state transitions. This section covers the full workflow:

- [Writing Tests](../writing_tests/index.md): Authoring new Python test cases using the execution-testing framework.
- [Filling Tests](../filling_tests/index.md): Generating JSON test fixtures (vectors) from the Python test cases using the `fill` command.
- [Running Tests](../running_tests/index.md): Executing the generated fixtures against clients, either directly or via Hive.
