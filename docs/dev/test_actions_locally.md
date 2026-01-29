# Running Github Actions Locally

The Github Actions workflows can be tested locally using [nektos/act](https://github.com/nektos/act) without pushing changes to the remote. The local repository state will be used in the executed workflow.

## Prerequisites

1. A docker installation without `sudo` prefix requirement ([see also dockerdocs](https://docs.docker.com/engine/install/linux-postinstall/#manage-docker-as-a-non-root-user)):

    ```bash
    sudo usermod -aG docker $USER
    ```

2. Install the Github CLI (`gh`): [linux](https://github.com/cli/cli/blob/trunk/docs/install_linux.md), [macos](https://github.com/cli/cli/tree/trunk?tab=readme-ov-file#macos).
3. Authenticate your Github account with the Github CLI:

    ```bash
    gh auth login
    ```

    This is required to set `GITHUB_TOKEN` to the output of `gh auth token` when running the workflows.

4. Install the `act` tool as a Github extension ([nektos/act docs](https://nektosact.com/installation/gh.html)):

    ```bash
    gh extension install https://github.com/nektos/gh-act
    ```

    or use one of the [other available methods](https://nektosact.com/installation/index.html).

!!! note "Updating nektos/act to the latest version via the Github CLI"
    The `act` tool can be updated via the Github CLI:

    ```bash
    gh extension upgrade nektos/act
    ```

## Listing the Available Workflows

```bash
gh act --list
```

will output something similar to:

```bash
INFO[0000] Using docker host 'unix:///var/run/docker.sock', and daemon socket 'unix:///var/run/docker.sock'
Stage  Job ID              Job name          Workflow name   Workflow file      Events
0      checks              Spellcheck        Check     check.yaml   push,pull_request,workflow_dispatch,workflow_call
0      checks              Python Lint       Check     check.yaml   push,pull_request,workflow_dispatch,workflow_call
0      checks              Python Format     Check     check.yaml   push,pull_request,workflow_dispatch,workflow_call
0      checks              Python Typecheck  Check     check.yaml   push,pull_request,workflow_dispatch,workflow_call
0      checks              Spec Lint         Check     check.yaml   push,pull_request,workflow_dispatch,workflow_call
0      checks              Lock Check        Check     check.yaml   push,pull_request,workflow_dispatch,workflow_call
0      checks              Action Lint       Check     check.yaml   push,pull_request,workflow_dispatch,workflow_call
0      checks              Changelog         Check     check.yaml   push,pull_request,workflow_dispatch,workflow_call
0      markdownlint        Markdown Lint     Check     check.yaml   push,pull_request,workflow_dispatch,workflow_call
0      sha-pinned-actions  SHA Pinned Actions Check    check.yaml   push,pull_request,workflow_dispatch,workflow_call
...
```

The `Job ID` is required to run a specific workflow and is provided to the `-j` option of `gh act`.

### Running Workflows that require Github Vars

Create a text file containing the required variables and variables, e.g., `.act_github_vars` (this is in `.gitignore`):

```text
UV_VERSION=0.5.15
DEFAULT_PYTHON_VERSION=3.12
```

and use the `--var-file` option to specify the file:

```bash
gh act --workflows .github/workflows/check.yaml --var-file=gh_vars.txt
```

### Running Workflows that use a Matrix Strategy

This is optional, recent versions will automatically detect the matrix strategy and run supported values. To run a specific matrix item, use the `--matrix` option:

```bash
gh act --workflows .github/workflows/check.yaml --var-file=gh_vars.txt --matrix name:"Python Lint"
```

### Running Release Workflows

Release builds require the `ref` input to be specified. To test a release build locally:

1. Create a JSON file specifying the input data required for a release build (the release tag), e.g, `event.json`:

    ```json
    {
        "ref": "refs/tags/stable@v4.2.0"
    }
    ```

2. Run `act` and specify the workflow file, the Github token, and the event file:

    ```bash
    gh act -j build --workflows .github/workflows/release_fixture_feature.yaml -s GITHUB_TOKEN=$(gh auth token) -e event.json
    ```

### Manually Specifying the Docker Image

It's possible to specify the Docker image used by the `act` tool for a specific platform defined in a workflow using the `-P` (`--platform`) option. For example, use map `ubuntu-latest` in the workflow to use `ubuntu-24.04`:

```bash
-P ubuntu-latest=ubuntu:24.04
```

This can be added to any `gh act` command.

### Fixing Permission Errors with Tool Cache

When running workflows that use `setup-uv` or similar setup actions, you may encounter permission errors like:

```text
::error::EACCES: permission denied, mkdir '/opt/hostedtoolcache/uv/0.9.27'
```

This happens because the container user doesn't have write access to `/opt/hostedtoolcache/`. Fix this by redirecting the tool cache to a writable location:

```bash
gh act --workflows .github/workflows/check.yaml \
  -P ubuntu-latest=ghcr.io/catthehacker/ubuntu:runner-latest \
  --env RUNNER_TOOL_CACHE=/tmp/tool_cache
```

The `RUNNER_TOOL_CACHE` environment variable tells setup actions where to install tools, avoiding the permission issue without requiring root access.
