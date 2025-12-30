# Grammar Check Subpaths

Status legend: `[ ]` pending, `[~]` in progress, `[x]` complete

---

## src/ethereum/forks - VM Instructions

- [x] `src/ethereum/forks/*/vm/instructions/arithmetic.py`, `comparison.py`, `bitwise.py` (~72 files)
- [x] `src/ethereum/forks/*/vm/instructions/block.py`, `environment.py`, `control_flow.py` (~72 files)
- [ ] `src/ethereum/forks/*/vm/instructions/keccak.py`, `log.py`, `memory.py`, `stack.py` (~96 files)
- [ ] `src/ethereum/forks/*/vm/instructions/storage.py`, `system.py`, `__init__.py` (~72 files)

## src/ethereum/forks - VM Core

- [ ] `src/ethereum/forks/*/vm/interpreter.py`, `runtime.py` (~48 files)
- [ ] `src/ethereum/forks/*/vm/gas.py`, `memory.py`, `stack.py`, `exceptions.py` (~96 files)
- [ ] `src/ethereum/forks/*/vm/__init__.py` (~24 files)

## src/ethereum/forks - Precompiled Contracts

- [ ] `src/ethereum/forks/*/vm/precompiled_contracts/__init__.py`, `mapping.py` (~48 files)
- [ ] `src/ethereum/forks/*/vm/precompiled_contracts/ecrecover.py`, `sha256.py`, `ripemd160.py`, `identity.py` (~96 files)
- [ ] `src/ethereum/forks/*/vm/precompiled_contracts/modexp.py`, `alt_bn128.py` (~38 files)
- [ ] `src/ethereum/forks/*/vm/precompiled_contracts/blake2f.py` (~17 files)
- [ ] `src/ethereum/forks/*/vm/precompiled_contracts/point_evaluation.py`, `p256verify.py` (~16 files)
- [ ] `src/ethereum/forks/*/vm/precompiled_contracts/bls12_381/*.py` (~32 files)

## src/ethereum/forks - Utils & State

- [ ] `src/ethereum/forks/*/utils/*.py` (~96 files)
- [ ] `src/ethereum/forks/*/trie.py`, `state.py` (~48 files)

## src/ethereum/forks - Blocks & Transactions

- [ ] `src/ethereum/forks/*/blocks.py`, `transactions.py`, `bloom.py` (~72 files)
- [ ] `src/ethereum/forks/*/__init__.py`, `fork.py`, `fork_types.py` (~72 files)

## src/ethereum/forks - Misc

- [ ] `src/ethereum/forks/*/exceptions.py`, `requests.py`, `vm/eoa_delegation.py`, `dao.py` (~40 files)

## src/ethereum (non-forks)

- [ ] `src/ethereum/*.py`, `src/ethereum/crypto/*.py`, `src/ethereum/utils/*.py` (~15 files)

## src/ethereum_spec_tools

- [ ] `src/ethereum_spec_tools/**/*.py` (~39 files)

## src/ethereum_optimized

- [ ] `src/ethereum_optimized/**/*.py` (~4 files)

---

## packages/testing - CLI Plugins

- [ ] `packages/testing/src/execution_testing/cli/pytest_commands/plugins/consume/**/*.py` (~32 files)
- [ ] `packages/testing/src/execution_testing/cli/pytest_commands/plugins/filler/**/*.py` (~27 files)
- [ ] `packages/testing/src/execution_testing/cli/pytest_commands/plugins/execute/**/*.py` (~21 files)
- [ ] `packages/testing/src/execution_testing/cli/pytest_commands/plugins/forks/**/*.py`, `shared/**/*.py`, `help/**/*.py` (~16 files)
- [ ] `packages/testing/src/execution_testing/cli/pytest_commands/plugins/*.py` (root plugins, ~6 files)

## packages/testing - CLI Core

- [ ] `packages/testing/src/execution_testing/cli/pytest_commands/*.py` (~10 files)
- [ ] `packages/testing/src/execution_testing/cli/gentest/**/*.py`, `fuzzer_bridge/**/*.py` (~15 files)
- [ ] `packages/testing/src/execution_testing/cli/eest/**/*.py`, `input/**/*.py`, `fillerconvert/**/*.py` (~15 files)
- [ ] `packages/testing/src/execution_testing/cli/*.py` (root cli files, ~15 files)
- [ ] `packages/testing/src/execution_testing/cli/tests/**/*.py` (~10 files)

## packages/testing - Core Modules

- [ ] `packages/testing/src/execution_testing/test_types/**/*.py` (~32 files)
- [ ] `packages/testing/src/execution_testing/specs/**/*.py` (~28 files)
- [ ] `packages/testing/src/execution_testing/fixtures/**/*.py` (~16 files)
- [ ] `packages/testing/src/execution_testing/client_clis/**/*.py` (~21 files)
- [ ] `packages/testing/src/execution_testing/base_types/**/*.py` (~15 files)
- [ ] `packages/testing/src/execution_testing/forks/**/*.py` (~13 files)
- [ ] `packages/testing/src/execution_testing/tools/**/*.py`, `exceptions/**/*.py` (~24 files)
- [ ] `packages/testing/src/execution_testing/vm/**/*.py`, `rpc/**/*.py`, `config/**/*.py` (~17 files)
- [ ] `packages/testing/src/execution_testing/logging/**/*.py`, `execution/**/*.py`, `checklists/**/*.py`, `benchmark/**/*.py` (~14 files)
- [ ] `packages/testing/src/execution_testing/*.py` (root files, ~2 files)

---

## tests

- [ ] `tests/static/**/*.py` (~75 files)
- [ ] `tests/unscheduled/**/*.py` (~73 files)
- [ ] `tests/prague/**/*.py` (~69 files)
- [ ] `tests/frontier/**/*.py` (~50 files)
- [ ] `tests/cancun/**/*.py` (~44 files)
- [ ] `tests/osaka/**/*.py` (~43 files)
- [ ] `tests/benchmark/**/*.py` (~36 files)
- [ ] `tests/json_infra/**/*.py` (~22 files)
- [ ] `tests/shanghai/**/*.py` (~19 files)
- [ ] `tests/byzantium/**/*.py` (~11 files)
- [ ] `tests/istanbul/**/*.py`, `berlin/**/*.py` (~18 files)
- [ ] `tests/constantinople/**/*.py`, `amsterdam/**/*.py` (~16 files)
- [ ] `tests/london/**/*.py`, `homestead/**/*.py`, `paris/**/*.py` (~17 files)
- [ ] `tests/*.py`, `tests/common/**/*.py`, `tests/evm_tools/**/*.py` (~5 files)

---

## docs

- [ ] `docs/running_tests/**/*.md` (~29 files)
- [ ] `docs/writing_tests/**/*.md` (~20 files)
- [ ] `docs/library/**/*.md` (~18 files)
- [ ] `docs/dev/**/*.md`, `docs/filling_tests/**/*.md`, `docs/getting_started/**/*.md` (~25 files)
- [ ] `docs/*.md` (root docs, ~5 files)

---

## Root Files

- [ ] `*.md`, `*.py` (README, CONTRIBUTING, LICENSE, vulture_whitelist.py, etc.) (~7 files)

---

## .github

- [ ] `.github/**/*.md` (~6 files)

---

## lists, scripts & docs/scripts

- [ ] `lists/**/*.py`, `scripts/**/*.py`, `docs/scripts/**/*.py` (~10 files)
