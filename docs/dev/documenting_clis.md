# Documenting CLIs

EEST command line interfaces (CLIs) are documented using the [`click`](https://click.palletsprojects.com) library's built-in help system and the [`mkdocs-click`](https://github.com/mkdocs/mkdocs-click) extension for mkdocs. This allows generation of CLI documentation directly from the (click) source code, ensuring that the documentation is always up-to-date with the code.

Current limitations:

1. `mkdocs serve` does not automatically update the CLI documentation when the source code changes. You must restart the server to see the changes.
2. `mkdocs-click` does not automatically generate a short help string from sub-command docstrings. You must provide a short help string for each sub-command in the source code with `@click.command(short_help="...")`.

See the [markdown](https://github.com/ethereum/execution-specs/blob/a48e0b381d5225a6c3de2d06cd9ee7ae0b6ca9bb/docs/library/cli/evm_bytes.md) and corresponding [Python docstrings](https://github.com/danceratopz/execution-specs/blob/ca2b3b18a5d4058b2e2fd517ba7db31e86919a09/packages/testing/src/execution_testing/cli/evm_bytes.py) for the [`evm_bytes` CLI documentation](../library/cli/evm_bytes.md) as an example of how to document a CLI using `mkdocs-click`.
