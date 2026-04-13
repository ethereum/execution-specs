# CLAUDE.md

Ethereum Execution Layer Specification written in Python. This is a **specification**, not production code — readability over performance.

## Tooling

- **uv** is the package manager. **just** is the command runner (`just --list`).
- The `execution_testing` package under `packages/testing/` is a UV workspace member.

## Linting

When done with changes, ask the user if they'd like to run `/lint` before committing. Don't skip this unless the user explicitly says to.

## Code Style

- 79 char lines, strict mypy, `pathlib` over `os.path`
- `snake_case` for variables/functions, `PascalCase` for classes, `UPPER_CASE` for constants
- Docstrings: imperative mood ("Return" not "Returns"), blank line after summary for multi-line
- Descriptive English names — avoid EIP numbers in identifiers
- Custom spell-check dictionary: `whitelist.txt`

## Architecture

- Each fork under `src/ethereum/forks/` is a **complete copy** of its predecessor (WET principle). Do NOT abstract across forks.
- Import isolation (enforced by `ethereum-spec-lint`): relative imports within a fork, absolute from previous fork only, shared modules (`ethereum.crypto`, `ethereum.utils`) always OK. Never import from future or ancient (2+ back) forks.

## Branches

- **There is no `main` branch.** Default branch = most active fork (currently `forks/amsterdam`). Run `git remote show origin | grep HEAD` to check.
- `mainnet` = stable specs for forks live on mainnet
- PRs target the default branch
- PRs strictly follow the template in `.github/PULL_REQUEST_TEMPLATE.md`. In the Checklist section, include unchecked items that don't apply — only remove them if they are truly irrelevant to the PR type.

## PR Reviews

When reviewing PRs that implement or test EIPs:

1. Identify the EIP number(s) from the branch name, PR title, or changed file paths
2. Fetch each EIP spec from `https://eips.ethereum.org/EIPS/eip-<number>` before starting the review
3. Verify the implementation matches the EIP's specification requirements

## When to Use Skills

- Writing or modifying tests → run `/write-test` first
- Writing or modifying pytester-based plugin tests → run `/pytester` first
- Filling test fixtures → run `/fill-tests` first
- Implementing an EIP or modifying fork code in `src/` → run `/implement-eip` first
- Modifying GitHub Actions workflows → run `/edit-workflow` first
- Assessing EIP complexity or scope → run `/assess-eip`
- Working on EIP test coverage or checklists → run `/eip-checklist` first
- Checking if config/skills are stale → run `/audit-config`
- Writing or modifying docstrings in `src/ethereum/` → run `/write-docstring` first
- Done with changes and ready to lint → run `/lint`

## Available Skills

- `/write-test` — test writing patterns, fixtures, markers, bytecode helpers
- `/pytester` — pytester execution modes, isolation, output handling for plugin tests
- `/fill-tests` — `fill` CLI reference, flags, debugging, benchmark tests
- `/implement-eip` — fork structure, import rules, adding opcodes/precompiles/tx types
- `/edit-workflow` — GitHub Actions conventions and version pinning
- `/assess-eip` — structured EIP complexity assessment
- `/eip-checklist` — EIP testing checklist system for tracking coverage
- `/lint` — full static analysis suite with auto-fix workflow
- `/audit-config` — verify CLAUDE.md and skills are still accurate
- `/write-docstring` — narrative Markdown docstring conventions for the spec
- `/grammar-check` — audit grammar in documentation and code comments
