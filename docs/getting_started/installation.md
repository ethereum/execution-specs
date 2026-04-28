# Installation

## Quick Start

=== "All platforms"

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

=== "macOS"

    ```console
    git clone https://github.com/ethereum/execution-specs
    cd execution-specs
    curl -LsSf https://astral.sh/uv/install.sh | sh
    uv python install 3.12
    uv python pin 3.12
    uv sync
    brew install just
    just shell-completions
    ```

Further explanation, troubleshooting, and alternative installation paths are below.

## Prerequisites

The tools provided by [execution-specs](https://github.com/ethereum/execution-specs) use `uv` ([docs.astral.sh/uv](https://docs.astral.sh/uv/)) to manage dependencies and the virtual environment.

It's recommended to use the latest version of `uv`, which can be installed via `curl` (recommended; can self-update via `uv self update`) or pip (requires Python, can't self-update):

=== "curl"

    ```console
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

=== "pip"

    ```console
    pip install uv
    ```

When installed via `curl`, `uv` can also download Python for your platform if a required version (Python 3.11–3.14) is not already installed.

## Installing Python and Python Dependencies

Clone @ethereum/execution-specs and install the project dependencies. Python 3.11–3.14 are supported; Python 3.12 tends to be the smoothest for local setup because pre-built wheels are available across the dependency set.

The following commands use `uv` to install Python 3.12 and pin it for all commands run within the execution-specs directory:

=== "All platforms"

    ```console
    git clone https://github.com/ethereum/execution-specs
    cd execution-specs
    uv python install 3.12
    uv python pin 3.12
    uv sync
    ```

### Testing Your Python Environment

The following command can be used to verify that the environment is set up correctly. By targeting a single test subdirectory, it generates only a small subset of test vectors:

```console
uv run fill tests/istanbul/eip1344_chainid/
```

## Installing the `just` Task Runner

The @ethereum/execution-specs repository uses [`just`](https://just.systems/man/en/introduction.html) to run common tasks locally and in CI. Tasks range from static code checks to generating test vectors from the spec.

@ethereum/execution-specs requires `just` 1.43+. Note that the version currently distributed in Ubuntu 24.04 is too old; many other methods are available in the [installation docs](https://just.systems/man/en/packages.html).

`just` can be installed directly with `uv` from the [`rust-just` package](https://pypi.org/project/rust-just/).

=== "All platforms"

    ```console
    uv tool install --exclude-newer "10 days" rust-just    
    ```

    Using `--exclude-newer` adds a cool-down window that can help reduce exposure to supply-chain attacks.

=== "macOS"

    ```console
    brew install just
    ```

### Testing Your `just` Installation

To explore which tasks (recipes) are available, simply run `just` within the `execution-specs` directory:

```console
just
```

Then try running the available static code checks:

```console
just static
```

### Configuring Shell Completion

`just` supports tab completion for recipes. Run the following command for help on how to enable this feature for your shell:

```console
just shell-completions
```

More background is available in the [`just` documentation](https://just.systems/man/en/shell-completion-scripts.html).

## Installation Troubleshooting

If you run into problems, see [Installation Troubleshooting](./installation_troubleshooting.md).
