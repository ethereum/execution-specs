---
name: EIP Implementation Tracker
about: Track specification and testing progress for an EIP
title: 'EIP-<eip-number> Implementation Tracker'
labels: A-spec-specs, A-spec-tests, C-eip, C-test
assignees: ''

---

## [EIP-<eip-number>](https://eips.ethereum.org/EIPS/eip-<eip-number>)

### Target Fork

**<fork>**

### Instructions

- [ ] Assign issue to EIP specification and testing owner(s).

> [!IMPORTANT]
> A specifications specialist and a testing specialist should ideally share ownership of the EIP.

- [ ] Add the issue to the target fork milestone if applicable (i.e., the EIP is at least in the [CFI stage](https://eips.ethereum.org/EIPS/eip-7723#considered-for-inclusion)).

#### Guidance for Marking Items Complete

An item should only be checked off once the EIP is considered *stable*. In this context, stable means:

- No major issues or ambiguities are still being uncovered in the specification or tests.
- There are no open discussion points awaiting resolution.
- Client implementations have been consistently passing the tests for at least a week.

It is ultimately up to the owners' discretion to decide when an item should be marked as complete, using this guidance as the basis for that decision.

In exceptional cases, an EIP may require changes after some items have been marked complete or even after the entire issue has been completed and closed. This can happen, for example, when significant design optimizations are identified and agreed upon in ACD, or when critical security issues surface and require updates to the specification or tests.

When this occurs, owners should either unmark the relevant checkboxes if the issue is still open, or create a new tracking issue for the modifications if the original issue had already been closed.

### Specification + Testing Status

- [ ] Testing complexity assessed and documented.
- [ ] Specification implementation merged to `eips/<fork>/eip-<eip-number>` *(skip if the fork branch merge below is already complete)*.
- [ ] Specification updates merged to the corresponding `forks/<fork>` branch.
- [ ] EIP updates proposed in case of architectural choices surfaced during implementation.
- [ ] Required testing framework modifications implemented.
- [ ] Test suite implemented.
- [ ] Full code coverage for all changes.
- [ ] No regressions or failures in tests from prior forks (including static tests).
- [ ] [Testing checklist](https://github.com/ethereum/execution-specs/blob/HEAD/docs/writing_tests/checklist_templates/eip_testing_checklist_template.md) complete.
- [ ] Hardening session completed.
- [ ] Benchmarking tests written and results documented.
- [ ] Ran tests using `execute` to ensure compatibility, and marked specific tests to be skipped when they cannot be executed on live networks.
- [ ] Added Mainnet-marked tests ([example test](https://github.com/ethereum/execution-specs/blob/2a6f9ee98ba7c0d04c7d523a0ea0ee8a98a5c418/tests/osaka/eip7939_count_leading_zeros/test_eip_mainnet.py)).

### Process Status

- [ ] Hive tests passing on at least two implementations.
- [ ] EIP included in a devnet.