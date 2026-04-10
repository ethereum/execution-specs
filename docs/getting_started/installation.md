# Installation

## Prerequisites

The tools provided by [execution-specs](https://github.com/ethereum/execution-specs) use `uv` ([docs.astral.sh/uv](https://docs.astral.sh/uv/)) to manage their dependencies and virtual environment.

It's recommended to use the latest version of `uv` which can be installed via `curl` (recommended; can self-update via `uv self update`) or pip (requires Python, can't self-update):

=== "curl"

    ```console
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

=== "pip"

    ```console
    pip install uv
    ```

If installed via `curl`, `uv` will download Python for your target platform if one of the required versions (Python 3.11-3.14) is not available natively.

## Installing Python and Python Dependencies

Clone @ethereum/execution-specs and install its dependencies (via `uv sync`). We recommend using Python 3.12, the following uses `uv` to download and pins 3.12 for use with for all commands executed within the execution-specs folder:

=== "All platforms"

    ```console
    git clone https://github.com/ethereum/execution-specs
    cd execution-specs
    uv python install 3.12
    uv python pin 3.12
    uv sync
    ```

### Testing Your Python Environment

The following command that generates a small subset of the test vectors can be used to verify the installation:

```console
uv run fill tests/istanbul/eip1344_chainid/
```

## Installing the `just` Task Runner

The @ethereum/execution-specs repository uses [`just`](https://just.systems/man/en/introduction.html) to run common tasks locally and in CI. Tasks range from static code checks to generating test vectors from the spec.

@ethereum/execution-specs requires `just` 1.43+. Note that the version currently distributed in Ubuntu 24.04 is too old; many other methods are available in the [installation docs](https://just.systems/man/en/packages.html).

`just` can be installed directly with `uv` from the [`rust-just` package](https://pypi.org/project/rust-just/).

=== "All platforms"

    ```console
    uv tool install rust-just==1.48.1
    ```

=== "macOS"

    ```console
    brew install just
    ```

### Configuring Shell Completion

Run the following command to print the commands required to enable tab completion of recipes for your shell:

```console
just shell-completions
```

More background is available in the [`just` documentation](https://just.systems/man/en/shell-completion-scripts.html).

### Testing Your `just` Installation

To explore which tasks (aka recipes) are available simply run `just` within the `execution-specs` folder:

```console
just
```

and then try to run the available static code checks:

```console
just static
```

## Installation Troubleshooting

If you encounter issues during installation, see the [Installation Troubleshooting](./installation_troubleshooting.md) guide.
