# EIP-8037 coverage evidence

Measured on 2026-09-04 against Amsterdam source revision
`e4a1fb6faf150425da9c1d9afb9005c2dd82eee3` (#3511), with the follow-up tests
in this directory. No execution-specification source changes are included.

From the repository root:

```sh
uv run --group test fill \
  tests/amsterdam/eip8037_state_creation_gas_cost_increase/ \
  --fork Amsterdam -n 4 --dist=loadgroup \
  --output .just/state-gas-followup/fixtures --clean \
  --cov=ethereum.forks.amsterdam --cov-branch \
  --cov-report=term \
  --cov-report=json:.just/state-gas-followup/coverage.json \
  --cov-report=html:.just/state-gas-followup/coverage
```

The run generated **2,049 fixture variants successfully**, including the
BPO2-to-Amsterdam transition. The follow-up adds 84 variants: 40 for system
calls, 36 for nonempty code-deposit transitions, and eight for header gas
validation (including valid controls).

The measured scope is the Amsterdam Python package, using only this EIP's
suite. Statement coverage is 2,859/3,814 (74.96%); branch coverage is
426/830 (51.33%). Coverage.py's combined statement/branch figure is 70.74%.
These percentages are not a measure of specification completeness.

| Source module | Statement coverage | Branch coverage |
| --- | ---: | ---: |
| `fork.py` | 64.43% | 35.58% |
| `vm/gas.py` | 96.20% | 76.47% |
| `vm/interpreter.py` | 97.99% | 92.11% |
| `vm/instructions/system.py` | 94.20% | 77.03% |
| `vm/instructions/storage.py` | 98.51% | 96.43% |
| `vm/eoa_delegation.py` | 92.08% | 83.33% |

Use the generated HTML/JSON reports to inspect specific uncovered lines.
The denominator includes behavior outside EIP-8037; this run does not replace
coverage from other EIP suites. Malformed-header fixtures describe rejection
expectations for a block-consuming client; generating them does not itself
prove that a client rejects those headers.

The system-call probes were also checked with two temporary implementation
mutations, both subsequently reverted:

- Moving 1,000 gas from the reservoir into execution while preserving the total
  caused all 24 selected entry-grant/reservoir fixture variants to fail.
- Capping system execution gas at the transaction cap caused all eight
  entry-grant fixture variants to fail.

The failures were mismatched observed gas or missing storage writes, not
collection errors. The unmodified implementation passes the suite. Fixture
consumption against an independent client is separate validation.
