# Execution Specification Releases

## About Versions

EELS' versioning scheme is intended to be compatible with Python's
[Version Specifiers], and is not compatible with [SemVer] (although it does
borrow some of SemVer's concepts.)

[Version Specifiers]: https://packaging.python.org/en/latest/specifications/version-specifiers/
[SemVer]: https://semver.org/

### Format

The general format of EELS version numbers is as follows:

```
COMPAT "." HARDFORK ( "." PATCH | ".0rc" DEVNET [ ".post" PATCH ] ) [ ".dev" DEV ]
```

Where:

- `COMPAT` is incremented when a release contains a backwards-incompatible change to an EELS' interface (Python API, command line tools, etc.)
- `HARDFORK` is the number of hardforks included in the release after Frontier.
- `DEVNET`, if present, is incremented when a release targets a new devnet.
- `DEV`, if present, indicates a pre-release preview and is incremented for each pre-release before the final release.
- `PATCH`, if present, is incremented for each release that does not increment any of `COMPAT`, `HARDFORK`, `DEV`, or `DEVNET`. It is reset to zero when any of `COMPAT`, `HARDFORK`, or `DEVNET` is incremented.

### Examples

The following table is a hypothetical complete example of all of the releases between `1.15.0rc1.dev1` and `2.16.0`, in order from oldest at the top to the newest at the bottom.

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
 
-__version__ = "1.15.0"
+__version__ = "1.16.0rc1"
 
 #
 #  Ensure we can reach 1024 frames of recursion
```

### Creating the Pull Request

The usual. `git checkout -b release-vX.Y.Z`, `git commit -a`, and `git push`.

### Waiting

```
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
`1.15.0rc5.post3` becomes `v1.15.0rc5.post3`.)

To create and push the tag:

```bash
git checkout master     # Replace `master` with the pull request's base branch.
git pull
git tag -a -s v1.15.0   # Replace `v1.15.0` with the tag name from earlier.
git push origin v1.15.0 # Replace the tag name here too.
```

> [!IMPORTANT]
> If `git tag` complains about a missing GPG/PGP key, follow
> [this guide][keygen] to generate one. It's best to add the key to your GitHub
> account as well.

[keygen]: https://docs.github.com/en/authentication/managing-commit-signature-verification/generating-a-new-gpg-key

### Creating the GitHub Release

Go [here][release], choose the newly created tag, and generate some release
notes.

[release]: https://github.com/ethereum/execution-specs/releases/new

### Publishing to PyPI

See the [Python Packaging User Guide][ppug]

[ppug]: https://packaging.python.org/en/latest/tutorials/packaging-projects/#generating-distribution-archives
