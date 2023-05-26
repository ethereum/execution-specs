# VS Code Setup

VS Code setup is optional, but does offer the following advantages:

- Auto-format your Python code to conform to the repositories code standards ([black](https://black.readthedocs.io/en/stable/)).
- Spell-check your code and docs.
- Graphical exploration of test cases and easy execution/debug.

## Installation

Please refer to the [Visual Studio Code docs](https://code.visualstudio.com/docs/setup/setup-overview) for help with installation.


## VS Code Settings file

The [ethereum/execution-spec-tests](https://github.com/ethereum/execution-spec-tests) repo includes configuration files for VS Code in the `.vscode/` sub-directory:

```console
📁 execution-test-specs/
└──📁 .vscode/                   
    ├── 📄 settings.recommended.json
    ├── 📄 extensions.json 
    └── 📄 launch.json
```

To enable the recommended settings, copy the settings file to the expected location:
```console
cp .vscode/settings.recommended.json .vscode/settings.json
```

!!! note "Workspace Trust"
    Trust the `execution-specs-test` repository when opening in VS Code to be prompted to install the plugins recommended via the `extensions.json` file.
