# Releasing

This is the maintainer runbook for cutting an EELS release. For the
contributor-facing explanation of the versioning scheme, see
[Spec Releases](../specs/spec_releases.md).

## Overview

1. Choose a version number (see
   [Spec Releases](../specs/spec_releases.md)).
2. Update the version in source code.
3. Create a pull request.
4. Wait for it to get merged.
5. Create a tag.
6. Create a GitHub release.
7. Publish to PyPI.

## Updating the version in source code

The version number is set in `src/ethereum/__init__.py`. Change it
there. For example:

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

## Creating the pull request

The usual: `git checkout -b release-vX.Y.Z`, `git commit -a`, and
`git push`.

## Creating the tag

> [!WARNING]
> Do not create the tag from the `HEAD` branch of the pull request.
>
> GitHub can rewrite commits when merging pull requests, and tagging the
> original commit will make the git history messier than necessary.

The tag name should be the letter `v` followed by the version number
(e.g. `1.15.0rc5.post3` becomes `v1.15.0rc5.post3`).

To create and push the tag:

```bash
git checkout master     # Replace `master` with the pull request's base branch.
git pull
git tag -a -s v1.15.0   # Replace `v1.15.0` with the tag name from earlier.
git push origin v1.15.0 # Replace the tag name here too.
```

> [!IMPORTANT]
> If `git tag` complains about a missing GPG/PGP key, follow
> [this guide][keygen] to generate one. It's best to add the key to
> your GitHub account as well.

[keygen]: https://docs.github.com/en/authentication/managing-commit-signature-verification/generating-a-new-gpg-key

## Creating the GitHub release

Go to the [release page][release], choose the newly created tag, and
generate release notes.

[release]: https://github.com/ethereum/execution-specs/releases/new

## Publishing to PyPI

The default branch also holds the forks still under development. A release ships only the forks up to and including the fork it is for, in fork order. Build the archives from the release tag, naming the last fork to ship:

```bash
git checkout v2.21.0              # The release tag.
just build-spec-release amsterdam
```

The recipe exports the committed tree to a temporary directory, removes the later forks from it and from the packages list in `pyproject.toml`, and builds the sdist and wheel into `.just/spec-release/`. It checks that both archives contain exactly the forks up to the named one, then installs the wheel alone in a clean environment and imports every module in it. A fork that imports from a fork left out fails this check. The checkout is not modified.

Upload the two archives in `.just/spec-release/` as described in the [Python Packaging User Guide][ppug].

[ppug]: https://packaging.python.org/en/latest/tutorials/packaging-projects/#generating-distribution-archives
