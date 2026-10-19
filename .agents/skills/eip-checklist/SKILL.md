---
name: eip-checklist
description: Track EIP test coverage with the repository checklist system.
---

# EIP Checklist

Guide for using the EIP testing checklist system to track test coverage. Run this skill when working on EIP test coverage or checklists.

## What It Is

The `EIPChecklist` class (in `execution_testing.checklists.eip_checklist`) provides a hierarchical marker system for tagging tests with what aspect of an EIP they cover. Categories include:

- `General`, `Opcode`, `Precompile`, `SystemContract`, `TransactionType`
- `BlockHeaderField`, `BlockBodyField`, `GasCostChanges`, `GasRefundsChanges`
- `ExecutionLayerRequest`, `BlobCountChanges`

Each category has deep sub-items (e.g., `EIPChecklist.Opcode.Test.GasUsage.Normal`).

## Usage in Tests

```python
@EIPChecklist.TransactionType.Test.IntrinsicValidity.GasLimit.Exact()
def test_exact_intrinsic_gas(state_test: StateTestFiller):
    ...

# Multi-EIP coverage:
@EIPChecklist.TransactionType.Test.Signature.Invalid.V.Two(eip=[2930])
def test_invalid_v(state_test: StateTestFiller):
    ...
```

## Generating Checklists

Run `uv run checklist` to generate coverage reports. Template at `docs/writing_tests/checklist_templates/eip_testing_checklist_template.md`.

## Marking Items as Externally Covered or N/A

Create `eip_checklist_external_coverage.txt` in the EIP test directory:

```
general/code_coverage/eels = Covered by EELS test suite
```

Create `eip_checklist_not_applicable.txt` for inapplicable items:

```
system_contract = EIP-7702 does not introduce a system contract
precompile/ = EIP-7702 does not introduce a precompile
```

(trailing `/` marks entire category as N/A)

## Code Coverage Items

`general/code_coverage/missed_lines` claims that every remaining miss is acceptable; it is not a place to park gaps.

- Measure branches: `uv run fill --cov=ethereum --cov-branch --cov-report=term-missing <eip test dir> --until <Fork>`. A line report counts an `if` whose false path never ran as covered, and without `--until` a fork under development fills nothing. Before calling a miss uncovered, rerun it against every suite that can reach that code.
- A missed branch is a test to write. Only two kinds of miss are acceptable: code that runs only outside `fill` (such as block validation in `fork.py`, run by `just json-loader`), and code the spec makes unreachable.
- An unreachable claim cites the guard that rules the branch out and a construction that was tried and failed, ideally by a second person or agent. "Nothing on mainnet does this" is not a reason while custom predeploy code (`pre_alloc_mutable`) or a crafted transaction reaches the branch at fill time.
- The entry lists only what is still missed, why, and a re-verify command that has been run as written; never covered branches or test names, which go stale. Re-derive the entry whenever the code it reasons about changes.

## Completed Examples

Reference these for patterns:

- `tests/prague/eip7702_set_code_tx/` — comprehensive checklist for a transaction type EIP
- `tests/osaka/eip7951_p256verify_precompiles/` — precompile checklist example

## References

See `docs/writing_tests/checklist_templates/` for templates and detailed documentation.
