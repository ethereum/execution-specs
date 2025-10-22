# Consume Cache and Fixture Inputs

The `consume cache` command can be used to resolve, download and cache fixture releases:

```console
consume cache --input=stable@v4.5.0
```

All `consume` subcommands have an `--input` argument, which implements the same functionality as `consume cache` to download and cache fixtures, respectively obtain downloaded fixtures from the cache.

## Example: Two-liner to Download the Latest Fixture Release

Releases can be downloaded using EEST tooling without (manually) cloning and installing the @ethereum/execution-spec-tests tools as following:

1. Install `uv` (a fast, rust-based Python package manager):

    ```console
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

2. Run EEST's `consume cache` command via `uv` and request the latest ["stable" fixture release](../releases.md):

    ```console
    uvx --from git+https://github.com/ethereum/execution-spec-tests \
        consume cache --input=stable@latest
    ```

    Expected output, as of `v4.5.0`:

    ```console
    Updated https://github.com/ethereum/execution-spec-tests (8c3cbd7a4eef3967abd78db32ee45ef8f7cf8271)
    Updated https://github.com/petertdavies/ethereum-spec-evm-resolver (623ac4565025e72b65f45b926da2a3552041b469)
    Built ethereum-execution-spec-tests @ git+https://github.com/ethereum/execution-spec-tests@8c3cbd7a4eef3967abd78db32ee45ef8f7cf8271

    Installed 69 packages in 10ms
    Exit: Fixtures downloaded and cached.
    Path: /home/dtopz/.cache/ethereum-execution-spec-tests/cached_downloads/ethereum/execution-spec-tests/v4.5.0/fixtures_stable/fixtures
    Input: https://github.com/ethereum/execution-spec-tests/releases/download/v4.5.0/fixtures_stable.tar.gz
    Release page: https://github.com/ethereum/execution-spec-tests/releases/tag/v4.5.0
    ```

    **Note:** Use direct URLs to avoid GitHub API calls (better for CI environments). Version specifiers like `stable@latest` will always use the GitHub API to resolve versions. More details on the arguments to `--input` are provided below.

    **Explanation:** `uv` creates a local Python virtual environment in `~/.cache/uv/`, installs EEST and executes the `consume cache` command to resolve and download the release, which gets cached at `~/.cache/ethereum-execution-spec-tests`. Subsequent commands will use the cached version of the fixtures.

## The `--input` Flag to Specify Fixtures

All `consume` sub-commands take an `--input=<fixture_path>|<release_spec>|<url>` flag to specify which fixtures should be used for the command, `<fixtures>` may be:

1. **A local directory**: Fixtures from your local file system.
2. **A release specification**: An EEST release tag or "release specification" `stable@latest`, `fusaka-devnet-1@v1.0.0`, etc.
3. **A URLs**: A full URL to a custom hosted release or a Github release.

### Release Specifications

A release specification has the format `<release_name>@<version>`.

**Supported release names:**

- `stable`: Latest stable fork release.
- `develop`: Latest development fork release.
- Custom release names: e.g., `pectra-devnet-4`, `eip7692`.

**Supported version formats:**

- `latest`: Most recent release for the specified name.
- `v1.2.3`: Specific semantic version.

### Examples

Examples using a release specification:

```bash
# Latest standard, full stable release (all forks up to and including the latest deployed mainnet fork)
uv run consume engine --input stable@latest

# Latest standard, full development release (all forks up to and including the latest development fork)
uv run consume rlp --input develop@latest

# Standard, full releases by tag
uv run consume engine --input stable@v4.1.0
uv run consume rlp --input develop@v4.2.1

# Pre-release tags
uv run consume cache --input pectra-devnet-6@v1.0.0
uv run consume direct --input eip7692@latest --bin ../go-ethereum/build/bin/evm
```

Examples using a URL, the target must be a `.tar.gz`:

```bash
# GitHub release URL
uv run consume engine --input https://github.com/ethereum/execution-spec-tests/releases/download/v4.1.0/fixtures_develop.tar.gz

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
uv run consume cache --input stable@latest --cache-folder /path/to/custom/cache
```

Or extract directly to a specific directory (bypasses cache structure):

```bash
uv run consume cache --input fusaka-devnet-2@v1.1.0 --extract-to ./benchmark-fixtures
```

**Cache structure:**

```text
❯ tree ~/.cache/ethereum-execution-spec-tests/ -L 5
/home/dtopz/.cache/ethereum-execution-spec-tests/
├── cached_downloads
│   ├── ethereum
│   │   └── execution-spec-tests
│   │       ├── pectra-devnet-5%40v1.0.0
│   │       │   └── fixtures_pectra-devnet-5
│   │       ├── pectra-devnet-6%40v1.0.0
│   │       │   └── fixtures_pectra-devnet-6
│   │       ├── v4.0.0
│   │       │   └── fixtures_develop
│   │       ├── v4.1.0
│   │       │   └── fixtures_develop
│   │       ├── v4.2.0
│   │       │   ├── fixtures_develop
│   │       │   ├── fixtures_eip7692
│   │       │   └── fixtures_stable
│   │       ├── v4.3.0
│   │       │   └── fixtures_develop
│   │       └── v4.5.0
│   │           └── fixtures_stable
│   └── other
└── release_information.json
```

## The Fixture Index File

The [`fill` command](../../filling_tests/index.md) generates a JSON file `<fixture_path>/.meta/index.json` that indexes the fixtures its generated. This index file is used by `consume` commands to allow fast collection of test subsets specified on the command-line, for example, via the `--sim.limit` flag. For help with `--sim.limit` when running `./hive`, see [Hive Common Options](../hive/common_options.md), for an overview of other available test selection flags when running `consume` directly, see [Useful Pytest Options](../useful_pytest_options.md).

## CI-Friendly Behavior for Direct URLs

When using direct GitHub release URLs (instead of version specifiers), the consume command automatically avoids unnecessary GitHub API calls to prevent rate limiting in CI environments:

```console
consume cache --input=https://github.com/ethereum/execution-spec-tests/releases/download/v4.5.0/fixtures_stable.tar.gz
```

**API Call Behavior:**

- ✅ **Direct URLs**: No API calls made, cleaner output (no "Release page:" line).
- ℹ️ **Version specifiers**: API calls required to resolve versions, includes release page info.

Examples:

```console
# No API calls - direct download
consume cache --input=https://github.com/ethereum/execution-spec-tests/releases/download/v4.5.0/fixtures_stable.tar.gz

# API calls required - version resolution  
consume cache --input=stable@latest
```
