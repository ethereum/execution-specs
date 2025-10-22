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
Stage  Job ID                Job name                                                      Workflow name                             Workflow file          Events                             
0      evmone-coverage-diff  evmone-coverage-diff                                          Evmone Coverage Report                    coverage.yaml          pull_request                       
0      deploy                deploy                                                        Deploy Docs Main                          docs_main.yaml         push                               
0      deploy                deploy                                                        Deploy Docs Tags                          docs_tags.yaml         push                               
0      features              features                                                      Build and Package Fixtures                fixtures.yaml          push,workflow_dispatch             
0      feature-names         feature-names                                                 Build and Package Fixtures for a feature  fixtures_feature.yaml  push,workflow_dispatch             
0      lint                  Lint python sources with ruff                                 Tox                                       tox_verify.yaml        push,pull_request,workflow_dispatch
0      typecheck             Typecheck python sources with mypy                            Tox                                       tox_verify.yaml        push,pull_request,workflow_dispatch
0      spellcheck            Spellcheck sources with pyspelling                            Tox                                       tox_verify.yaml        push,pull_request,workflow_dispatch
0      markdownlint          Lint markdown files with markdownlint                         Tox                                       tox_verify.yaml        push,pull_request,workflow_dispatch
0      mkdocs                Build html documentation with mkdocs                          Tox                                       tox_verify.yaml        push,pull_request,workflow_dispatch
0      pytest_framework      Run unit tests, ${{ matrix.os }}, ${{ matrix.python }}        Tox                                       tox_verify.yaml        push,pull_request,workflow_dispatch
0      tests_deployed        Fill tests, deployed, ${{ matrix.os }}, ${{ matrix.python }}  Tox                                       tox_verify.yaml        push,pull_request,workflow_dispatch
1      build                 build                                                         Build and Package Fixtures                fixtures.yaml          push,workflow_dispatch             
1      build                 build                                                         Build and Package Fixtures for a feature  fixtures_feature.yaml  push,workflow_dispatch             
2      release               release                                                       Build and Package Fixtures                fixtures.yaml          push,workflow_dispatch             
2      release               release                                                       Build and Package Fixtures for a feature  fixtures_feature.yaml  push,workflow_dispatch
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
gh act --workflows .github/workflows/tox_verify.yaml -s GITHUB_TOKEN=$(gh auth token) --var-file=gh_vars.txt -j lint 
```

### Running Workflows that use a Matrix Strategy

This is optional, recent versions will automatically detect the matrix strategy and run supported values. To run a specific matrix value, use the `--matrix` option:

```bash
gh act --workflows .github/workflows/tox_verify.yaml -s GITHUB_TOKEN=$(gh auth token) --matrix python:3.12 -j pytest_framework
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
    gh act -j build --workflows .github/workflows/fixtures_feature.yaml -s GITHUB_TOKEN=$(gh auth token) -e event.json
    ```

### Manually Specifying the Docker Image

It's possible to specify the Docker image used by the `act` tool for a specific platform defined in a workflow using the `-P` (`--platform`) option. For example, use map `ubuntu-latest` in the workflow to use `ubuntu-24.04`:

```bash
-P ubuntu-latest=ubuntu:24.04
```

This can be added to any `gh act` command.
