# Library (Tools) Reference Documentation

Execution spec tests consists of several packages that implement helper classes and tools that enable and simplify test case implementation. This section contains their reference documentation:

- [`execution_testing.base_types`](./execution_testing_base_types.md) - provides the basic types on top of which other testing libraries are built.
- [`execution_testing.exceptions`](./execution_testing_exceptions.md) - provides definitions for exceptions used in all tests.
- [`execution_testing.fixtures`](./execution_testing_fixtures.md) - provides definitions of all test fixture types that are produced in this repository and can be consumed by clients.
- [`execution_testing.forks`](./execution_testing_forks.md) - provides definitions for supported forks used in tests.
- [`execution_testing.specs`](./execution_testing_specs.md) - provides definitions for all spec types used to define test cases, and generate different kinds of test fixtures.
- [`execution_testing.tools`](./execution_testing_tools.md) - provides primitives and helpers to test Ethereum execution clients.
- [`execution_testing.test_types`](./execution_testing_test_types.md) - provides Ethereum types built on top of the base types which are used to define test cases and interact with other libraries.
- [`execution_testing.vm`](./execution_testing_vm.md) - provides definitions for the Ethereum Virtual Machine (EVM) as used to define bytecode in test cases.
- [`execution_testing.client_clis`](./execution_testing_client_clis.md) - a wrapper for the transition (`t8n`) tool.
- [`pytest_plugins`](./pytest_plugins/index.md) - contains pytest customizations that provide additional functionality for generating test fixtures.
