# VS Code Setup

VS Code setup is optional, but does offer the following advantages:

- Auto-format your Python code to conform to the repository's [code standards](../writing_tests/code_standards.md) ([ruff](https://docs.astral.sh/ruff/)).
- Inline linting and auto-completion (thanks to Python type hints).
- Spell-check your code and docs.
- Graphical exploration of test cases and easy test execution/debug.

## Installation

Please refer to the [Visual Studio Code docs](https://code.visualstudio.com/docs/setup/setup-overview) for help with installation.

## VS Code Settings file

The [ethereum/execution-spec-tests](https://github.com/ethereum/execution-spec-tests) repo includes configuration files for VS Code in the `.vscode/` sub-directory:

```text
📁 execution-test-specs/
└──📁 .vscode/
    ├── 📄 settings.json
    ├── 📄 extensions.json
    └── 📄 launch.recommended.json
```

By default, the repository settings are applied via `.vscode/settings.json`.

To enable the recommended launch configurations (that include some useful debugging configurations), copy the recommended launch configuration file to `.vscode/launch.json`:

```console
cp .vscode/launch.recommended.json .vscode/launch.json
```

## VS Code Extension Configuration

The extensions listed in `.vscode/extensions.json` are required for a smooth developer experience.

1. Open the root folder of your local `execution-spec-tests` clone in VS Code, it will prompt you to install the repository's required extensions (from `.vscode/extensions.json` - you will be required to trust the `executions-spec-tests` repository first). These extensions are used to format, lint, type check and run tests on the codebase. After all the required extensions are installed a VS Code reload will be required.

2. If previously installed, ensure that the following `ms-python` extensions are disabled for the `execution-spec-tests` workspace to ensure there are no conflicts with the `ruff` formatter. In the VS Code Extensions tab, search for the each of the extensions below, and if installed and enabled, open the "Disabled" menu and select "Disable (Workspace)". This ensures that the extensions will be available with other workspaces that may need them.

    - [`ms-python.isort`](https://marketplace.visualstudio.com/items?itemName=ms-python.isort)
    - [`ms-python.flake8`](https://marketplace.visualstudio.com/items?itemName=ms-python.flake8)
    - [`ms-python.black-formatter`](https://marketplace.visualstudio.com/items?itemName=ms-python.black-formatter)

    <figure markdown>
        ![Disabling extensions for the current workspace](./img/vscode_extension_disable_for_workspace.png){width=auto align=center}
    </figure>

## Configuration for Testing EVM Features Under Active Development

An additional step is required to enable fixture generations for features from forks that are under active development and have not been deployed to mainnet, see [Filling Tests for Features under Development](../filling_tests/filling_tests_dev_fork.md#vs-code-setup).
