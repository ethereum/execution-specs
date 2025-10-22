# Library (Tools) Reference Documentation

Execution spec tests consists of several packages that implement helper classes and tools that enable and simplify test case implementation. This section contains their reference documentation:

- [`ethereum_test_base_types`](./ethereum_test_base_types.md) - provides the basic types on top of which other testing libraries are built.
- [`ethereum_test_exceptions`](./ethereum_test_exceptions.md) - provides definitions for exceptions used in all tests.
- [`ethereum_test_fixtures`](./ethereum_test_fixtures.md) - provides definitions of all test fixture types that are produced in this repository and can be consumed by clients.
- [`ethereum_test_forks`](./ethereum_test_forks.md) - provides definitions for supported forks used in tests.
- [`ethereum_test_specs`](./ethereum_test_specs.md) - provides definitions for all spec types used to define test cases, and generate different kinds of test fixtures.
- [`ethereum_test_tools`](./ethereum_test_tools.md) - provides primitives and helpers to test Ethereum execution clients.
- [`ethereum_test_types`](./ethereum_test_types.md) - provides Ethereum types built on top of the base types which are used to define test cases and interact with other libraries.
- [`ethereum_test_vm`](./ethereum_test_vm.md) - provides definitions for the Ethereum Virtual Machine (EVM) as used to define bytecode in test cases.
- [`ethereum_clis`](./ethereum_clis.md) - a wrapper for the transition (`t8n`) tool.
- [`pytest_plugins`](./pytest_plugins/index.md) - contains pytest customizations that provide additional functionality for generating test fixtures.
