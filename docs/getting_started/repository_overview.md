# Repository Overview 

The most relevant folders in the repo are:
```
📁 execution-test-specs/
├─╴📁 fillers/                   # test cases
│   ├── 📁 eips/
│   ├── 📁 vm/
│   └── 📁 ...
├─╴📁 out/                       # default fixture output dir
│   ├── 📁 eips/
│   ├── 📁 vm/
│   └── 📁 ...
├─╴📁 src/                       # library & framework packages
│   ├── 📁 ethereum_test_fork/
│   ├── 📁 ethereum_test_tools/
│   └── 📁 ...
└── 📁 docs/                     # markdown documentation
    ├── 📁 getting_started
    ├── 📁 dev
    └── 📁 ...
```


#### `fillers/`

Contains the implementation of the Ethereum consensus tests available in this repository.

#### `src/`

Contains various packages that help to define test cases and to interface with the `evm t8n` and `evm b11r` commands. Additionally, it contains some packages that enable test case (filler) execution by customizing pytest which acts as the test framework.

#### `docs/`

Contains documentation configuration and source files.