# Post-Mortems of Missed Test Scenarios

This page contains a collection of post-mortem analyses for test cases that were not initially identified by the testing process.

The objective is to document and learn from missed scenarios — including those that were caught on the client side due to consensus issue, client developer raised issues, external reviewers, or external bug bounties — in order to improve test coverage and reduce the likelihood of similar omissions in the future.

Each entry must include an explanation of why the test case was missed plus the changes that were implemented in documentation or framework to improve the testing process.

## List

## 2026-01 - Data Copy Word Cost Gas Calculation - Byzantium+

### Description

A bug was discovered in Nethermind's implementation of CALLDATACOPY and CODECOPY opcodes where the word copy cost (3 gas per 32-byte word) was not being correctly charged. The issue was identified during internal fuzz testing and fixed in [Nethermind PR #10116](https://github.com/NethermindEth/nethermind/pull/10116).

The EVM specification requires data copy operations to charge:

- Static cost: 3 gas
- Word copy cost: 3 * ceil(size/32) gas
- Memory expansion cost (if applicable)

The bug allowed these operations to complete successfully even when insufficient gas was provided for the word copy cost component.

### Root Cause Analysis

- The word copy cost is a well-documented part of the EVM specification, but existing test coverage did not specifically isolate this gas component.
- Tests typically provided ample gas, which masked potential issues with individual gas cost components.
- The scenario of having exactly enough gas for memory expansion but not for word copy cost was not explicitly tested.

### Steps Taken To Avoid Recurrence

- Added regression tests that use sub-calls with controlled gas limits to isolate specific gas cost components.
- Tests verify both the success case (sufficient gas) and failure case (insufficient gas for word copy cost).

### Implemented Test Case

- `tests/frontier/opcodes/test_data_copy_oog.py::test_calldatacopy_word_copy_oog`
- `tests/frontier/opcodes/test_data_copy_oog.py::test_codecopy_word_copy_oog`

### Framework/Documentation Changes

None required - the existing framework supported writing these tests.

---

## 2026-06 - Block Access List Storage Change Cardinality - Amsterdam

### Description

A stateless zkEVM client implementation was found to mishandle a single account that accumulates a large number of distinct storage changes in the block access list (EIP-7928). When preloading the transaction recipient's BAL storage keys, the client copied them into a fixed-size buffer sized for 16 slots with no bounds check. A transaction that wrote more than 16 distinct storage slots to one contract overflowed the buffer into adjacent state, corrupting the transaction's computed gas usage and therefore the block validity verdict.

The bug was latent against the existing test suite: no fixture exercised more than eight distinct storage changes for a single account, and those eight were spread one-per-transaction (`test_bal_cross_tx_storage_chain`), so the per-account, per-transaction storage-change cardinality never approached the buffer boundary.

### Root Cause Analysis

- Existing BAL storage tests focused on the correctness of recording, ordering, and the uniqueness rules for small numbers of slots; the high-cardinality case (many distinct slots for one account in one transaction) was implicitly assumed covered or low-risk.
- No fixture pushed a single account past a handful of storage changes, so fixed-size per-account buffers in client implementations were never stressed.
- The block access list is a new structure in EIP-7928, so client-side handling of large per-account storage-change lists had little prior fuzzing or property-based coverage.

### Steps Taken To Avoid Recurrence

- Added a parametrized regression test that writes many distinct, previously-zero storage slots (17, 32, and 128) to one contract in a single transaction and asserts the BAL records every slot, in ascending order, at a single block access index.

### Implemented Test Case

- `tests/amsterdam/eip7928_block_level_access_lists/test_block_access_lists.py::test_bal_many_storage_writes_single_account`

### Framework/Documentation Changes

None required - the existing framework supported writing these tests.

---

## 2026-06 - CALL Soft-Fail New-Account State-Gas Refund - Amsterdam

### Description

