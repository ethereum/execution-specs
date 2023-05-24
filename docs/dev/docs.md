# Documentation

`execution-spec-tests` documentation is generated via [`mkdocs`](https://www.mkdocs.org/) and hosted remotely on [readthedocs.io](https://execution-spec-tests.readthedocs.io/en/latest/).

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


### Test Remote Deployment
This can be used to generate and deploy a local version of the documentation remotely on Github pages in order to share a preview with other developers. Note, as the documentation is generated locally, even changes that have not been pushed will be deployed:
```console
mkdocs gh-deploy
```
It will be deployed to the Github pages of the repo's username (branch is ignored), e.g., [https://danceratopz.github.io/execution-spec-tests](https://danceratopz.github.io/execution-spec-tests).


### Production Deployment

Read the docs should pick up a push to the `main` branch and deploy an up-to-date version of the documentation. Active maintainers who wish to manage the documentation on [readthedocs.org](https://readthedocs.org/projects/execution-spec-tests/) require a readthedocs account and be given permission (please ask one of the active maintainers).