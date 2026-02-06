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

## Completed Examples

Reference these for patterns:

- `tests/prague/eip7702_set_code_tx/` — comprehensive checklist for a transaction type EIP
- `tests/osaka/eip7951_p256verify_precompiles/` — precompile checklist example

## References

See `docs/writing_tests/checklist_templates/` for templates and detailed documentation.