EIP-8037's specification text states that the new-account state gas charged for a `CALL*` is refilled to the `state_gas_reservoir` (and `execution_state_gas_used` decreases) when the operation is unsuccessful before entering the call frame (insufficient balance or stack depth), and it draws **no distinction** between `CALL*` and `CREATE`/`CREATE2`. The executable spec implemented this refund only for `CREATE`/`CREATE2` (`generic_create`); the `CALL` paths charged the new-account state gas and then retained it on the soft-fail. The mismatch was surfaced by external review (a testing/security discussion triaging an auto-hunt finding that flagged "CALL state gas not refunded on soft-fail"), not by the test suite.

### Root Cause Analysis

- The single existing test for the scenario (`test_call_insufficient_balance_returns_reservoir`) did not isolate the refund: for a fresh target it provisioned the reservoir with `sstore_state_gas + NEW_ACCOUNT`, so the follow-up `SSTORE` succeeded whether or not the new-account charge was refunded. The behavior was pinned only incidentally through the filled post-state root, never as an intent-named assertion.
- That test's docstring stated "the call fails before any state gas is charged for the target account", which described the EIP prose but contradicted both the executable spec (the charge happens before the balance check) and the test's own reservoir sizing. The contradiction masked the divergence during review.
- The `CALL*`-vs-`CREATE` symmetry asserted by the prose was assumed covered because both opcodes had insufficient-balance tests; no test compared their refund behavior directly.

### Steps Taken To Avoid Recurrence

- Aligned `call()`/`generic_call()` with the prose (refund the new-account state gas on the insufficient-balance and stack-depth soft-fails, symmetric with `CREATE`).
- Rewrote `test_call_insufficient_balance_returns_reservoir` so its docstring matches the behavior and its reservoir is sized to require the refund.
- Added an intent-named regression that reuses the refunded reservoir for a subsequent account-creating `CALL`, pinning the `CALL`/`CREATE` symmetry directly rather than incidentally.

### Implemented Test Case

- `tests/amsterdam/eip8037_state_creation_gas_cost_increase/test_state_gas_call.py::test_call_softfail_refund_reused_by_new_account_call`
- `tests/amsterdam/eip8037_state_creation_gas_cost_increase/test_state_gas_call.py::test_call_insufficient_balance_returns_reservoir`

### Framework/Documentation Changes

- None to the framework. This post-mortem entry documents the miss; the underlying EIP prose vs executable-spec divergence is flagged on the PR for the authors to confirm the intended direction.

---

## TEMPLATE

## Date - Title - Fork

### Description

Provide a concise summary of the issue, how it was discovered, emphasizing the how it relates to the specifications and testing.

*Example:*

> A consensus-breaking issue was found during the bug-bounty phase of the Pectra fork specifically in the EIP-2537, which involved calling the BLS pairing precompile using two special points: the infinity point and a point that is outside of the BLS12-381 curve.
> The specification correctly specified the behavior of the precompile when one of these inputs was used, but it did not specify the behavior of the combined input.

### Root Cause Analysis

Explain why this scenario was not covered by the test suite. Consider whether it was due to ambiguous specification wording, gaps in test generation logic, overlooked edge cases, or incorrect assumptions about expected behavior.

*Consider prompting questions:*

- Was the behavior implied but not explicitly stated in the specification?
- Was the area considered low-risk or assumed covered elsewhere?
- Were there limitations in the current test generation tools or processes?
- Was there any different type of testing that could have caught the issue at an earlier stage? (Fuzzing, property based testing)

### Steps Taken To Avoid Recurrence

List the actions taken to reduce the chance of this type of miss happening again. E.g. procedure changes, checklist updates, review practices, framework improvements.

### Implemented Test Case

IDs of the tests added that now cover the missed scenario and link to the documentation page where they are included.

*Example:*

- [`tests/prague/eip2537_bls_12_381_precompiles/test_bls12_g1msm.py::test_invalid\[fork_Prague-state_test---bls_g1_truncated_input-\]`](../tests/prague/eip2537_bls_12_381_precompiles/test_bls12_g1msm/test_invalid.md)

### Framework/Documentation Changes

Note any modifications that were introduced in the framework and/or documentation to prevent similar misses.

*Example:*

- Updated EIP checklist to include testing combinations of interesting points related to the elliptic-curve under test, and all combinations between them.
