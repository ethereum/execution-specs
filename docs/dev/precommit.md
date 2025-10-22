# Enabling Pre-Commit Checks

There's a [pre-commit](https://pre-commit.com/) config file available in the repository root (`.pre-commit-config.yaml`) that can be used to enable automatic checks upon commit - the commit will not go through if the checks don't pass.

To enable pre-commit, the following must be run once:

```console
uvx pre-commit install
```

!!! note "Bypassing pre-commit checks"
    Enabling of pre-commit checks is not mandatory (it cannot be enforced) and even if it is enabled, it can always be bypassed with:

    ```console
    git commit --no-verify
    ```
