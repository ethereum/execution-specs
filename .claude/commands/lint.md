# Lint

Run the full static analysis suite and fix issues. This matches the CI check on every PR.

## Step 1: Run the Full Check

```bash
uvx tox -e static
```

This runs ruff, mypy, codespell, ethereum-spec-lint, and actionlint in one pass. If everything passes, you're done.

## Step 2: Auto-Fix Formatting and Lint Issues

If tox reports ruff errors, run these first — they resolve most issues automatically:

```bash
uv run ruff format
uv run ruff check --fix
```

## Step 3: Resolve Remaining Issues Manually

After auto-fix, re-run to see what's left:

```bash
uvx tox -e static
```

- **Remaining ruff issues**: fix manually (auto-fix can't handle all rules)
- **mypy errors**: fix type annotations, add missing types, correct signatures
- **codespell errors**: fix typos, or add intentional words to `whitelist.txt`
- **ethereum-spec-lint errors**: fix import isolation violations (see `/implement-eip` for import rules)
- **actionlint errors**: fix workflow YAML issues (see `/edit-workflow`)

## Step 4: Final Verification

Re-run until clean:

```bash
uvx tox -e static
```
