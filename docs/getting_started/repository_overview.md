<!-- markdownlint-disable MD001 (MD001=heading-increment due to #### usage below) -->
# Repository Overview

The most relevant folders and files in the repo are:

```text
📁 execution-specs/
├─╴📁 src/                       # EELS - the execution layer specs
│   ├── 📁 ethereum/
│   │    └── 📁 forks/
│   │         ├── 📁 amsterdam/
|   |         ├── 📁 berlin/
│   │         └── 📁 ...
│   └── 📁 ethereum/forks/...
├─╴📁 tests/                     # Test cases for EELS organized by fork
│   ├── 📁 amsterdam/
│   ├── 📁 berlin/
│   └── 📁 ...
├─╴📁 packages/                  # Test generation library & framework packages
│   └── 📁 testing/
│       └── 📁 src/
│           └── 📁 execution_testing/
├─╴📁 docs/                      # Markdown documentation
│   ├── 📁 getting_started/
│   ├── 📁 writing_tests/
│   └── 📁 ...
├── 📄 Justfile                  # Task runner config, run `just` to see tasks
├── 📄 uv.lock                   # Defines pinned project Python dependencies
└── 📄 whitelist.txt             # Spellcheck dictionary
```

#### `src/`

Contains the Ethereum Execution Layer Specs, each fork is a sub-package.

#### `tests/`

Contains the implementation of the Ethereum consensus tests available in this repository, organized by the fork in which the functionality was introduced.

#### `packages/execution_testing/`

Contains the `execution_testing` package which provides tools to define test cases and to interface with `t8n` command interfaces that are required to generate tests. Additionally, it contains packages that enable test case execution by customizing pytest which acts as the test framework. It also ships the reference EVM `t8n` implementation, which `fill` runs in-process to generate the fixtures in this repository, and which external consumers can drive through the `ethereum-spec-evm` CLI.

Its main packages:

- [`base_types`](https://github.com/ethereum/execution-specs/tree/HEAD/packages/testing/src/execution_testing/base_types): the basic types on top of which the other packages are built.
- [`exceptions`](https://github.com/ethereum/execution-specs/tree/HEAD/packages/testing/src/execution_testing/exceptions): the exceptions used in all tests.
- [`fixtures`](https://github.com/ethereum/execution-specs/tree/HEAD/packages/testing/src/execution_testing/fixtures): the test fixture types produced in this repository and consumed by clients.
- [`forks`](https://github.com/ethereum/execution-specs/tree/HEAD/packages/testing/src/execution_testing/forks): the supported forks used in tests.
- [`specs`](https://github.com/ethereum/execution-specs/tree/HEAD/packages/testing/src/execution_testing/specs): the spec types used to define test cases and generate fixtures.
- [`tools`](https://github.com/ethereum/execution-specs/tree/HEAD/packages/testing/src/execution_testing/tools): primitives and helpers to test Ethereum execution clients.
- [`test_types`](https://github.com/ethereum/execution-specs/tree/HEAD/packages/testing/src/execution_testing/test_types): Ethereum types built on the base types, used to define test cases.
- [`vm`](https://github.com/ethereum/execution-specs/tree/HEAD/packages/testing/src/execution_testing/vm): the EVM definitions used to write bytecode in test cases.
- [`client_clis`](https://github.com/ethereum/execution-specs/tree/HEAD/packages/testing/src/execution_testing/client_clis): wrappers for the transition (`t8n`) tool.
- [`evm_tools`](https://github.com/ethereum/execution-specs/tree/HEAD/packages/testing/src/execution_testing/evm_tools): the `ethereum-spec-evm` CLI: `t8n`, `b11r` and state-test tools that run the execution specs directly.
- [`cli/pytest_commands/plugins`](https://github.com/ethereum/execution-specs/tree/HEAD/packages/testing/src/execution_testing/cli/pytest_commands/plugins): the pytest customizations that generate test fixtures.

It also ships these CLIs:

- `check_eip_versions`: checks that the EIP versions tests reference match the latest ethereum/EIPs, see [Referencing an EIP Spec Version](../writing_tests/reference_specification.md).
- `eest`: helps with routine tasks in this repository.
- `evm_bytes`: converts EVM bytes from a binary file or hex string to the Python opcode minilang.
- `extract_config`: extracts client configuration files via Hive, see [Extracting Client Configs](../running_tests/hive/extract_config.md).

#### `docs/`

Contains documentation configuration and source files.
