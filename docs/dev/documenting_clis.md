# Documenting CLIs

EEST command line interfaces (CLIs) are documented using the [`click`](https://click.palletsprojects.com) library's built-in help system and the [`mkdocs-click`](https://github.com/mkdocs/mkdocs-click) extension for mkdocs. This allows generation of CLI documentation directly from the (click) source code, ensuring that the documentation is always up-to-date with the code.

Current limitations:

1. `mkdocs serve` does not automatically update the CLI documentation when the source code changes. You must restart the server to see the changes.
2. `mkdocs-click` does not automatically generate a short help string from sub-command docstrings. You must provide a short help string for each sub-command in the source code with `@click.command(short_help="...")`.

See the [markdown](https://github.com/ethereum/execution-spec-tests/blob/main/docs/library/cli/evm_bytes.md) and corresponding [Python docstrings](https://github.com/ethereum/execution-spec-tests/blob/main/src/cli/evm_bytes.py) for the [`evm_bytes` CLI documentation](../library/cli/evm_bytes.md) as an example of how to document a CLI using `mkdocs-click`.
