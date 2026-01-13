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

- [`tests/prague/eip2537_bls_12_381_precompiles/test_bls12_g1msm.py::test_invalid\[fork_Prague-state_test---bls_g1_truncated_input-\]`](https://eest.ethereum.org/main/tests/prague/eip2537_bls_12_381_precompiles/test_bls12_g1msm/test_invalid/)

### Framework/Documentation Changes

Note any modifications that were introduced in the framework and/or documentation to prevent similar misses.

*Example:*

- Updated EIP checklist to include testing combinations of interesting points related to the elliptic-curve under test, and all combinations between them.
