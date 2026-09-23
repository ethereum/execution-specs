---
name: edit-workflow
description: Apply repository conventions when editing GitHub Actions workflows.
---

# Edit Workflow

GitHub Actions conventions. Run this skill before modifying workflow files in `.github/`.

## Action Version Pinning (Required)

All actions must be pinned to commit SHA with version comment:

```yaml
uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
```

- Never use version tags alone (`@v4` is wrong)
- Local actions (`./.github/actions/*`) are exempt from pinning

## Runner Selection

Self-hosted runners (`[self-hosted-ghr, size-*-x64]`) are a shared EF devops
pool — reserve them for jobs that need the capacity. Non-critical or low-load
jobs belong on GitHub-hosted runners (`ubuntu-latest`), which also avoids a
provisioning wait (~2.5 min) if the self-hosted warm pool is exhausted.

- **Pattern**: lightweight job (short runtime, no heavy parallelism) →
  `ubuntu-latest` (e.g. `spec-tools` in #3177).
- **Anti-pattern**: defaulting a quick gate, lint, or cache-restore job to
  `size-xl-x64` "to be safe".
- **Exception**: a job may need self-hosted for reasons other than load, e.g.
  Docker Hub pulls from GHR egress IPs to dodge per-IP rate limits (#3185
  keeps push runs self-hosted while PR runs use `ubuntu-latest`).

If unsure which runner a job needs, flag it and ask instead of guessing.

## Validation

Run `just lint-actions` before committing to validate YAML syntax and structure.
