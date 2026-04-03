# Lint

Run the full static analysis suite and fix issues. This matches the CI check on every PR.

## Step 1: Run the Full Check

```bash
just static
```

This runs ruff, mypy, codespell, ethereum-spec-lint, and actionlint in one pass. If everything passes, you're done.

## Step 2: Auto-Fix Formatting and Lint Issues

If static checks report ruff errors, run the fix recipe first — it resolves most issues automatically:

```bash
just fix
```

## Step 3: Resolve Remaining Issues Manually

After auto-fix, re-run to see what's left:

```bash
just static
```

- **Remaining ruff issues**: fix manually (auto-fix can't handle all rules)
- **mypy errors**: fix type annotations, add missing types, correct signatures
- **codespell errors**: fix typos, or add intentional words via `just whitelist <word>`
- **ethereum-spec-lint errors**: fix import isolation violations (see `/implement-eip` for import rules)
- **actionlint errors**: fix workflow YAML issues (see `/edit-workflow`)

## Step 4: Final Verification

Re-run until clean:

```bash
just static
```
