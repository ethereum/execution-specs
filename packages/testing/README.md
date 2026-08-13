# The `ethereum-execution-testing` Package

Test generation and execution framework for the [Ethereum Execution Layer Specifications (EELS)](https://github.com/ethereum/execution-specs).

The package provides:

- The `execution_testing` library: base types, fork definitions, and test-spec primitives used to write consensus test cases.
- The pytest-based commands that generate and run test fixtures against execution clients: `fill`, `execute`, `consume`, and friends.
- `ethereum-spec-evm` — the reference EVM CLI that executes the spec directly: a `t8n` transition tool (also available as a daemon), a `b11r` block builder, and a state-test runner.

## Installing `ethereum-spec-evm` standalone

This package depends on `ethereum-execution` (the spec itself), and the two are developed in lockstep: the spec releases published on PyPI only carry forks that are live on mainnet and generally cannot satisfy this package's dependency pins. Install both packages from the same clone.

With `uv` (resolves the sibling spec package from the checkout automatically):

```console
git clone https://github.com/ethereum/execution-specs
uv tool install ./execution-specs/packages/testing
```

With `pip`, in a virtual environment:

```console
pip install ./execution-specs ./execution-specs/packages/testing
```

With `pipx`:

```console
pipx install ./execution-specs
pipx inject --include-apps ethereum-execution ./execution-specs/packages/testing
```

## Documentation

Repository documentation, including this framework's reference documentation: <https://steel.ethereum.foundation/docs/execution-specs/>
