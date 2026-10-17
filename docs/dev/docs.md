# Documentation

The `execution-specs` documentation is generated via [`mkdocs`](https://www.mkdocs.org/) and hosted at [steel.ethereum.foundation/docs/execution-specs/](https://steel.ethereum.foundation/docs/execution-specs/).

## Prerequisites

```console
uv sync
```

## Build and Verify the Documentation

One time build in strict mode:

```console
just docs
```

Run all docs related checks:

```console
just spellcheck
just lint-md
just docs
```

### Local Deployment and Test

Serve the site locally with live reload on changes to `docs/**/*.md`:

```console
just docs-serve
```

## Implementation

### Plugins

The documentation flow uses `mkdocs` and the following additional plugins:

- [mkdocs](https://www.mkdocs.org/): The main doc generation tool.
- [mkdocs-material](https://squidfunk.github.io/mkdocs-material): Provides many additional features and styling for mkdocs.
- [mkdocstrings](https://mkdocstrings.github.io/) and [mkdocstrings-python](https://mkdocstrings.github.io/python/): To generate documentation from Python docstrings.
- [mkdocs-gen-files](https://oprypin.github.io/mkdocs-gen-files): To generate pages at build time, such as the `fill` command-line options page.
- [mkdocs-literate-nav](https://oprypin.github.io/mkdocs-literate-nav/index.html): To define the navigation layout in `navigation.md`.
- @blueswen/mkdocs-glightbox - for improved image and inline content display.

### Navigation

All pages that are to be included in the documentation and the navigation bar must be included in `navigation.md`. This is enabled by [mkdocs-literate-nav](https://oprypin.github.io/mkdocs-literate-nav/index.html).
