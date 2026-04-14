# Dependency Management and Packaging

EELS uses [`uv`](https://docs.astral.sh/uv/) to manage and pin its dependencies, and a minimum `uv>=0.7.0` is required.

## Workspace Layout

The repo is a `uv` workspace with two members, each defined by its own `pyproject.toml`:

| Package                      | `pyproject.toml`                                                                                                            | Contents                                                 |
| ---------------------------- | --------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------- |
| `ethereum-execution`         | [`pyproject.toml`](https://github.com/ethereum/execution-specs/blob/a830dab6f130151ab9023a473b7543120aa21961/pyproject.toml)                                  | The Python specs (`src/ethereum/`) and associated tools. |
| `ethereum-execution-testing` | [`packages/testing/pyproject.toml`](https://github.com/ethereum/execution-specs/blob/a830dab6f130151ab9023a473b7543120aa21961/packages/testing/pyproject.toml) | The EEST test framework under `packages/testing/`.       |

A single [`uv.lock`](https://github.com/ethereum/execution-specs/blob/a830dab6f130151ab9023a473b7543120aa21961/uv.lock) at the repo root pins dependencies for both packages.

## Managing Dependencies

We aim to provide specific [version specifiers](https://peps.python.org/pep-0440/#version-specifiers) for all of our dependencies.

!!! note "Packages should be managed via `uv`"

    Dependencies should be managed using `uv` on the command-line to ensure that version compatibility is maintained across all dependencies and that `uv.lock` is updated as required.

    The docs below cover common operations, see the `uv` [documentation on managing dependencies](https://docs.astral.sh/uv/concepts/projects/dependencies/#multiple-sources) for more information.

!!! info "Target the right workspace member"

    Run `uv` commands from the repo root. By default they target `ethereum-execution` (the specs package). To target the test framework, pass `--package ethereum-execution-testing` (or equivalently, `cd packages/testing/` first and run `uv` from there).

    Either way, the single `uv.lock` at the repo root is updated and should be committed alongside the `pyproject.toml` change.

!!! info "Separate PRs are preferred when managing dependencies"

    An upgrade of all pinned dependencies in `uv.lock` must be performed in a dedicated PR.

    For other dependency changes, they can be included in the PR that adds or removes use of the library. But if a version bump is made without related source code changes, it should be done in a dedicated PR. This makes the change:

    - Easier to track.
    - Trivial to revert.

### Adding or modifying direct dependencies

Direct dependencies are the packages listed in each package's `[project] dependencies` table.

!!! example "Adding a direct dependency to the specs package"

    ```console
    uv add "requests>=2.31,<2.33"
    ```

!!! example "Adding a direct dependency to the testing package"

    ```console
    uv add --package ethereum-execution-testing "requests>=2.31,<2.33"
    ```

### Adding or modifying development dependencies

Development dependencies are grouped into `[dependency-groups]`, one group per concern, plus a `dev` meta-group that includes them all.

Groups defined by the specs package:

- `test`, `lint`, `actionlint`, `doc`, `mkdocs`.
- `dev` includes all of the above plus the `optimized` extra.

Groups defined by the testing package:

- `test`, `lint`.
- `dev` includes both.

!!! example "Adding a dev dependency to the specs `lint` group"

    ```console
    uv add --group lint "types-requests>=2.31,<2.33"
    ```

!!! example "Adding a dev dependency to the testing package `test` group"

    ```console
    uv add --package ethereum-execution-testing --group test "pytest-timeout>=2.3,<3"
    ```

### Adding or modifying optional dependencies

The specs package defines a single optional extra, `optimized`, which pulls in `rust-pyspec-glue` and `ethash` for EVM performance.

!!! example "Updating an optional dependency"

    ```console
    uv add --optional optimized "ethash>=1.1.0,<2"
    ```

## Upgrading Pinned Dependencies in `uv.lock`

To upgrade all pinned dependencies in `uv.lock` to the latest versions permitted by both packages' version specifiers, run:

```console
uv lock --upgrade
```

Project-wide dependency upgrades must be made via a dedicated PR.

To upgrade a single package, run:

```console
uv lock --upgrade-package <package>
```

See [Locking and Syncing](https://docs.astral.sh/uv/concepts/projects/sync/#upgrading-locked-package-versions) in the `uv` docs for more information.

## Verifying `uv.lock`

After any dependency change, verify that `uv.lock` is consistent with both `pyproject.toml` files:

```console
just lock-check
```

This recipe also runs as part of `just static` and must be clean before committing.
