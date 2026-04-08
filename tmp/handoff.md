# Handoff: pytest-split based fixture release workflow

## PR Summary

Replace the manual fork-range based CI splitting strategy for fixture releases
with dynamic, duration-aware load balancing using pytest-split. This distributes
~270k tests across N CI runners based on actual execution times, reducing wall
clock time and eliminating the need to manually maintain fork-range boundaries
as new forks are added.

### Key results

- **10 parallel runners** instead of 5 fork-range runners.
- **Self-improving**: every run stores durations for the next run's balancing.
- **No `.test_durations` in git**: durations are workflow artifacts, never
  committed.
- **Pre-alloc generation parallelized** across fork-range runners (5 runners,
  ~4 min each vs 10 min on a single runner).

---

## Architecture

### Before

```
setup → build (5 runners, fork-range split) → combine → release
```

Each build runner ran both phases of the fill command (phase 1: generate
pre-alloc groups, phase 2: fill all fixture formats) for a fixed fork range
(e.g., Frontier-Shanghai, Cancun, Prague, Osaka, BPO1-BPO2). Fork ranges were
hardcoded in `fork-ranges.yaml`.

### After

```
setup → generate-pre-alloc (5 fork-range runners) → build (10 pytest-split runners) → combine → release
```

- **Pre-alloc** is generated per fork-range (pre-alloc groups must be complete
  per fork). Each runner uploads its pre-alloc artifact.
- **Build** runners download ALL pre-alloc artifacts, then run phase 2 only
  with `--use-pre-alloc-groups`. Tests are distributed by pytest-split using
  the `GroupedLeastDuration` algorithm.
- **Combine** merges fixture directories, index files, and durations from all
  runners.

---

## Components

### 1. `GroupedLeastDuration` splitting algorithm

**Files:**

- `packages/testing/src/execution_testing/pytest_plugins/split/grouped_least_duration.py`
- `packages/testing/src/execution_testing/pytest_plugins/split/test_grouped_least_duration.py`

Groups tests by `(test_case, fork)` — stripping the fixture format token
(`state_test`, `blockchain_test`, etc.) from the parameter list. Format
variants of the same test case share a t8n cache and must stay on the same
runner. Different test case parametrizations can go to different runners/workers.

Algorithm:

1. Group items by key (preserving collection order within each group).
2. Sum durations per group (average for unknowns).
3. Greedy least-duration bin-packing: heaviest groups first, assigned to the
   runner with the smallest current total.
4. Within each runner, groups are ordered heaviest-first for optimal xdist
   work-stealing.

**Key design decisions:**

- Grouping was initially `(function, fork)` which created 19,000-second monster
  groups. Changed to `(test_case, fork)` which breaks them into ~1,200s groups
  (3-4 format variants each).
- Format tokens are identified by a hardcoded set matching the known fixture
  format names.

### 2. `--grouped-split` pytest plugin

**File:** `packages/testing/src/execution_testing/pytest_plugins/split/plugin.py`

Registered via `-p` in `pytest-fill.ini`. When `--grouped-split` is passed with
`--splits N` and `--group K`:

1. Unregisters pytest-split's built-in `PytestSplitPlugin` (avoids double
   splitting).
2. Loads and normalizes the `.test_durations` file (strips `@xdist_group`
   suffixes).
3. Applies `GroupedLeastDuration` to select this runner's items.
4. Reports duration coverage and runner assignment in the terminal summary
   (transferred from xdist workers to controller via `workeroutput`).

**Why a plugin, not `conftest.py`:** The fill command uses `-c pytest-fill.ini`
which prevents root `conftest.py` discovery. The plugin is loaded explicitly
via `-p`.

### 3. `FillCommand` changes

**File:** `packages/testing/src/execution_testing/cli/pytest_commands/fill.py`

Two changes to `create_executions`:

- `--use-pre-alloc-groups` now takes priority over two-phase detection, so
  `--use-pre-alloc-groups --generate-all-formats` correctly runs a single
  phase.
