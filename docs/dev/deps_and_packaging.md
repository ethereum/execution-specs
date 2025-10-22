# EEST Dependency Management and Packaging

EEST uses [`uv`](https://docs.astral.sh/uv/) to manage and pin its dependencies.

A minimum version of `uv>=0.7.0` is required to ensure `uv` writes `uv.lock` files with consistent fields and formatting (see [ethereum/execution-spec-tests#1597](https://github.com/ethereum/execution-spec-tests/pull/1597)).

## Managing Dependencies

We aim to provide specific [version specifiers](https://peps.python.org/pep-0440/#version-specifiers) for each of our direct and extra dependencies.

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

### Adding/modifying optional dependencies

The package versions in the optional "extra" groups should also be managed via uv on the command-line These are the: `lint`, `docs`, `test` optional groups defined in the `pyproject.toml`:

```toml
[project.optional-dependencies]
test = ["pytest-cov>=4.1.0,<5"]
lint = [
    "ruff==0.9.4",
    "mypy>=1.15.0,<1.16",
    "types-requests>=2.31,<2.33",
]
docs = [
    ...
]
```

!!! example "Example: Updating an optional dependency"

    ```
    uv add --optional lint "types-requests>=2.31,<2.33"
    ```

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
