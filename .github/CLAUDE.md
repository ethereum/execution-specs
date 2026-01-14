# GitHub Actions Guidelines

## Action Version Pinning (Required)

All GitHub Actions must be pinned to a specific commit SHA with a version comment:

```yaml
uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
```

Never use version tags alone:

```yaml
uses: actions/checkout@v4  # Wrong
```

Local actions (`./.github/actions/*`) don't need version pinning.

## Linting Workflows

Run `uvx tox -e static` before committing workflow changes to ensure `actionlint` validates the YAML syntax and structure.