- `--generate-pre-alloc-groups` without `--generate-all-formats` runs phase 1
  only (no wasted phase 2).

### 4. Build matrix generation

**File:** `.github/scripts/generate_build_matrix.py`

Outputs two matrices:

- `build_matrix`: pytest-split groups (`{feature, label, splits, group}`)
- `pre_alloc_matrix`: fork-range entries (`{feature, label, from_fork, until_fork}`)

Split count is configured per feature in `feature.yaml` (e.g., `splits: 10`).

### 5. Workflow and action changes

**Files:**

- `.github/workflows/release_fixture_feature.yaml`
- `.github/actions/build-fixtures/action.yaml`

Major changes:

- New `generate-pre-alloc` matrix job (fork-range based, parallel).
- Build job downloads all pre-alloc artifacts + latest durations artifact.
- Fill command passes `--grouped-split --splits N --group K
  --generate-all-formats --use-pre-alloc-groups`.
- Durations always stored (`--store-durations`), always merged in combine step.
- Durations downloaded from latest previous run via `gh run download`.
- `store_durations` dispatch input removed (always on).

### 6. Duration normalization

**Issue discovered:** `--store-durations` records nodeids with `@t8n-cache-*`
xdist group suffixes, but `item.nodeid` during collection does not include
them. Every duration lookup was failing, defeating the load balancing entirely.

**Fix:** `normalize_durations()` strips `@*` suffixes from duration keys when
loading. Applied in the plugin, algorithm, and balance check script.

### 7. Balance check script

**File:** `scripts/check_split_balance.py`

Simulates a grouped split against collected nodeids and a durations file.
Prints per-runner group counts and estimated durations. Useful for tuning
splits count and verifying balance without running CI.

```bash
uv run fill --collect-only -q 2>/dev/null | grep '::' | sed 's/ (.*)//' > /tmp/nodeids.txt
uv run python scripts/check_split_balance.py --durations .test_durations --nodeids /tmp/nodeids.txt --splits 10
```

---

## Known limitations and future work

### Potential Worker starvation from indivisible heavy tests

The `test_genesis_hash_available[fork_Osaka-blockchain_test_engine_x-256_empty_blocks]`
test takes ~1,042s (17 min).

### Post-test merge overhead

After all xdist workers finish, the master process serially merges partial
fixture files (`.partial.*.jsonl` → `.json`). This could cause delays at the end of the test session, but it has not been investigated properly
Potential mitigations:

- `--single-fixture-per-file` avoids merges entirely (one JSON per test case).
- Custom xdist scheduler distributing at the file level (so each worker writes
  complete files).
- Parallel merge in the combine step instead of per-runner.

### RESOLVED: xdist was not respecting item ordering

Root cause: xdist's `--loadscope-reorder` (default=True) re-sorted the
workqueue by item count per scope, destroying the split plugin's
heaviest-first ordering. Since every group has exactly 3 items (format
variants), the sort was effectively random. This clustered heavy groups
on the same workers via xdist's pre-loading mechanism.

Fix: Added `--no-loadscope-reorder` to `pytest-fill.ini`. This preserves
collection order in the workqueue so heavy groups are dispatched first
when all workers are available. No custom xdist scheduler needed.

### Durations accuracy

The initial `.test_durations` was generated from a fork-range split run.
Durations improve with each subsequent run as they reflect the actual
pytest-split distribution. After 2-3 iterations, durations should stabilize.

---

## Before merging

- [ ] Revert `filler.py:2290` from `logger.info` back to `logger.debug`
  (temporary worker timing promotion).
- [ ] Remove `.test_durations` from disk (not in git, but may be locally).
- [ ] Decide on `splits: 10` vs a different count for mainnet.
- [ ] Consider interactive rebase to clean up fixup commits.
- [ ] Squash the `restrict mainnet fill to tests/istanbul` + revert commits.
