# Devnet Release

Cut a `tests-<feature>@vX.Y.Z` devnet fixture release end to end: dispatch the fill, open the hive wiring PRs, and update the draft release notes with a Discord announcement. Devnet releases only. Mainnet `tests@vX.Y.Z` releases follow a different flow (nightly cached path) and are out of scope.

## Step 1: Gather Inputs

Ask the user for the **test release tracker link** (required, a `C-tracker` issue, e.g. #3311). Never proceed without it. Read the tracker: its scope drives the version bump, the release notes, and the Discord message.

Derive, and confirm with the user if ambiguous:

- `feature`: e.g. `glamsterdam-devnet`, `frames-devnet` (the tag becomes `tests-<feature>@<version>`)
- `branch`: the devnet branch, e.g. `devnets/glamsterdam/8`, `devnets/frames/0`
- previous release tag for the supersedes line and changelog links: `gh release list --repo ethereum/execution-specs`

## Step 2: Choose the Version

`vX.Y.Z`, where X tracks the devnet number for the family (`glamsterdam-devnet-8` releases are `v8.y.z`):

- **X bump (new devnet)**: first release for a new devnet, built from a new `devnets/<family>/<N>` branch
- **Y bump (spec change)**: consensus-breaking spec change or repricing on the same devnet
- **Z bump (tests only)**: new tests, coverage, or fixture-format additions with zero spec changes

Precedent ladder (glamsterdam):

- `tests-glamsterdam-devnet@v8.0.0` (new devnet)
- `tests-glamsterdam-devnet@v7.2.1` (new tests only)
- `tests-glamsterdam-devnet@v7.2.0` (new spec, breaking)
- `tests-glamsterdam-devnet@v7.1.0` (new spec, breaking)
- `tests-glamsterdam-devnet@v7.0.0` (new devnet)
- `tests-glamsterdam-devnet@v6.1.1` (new tests only)
- `tests-glamsterdam-devnet@v6.1.0` (new spec)
- `tests-glamsterdam-devnet@v6.0.1` (new tests only)
- `tests-glamsterdam-devnet@v6.0.0` (new devnet)

Confirm the chosen version with the user before dispatching.

## Step 3: Dispatch the Fill

```bash
gh workflow run release_fixtures.yaml --repo ethereum/execution-specs \
  -f feature=<feature> -f version=vX.Y.Z -f branch=devnets/<family>/<N>
```

- `version` excludes the `tests-<feature>@` prefix, the workflow builds the tag.
- Add `--ref <branch>` only when the release depends on workflow or feature-config changes that exist only on the devnet branch (precedent: `tests-frames-devnet@v0.0.0`).
- Watch it: `gh run list --repo ethereum/execution-specs --workflow=release_fixtures.yaml`, then `gh run watch <id>`. A full devnet fill takes hours (v8.0.0 filled ~90k fixtures).
- Success creates a **draft** release `tests-<feature>@vX.Y.Z`. The user publishes drafts manually. Never publish a release yourself.
- Dispatch failures on older devnet branches: the workflow file runs from the default branch but fills `-f branch`, so branches predating workflow-script changes can break the build-matrix step (precedent #3202).

## Step 4: Hive Wiring PRs

Open these once the draft release exists. Confirm with the user before pushing anything.

**hive-tests** (checkout `~/ethereum/hive-tests`): push branches to `ethpandaops/hive-tests` directly and open same-repo PRs. The spencer-tb remote is not a GitHub fork, cross-repo PRs fail with "no commits between".

- Every release: bump `EELS_BUILD_ARG_FIXTURES` to the new tag in both `.github/workflows/hive-<devnet>.yaml` and `hive-<devnet>-quick.yaml` (precedent ethpandaops/hive-tests#77). Pointing at a still-draft tag is accepted practice, scheduled runs fail until publish.
- New devnet (X bump) additionally: `git mv` the workflow pair to the new devnet name, then update the workflow `name`, `common_client_tag`, `EELS_BUILD_ARG_BRANCH`, and `EELS_BUILD_ARG_FIXTURES`. S3 paths and crons stay unchanged (precedents #65 devnet-6 to 7, #75 devnet-7 to 8).

**hive-ui** (new devnet only): update the workflow links in `public/discovery.json` to the new devnet workflows. The `address` S3 paths are stable. No push access to ethpandaops here, use the spencer-tb/hive-ui fork, cross-repo PRs work (precedent ethpandaops/hive-ui#77).

## Step 5: Update the Draft Release Notes

Compose the notes from the template below, then apply with:

```bash
gh release edit "tests-<feature>@vX.Y.Z" --repo ethereum/execution-specs --notes-file <file>
```

End the notes with the Discord announcement (Step 6) in a fenced block and the hive PR links, so the user can publish, post, and merge from one page:

```markdown
---
### Discord announcement (copy paste)

<the Step 6 message>

### Hive wiring
- hive-tests: <PR link>
- hive-ui: <PR link, new devnet only>
```

### Prose rules

- No spaced em-dashes (" — ") and no semicolons anywhere in notes or Discord text. Hyphens in compound words and "- " list bullets are fine (house style, cf. `scripts/check_ai_prose.py`).
- Single backticks for code, never double.
- Terse. Each Key Updates bullet is one EIP-prefixed sentence with the EIPs PR and the EELS PR referenced.

### Template

```markdown
### `tests-<feature>@vX.Y.Z`

<One line: release kind and devnet target.> It supersedes [`<prev-tag>`](https://github.com/ethereum/execution-specs/releases/tag/<prev-tag-url-encoded>) and is built from the [`devnets/<family>/<N>`](https://github.com/ethereum/execution-specs/tree/devnets/<family>/<N>) branch.

The full scope, EIP PRs, and checklist are tracked in the [test release tracker (#NNNN)](https://github.com/ethereum/execution-specs/issues/NNNN), so PTAL!

### Key Updates
- EIP-XXXX: <change in one sentence> ([EIPs#NNNNN](https://github.com/ethereum/EIPs/pull/NNNNN), #NNNN)

<X bump only: full EIP table with the ⬆️ updated / 🆕 new legend, see the v8.0.0 example.>

**Full Changelog**: https://github.com/ethereum/execution-specs/compare/<prev-tag>...<new-tag>
```

### Example 1: new devnet (X bump), `tests-glamsterdam-devnet@v8.0.0`

```markdown
### `tests-glamsterdam-devnet@v8.0.0`

This is the first test release targeting **`glamsterdam-devnet-8`**. It supersedes the final `glamsterdam-devnet-7` release ([`tests-glamsterdam-devnet@v7.2.1`](https://github.com/ethereum/execution-specs/releases/tag/tests-glamsterdam-devnet%40v7.2.1)) and is built from the [`devnets/glamsterdam/8`](https://github.com/ethereum/execution-specs/tree/devnets/glamsterdam/8) branch.

Expect at least 2 follow up releases with additional test coverage.

The full scope, EIP PRs, and checklist are tracked in the **[test release tracker (#3167)](https://github.com/ethereum/execution-specs/issues/3167)**, so PTAL!

### Key Updates
- EIP-2780: Transfer log cost is folded into `TX_VALUE_COST`: create transactions with value now pay the full value cost where they previously paid only the transfer-log component ([EIPs#11997](https://github.com/ethereum/EIPs/pull/11997), #3214)
- EIP-8037: "Regular gas" is renamed to "execution gas", terminology only, no behaviour change ([EIPs#11998](https://github.com/ethereum/EIPs/pull/11998), #3238, #3263)
- EIP-8038: Access-list costs are derived as the cold cost minus `WARM_ACCESS` (`3000 to 2900` per address and per storage key), making a prepaid entry gas-neutral with a cold access instead of 100 more expensive. EIP-2930's discount is intentionally not restored (EIPs PR TBD, #3271)
- EIP-8070: The eth/72 sparse blobpool Engine API changes (`engine_getBlobsV4`) are now mandatory for all ELs, including discv5 advertisement. Tests are execute-only and run via `execute` + hive rather than shipping in the fixture tarballs (#2948, [hive#1365](https://github.com/ethereum/hive/pull/1365))


## EIP list

| EIP | Title | |
|-----|-------|---|
| EIP-2780 | Resource-based intrinsic transaction gas | ⬆️ |
| EIP-7708 | ETH transfers emit a log | |
| EIP-7778 | Block Gas Accounting without Refunds | |
| EIP-7843 | `SLOTNUM` opcode | |
| EIP-7928 | Block-Level Access Lists | |
| EIP-7954 | Increase Maximum Contract Size | |
| EIP-7976 | Increase Calldata Floor Cost (64/64) | |
| EIP-7981 | Increase Access List Cost | |
| EIP-7997 | Deterministic Factory Predeploy | |
| EIP-8024 | Backward compatible `SWAPN`, `DUPN`, `EXCHANGE` | |
| EIP-8037 | State Creation Gas Cost Increase | ⬆️ |
| EIP-8038 | State-access gas cost update | ⬆️ |
| EIP-8070 | eth/72 - Sparse Blobpool | 🆕 |
| EIP-8246 | Remove SELFDESTRUCT balance burn | |
| EIP-8282 | Builder Execution Requests | |
| EIP-7610 | Revert creation in case of non-empty storage | |

**Key:** ⬆️ updated since `glamsterdam-devnet-7` · 🆕 newly mandatory / newly tested

**Full Changelog**: https://github.com/ethereum/execution-specs/compare/tests-glamsterdam-devnet@v7.2.1...tests-glamsterdam-devnet@v8.0.0
```

### Example 2: spec change (Y bump), `tests-glamsterdam-devnet@v7.2.0`

```markdown
### `tests-glamsterdam-devnet@v7.2.0`

This is a follow-up release targeting **`glamsterdam-devnet-7`**. It supersedes [`tests-glamsterdam-devnet@v7.1.0`](https://github.com/ethereum/execution-specs/releases/tag/tests-glamsterdam-devnet%40v7.1.0) and is built from the [`devnets/glamsterdam/7`](https://github.com/ethereum/execution-specs/tree/devnets/glamsterdam/7) branch.

The full scope, EIP PRs, and checklist are tracked in the [test release tracker (#3147)](https://github.com/ethereum/execution-specs/issues/3147), so PTAL!

### EIP-8037 Updates
- The calldata floor now binds the block-level regular gas dimension: each transaction contributes `max(pre_refund_gas - state_gas, calldata_floor)` to block gas, so state-gas spending cannot discount the floor ([EIPs#11908](https://github.com/ethereum/EIPs/pull/11908), #3144). New tests pin the floor-bound block accounting, including the `tx_regular < floor < tx_regular + state` regime.

**Full Changelog**: https://github.com/ethereum/execution-specs/compare/tests-glamsterdam-devnet@v7.1.0...tests-glamsterdam-devnet@v7.2.0
```

### Example 3: tests only (Z bump), `tests-glamsterdam-devnet@v7.2.1`

```markdown
### `tests-glamsterdam-devnet@v7.2.1`

This release is equivalent to [`tests-glamsterdam-devnet@v7.2.0`](https://github.com/ethereum/execution-specs/releases/tag/tests-glamsterdam-devnet%40v7.2.0), with the addition of EngineX fixtures to allow for running same tests but with `consume enginex`.

The full scope can be found in the [test release tracker (#3123)](https://github.com/ethereum/execution-specs/issues/3123), so PTAL!

**Full Changelog**: https://github.com/ethereum/execution-specs/compare/tests-glamsterdam-devnet@v7.1.0...tests-glamsterdam-devnet@v7.2.0
```

## Step 6: Discord Message

Raw markdown, prefixed `:test_tube:`. Same prose rules as the notes. Goes into the draft notes (Step 5) for the user to copy paste, never posted by you.

### Template

```markdown
:test_tube:  `<feature>@vX.Y.Z`: https://github.com/ethereum/execution-specs/releases/tag/tests-<feature>@vX.Y.Z

We are using this EELS branch for reference: [`devnets/<family>/<N>`](https://github.com/ethereum/execution-specs/tree/devnets/<family>/<N>)

PTAL at the release notes & the test [release tracker](https://github.com/ethereum/execution-specs/issues/NNNN) for the full scope.
<One or two sentences of context: what changed, what stayed the same, who to thank.>

**New in vX.Y.Z:**
- EIP-XXXX: <change in one sentence> [EIPs#NNNNN](https://github.com/ethereum/EIPs/pull/NNNNN).
```

### Example 1: new devnet (X bump), v7.0.0

```markdown
:test_tube:  `glamsterdam-devnet@v7.0.0`: https://github.com/ethereum/execution-specs/releases/tag/tests-glamsterdam-devnet@v7.0.0

We are using this EELS branch for reference: [`devnets/glamsterdam/7`](https://github.com/ethereum/execution-specs/tree/devnets/glamsterdam/7)

PTAL at the release notes & the test [release tracker](https://github.com/ethereum/execution-specs/issues/3034) for the full scope.
No new EIPs. Repricing numbers (EIP-2780, EIP-8038) are unchanged from devnet-6.

**New in v7.0.0:**
- EIP-2780/EIP-8037 intrinsic gas rework: state-dependent tx costs move out of intrinsic gas into runtime charges at the top frame [EIPs#11844](https://github.com/ethereum/EIPs/pull/11844) & [EIPs#11891](https://github.com/ethereum/EIPs/pull/11891), for more info: https://discord.com/channels/595666850260713488/1504670887851327648.
- EIP-8037 account creation state gas is now charged at access [EIPs#11858](https://github.com/ethereum/EIPs/pull/11858).
- Calldata floor is now anchored on the decomposed EIP-2780 base, EELS <-> EIP text alignment.
- EIP-8038/EIP-7928: SSTORE access cost check moved before the storage read [EIPs#11854](https://github.com/ethereum/EIPs/pull/11854).
- Final EIP-8282 builder contracts with disable switch, at new mined addresses [EIPs#11899](https://github.com/ethereum/EIPs/pull/11899).
  - Builder Deposit Contract: `0x0000BFF46984E3725691FA540A8C7589300D8282`
  - Builder Exit Contract: `0x000064D678505AD48F8CCB093BC65613800E8282`
```

### Example 2: spec change (Y bump), v7.2.0

```markdown
:test_tube:  `glamsterdam-devnet@v7.2.0`: https://github.com/ethereum/execution-specs/releases/tag/tests-glamsterdam-devnet@v7.2.0

We are using this EELS branch for reference: [`devnets/glamsterdam/7`](https://github.com/ethereum/execution-specs/tree/devnets/glamsterdam/7). [Release notes](https://github.com/ethereum/execution-specs/releases/tag/tests-glamsterdam-devnet%40v7.2.0) & new test [release tracker](https://github.com/ethereum/execution-specs/issues/3147).

A small spec change (bug fix) with minor test updates, no new EIPs. Thanks @Jochem Brouwer & @nero_eth!

**New in v7.2.0:**
- EIP-8037: calldata floor now applies to block-level regular gas, so state gas cannot discount the floor, [EIPs#11908](https://github.com/ethereum/EIPs/pull/11908).
```

### Example 3: tests only (Z bump), v6.0.1

```markdown
:test_tube:  `glamsterdam-devnet@v6.0.1` release

-> https://github.com/ethereum/execution-specs/releases/tag/tests-glamsterdam-devnet%40v6.0.1

Follow-up release adding additional coverage for EIP-8037 and EIP-8038 to `tests-glamsterdam-devnet@v6.0.0`.

No spec changes or changes to existing tests.
```

## Known Snags

- Branch prep (resets, cherry-squashes) happens before this skill, it only releases from an existing devnet branch. Never force-push devnet branches, add commits on top.
- (2026-08) New devnet branches cut from `forks/amsterdam` need the Engine X BAL drift masking squash (864fa03a15, PR #3219) cherry-picked on top until #3219/#3265 merge, otherwise the release fill fails with mass `blockAccessList` drift (precedent: frames v0.0.0 attempt 1).
- frames/Bogota: the feature entry must use `--fork=Bogota`, not `--until=Bogota` (the build-matrix `FORK_ORDER` ends at Amsterdam).
