# Edit Workflow

GitHub Actions conventions. Run this skill before modifying workflow files in `.github/`.

## Action Version Pinning (Required)

All actions must be pinned to commit SHA with version comment:

```yaml
uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
```

- Never use version tags alone (`@v4` is wrong)
- Local actions (`./.github/actions/*`) are exempt from pinning

## Validation

Run `just lint-actions` before committing to validate YAML syntax and structure.
