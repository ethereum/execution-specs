# EIP-7981 coverage evidence

Measured on the local checklist branch after the recipient-cost regression
(`867aa5136f`). All 547 EIP-7981 fill cases pass, including activation
transitions. Each test implementation commit was independently filled and
passed `just static` before being committed.

## Reproduce

From the repository root:

```sh
COVERAGE_FILE=/tmp/eip7981-coverage uv run coverage run --branch \
  --source=ethereum.forks.amsterdam.transactions,execution_testing.forks.forks.eips.amsterdam.eip_7981,tests/amsterdam/eip7981_increase_access_list_cost \
  .venv/bin/fill tests/amsterdam/eip7981_increase_access_list_cost \
  --fork Amsterdam --output /tmp/eip7981-coverage-fixtures -q
COVERAGE_FILE=/tmp/eip7981-coverage uv run coverage json \
  -o /tmp/eip7981-coverage.json
uv run checklist tests/amsterdam/eip7981_increase_access_list_cost --eip 7981
```

Use a fresh output directory or `--clean` when repeating the fill. Coverage
starts before pytest imports the fork plugins; otherwise pytest-cov reports
already-imported class definitions as missed. The ordinary `fill --cov`
run was also performed and all test modules were fully covered.

## Measured statements

Line numbers refer to the measured source revision above. Fractions below
are statement coverage, not branch percentages or protocol-wide coverage.

| File | Covered statements | Missing lines |
| --- | --- | --- |
| `eip_7981.py` | 33/34 | 108 |
| `transactions.py` | 251/290 | 555, 570, 571, 572, 573, 574, 575, 576, 577, 578, 579, 580, 581, 583, 585, 623, 626, 630, 637, 639, 644, 650, 654, 663, 667, 812, 823, 842, 844, 855, 858, 881, 883, 888, 903, 909, 915, 921, 939 |
| `__init__.py` | 0/0 | None |
| `conftest.py` | 61/72 | 34, 37, 40, 41, 43, 58, 94, 95, 96, 103, 104 |
| `helpers.py` | 9/9 | None |
| `spec.py` | 4/4 | None |
| `test_access_list_cost.py` | 107/107 | None |
| `test_eip_mainnet.py` | 22/22 | None |
| `test_execution_gas.py` | 37/37 | None |
| `test_floor_boundary_exact_balance.py` | 29/29 | None |
| `test_fork_transition.py` | 96/96 | None |
| `test_transaction_validity.py` | 66/66 | None |

## Scope and missed lines

All EIP-7981 access-list accounting statements and the construction of the
intrinsic and floor costs in `calculate_intrinsic_cost` (lines 734-782)
are exercised. Both address/key token constants are also exercised.
Absent and empty lists, repeated entries and keys, all supported transaction
types, creation, recipient/value variants, and both gas-used branches are
represented. This satisfies the EIP-specific EELS line-coverage item;
it does not claim full coverage of all transaction rules in that module.

The remaining misses in EELS `transactions.py` are existing decoding,
validation and signature error paths outside the access-list surcharge.
Their coverage belongs to the tests for the corresponding transaction
rules, not duplicate EIP-7981 cases.

The testing-fork mixin's line 108 is its standalone floor-enforcement
return. Amsterdam's outer EIP-2780 calculator always requests the inner
intrinsic cost without floor enforcement, then enforces the complete
floor itself. This line is not reachable through the current Amsterdam
composition; runtime floor validity is covered through the outer method.

The shared `conftest.py` misses are unused fixture interfaces: the default
or bytecode recipient, the creation recipient branch, rejection of an
invalid fixture parameter, the default access-list fixture overridden by
parametrization, and explicit authorization-list override forms. Creation
and contract execution are exercised by direct transaction tests, rather
than these generic recipient fixture branches. No test-body statements
are missed. Adding consensus permutations solely to hit these fixture
branches would not exercise a new protocol behavior.

## Applicability and limits

The new-transaction-type template is excluded only for unchanged rules.
Its exact/insufficient gas limits, floor-above-intrinsic behavior and
creation items remain applicable to the existing repriced types. The
floor-above-intrinsic ID appears twice in the template for valid and
invalid outcomes; the exact-balance test covers both.

EIP-7981 introduces no new opcode, precompile, system contract, transaction
encoding, header/body field, execution request, blob limit, or block-level
constraint. Its refund rules are unchanged; separate refund/revert tests
check their interaction with the surcharge.

Optional second-client line instrumentation is deferred. Functional
validation on every client through both consume modes, and latest-devnet
execute validation, remain separate open tasks. Neither checklist
completion nor a successful EELS fill establishes those results.
