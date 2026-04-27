# Spec Releases

EELS is published as a versioned Python package. This page explains how the version number is structured and how it relates to Ethereum hardforks and devnets. For the maintainer runbook (tagging, publishing to PyPI), see [Releasing](../dev/releasing.md).

## About versions

EELS' versioning scheme is intended to be compatible with Python's [Version Specifiers], and is *not* compatible with [SemVer] (although it borrows some of SemVer's concepts).

[Version Specifiers]: https://packaging.python.org/en/latest/specifications/version-specifiers/
[SemVer]: https://semver.org/

### Format

The general format of EELS version numbers is:

```text
COMPAT "." HARDFORK ( "." PATCH | ".0rc" DEVNET [ ".post" PATCH ] ) [ ".dev" DEV ]
```

Where:

- `COMPAT` is incremented when a release contains a backwards-incompatible change to an EELS interface (Python API, command-line tools, etc.).
- `HARDFORK` is the number of hardforks included in the release after Frontier.
- `DEVNET`, if present, is incremented when a release targets a new devnet.
- `DEV`, if present, indicates a pre-release preview and is incremented for each pre-release before the final release.
- `PATCH`, if present, is incremented for each release that does not increment any of `COMPAT`, `HARDFORK`, `DEV`, or `DEVNET`. It is reset to zero when any of `COMPAT`, `HARDFORK`, or `DEVNET` is incremented.

### Examples

The following table is a hypothetical complete example of all of the releases between `1.15.0rc1.dev1` and `2.16.0`, oldest at the top:

| Fork   | Description        | Version Number    |
| ------ | ------------------ | ----------------- |
| cancun | preview of devnet1 | `1.15.0rc1.dev1`  |
| cancun | preview of devnet1 | `1.15.0rc1.dev2`  |
| cancun | preview of devnet1 | `1.15.0rc1.dev3`  |
|        |                    |                   |
| cancun | finalize devnet1   | `1.15.0rc1`       |
|        |                    |                   |
| cancun | devnet1 bugfix     | `1.15.0rc1.post1` |
| cancun | devnet1 bugfix     | `1.15.0rc1.post2` |
| cancun | devnet1 bugfix     | `1.15.0rc1.post3` |
|        |                    |                   |
| cancun | finalize devnet2   | `1.15.0rc2`       |
|        |                    |                   |
| cancun | finalize mainnet   | `1.15.0`          |
|        |                    |                   |
| cancun | mainnet bugfix     | `1.15.1`          |
|        |                    |                   |
| cancun | breaking change    | `2.15.0`          |
|        |                    |                   |
| prague | preview of devnet1 | `2.16.0rc1.dev1`  |
|        |                    |                   |
| prague | finalize devnet1   | `2.16.0rc1`       |
|        |                    |                   |
| prague | finalize mainnet   | `2.16.0`          |

## Choosing a version number

When proposing a new release, find the format matching the current version number in the table below, then choose the new version according to the reason for the new release:

| Current Version           | Action               | New Version            |
| ------------------------- | -------------------- | ---------------------- |
| **`1.3.5`**               |                      |                        |
|                           | Mainnet Release      | `1.4.0`                |
|                           | Devnet Release       | `1.4.0rc1`             |
|                           | Bug Fix Release      | `1.3.6`                |
|                           | Breaking Release     | `2.3.0`                |
|                           |                      |                        |
| **`1.3.0rc5`**            |                      |                        |
|                           | Mainnet Release      | `1.3.0`                |
|                           | Devnet Release       | `1.3.0rc6`             |
|                           | Bug Fix Release      | `1.3.0rc5.post1`       |
|                           | Breaking Release     | `2.3.0rc5`             |
|                           |                      |                        |
| **`1.3.0rc5.post7`**      |                      |                        |
|                           | Mainnet Release      | `1.3.0`                |
|                           | Devnet Release       | `1.3.0rc6`             |
|                           | Bug Fix Release      | `1.3.0rc5.post8`       |
|                           | Breaking Release     | `2.3.0rc5`             |
|                           |                      |                        |
| **`1.3.5.dev7`**          |                      |                        |
|                           | Mainnet Release      | `1.3.5`                |
|                           | Another Preview      | `1.3.5.dev8`           |
|                           |                      |                        |
| **`1.3.0rc5.dev7`**       |                      |                        |
|                           | Devnet Release       | `1.3.0rc5`             |
|                           | Another Preview      | `1.3.0rc5.dev8`        |
|                           |                      |                        |
| **`1.3.0rc5.post7.dev9`** |                      |                        |
|                           | Devnet Release       | `1.3.0rc5.post7`       |
|                           | Another Preview      | `1.3.0rc5.post7.dev10` |

!!! note
    Append `.dev1` to any new version number to make it a pre-release, unless it already contained a `.devN` suffix. If it did, increment `N` to make another pre-release instead.

The version number is stored in `src/ethereum/__init__.py`.
