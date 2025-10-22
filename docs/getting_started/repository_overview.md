<!-- markdownlint-disable MD001 (MD001=heading-increment due to #### usage below) -->
# Repository Overview

The most relevant folders and files in the repo are:

```text
📁 execution-test-specs/
├─╴📁 tests/                     # test cases
│   ├── 📁 eips/
│   ├── 📁 vm/
│   └── 📁 ...
├─╴📁 fixtures/                  # default fixture output dir
│   ├── 📁 blockchain_tests/
│   ├── 📁 blockchain_tests_engine/
│   ├── 📁 state_tests/
│   └── 📁 ...
├─╴📁 src/                       # library & framework packages
│   ├── 📁 ethereum_test_fork/
│   ├── 📁 ethereum_test_tools/
│   └── 📁 ...
├─╴📁 docs/                      # markdown documentation
│   ├── 📁 getting_started
│   ├── 📁 dev
│   └── 📁 ...
├─╴📁 .vscode/                   # visual studio code config
│   ├── 📄 settings.recommended.json # copy to settings.json
│   ├── 📄 launch.recommended.json
│   └── 📄 extensions.json
└── 📄 whitelist.txt             # spellcheck dictionary
```

#### `tests/`

Contains the implementation of the Ethereum consensus tests available in this repository.

#### `src/`

Contains various packages that help to define test cases and to interface with the `evm t8n` command. Additionally, it contains some packages that enable test case execution by customizing pytest which acts as the test framework.

#### `docs/`

Contains documentation configuration and source files.

#### `.vscode/`

See [VS Code Setup](./setup_vs_code.md).
