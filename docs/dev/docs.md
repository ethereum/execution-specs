# Documentation

The `execution-spec-tests` documentation is generated via [`mkdocs`](https://www.mkdocs.org/) and hosted remotely on [readthedocs.io](https://execution-spec-tests.readthedocs.io/en/latest/).

## Prerequisites
```console
pip install -e .[docs]
```

## Build the Documentation
One time build:
```console
mkdocs build
```

### Local Deployment and Test
This runs continually and re-generates the documentation upon changes in the `./docs/` sub-director and deploys the site locally ([127.0.0.1:8000](http://127.0.0.1:8000/), by default):
```console
mkdocs serve
```
Note: The `gen-files` plugin currently breaks the `serve` command by continually re-generating the documentation. Disable this config in mkdocs.yml to avoid this behaviour.


### Test Remote Deployment
This can be used to generate and deploy a local version of the documentation remotely on Github pages in order to share a preview with other developers. Note, as the documentation is generated locally, even changes that have not been pushed will be deployed:
```console
mkdocs gh-deploy
```
It will be deployed to the Github pages of the repo's username (branch is ignored), e.g., [https://danceratopz.github.io/execution-spec-tests](https://danceratopz.github.io/execution-spec-tests).


### Production Deployment

Read the docs should pick up a push to the `main` branch and deploy an up-to-date version of the documentation. Active maintainers who wish to manage the documentation on [readthedocs.org](https://readthedocs.org/projects/execution-spec-tests/) require a readthedocs account and be given permission (please ask one of the active maintainers).

## Implementation

### Plugins

The documentation flow uses `mkdocs` and the following additional plugins:

- [mkdocs](https://www.mkdocs.org/): The main doc generation tool.
- [mkdocs-material](https://squidfunk.github.io/mkdocs-material): Provides many additional features and styling for mkdocs.
- [mkdocstrings](https://mkdocstrings.github.io/) and [mkdocstrings-python](https://mkdocstrings.github.io/python/): To generate documentation from Python docstrings.
- [mkdocs-awesome-pages-plugin](https://github.com/lukasgeiter/mkdocs-awesome-pages-plugin): To allow a flexible combination of manually ordering and automatically ordering items in the navigation bars via `.pages` files in sub-directories.
- [mkdocs-gen-files](https://oprypin.github.io/mkdocs-gen-files): To generate markdown files automatically for each test filler Python module. This could be used to [programmatically generate the nav section](https://oprypin.github.io/mkdocs-gen-files/extras.html). 
- [mkdocs-git-authors-plugin](https://timvink.github.io/mkdocs-git-authors-plugin/): To display doc contributors in the page footer.
- [mkdocs-glightbox](https://github.com/blueswen/mkdocs-glightbox) - for improved image and inline content display.