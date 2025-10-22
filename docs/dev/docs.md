# Documentation

The `execution-spec-tests` documentation is generated via [`mkdocs`](https://www.mkdocs.org/) and hosted remotely on Github Pages at [eest.ethereum.org](https://eest.ethereum.org/).

## Prerequisites

```console
uv sync --all-extras
```

## Build and Verify the Documentation

One time build in strict mode:

```console
uv run mkdocs build --strict
```

Perform all docs related checks via `tox` in parallel:

```console
uvx --with=tox-uv tox -e spellcheck,markdownlint,mkdocs --parallel
```

### Local Deployment and Test

This runs continually: Deploys the site locally and re-generates the site upon modifications to `docs/**/*.md` or `tests/**/*.py`:

```console
uv run mkdocs serve
```

For more help (including ensuring a clean build), see the `gen_test_doc` pytest plugin's documentation:

::: src.pytest_plugins.filler.gen_test_doc.gen_test_doc
    options:
        members: no

## Remote Deployment and Versioning

The execution-specs-test docs are hosted using Github pages at [eest.ethereum.org](https://eest.ethereum.org/). Versions are updated/deployed automatically as part of Github Actions, but this can also be performed on the command-line.

Our mkdocs configuration uses [mike](https://github.com/jimporter/mike) as a version provider. All deployments should be made via `mike` (whether as part of CI/CD or executed locally).

The deployed versions of the docs managed via `mike` are kept in the [gh-pages](https://github.com/ethereum/execution-spec-tests/tree/gh-pages) branch. When you run `mike` it commits to this branch and optionally pushes the changes directly to remote.

### Aliases

We currently have two aliases (which both point to `main` as of [#998](https://github.com/ethereum/execution-spec-tests/pull/998)):

- [`latest`](https://eest.ethereum.org/latest): the current state of the main branch.
- [`development`](https://eest.ethereum.org/development): the current state of the main branch.

These aliases point to specific versions, as configured below. It's possible to share links containing either of these aliases or to specific versions, i.e, the following are all valid links:

- https://eest.ethereum.org/ (redirects to latest/main)
- https://eest.ethereum.org/latest (redirects to main)
- https://eest.ethereum.org/development (redirects main)
- https://eest.ethereum.org/main
- https://eest.ethereum.org/v1.0.0

### CI/CD: Doc Deployment via Github Actions

There are two workflows that automatically deploy updated/new versions of the docs:

| Workflow `yaml` File | What | When |
|----------------------|------|------|
| `docs_main.yaml`     | Update "main" version of docs | Push to 'main' branch, (e.g., on PR merge) |
| `docs_tags.yaml`     | Deploy new version of docs; tag is used as version name | Upon creating a tag matching `v*` |

### Build and Deployment (without alias update)

Build a new version and deploy it to remote (this version will then show up in the version selector list):

```console
uv run mike deploy -rebase --push v1.2.3
```

!!! note "Local deployment"
    If you deploy locally, the documentation will be built with any changes made in your local repository. Check out the tag to deploy tagged versions.

### Build, Deploy and Update the Alias

Build, deploy and update the version an alias points to with:

```console
uv run mike deploy --rebase --push --update-aliases v1.2.3 latest
```

where `v1.2.3` indicates the version's name and `development` is the alias. This will overwrite the version if it already exists.  

!!! note "Updating the 'main' version locally"
    "main" is just a version name (intended to reflect that it is build from the main branch). However, `mike` will build the docs site from the current local repository state (including local modifications). Therefore, make sure you're on the HEAD of the main branch before executing (unless you know what you're doing :wink:)!

    ```console
    uv run mike deploy --rebase --push main
    ```

    If the alias accidentally go change:

    ```console
    uv run mike deploy --rebase --push --update-aliases main development
    ```

### Viewing and Deleting Versions

List versions:

```console
uv run mike list
```

Delete a version:

```console
uv run mike delete v1.2.3a1-eof
```

### Set Default Version

Set the default version of the docs to open upon loading the page:

```console
uv run mike set-default --push latest
```

Typically, this must only be executed once for a repo.

## Implementation

### Plugins

The documentation flow uses `mkdocs` and the following additional plugins:

- [mkdocs](https://www.mkdocs.org/): The main doc generation tool.
- [mkdocs-material](https://squidfunk.github.io/mkdocs-material): Provides many additional features and styling for mkdocs.
- [mkdocstrings](https://mkdocstrings.github.io/) and [mkdocstrings-python](https://mkdocstrings.github.io/python/): To generate documentation from Python docstrings.
- [mkdocs-gen-files](https://oprypin.github.io/mkdocs-gen-files): To generate markdown files automatically for each test case Python module. See [this page](https://mkdocstrings.github.io/crystal/quickstart/migrate.html) for example usage. This plugin is used to [programmatically generate the nav section](https://oprypin.github.io/mkdocs-gen-files/extras.html) for the generated test case reference documentation.
- [mkdocs-literate-nav](https://oprypin.github.io/mkdocs-literate-nav/index.html): Is used to define the navigation layout for non-generated content and was created to work well with `mkdocs-gen-files` to add nav content for generated content.
- @blueswen/mkdocs-glightbox - for improved image and inline content display.

### The "Test Case Reference" Section

This section is auto-generated via a combination of:

1. [mkdocstrings](https://mkdocstrings.github.io/) and [mkdocstrings-python](https://mkdocstrings.github.io/python/),
2. [mkdocs-gen-files](https://oprypin.github.io/mkdocs-gen-files),
3. [mkdocs-literate-nav](https://oprypin.github.io/mkdocs-literate-nav/index.html).

It auto-generates a sequence of nested pages (with nav entries) of all python modules detected under `./tests`. Each page contains a stub to the doc generated by mkdocstrings from the module's docstrings and source code. The mkdocs-gen-files and mkdocs-literate-nav plugins were created exactly for [this purpose](https://mkdocstrings.github.io/crystal/quickstart/migrate.html).

No action is necessary if a new test directory or module is added to `./tests`, it will be picked up automatically.

!!! info "Working with generated content"
    The files in the `./tests` directory are watched by `mkdocs serve`. Run `mkdocs serve` and edit the source docstrings: The browser will reload with the new content automatically.

### Navigation

All pages that are to be included in the documentation and the navigation bar must be included in `navigation.md`, except "Test Case Reference" entries. This is enabled by [mkdocs-literate-nav](https://oprypin.github.io/mkdocs-literate-nav/index.html). The nav entries for the automatically generated "Test Case Reference" section are generated in [mkdocs-gen-files](https://oprypin.github.io/mkdocs-gen-files) and appended to `navigation.md`.

!!! info "Current nav ordering limitations"
    The "Test Case Reference" section must currently be the last section in the nav. This is because our mkdocs flow:

    1. Reads `navigation.md`.
    2. Generates the Test Case Reference documentation and appends the Test Case Reference entries to `navigation.md`
    3. Generates the nav.

    If necessary, we could probably split `navigation.md` into two files
    
    - `navigation-pre-test-case-reference.md`,
    - `navigation-post-test-case-reference.md`,

    and create an arbitrary ordering in the Test Case Reference doc gen script. But this is untested.

## Read the Docs

Originally, before June 2023, documentation was hosted at readthedocs.io. Currently, this page no longer exists (execution-spec-tests.readthedocs.io).
