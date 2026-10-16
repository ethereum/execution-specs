# Reassign Reviewer

Reassign a fresh reviewer to the current PR after fixes have been pushed. Only the PR author should invoke this skill.

## Steps

1. Determine the current PR number. If not provided as an argument, detect it from the current branch:
   ```bash
   gh pr view --json number --jq .number
   ```

2. Run the reviewer assignment script in rereview mode:
   ```bash
   uv run .github/scripts/assign_reviewer.py \
     --repo ethereum/execution-specs \
     --pr <PR_NUMBER> \
     --mode rereview \
     --assign
   ```

3. Report who was assigned and why (summarise the selection factors briefly).

## Requirements

- The environment variables `STEEL_OOO_URL` and `STEEL_OOO_KEY` must be set for OOO checking. If they are not set, warn the user but proceed without OOO data.
- The `gh` CLI must be authenticated.

## When to use

Invoke this skill after:
- A reviewer requested changes
- The PR author (and optionally another contributor) pushed fixes
- The author wants a fresh pair of eyes on the updated PR
