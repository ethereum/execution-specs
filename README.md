# Ethereum Execution Layer Specifications

[![GitPOAP Badge](https://public-api.gitpoap.io/v1/repo/ethereum/execution-specs/badge)](https://www.gitpoap.io/gh/ethereum/execution-specs)
[![codecov](https://codecov.io/gh/ethereum/execution-specs/graph/badge.svg?token=0LQZO56RTM)](https://codecov.io/gh/ethereum/execution-specs)
[![Python Specification](https://github.com/ethereum/execution-specs/actions/workflows/test.yaml/badge.svg)](https://github.com/ethereum/execution-specs/actions/workflows/test.yaml)

The Ethereum Execution Layer Specifications (EELS) are an executable Python reference implementation of Ethereum's execution layer, along with the test cases that verify it. Clients read EELS to know what Ethereum should do on any given block; EIP authors prototype protocol changes here before the prose EIP is final; test vectors produced from this repository are run against every production client.

The [JSON-RPC API specification](https://github.com/ethereum/execution-apis) lives in a separate repository.

- **Rendered documentation**: <https://steel.ethereum.foundation/docs/>
- **Rendered specification (pyspec)**: <https://ethereum.github.io/execution-specs/>
- **Protocol history**: [docs/specs/protocol_history.md](docs/specs/protocol_history.md)

## Quick Start

Requires a Unix-like shell. All platforms:

```console
git clone https://github.com/ethereum/execution-specs
cd execution-specs
curl -LsSf https://astral.sh/uv/install.sh | sh
uv python install 3.12
uv python pin 3.12
uv sync
uv tool install --exclude-newer "10 days" rust-just
just shell-completions
```

Python 3.11–3.14 are supported; 3.12 is recommended for local development. For alternative `just` installation paths, macOS-specific installation notes, and troubleshooting, see [Installation](docs/getting_started/installation.md).

To build and browse the HTML documentation locally:

```console
just docs-serve-fast
```

Then open <http://localhost:8000>.

To build the `docc`-rendered Python specification, run:

```console
just docs-spec
```

the path to the generated HTML will be printed.

## License

The Ethereum Execution Layer Specification is licensed under the [Creative Commons Zero v1.0 Universal](LICENSE.md).
