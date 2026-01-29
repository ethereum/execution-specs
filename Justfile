# Justfile for ethereum/execution-specs
# All recipes delegate to tox (source of truth)

set quiet := true

default:
    @just --list

# Static checks (parallel for speed)
check:
    uvx tox --parallel -e lint,format,typecheck,spellcheck,spec-lint,lockcheck,actionlint,markdownlint,changelog

lint:
    uvx tox -e lint

format:
    uvx tox -e format

typecheck:
    uvx tox -e typecheck

spellcheck:
    uvx tox -e spellcheck

spec-lint:
    uvx tox -e spec-lint

lockcheck:
    uvx tox -e lockcheck

actionlint:
    uvx tox -e actionlint

markdownlint:
    uvx tox -e markdownlint

changelog:
    uvx tox -e changelog

# Auto-fix lint and format issues (runs uv directly, no tox env)
fix:
    uv run ruff check --fix
    uv run ruff format

# Tests
test:
    uvx tox -e py3

test-unit:
    uvx tox -e tests_pytest_py3

# Documentation
docs:
    uvx tox -e mkdocs

docs-serve:
    FAST_DOCS=True uv run mkdocs serve
