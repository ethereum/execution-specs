---
name: write-test
description: Write consensus tests using repository patterns and fixtures.
---

# Write Test

Conventions and patterns for writing consensus tests. Run this skill before writing or modifying tests.

## Test Structure

- All test imports come from `execution_testing` — it is the public API
- Core fixtures: `pre: Alloc` (pre-state builder), `state_test: StateTestFiller`, `blockchain_test: BlockchainTestFiller`, `fork: Fork`
- Rule: use `state_test` for single-transaction tests; `fill` auto-derives a `blockchain_test` from each, so no coverage is lost.
- Exception: use `blockchain_test` when the test needs more than one transaction (a `state_test` holds exactly one) or more than one block (e.g. transaction-ordering or fork-transition tests).
- Anti-pattern: wrapping one transaction in a `Block` to reach `blockchain_test`. A `state_test` can assert the transaction's gas used and receipt logs (the tx's `expected_receipt=TransactionReceipt(cumulative_gas_used=...)`), reserve state gas (the tx's `state_gas_reservoir=`), and other block-header fields (`blockchain_test_header_verify=Header(...)`) without it.

## Pre-State Setup

- `pre.fund_eoa()` — create funded EOA, returns Address. Accepts `amount=`, `nonce=`
- `pre.deploy_contract(code=..., storage={...})` — deploy contract, returns Address
- Anti-pattern: do NOT manipulate `pre` dict directly (`pre[addr] = Account(...)`)

## Bytecode Construction

- `Op.SSTORE(key, value)`, `Op.CALL(gas, addr, ...)`, etc. — concatenate with `+`
- `Op.PUSH32(val) + Op.PUSH32(val) + Op.EXP` for stack setup
- Macros: `Om.OOG` (consumes all gas), `Om.MSTORE(data, offset)` (arbitrary-length memory store)
- Metadata on opcodes for gas calculation: `Op.BALANCE(address=0x1234, address_warm=True)`, `Op.SSTORE(key=1, value=0, key_warm=True, original_value=1, new_value=0)` — see `docs/writing_tests/opcode_metadata.md`
- `bytecode.gas_cost(fork)` — calculates exact gas for a bytecode sequence using opcode metadata. Use this instead of manually computing gas

## Storage Helpers

- `storage = Storage()` then `storage.store_next(expected_value)` — auto-increments slot
- `Op.SSTORE(storage.store_next(sender), Op.ORIGIN)` — build bytecode + expected storage in one step
- Post-state: `post = {contract: Account(storage=storage)}`

## Markers

- `@pytest.mark.valid_from("ForkName")` — **mandatory** on every test
- `@pytest.mark.valid_until("ForkName")` — test only valid up to a fork
- `@pytest.mark.with_all_tx_types` — parametrize across all tx types
- `@pytest.mark.with_all_call_opcodes` — parametrize CALL/CALLCODE/DELEGATECALL/STATICCALL
- `@pytest.mark.with_all_evm_code_types` — parametrize across EVM code types
- `@pytest.mark.slow` — excluded by default in fill
- `@pytest.mark.exception_test` — marks tests expecting exceptions

## Fork-Aware Logic

- `fork >= Cancun` for conditional behavior based on fork
- `fork.fork_at(timestamp=...)` gives the fork active before/after a transition boundary
- For gas amounts, see **Gas Cost Expectations** below — prefer framework cost constructs over reading `fork.gas_costs()` constants directly

## Gas Cost Expectations

Never hand-reconstruct a gas amount by summing `fork.gas_costs()` constants (`NEW_ACCOUNT`, `CALL_VALUE`, `COLD_STORAGE_WRITE`, `VERY_LOW`, ...). Re-deriving the schedule duplicates the framework's own calculation and silently breaks when a future fork reprices. Instead:

- **Read the cost off the bytecode under test.** Set the relevant opcode metadata (`account_new`, `value_transfer`, `address_warm`, `key_warm`/`original_value`/`current_value`/`new_value`, `init_code_size`, `code_deposit_size`, `new_memory_size`, ...) and use `bytecode.gas_cost(fork)` (execution + state), `.execution_cost(fork)`, `.state_cost(fork)`, or `.refund(fork)`. Link the exact opcode to the behavior — e.g. `Op.SELFDESTRUCT(account_new=True).state_cost(fork)`.
- **Transaction-level costs:** `fork.transaction_intrinsic_cost_calculator()`; `fork.transaction_top_frame_state_gas(contract_creation=True)` for the created account's `NEW_ACCOUNT` (under EIP-2780 it is NOT part of the intrinsic — never subtract it from the intrinsic); `fork.transaction_data_floor_cost_calculator()`; `fork.call_value_stipend()`.
- **A single bare opcode/schedule cost** (e.g. an account-access constant) comes from a metadata-only opcode: `Op.BALANCE.with_metadata(address_warm=False).gas_cost(fork)`.
- **Fork-transition / cross-fork comparisons:** evaluate the same bytecode or intrinsic at each fork (`before = fork.fork_at(timestamp=...)`, `after = ...`) and compare `before` vs `after` costs — do not compare raw schedule constants.
- **Do not add "self-check" asserts** that compare a framework-computed value against a `fork.gas_costs()` decomposition of the same fork; they add no coverage over the runtime behavior the test already exercises and only break on repricing.
- **If the framework cannot express a cost, fix the framework** (wire the opcode into its gas/state map, add an accessor) rather than reconstructing it in the test. If the use case does not support the framework, the framework needs an update.
- **Exception:** a test whose *subject* is a specific schedule value (e.g. a regression that an opcode's cost is unchanged) may compare a runtime measurement (`CodeGasMeasure`) against `fork.gas_costs().OPCODE_*`. Even then, never hardcode the literal value.

## Transactions

- Rule: omit `gas_limit`. It auto-fills so the transaction executes in full without running out of gas.
- Exception: set `gas_limit` explicitly for gas-sensitive tests (intrinsic-gas boundaries, OOG, code-deposit limits, or gas metering).
- Anti-pattern: the `gas_limit=fork.transaction_gas_limit_cap()` boilerplate is now redundant.

## Exception Testing

- Pass `error=TransactionException.INTRINSIC_GAS_TOO_LOW` to `Transaction`
- Common exceptions: `GAS_ALLOWANCE_EXCEEDED`, `NONCE_MISMATCH_TOO_LOW`, `INSUFFICIENT_ACCOUNT_FUNDS`

## Test Organization

- Place tests in `tests/<fork>/eip<number>/` where `<fork>` is the fork that introduced the functionality
- Each EIP directory has `spec.py` with `ReferenceSpec(git_path=..., version=...)` and test files declaring `REFERENCE_SPEC_GIT_PATH` / `REFERENCE_SPEC_VERSION`
- Use `conftest.py` for shared fixtures within an EIP directory

## Test Docstrings

- Keep the docstring to a short summary of the scenario and the rule it pins — a sentence or two.
- Do not narrate the implementation: parametrized cases, gas decompositions, and case-by-case outcome walkthroughs are already expressed by the code. Prose restating them goes stale when the test changes and adds review burden.
- State only what the code cannot show (e.g. why a boundary value is chosen). Prefer a short inline comment at the relevant line over growing the docstring.
- Never hardcode numeric gas values in docstrings; name the constants instead.

## Parametrization

- `@pytest.mark.parametrize("name", [pytest.param(val, id="label"), ...])` with descriptive `id=` strings
- Stack parametrize decorators for multiple dimensions

## Unit Tests (execution_testing package)

Plain pytest. Tests are co-located with each module under `packages/testing/src/execution_testing/` in a sibling `tests/` directory. When adding a guardrail or validation, verify the tests fail without the change and pass with it.

## After Writing Tests

After writing or modifying tests, ask the user: "Would you like me to load the `/fill-tests` skill to verify the new tests fill correctly? (This loads an additional skill into context.)" If they agree, run `/fill-tests`, fill the new tests, then inspect the generated fixture JSON to verify the fixture contents match what the test intends.

## References

See `docs/writing_tests/` and `docs/writing_tests/opcode_metadata.md` for detailed documentation.
