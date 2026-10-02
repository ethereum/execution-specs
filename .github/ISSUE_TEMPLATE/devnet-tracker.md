---
name: Devnet Test Release Tracker
about: Track EL test release readiness for a devnet (tests-<feat>-devnet@vX.Y.Z)
title: '<feat>-devnet@vX.Y.Z Test Release Tracker'
labels: C-tracker, P-high
assignees: ''

---

## `<feat>`-devnet@v`X.Y.Z`

> [!NOTE]
> This is an **execution layer (EL) only** tracker — it does not cover
> consensus layer (CL) readiness.

### Overview

<!--
    Briefly describe the purpose of this devnet test release, its scope, and any
    relevant links (devnet specs repo, ACD notes, configuration / genesis).

    The `<feat>` keyword is typically the fork name or headliner feature
    (e.g. `bal`, `glamsterdam`). The release fills all forks until the
    development fork (e.g. `fill --until Amsterdam`) so clients can guard
    against regressions, and is run in Hive CI under the standard naming scheme.
-->

- **Target release tag**: <!-- e.g. tests-glamsterdam-devnet@v5.0.0 -->
- **EELS branch**: <!-- link to the `feat-devnet-N` branch being used for this devnet -->
- **Test release date**: <!-- YYYY-MM-DD or "TBD" — aim for 5 days before the devnet -->
- **Devnet launch date**: <!-- YYYY-MM-DD or "TBD" -->

> [!NOTE]
> **Versioning** (`vX.Y.Z`): `X` is the devnet number (e.g. `5` for
> `glamsterdam-devnet-5`), making the targeted devnet explicit. `Y`/`Z` follow
> the same semantics as the consensus test releases: `Y` (minor) is bumped for
> a change in behaviour (a spec/test change that alters existing fixtures), and
> `Z` (patch) is bumped for new test additions only.

> [!NOTE]
> Aim to cut the test (fixture) release **at least 5 days before** the devnet
> launch, to give client teams time to integrate and run them.

### Follows On From _(optional)_

<!--
    Optional. If there is a previous devnet release tracker, link it here for
    context — even if the scope has changed. If this is a test-only follow-up
    (most updates are test additions and the scope is semantically unchanged),
    keep this issue small and list only what is new below. If there is no
    predecessor (a brand new `<feat>` / first devnet), remove this section.
-->

This is a follow-up to the `tests-<feat>-devnet@vX.Y.Z` tracker (#`<issue>`),
with test additions only.

> [!TIP]
> For a test-only follow-up, the sections below can be trimmed to just what
> changed since the previous tracker.

### Aim

<!--
    A short statement of what we're aiming for in this devnet test release.
    Be explicit that the scope is tentative and will change.
-->

We aim to include the following EIPs in the first `<feat>-devnet-N` EELS test
release (`tests-<feat>-devnet@vX.Y.Z`). This scope is tentative — EIPs may be
added, dropped, or deferred as decisions land in ACD and during implementation.

### Instructions

- [ ] Add the issue to the target fork milestone if applicable.
- [ ] Link each included EIP's [EIP Implementation Tracker](https://github.com/ethereum/execution-specs/issues/new?template=eip-tracker.md) below.

> [!IMPORTANT]
> Per-EIP specification and testing progress is tracked in the individual EIP
> Implementation Tracker issues. This issue tracks devnet-level readiness only.

### Proposed Scope

<!--
    Group EIPs by confidence. Move EIPs between groups as decisions are made,
    and check an EIP off in "Confirmed" once its tracker issue is stable.

    Always pin the exact spec version each devnet targets — `eips.ethereum.org`
    renders the latest EIP, but a devnet freezes a specific version, and that
    skew is a common source of cross-client divergence. Pin via a commit
    permalink to the EIP markdown (github.com/ethereum/EIPs/blob/<sha>/EIPS/eip-<n>.md)
    and/or the open EIP PR(s) — a SHA and PR(s) ideally, but either works.
    Devnets routinely run ahead of the merged EIP, and a single EIP may have
    several relevant PRs — list them all.
-->

#### Confirmed

- [ ] [EIP-<eip-number>](https://eips.ethereum.org/EIPS/eip-<eip-number>) ([ethereum/EIPs#<pr>](https://github.com/ethereum/EIPs/pull/<pr>), [#<pr>](https://github.com/ethereum/EIPs/pull/<pr>)) — #<tracker-issue>
- [ ] [EIP-<eip-number>](https://eips.ethereum.org/EIPS/eip-<eip-number>) ([ethereum/EIPs#<pr>](https://github.com/ethereum/EIPs/pull/<pr>)) — #<tracker-issue>

#### To Be Discussed

<!-- Items pending an ACD / owner decision. Link the relevant EIP PR(s). -->

- [ ] [EIP-<eip-number>](https://eips.ethereum.org/EIPS/eip-<eip-number>) ([ethereum/EIPs#<pr>](https://github.com/ethereum/EIPs/pull/<pr>)) — <reason / link to discussion PR>

#### At Risk / Likely Dropped

<!-- EIPs that may not make this devnet. -->

- [ ] [EIP-<eip-number>](https://eips.ethereum.org/EIPS/eip-<eip-number>) ([ethereum/EIPs#<pr>](https://github.com/ethereum/EIPs/pull/<pr>)) — <reason>

### Notes & Risks

<!--
    Call out the integration challenges and known hard spots, e.g. cross-EIP
    alignment, ordering dependencies, framework changes.
-->

The most difficult changes are expected to be `<...>`. Highlight any cross-EIP
alignment, ordering dependencies, or testing-framework work that could block the
release here.

### Specification + Testing Status

- [ ] All included EIP specifications merged to the corresponding `feat-devnet-N` branch.
- [ ] Devnet branch (`feat-devnet-N`) created and rebased on the target `forks/<fork>` branch.
- [ ] Required testing framework modifications implemented.
- [ ] Sufficient test suites for the included EIPs implemented.
- [ ] No regressions or failures in tests from prior forks (including static tests).
- [ ] Fixtures generated and released for the devnet.
- [ ] [`hive-tests`](https://github.com/ethpandaops/hive-tests/tree/master/.github/workflows) repo checked/updated to run the latest set of fixtures.
- [ ] [`hive-ui`](https://github.com/ethpandaops/hive-ui/blob/master/public/discovery.json) discovery checked/updated to the latest devnet workflow file within the `hive-tests` repo.

### Process Status

- [ ] Hive tests passing on at least two implementations.
- [ ] Interop / cross-client testing completed.
- [ ] Devnet launched.
- [ ] Post-launch issues triaged and tracked.

### Closure

<!--
    Before closing this issue, link the test fixture release tag that shipped
    for this devnet.
-->

- [ ] Linked the test fixture release tag used for this devnet: <!-- e.g. https://github.com/ethereum/execution-specs/releases/tag/<tag> -->

> [!IMPORTANT]
> After tagging, any future changes must be added to a newly created devnet
> tracker rather than reopening or amending this one.
