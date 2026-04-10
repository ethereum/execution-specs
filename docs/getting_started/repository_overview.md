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

Contains the `execution_testing` package which provides tools to define test cases and to interface with `t8n` command interfaces that are required to generate tests. Additionally, it contains packages that enable test case execution by customizing pytest which acts as the test framework.

#### `docs/`

Contains documentation configuration and source files.
