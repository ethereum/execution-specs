# Testing Tools

This repository provides tools and libraries for generating cross-client
Ethereum tests.

## Quick Start

Relies on Python `3.10.0` and `geth` `v1.10.13` or later. 

```console
$ git clone https://github.com/lightclient/testing-tools
$ cd testing-tools
$ pip install -e .
$ tf --output="fixtures"
```

## Overview 

### `ethereum_test`

The `ethereum_test` package provides primitives and helpers to allow developers
to easily test the consensus logic of Ethereum clients. 

### `ethereum_test_filler`

The `ethereum_test_filler` pacakge is a CLI application that recursively searches
a given directory for Python modules that export test filler functions generated
using `ethereum_test`. It then processes the fillers using the transition tool
and the block builder tool, and writes the resulting fixture to file.

### `evm_block_builder`

This is a wrapper around the [block builder][b11r] (b11r) tool.

### `evm_transition_tool`

This is a wrapper around the [transaction][t8n] (t8n) tool.

[t8n]: https://github.com/ethereum/go-ethereum/tree/master/cmd/evm
[b11r]: https://github.com/ethereum/go-ethereum/pull/23843
