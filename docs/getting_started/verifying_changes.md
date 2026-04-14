# Verifying Changes

**TL;DR:** Run `just static` before every PR, preferably before every commit. Optionally, run the extra checks from the table below that match what you changed.

## Before You Open a PR

Run `just` to see all available recipes grouped by category. The checks that CI runs are defined in [`.github/workflows/test.yaml`](https://github.com/ethereum/execution-specs/blob/a830dab6f130151ab9023a473b7543120aa21961/.github/workflows/test.yaml) and [`.github/workflows/benchmark.yaml`](https://github.com/ethereum/execution-specs/blob/a830dab6f130151ab9023a473b7543120aa21961/.github/workflows/benchmark.yaml); these files are the source of truth.

Some CI jobs are slow. Only run the checks relevant to your change.

| Change type                                       | Run                                                                    | Comment                                                                                                |
| ------------------------------------------------- | ---------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| Any PR (baseline)                                 | `just static`                                                          | Lint, format, mypy, spellcheck, import isolation, workflow lint.                                       |
| Added or modified tests                           | `just fill tests/path/to/new/tests`                                    | See [Filling Tests](../filling_tests/index.md).                                                        |
| Framework changes (`packages/testing/`)           | `just test-tests`                                                      | Framework unit tests. Mirrors the `test-tests` CI job.                                                 |
| Benchmark framework changes                       | `just test-tests-bench`, `just bench-gas`, `just bench-opcode`, `just bench-opcode-config` | Benchmark unit tests and sanity checks. Mirrors the benchmark CI workflow.                             |
| Markdown touched                                  | `just lint-md`                                                         | Requires `markdownlint-cli2`; see [Linting Markdown](#linting-markdown).                               |
| Docs touched                                      | `just docs` or `just docs-fast`                                        | `docs-fast` skips the Test Case Reference section for faster iteration.                                |

## `just fix` and `just static`

`just static` is the baseline check for every PR. It runs spellcheck, lint, format check, mypy, EELS import isolation, and workflow linting.

`just fix` auto-applies formatting and the safe subset of `ruff` lint fixes. Run it first to clear anything mechanically fixable, then run `just static` to see what's left.

```console
just fix      # Auto-fix formatting and safe ruff lint rules.
just static   # Run all static checks.
```

## Filling New or Changed Tests

For PRs that add or modify tests, confirm the new or changed tests fill successfully:

```console
just fill tests/path/to/new/tests
```

Pass `--from <Fork>` and `--until <Fork>` to limit the fork range, mirroring the CI matrix. See [Filling Tests](../filling_tests/index.md) for the full `fill` reference.

## Linting Markdown

For PRs that touch markdown, run:

```console
just lint-md
```

### Additional Dependencies for `markdownlint`

We use `markdownlint-cli2` to lint documentation markdown files. This is an external (non-Python) package that must be installed separately:

```console
sudo apt install nodejs
sudo npm install -g markdownlint-cli2@0.17.2  # The version used in CI.
```

Or use a specific node version via `nvm`.

## Verifying Test Fixture Changes

When writing a PR that modifies either the framework or test cases, verify that changes don't cause issues with existing test cases.

All filled fixtures contain a `hash` field in the `_info` object, which is used to verify that the fixture hasn't changed.

### Using the Hasher Tool

The `hasher` command can be used to bulk-verify the hashes of fixtures in a directory.

| Flag             | Description                                                       |
| ---------------- | ----------------------------------------------------------------- |
| `--files` / `-f` | Prints a combined hash per JSON fixture file.                     |
| `--tests` / `-t` | Prints the hash of every test vector in JSON fixture files.       |
| `--root` / `-r`  | Prints a combined hash for all JSON fixture files in a directory. |

#### The `compare` Subcommand

The `hasher compare` subcommand directly compares two fixture directories
and shows only the differences:

```console
uv run hasher compare fixtures/ fixtures_new/
```

| Flag                | Description                                               |
| ------------------- | --------------------------------------------------------- |
| `--depth N` / `-d`  | Limit to N levels (0=root, 1=folders, 2=files, 3=tests).  |
| `--files` / `-f`    | Show differences at file level.                           |
| `--tests` / `-t`    | Show differences at individual test level.                |
| `--root` / `-r`     | Show only the root-level hash difference.                 |
| `--ignore-missing`  | Hide entries that exist in only one directory.            |
