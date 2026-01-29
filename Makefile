# Makefile for ethereum/execution-specs and Marius
# All targets delegate to tox (source of truth)

.PHONY: help check lint format typecheck spellcheck spec-lint lockcheck \
        actionlint markdownlint changelog fix test test-unit docs docs-serve

.DEFAULT_GOAL := help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}'

check: ## Run all static checks
	uvx tox -e check

lint: ## Python linting (ruff)
	uvx tox -e lint

format: ## Python format check (ruff)
	uvx tox -e format

typecheck: ## Python type check (mypy)
	uvx tox -e typecheck

spellcheck: ## Spelling check (codespell)
	uvx tox -e spellcheck

spec-lint: ## Ethereum spec lints
	uvx tox -e spec-lint

lockcheck: ## Verify uv.lock in sync
	uvx tox -e lockcheck

actionlint: ## GitHub Actions lint
	uvx tox -e actionlint

markdownlint: ## Markdown lint
	uvx tox -e markdownlint

changelog: ## Changelog validation
	uvx tox -e changelog

fix: ## Auto-fix lint/format issues (runs uv directly)
	uv run ruff check --fix
	uv run ruff format

test: ## Run test filler (py3)
	uvx tox -e py3

test-unit: ## Run framework unit tests
	uvx tox -e tests_pytest_py3

docs: ## Build HTML docs
	uvx tox -e mkdocs

docs-serve: ## Serve docs locally
	FAST_DOCS=True uv run mkdocs serve
