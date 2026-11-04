---
name: add-unscheduled-feature
description: Add an unscheduled feature (one EIP or a set of EIPs not scheduled for any fork) to src/ethereum/unscheduled/, with its framework fork and tests.
---

# Add an Unscheduled Feature

Move an unscheduled EIP, or a set of EIPs, from a `projects/<FEATURE>` branch
onto the development fork branch as a feature. Read
`src/ethereum/unscheduled/README.md` first: it is the reference for every rule
below. The process lives in `docs/specs/adding_a_new_eip.md`.

## Step 0: Gate

Confirm with the user before writing anything:

- The work exists on a `projects/<FEATURE>` branch.
- ACDT acknowledged adding it as a feature.
- The owners (GitHub handles) and the EIPs it contains.
- Whether it builds on the newest fork (default) or pins a `base` fork that
  is no longer under development.

If any of these is missing, stop and say so. Do not invent owners.

## Step 1: Name it

Pick a descriptive snake case name (`evmified_identity`, not `eip7666`). The
framework fork is its title case (`EvmifiedIdentity`). The names must match
exactly, since the transition tool maps one to the other.

## Step 2: Spec

Create `src/ethereum/unscheduled/<feature>/`:

1. `feature.toml` with `eips`, `owners`, `remove` and optionally `base`.
2. `__init__.py` with only a module docstring describing the feature.
3. New modules for new code, written like any fork module (relative imports
   within the fork, absolute imports from the previous fork or shared modules
   only).
4. Overlays for existing modules, holding only the definitions that change.
   An overlay replaces a definition whole, so copy the fork's current
   definition and edit it. Never edit `src/ethereum/forks/` for a feature.
5. Removals in `remove` for files, definitions, class attributes and
   imports that the feature deletes.

Port from the `projects/<FEATURE>` branch by diffing it against its base and
turning each changed definition into an overlay entry.

## Step 3: Build and check

```console
uv run ethereum-spec-unscheduled <feature> --update-lock
uv run ethereum-spec-unscheduled <feature> --output <scratch>
diff -ru src/ethereum/forks/<base> <scratch>/<feature>
uv run ethereum-spec-unscheduled <feature> --check
```

Read the diff end to end: it must be exactly the EIPs' changes. Fix every
`--check` failure in the feature, not in the fork.

## Step 4: Framework

1. One mixin per EIP in
   `packages/testing/src/execution_testing/forks/forks/eips/unscheduled/eip_<N>.py`.
2. The feature fork and its transition fork in
   `packages/testing/src/execution_testing/forks/forks/unscheduled.py`, on
   `LatestFork` or the pinned base fork.
3. Run the guard tests:
   `cd packages/testing && uv run pytest src/execution_testing/forks/tests/test_unscheduled_forks.py`.

## Step 5: Tests

Run `/write-test` first. Tests go in
`tests/unscheduled/<feature>/eip<N>_<name>/`, marked
`valid_from("EIP<N>")` or `valid_at_transition_to("EIP<N>")`.

```console
uv run fill tests/unscheduled/<feature> --fork <Feature> -n 2 --output <scratch> --clean
```

Prove the tests need the feature: temporarily make `resolve_fork` in
`src/ethereum_spec_tools/utils.py` return the base fork for the feature,
refill, and confirm that tests fail. Restore the file with `git checkout`
afterwards. Report which tests fail and which do not.

Pin each `REFERENCE_SPEC_VERSION` to the EIP file's blob hash
(`gh api repos/ethereum/EIPs/contents/EIPS/eip-<N>.md --jq .sha`) and check
the pins:

```console
GITHUB_TOKEN=$(gh auth token) uv run check_eip_versions \
    tests/unscheduled/<feature> --fork <Feature> --output <scratch> --clean
```

## Step 6: Finish

- Run `/lint`.
- Delete the `--output` and fill directories.
- Summarize for the user: the feature, its base, the replaced definitions in
  `base.lock`, the test results and the mutation check. Do not push or open
  a pull request unless the user asks.
