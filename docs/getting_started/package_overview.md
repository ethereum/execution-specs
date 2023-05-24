# Package Overview 

#### `ethereum_test_tools`

The `ethereum_test_tools` package provides primitives and helpers to allow
developers to easily test the consensus logic of Ethereum clients. 

#### `ethereum_test_filling_tool`

The `ethereum_test_filling_tool` package is a CLI application that recursively
searches a given directory for Python modules that export test filler functions
generated using `ethereum_test_tools`.
It then processes the fillers using the transition tool and the block builder
tool, and writes the resulting fixture to file.

#### `evm_block_builder`

This is a wrapper around the block builder (b11r) tool.

#### `evm_transition_tool`

This is a wrapper around the transaction (t8n) tool.

#### `fillers`

Contains all the Ethereum consensus tests available in this repository.