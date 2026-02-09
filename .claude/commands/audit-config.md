# Audit Config

Periodic verification skill to prevent CLAUDE.md and skills from going stale. Run this manually to check freshness (e.g., after a major refactor, before a release, or when onboarding).

## Checks to Perform

### 1. Verify File Paths

Check that every file path or directory referenced in `CLAUDE.md` and `.claude/commands/*.md` still exists. Report any broken references.

### 2. Verify CLI Commands

Run `--help` on referenced commands and confirm mentioned flags still exist:

- `uv run fill --help`
- `uv run ethereum-spec-new-fork --help`
- `uv run ethereum-spec-lint --help`
- `uv run checklist --help`

### 3. Verify Code Patterns

Spot-check code patterns mentioned in skills against actual code:

- Does `op_implementation` dict exist in the latest fork's `vm/instructions/__init__.py`?
- Does `PRE_COMPILED_CONTRACTS` exist in the latest fork's `vm/precompiled_contracts/mapping.py`?
- Does the `Ops` enum exist in `vm/instructions/__init__.py`?
- Does `FORK_CRITERIA` or equivalent exist in the latest fork's `__init__.py`?

### 4. Verify Fork List

Check that the fork order and default branch mentioned in `CLAUDE.md` match reality by inspecting `src/ethereum/forks/` and git branch configuration.

### 5. Verify Docs References

Confirm that `docs/` paths referenced in skills still exist:

- `docs/writing_tests/`
- `docs/writing_tests/opcode_metadata.md`
- `docs/writing_tests/checklist_templates/`
- `docs/filling_tests/`

## Output

Produce a summary with:

- **Current**: references that are still valid
- **Stale**: references that need updating, with suggested fixes
