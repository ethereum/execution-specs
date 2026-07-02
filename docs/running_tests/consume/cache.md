# Consume Cache and Fixture Inputs

The `consume cache` command can be used to resolve, download and cache fixture releases:

```console
consume cache --input=tests@v20.0.0
```

All `consume` subcommands have an `--input` argument, which implements the same functionality as `consume cache` to download and cache fixtures, respectively obtain downloaded fixtures from the cache.

## Example: Two-liner to Download the Latest Fixture Release

Releases can be downloaded without (manually) cloning and installing the @ethereum/execution-specs tools as following:

1. Install `uv` (a fast, rust-based Python package manager):

    ```console
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

2. Run the `consume cache` command via `uv` and request the latest [mainnet `tests` release](../releases.md):

    ```console
    uvx --from "git+https://github.com/ethereum/execution-specs.git#subdirectory=packages/testing" \
        consume cache --input=latest
    ```

    <!-- TODO: Re-capture this example output; the transcript below is constructed. -->
    Expected output, as of `tests@v20.0.0`:

    ```console
    Path: /home/dtopz/.cache/ethereum-execution-spec-tests/cached_downloads/ethereum/execution-specs/tests%40v20.0.0/fixtures/fixtures
    Input: https://github.com/ethereum/execution-specs/releases/download/tests%40v20.0.0/fixtures.tar.gz
    Release page: https://github.com/ethereum/execution-specs/releases/tag/tests%40v20.0.0
    ```

    **Note:** Use direct URLs to avoid GitHub API calls (better for CI environments). Version specifiers like `tests@latest` will always use the GitHub API to resolve versions. More details on the arguments to `--input` are provided below.

    **Explanation:** `uv` creates a local Python virtual environment in `~/.cache/uv/`, installs the testing package and executes the `consume cache` command to resolve and download the release, which gets cached at `~/.cache/ethereum-execution-spec-tests`. Subsequent commands will use the cached version of the fixtures.

## The `--input` Flag to Specify Fixtures

All `consume` sub-commands take an `--input=<fixture_path>|<release_spec>|<url>` flag to specify which fixtures should be used for the command, `<fixtures>` may be:

1. **A local directory**: Fixtures from your local file system.
2. **A release specification**: A fixture release tag or "release specification" `tests@latest`, `bal-devnet@v7.0.0`, etc.
3. **A URLs**: A full URL to a custom hosted release or a Github release.

### Release Specifications

A release specification has the format `<release_name>@<version>`.

**Supported release names:**

- `tests`: The mainnet release, all tests for all forks up to and including the latest mainnet fork. A bare `latest` or `vX.Y.Z` input is shorthand for `tests@latest`, respectively `tests@vX.Y.Z`.
- `<feat>-devnet`: Devnet releases, e.g. `bal-devnet`, `glamsterdam-devnet`.
- Other features: e.g. `benchmark`, `zkevm`.

Any release name is also accepted with its `tests-` git tag prefix, e.g. `tests-bal@v7.3.2`.

**Supported version formats:**

- `latest`: Highest version for the specified name (publish time only breaks ties).
- `v1.2.3`: Specific semantic version.

### Examples

Examples using a release specification:

```bash
# Latest mainnet (tests) release
uv run consume engine --input latest
uv run consume rlp --input tests@latest

# Mainnet release by version
uv run consume engine --input v20.0.0
uv run consume rlp --input tests@v20.0.0

# Feature releases, with or without the tests- tag prefix
uv run consume cache --input bal-devnet@v7.0.0
uv run consume cache --input glamsterdam-devnet@latest
uv run consume direct --input tests-bal@v7.3.2 --bin ../go-ethereum/build/bin/evm
```

Examples using a URL, the target must be a `.tar.gz`:

```bash
# GitHub release URL
uv run consume engine --input https://github.com/ethereum/execution-specs/releases/download/tests%40v20.0.0/fixtures.tar.gz

# Direct archive URL
uv run consume rlp --input https://example.com/custom-fixtures.tar.gz
```

## Caching System

### Automatic Caching

All remote fixture sources are automatically cached to avoid repeated downloads:

**Default cache location:**

```text
~/.cache/ethereum-execution-spec-tests/cached_downloads/
```

You can override this location with the `--cache-folder` flag:

```bash
uv run consume cache --input latest --cache-folder /path/to/custom/cache
```

Or extract directly to a specific directory (bypasses cache structure):

```bash
uv run consume cache --input bal-devnet@v7.0.0 --extract-to ./devnet-fixtures
```

**Cache structure:**

```text
❯ tree ~/.cache/ethereum-execution-spec-tests/ -L 5
/home/dtopz/.cache/ethereum-execution-spec-tests/
├── cached_downloads
│   ├── ethereum
│   │   └── execution-specs
│   │       ├── tests%40v20.0.0
│   │       │   └── fixtures
│   │       ├── tests-bal%40v7.3.2
│   │       │   └── fixtures_bal
│   │       └── tests-glamsterdam-devnet%40v6.1.0
│   │           └── fixtures_glamsterdam-devnet
│   └── other
└── release_information.json
```

## The Fixture Index File

The [`fill` command](../../filling_tests/index.md) generates a JSON file `<fixture_path>/.meta/index.json` that indexes the fixtures its generated. This index file is used by `consume` commands to allow fast collection of test subsets specified on the command-line, for example, via the `--sim.limit` flag. For help with `--sim.limit` when running `./hive`, see [Hive Common Options](../hive/common_options.md), for an overview of other available test selection flags when running `consume` directly, see [Useful Pytest Options](../useful_pytest_options.md).

## CI-Friendly Behavior for Direct URLs

When using direct GitHub release URLs (instead of version specifiers), the consume command automatically avoids unnecessary GitHub API calls to prevent rate limiting in CI environments:

```console
consume cache --input=https://github.com/ethereum/execution-specs/releases/download/tests%40v20.0.0/fixtures.tar.gz
```

**API Call Behavior:**

- ✅ **Direct URLs**: No API calls made, cleaner output (no "Release page:" line).
- ℹ️ **Version specifiers**: API calls required to resolve versions, includes release page info.

Examples:

```console
# No API calls - direct download
consume cache --input=https://github.com/ethereum/execution-specs/releases/download/tests%40v20.0.0/fixtures.tar.gz

# API calls required - version resolution
consume cache --input=latest
```
