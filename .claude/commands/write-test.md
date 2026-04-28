# Write Test

Conventions and patterns for writing consensus tests. Run this skill before writing or modifying tests.

## Test Structure

- All test imports come from `execution_testing` — it is the public API
- Core fixtures: `pre: Alloc` (pre-state builder), `state_test: StateTestFiller`, `blockchain_test: BlockchainTestFiller`, `fork: Fork`
- Prefer `state_test` for single-tx tests (simpler, avoids block-building false positives); `fill` auto-generates a `blockchain_test` from every `state_test`
- Use `blockchain_test` only for multi-block scenarios

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
- `fork.gas_costs()` returns `GasCosts` dataclass with constants like `G_WARM_SLOAD`, `G_COLD_ACCOUNT_ACCESS`, `G_BASE`, etc.
- `fork.transaction_intrinsic_cost_calculator()` for computing tx intrinsic gas

## Exception Testing

- Pass `error=TransactionException.INTRINSIC_GAS_TOO_LOW` to `Transaction`
- Common exceptions: `GAS_ALLOWANCE_EXCEEDED`, `NONCE_MISMATCH_TOO_LOW`, `INSUFFICIENT_ACCOUNT_FUNDS`

## Test Organization

- Place tests in `tests/<fork>/eip<number>/` where `<fork>` is the fork that introduced the functionality
- Each EIP directory has `spec.py` with `ReferenceSpec(git_path=..., version=...)` and test files declaring `REFERENCE_SPEC_GIT_PATH` / `REFERENCE_SPEC_VERSION`
- Use `conftest.py` for shared fixtures within an EIP directory

## Parametrization

- `@pytest.mark.parametrize("name", [pytest.param(val, id="label"), ...])` with descriptive `id=` strings
- Stack parametrize decorators for multiple dimensions

## Unit Tests (execution_testing package)

Plain pytest. Tests are co-located with each module under `packages/testing/src/execution_testing/` in a sibling `tests/` directory. When adding a guardrail or validation, verify the tests fail without the change and pass with it.

## After Writing Tests

After writing or modifying tests, ask the user: "Would you like me to load the `/fill-tests` skill to verify the new tests fill correctly? (This loads an additional skill into context.)" If they agree, run `/fill-tests`, fill the new tests, then inspect the generated fixture JSON to verify the fixture contents match what the test intends.

## References

See `docs/writing_tests/` and `docs/writing_tests/opcode_metadata.md` for detailed documentation.
