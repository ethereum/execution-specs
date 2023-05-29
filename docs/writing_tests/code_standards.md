# Code Standards

The Python code in the tests subdirectory `./fillers` must fulfill the following checks:

1. `fname8 fillers` - spell check passes using the `./whitelist.txt` dictionary file.
2. `isort fillers --check --diff` - Python imports ordered and arranged according to `isort`'s standards.
3. `black fillers --check --diff` - Python source must be [black-formatted](https://black.readthedocs.io/en/stable/).
4. `flake8 fillers` - Python lint checked.
5. `mypy fillers` - Objects that provide typehints pass type-checking via `mypy`.
6. `pytest` - All tests fillers must execute correctly.
7. `mkdocs build --strict` - Documentation generated without warnings.

While this seems like a long list, a correctly configured editor (see [VS Code Setup](../getting_started/setup_vs_code.md)) essentially assures:

1. 1, 2 and 3 are automatically covered.
2. 4 & 5 are mostly covered. Additionally, if you skip type hints, they won't be checked; we can help you add these in the PR.

These checks must pass in order for the execution-spec-tests Github Actions to pass upon pushing to remote. In order to help verify these checks, the `tox` tool can be used locally, see [Verifying Changes](./verifying_changes.md).