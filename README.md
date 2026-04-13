# Ethereum Execution Client Specifications

[![GitPOAP Badge](https://public-api.gitpoap.io/v1/repo/ethereum/execution-specs/badge)](https://www.gitpoap.io/gh/ethereum/execution-specs)
[![codecov](https://codecov.io/gh/ethereum/execution-specs/graph/badge.svg?token=0LQZO56RTM)](https://codecov.io/gh/ethereum/execution-specs)
[![Python Specification](https://github.com/ethereum/execution-specs/actions/workflows/test.yaml/badge.svg)](https://github.com/ethereum/execution-specs/actions/workflows/test.yaml)

## Description

This repository contains the specifications related to the Ethereum execution client, specifically the [pyspec](/src/ethereum/__init__.py) and specifications for [network upgrades](/src/ethereum/__init__.py). The [JSON-RPC API specification](https://github.com/ethereum/execution-apis) can be found in a separate repository.

### Ethereum Protocol Releases

For the full list of mainnet hardforks, their activation points, included
EIPs, and fork manifests, see [Protocol History](docs/specs/protocol_history.md).

## Execution Specification (work-in-progress)

The execution specification is a python implementation of Ethereum that prioritizes readability and simplicity. It will be accompanied by both narrative and API level documentation of the various components written in markdown and rendered using docc...

* [Rendered specification](https://ethereum.github.io/execution-specs/)

## Usage

The Ethereum specification is maintained as a Python library, for better integration with tooling and testing.

Requires:

* Python 3.11+,
* [`uv`](https://docs.astral.sh/uv/) package manager,
* [`just`](https://just.systems/) command runner (install via your package manager, [`uv tool install just-bin`](https://pypi.org/project/just-bin/), or [pre-built binaries](https://just.systems/man/en/pre-built-binaries.html)).

### Building Specification Documentation

Building the spec documentation:

```bash
just docs-spec
```

The path to the generated HTML will be printed to the console.

### Browsing Updated Documentation

To view the updated local documentation, run:

```bash
uv run mkdocs serve
```

then connect to `localhost:8000` in a browser

## License

The Ethereum Execution Layer Specification code is licensed under the [Creative Commons Zero v1.0 Universal](LICENSE.md).
