# VS Code Setup

VS Code setup is optional, but does offer the following advantages:

- Auto-format your Python code to conform to the repository's [code standards](../writing_tests/code_standards.md) ([black](https://black.readthedocs.io/en/stable/)).
- Inline linting and auto-completion (thanks to Python type hints).
- Spell-check your code and docs.
- Graphical exploration of test cases and easy test execution/debug.

## Installation

Please refer to the [Visual Studio Code docs](https://code.visualstudio.com/docs/setup/setup-overview) for help with installation.

## VS Code Settings file

The [ethereum/execution-spec-tests](https://github.com/ethereum/execution-spec-tests) repo includes configuration files for VS Code in the `.vscode/` sub-directory:

```
📁 execution-test-specs/
└──📁 .vscode/
    ├── 📄 settings.recommended.json
    ├── 📄 extensions.json
    └── 📄 launch.recommended.json
```

To enable the recommended settings, copy the settings file to the expected location:

```console
cp .vscode/settings.recommended.json .vscode/settings.json
```

To additionally enable the recommended launch configurations:

```console
cp .vscode/launch.recommended.json .vscode/launch.json
```

## Additional VS Code Extensions

Open the folder in VS Code where execution-spec-tests is cloned: VS Code should prompt to install the repository's required extensions from `.vscode/extensions.json`:

- [`ms-python.python`](https://marketplace.visualstudio.com/items?itemName=ms-python.python)
- [`ms-python.isort`](https://marketplace.visualstudio.com/items?itemName=ms-python.isort)
- [`ms-python.flake8`](https://marketplace.visualstudio.com/items?itemName=ms-python.flake8)
- [`ms-python.black-formatter`](https://marketplace.visualstudio.com/items?itemName=ms-python.black-formatter)
- [`esbenp.prettier-vscode`](https://marketplace.visualstudio.com/items?itemName=esbenp.prettier-vscode)
- [`streetsidesoftware.code-spell-checker`](https://marketplace.visualstudio.com/items?itemName=streetsidesoftware.code-spell-checker)
- [`tamasfe.even-better-toml`](https://marketplace.visualstudio.com/items?itemName=tamasfe.even-better-toml)

!!! note "Workspace Trust"
Trust the `execution-specs-test` repository when opening in VS Code to be prompted to install the plugins recommended via the `extensions.json` file.

## Configuration for Testing EVM Features Under Active Development

An additional step is required to enable fixture generations for features from forks that are under active development and have not been deployed to mainnet, see [Executing Tests for Features under Development](./executing_tests_dev_fork.md#vs-code-setup).
