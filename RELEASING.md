# Execution Specification Releases

## About Versions

EELS' versioning scheme is intended to be compatible with Python's
[Version Specifiers], and is not compatible with [SemVer] (although it does
borrow some of SemVer's concepts.)

[Version Specifiers]: https://packaging.python.org/en/latest/specifications/version-specifiers/
[SemVer]: https://semver.org/

### Format

The general format of EELS version numbers is as follows:

```text
COMPAT "." HARDFORK ( "." PATCH | ".0rc" DEVNET [ ".post" PATCH ] ) [ ".dev" DEV ]
```

Where:

- `COMPAT` is incremented when a release contains a backwards-incompatible change to an EELS' interface (Python API, command line tools, etc.)
- `HARDFORK` is the number of named hardforks included in the release after Frontier. Parameter-only forks (such as BPO forks) do not increment this value.
- `PATCH`, if present, is incremented for releases that do not increment `COMPAT`, `HARDFORK`, `DEV`, or `DEVNET`. This includes parameter-only forks (e.g. BPO forks), packaging fixes, spec corrections, tooling fixes, and fixture regeneration. It is reset to zero when any of `COMPAT`, `HARDFORK`, or `DEVNET` is incremented.
- `DEVNET`, if present, is incremented when a release targets a new devnet.
- `DEV`, if present, indicates a pre-release preview and is incremented for each pre-release before the final release.

### COMPAT Discontinuity

Starting with version `6.19.0`, the `COMPAT` segment jumped from `2` to `6`. Versions `3.x`, `4.x`, and `5.x` were never released. This was done to leapfrog [EEST]'s v5.x releases when the two projects were unified, ensuring that all `6.x` and later versions unambiguously belong to the combined project.

[EEST]: https://github.com/ethereum/execution-spec-tests

### Examples

The following table is a hypothetical complete example of all of the releases between `6.19.0rc1.dev1` and `7.20.0`, in order from oldest at the top to the newest at the bottom.

| Fork       | Description        | Version Number     |
| ---------- | ------------------ | ------------------ |
| amsterdam  | preview of devnet1 | `6.19.0rc1.dev1`   |
| amsterdam  | preview of devnet1 | `6.19.0rc1.dev2`   |
| amsterdam  | preview of devnet1 | `6.19.0rc1.dev3`   |
|            |                    |                    |
| amsterdam  | finalize devnet1   | `6.19.0rc1`        |
|            |                    |                    |
| amsterdam  | devnet1 bugfix     | `6.19.0rc1.post1`  |
| amsterdam  | devnet1 bugfix     | `6.19.0rc1.post2`  |
|            |                    |                    |
| amsterdam  | finalize devnet2   | `6.19.0rc2`        |
|            |                    |                    |
| amsterdam  | finalize mainnet   | `6.19.0`           |
|            |                    |                    |
| amsterdam  | BPO fork           | `6.19.1`           |
| amsterdam  | BPO fork           | `6.19.2`           |
| amsterdam  | packaging fix      | `6.19.3`           |
|            |                    |                    |
| amsterdam  | breaking change    | `7.19.0`           |
|            |                    |                    |
| next-fork  | preview of devnet1 | `7.20.0rc1.dev1`   |
|            |                    |                    |
| next-fork  | finalize devnet1   | `7.20.0rc1`        |
|            |                    |                    |
| next-fork  | finalize mainnet   | `7.20.0`           |

## Creating a Release

### Overview

1. Choose a version number.
1. Update version in source code.
1. Create a pull request.
1. Wait for it to get merged.
1. Create a tag.
1. Create GitHub release.
1. Publish to PyPI.

### Choosing a Version Number

To choose the next version number, find the format matching the current version
number in the table below, then choose the new version according to the reason
for the new release.

| Current Version           | Action               | New Version            |
| ------------------------- | -------------------- | ---------------------- |
| **`6.19.3`**              |                      |                        |
|                           | Mainnet Named Fork Release | `6.20.0`         |
|                           | Devnet Release       | `6.20.0rc1`            |
|                           | Patch Release        | `6.19.4`               |
|                           | Breaking Release     | `7.19.0`               |
|                           |                      |                        |
| **`6.19.0rc5`**           |                      |                        |
|                           | Mainnet Release      | `6.19.0`               |
|                           | Devnet Release       | `6.19.0rc6`            |
|                           | Bug Fix Release      | `6.19.0rc5.post1`      |
|                           | Breaking Release     | `7.19.0rc5`            |
|                           |                      |                        |
| **`6.19.0rc5.post7`**     |                      |                        |
|                           | Mainnet Release      | `6.19.0`               |
|                           | Devnet Release       | `6.19.0rc6`            |
|                           | Bug Fix Release      | `6.19.0rc5.post8`      |
|                           | Breaking Release     | `7.19.0rc5`            |
|                           |                      |                        |
| **`6.19.3.dev7`**         |                      |                        |
|                           | Mainnet Release      | `6.19.3`               |
|                           | Another Preview      | `6.19.3.dev8`          |
|                           |                      |                        |
| **`6.19.0rc5.dev7`**      |                      |                        |
|                           | Devnet Release       | `6.19.0rc5`            |
|                           | Another Preview      | `6.19.0rc5.dev8`       |
|                           |                      |                        |
| **`6.19.0rc5.post7.dev9`** |                     |                        |
|                           | Devnet Release       | `6.19.0rc5.post7`      |
|                           | Another Preview      | `6.19.0rc5.post7.dev10`|

> [!NOTE]
> Append `.dev1` to any new version number to make it a pre-release, unless it
> already contained a `.devN` suffix. If it did, increment `N` to make another
> pre-release instead.

### Updating Version in Source Code

The version number is set in `src/ethereum/__init__.py`. Change it there. For
example:

```patch
diff --git a/src/ethereum/__init__.py b/src/ethereum/__init__.py
index 252f2f317..8cdd89a55 100644
--- a/src/ethereum/__init__.py
+++ b/src/ethereum/__init__.py
@@ -18,7 +18,7 @@ possible, to aid in defining the behavior of Ethereum clients.
 """
 import sys
 
-__version__ = "6.19.0"
+__version__ = "6.20.0rc1"
 
 #
 #  Ensure we can reach 1024 frames of recursion
```

### Creating the Pull Request

The usual. `git checkout -b release-vX.Y.Z`, `git commit -a`, and `git push`.

### Waiting

```text
  ______________________________________
/ Just because the message may never be  \\
| received does not mean it is not worth |
\\ sending.                               /
  --------------------------------------
         \   ^__^
          \  (oo)\_______
             (__)\       )\/\\
                 ||----w |
                 ||     ||
```

### Creating the Tag

> [!WARNING]
> Do not create the tag from the `HEAD` branch of the pull request.
>
> GitHub can rewrite commits when merging pull requests, and tagging the
> original commit will make the git history messier than necessary.

The tag name should be the letter `v` followed by the version number (eg.
`6.19.0rc5.post3` becomes `v6.19.0rc5.post3`.)

To create and push the tag:

```bash
git checkout master     # Replace `master` with the pull request's base branch.
git pull
git tag -a -s v6.19.0   # Replace `v6.19.0` with the tag name from earlier.
git push origin v6.19.0 # Replace the tag name here too.
```

> [!IMPORTANT]
> If `git tag` complains about a missing GPG/PGP key, follow
> [this guide][keygen] to generate one. It's best to add the key to your GitHub
> account as well.

[keygen]: https://docs.github.com/en/authentication/managing-commit-signature-verification/generating-a-new-gpg-key

### Creating the GitHub Release

Go to the [release page][release], choose the newly created tag, and generate some release
notes.

[release]: https://github.com/ethereum/execution-specs/releases/new

### Publishing to PyPI

See the [Python Packaging User Guide][ppug]

[ppug]: https://packaging.python.org/en/latest/tutorials/packaging-projects/#generating-distribution-archives
