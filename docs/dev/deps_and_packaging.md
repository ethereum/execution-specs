# EEST Dependency Management and Packaging

EEST uses [`uv`](https://docs.astral.sh/uv/) to manage and pin its dependencies.

A minimum version of `uv>=0.7.0` is required to ensure `uv` writes `uv.lock` files with consistent fields and formatting (see [ethereum/execution-spec-tests#1597](https://github.com/ethereum/execution-spec-tests/pull/1597)).

## Managing Dependencies

We aim to provide specific [version specifiers](https://peps.python.org/pep-0440/#version-specifiers) for all of our dependencies.

!!! note "Packages should be managed via `uv`"

    Dependencies should be managed using `uv` on the command-line to ensure that version compatibility is ensured across all dependencies and that `uv.lock` is updated as required.

    The docs below cover common operations, see the `uv` [documentation on managing dependencies](https://docs.astral.sh/uv/concepts/projects/dependencies/#multiple-sources) for more information.

!!! info "Separate PRs are preferred when managing dependencies"

    An upgrade of all pinned dependencies in `uv.lock` must be performed in a dedicated PR!
    
    For other dependency changes, they can be included in the PR that removed use of the library, for example. But if a version bump is made, without related source code changes, it should be done in a dedicated PR. This makes the change:

    - Easier to track.
    - Trivial to revert.

### Adding/modifying direct dependencies

These are packages listed in the project's direct dependencies, i.e., in `pyproject.toml` `[project]` section:

```toml
[project]
...
dependencies = [
    "click>=8.1.0,<9",
    ...
    "pytest-regex>=0.2.0,<0.3",
]
```

or, for source package dependencies (directly installed via a `git+` specifier from Github), in the `[tool.uv.sources]` section:

```toml
[tool.uv.sources]
ethereum-spec-evm-resolver = { git = "https://github.com/petertdavies/ethereum-spec-evm-resolver", rev = \
...
```

!!! example "Example: Updating direct dependencies"

    Example of a package dependency update:
    ```console
    uv add "requests>=2.31,<2.33"
    ```

    Example of a source dependency update:
    ```console
    uv add "ethereum-spec-evm-resolver @ git+https://github.com/petertdavies/ethereum-spec-evm-resolver@623ac4565025e72b65f45b926da2a3552041b469"
    ```

### Adding/modifying development dependencies

Development dependencies are managed in dependency groups: `lint`, `doc`, `test`, and `mkdocs` defined in the `pyproject.toml`:

```toml
[dependency-groups]
test = [
    "pytest>=8,<9",
    "pytest-cov>=4.1.0,<5",
    ...
]
lint = [
    "ruff==0.13.2",
    "mypy==1.17.0",
    "types-requests>=2.31,<2.33",
    ...
]
```

These can be modified via `uv`on the command-line or edited by hand. If editing manually, you must run `uv lock` afterwards to update the lockfile.

!!! example "Example: Updating a development dependency"

    Using uv:
    ```console
    uv add --group lint "types-requests>=2.31,<2.33"
    ```

    Or edit `pyproject.toml` manually and then run:
    ```console
    uv lock
    ```

### Adding/modifying optional dependencies

The `optimized` optional extra provides performance enhancements and is the only remaining optional dependency group:

```toml
[project.optional-dependencies]
optimized = [
    "rust-pyspec-glue>=0.0.9,<0.1.0",
    "ethash>=1.1.0,<2",
]
```

!!! example "Example: Updating an optional dependency"

    ```console
    uv add --optional optimized "ethash>=1.1.0,<2"
    ```

    Or edit `pyproject.toml` by hand and run `uv lock`.

## Upgrading Pinned Dependencies in `uv.lock`

To upgrade all pinned dependencies in `uv.lock` to the latest version permitted by EEST's `project.toml` version specifiers run:

```console
uv lock --upgrade
```

Project-wide dependency upgrades must be made via a dedicated PR!

To upgrade a single package run:

```console
uv lock --upgrade-package <package>
```

See [Locking and Syncing](https://docs.astral.sh/uv/concepts/projects/sync/#upgrading-locked-package-versions) in the `uv` docs for more information.
