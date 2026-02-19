<!-- markdownlint-disable MD001 (MD001=heading-increment due to #### usage below) -->
# Repository Overview

The most relevant folders and files in the repo are:

```text
📁 execution-specs/
├─╴📁 tests/                     # test cases organized by fork
│   ├── 📁 amsterdam/
│   ├── 📁 osaka/
│   ├── 📁 prague/
│   └── 📁 ...
├─╴📁 fixtures/                  # default fixture output dir
│   ├── 📁 blockchain_tests/
│   ├── 📁 blockchain_tests_engine/
│   ├── 📁 state_tests/
│   └── 📁 ...
├─╴📁 packages/                  # library & framework packages
│   └── 📁 testing/
│       └── 📁 src/
│           └── 📁 execution_testing/
├─╴📁 src/                       # execution spec packages
│   ├── 📁 ethereum/
│   └── 📁 ...
├─╴📁 docs/                      # markdown documentation
│   ├── 📁 getting_started/
│   ├── 📁 dev/
│   └── 📁 ...
└── 📄 whitelist.txt             # spellcheck dictionary
```

#### `tests/`

Contains the implementation of the Ethereum consensus tests available in this repository, organized by fork.

#### `packages/`

Contains the `execution_testing` package which provides tools to define test cases and to interface with the `evm t8n` command. Additionally, it contains packages that enable test case execution by customizing pytest which acts as the test framework.

#### `src/`

Contains the Ethereum execution spec packages.

#### `docs/`

Contains documentation configuration and source files.
