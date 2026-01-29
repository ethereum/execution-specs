# Build Tools

This repository provides three equivalent ways to run checks and common tasks: **Justfile**, **Makefile**, and **tox**. All three delegate to tox as the source of truth.

## Quick Reference

| Task | just | make | tox |
|------|------|------|-----|
| All static checks | `just check` | `make check` | `uvx tox -e check` |
| Python lint | `just lint` | `make lint` | `uvx tox -e lint` |
| Python format check | `just format` | `make format` | `uvx tox -e format` |
| Python typecheck | `just typecheck` | `make typecheck` | `uvx tox -e typecheck` |
| Spellcheck | `just spellcheck` | `make spellcheck` | `uvx tox -e spellcheck` |
| Spec lint | `just spec-lint` | `make spec-lint` | `uvx tox -e spec-lint` |
| Lock file check | `just lockcheck` | `make lockcheck` | `uvx tox -e lockcheck` |
| Actions lint | `just actionlint` | `make actionlint` | `uvx tox -e actionlint` |
| Markdown lint | `just markdownlint` | `make markdownlint` | `uvx tox -e markdownlint` |
| Changelog check | `just changelog` | `make changelog` | `uvx tox -e changelog` |
| **Auto-fix lint/format** | `just fix` | `make fix` | _(no tox env)_ |
| Run tests | `just test` | `make test` | `uvx tox -e py3` |
| Run unit tests | `just test-unit` | `make test-unit` | `uvx tox -e tests_pytest_py3` |
| Build docs | `just docs` | `make docs` | `uvx tox -e mkdocs` |
| Serve docs locally | `just docs-serve` | `make docs-serve` | _(direct uv run)_ |

## When to Use Which Tool

| Tool | Best For | Notes |
|------|----------|-------|
| **just** | Daily development | Short commands, tab completion, cross-platform |
| **make** | CI/scripts, familiarity | Universal availability, well-known |
| **tox** | Advanced usage | Full control, parallel runs, custom envs |

## Listing Available Commands

```console
just --list       # List all just recipes
make help         # Show make targets with descriptions
uvx tox -av       # List all tox environments with descriptions
```

## Auto-fixing Issues

The `fix` recipe runs ruff directly (not via tox) to auto-fix lint and format issues:

```console
just fix          # or: make fix
```

This is equivalent to:

```console
uv run ruff check --fix
uv run ruff format
```

## Adding New Recipes

When adding a new check or task:

1. Add the tox environment in `tox.ini` (source of truth).
2. Add corresponding recipes to both `Justfile` and `Makefile`.
3. Keep the interface consistent across all three tools.
