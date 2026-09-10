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
- Exception: use `blockchain_test` when the test needs more than one transaction (a `state_test` holds exactly one), more than one block (e.g. transaction-ordering or fork-transition tests), or calls a system contract: the state-test pre-alloc omits the predeploys a fork lists only in `pre_allocation_blockchain()`, so the `CALL` hits an empty account, "succeeds", and the test passes vacuously.
- Anti-pattern: wrapping one transaction in a `Block` to reach `blockchain_test`. A `state_test` can assert the transaction's gas used and receipt logs (the tx's `expected_receipt=TransactionReceipt(cumulative_gas_used=...)`), reserve state gas (the tx's `state_gas_reservoir=`), and other block-header fields (`blockchain_test_header_verify=Header(...)`) without it.
- If the framework cannot express what a test needs — a fork-derived parameter set, a protocol constant, a cost — add it to the framework (a `fork.*()` accessor, a mixin ClassVar, a covariant marker) instead of building it in the test. Importing a helper from a sibling `test_*.py` is the sign it belongs there.

## Pre-State Setup

- `pre.fund_eoa()` — create funded EOA, returns Address. Accepts `amount=`, `nonce=`. With `amount=0` nothing is added to the pre-alloc; you get a fresh, nonexistent address.
- `pre.deploy_contract(code=..., storage={...})` — deploy contract, returns Address
- Do not assign into `pre` directly. The one exception is overriding a predeploy's code, `pre[addr] = Account(...)` under `@pytest.mark.pre_alloc_mutable`: it replaces the whole account (storage gone, nonce 1) and skips the test in execute mode, so reserve it for scenarios a live chain cannot host.

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
- `Account(storage=...)` compares storage **exhaustively**: any slot you omit must be zero. Opt an omitted key out with `Storage.set_expect_any(key)`.

## Block Access Lists

Every Amsterdam+ fixture carries a BAL whether or not the test asserts one. An `expected_block_access_list=` is a fill-time check that the spec built the BAL you predicted, so write one when the access pattern is the point of the test or a known edge (a revert, a system call, a withdrawal, a self-destruct), not by default. When you do write one, pair it with a `post` witness: the BAL records access, not outcome, so a transaction that ran and failed still merges its touches and satisfies the expectation, and only `post` tells the two apart.

- Field semantics: a field left unset is not checked, `[]` asserts empty, and a non-empty list matches as an **ordered subsequence** (extra actual entries are skipped; yours must appear in order). `BalAccountExpectation()` with no field set raises; use `.empty()` for an account with no changes and `{address: None}` to assert an address is absent.
- Reads and created accounts survive a frame's revert; writes do not. A test that reverts after touching state still expects those touches, and a missing entry is not evidence the access never happened.
- Withdrawals and pre/post-execution system calls add entries no transaction accounts for (index `0` before, `len(txs) + 1` after). An expectation built only from the transaction list comes up short.

## Markers

- `@pytest.mark.valid_from("ForkName")` — **mandatory** on every test
- `@pytest.mark.valid_until("ForkName")` — test only valid up to a fork
- `@pytest.mark.with_all_tx_types` — parametrize across all tx types
- `@pytest.mark.with_all_call_opcodes` — parametrize CALL/CALLCODE/DELEGATECALL/STATICCALL
- `@pytest.mark.with_all_system_contracts`, `with_all_precompiles`, `with_all_system_contract_request_types` (yields the request *class* as `request_class`), … — parametrize over a fork-derived set; `selector=lambda value: ...` narrows any `with_all_*` marker
- `@pytest.mark.slow` — excluded by default in fill
- `@pytest.mark.exception_test` — marks tests expecting exceptions.
- A mark that only some cases earn goes on that case, `pytest.param(..., marks=...)`, not the function: `exception_test` on the function fails the passing cases, and a function-level `EIPChecklist` item stays green after the one case that proved it is deleted.

## Fork-Aware Logic

- Branch on `fork.is_eip_enabled(N)` for behaviour an EIP introduces; EIPs move between forks, so `fork >= Cancun` is only for facts about the fork itself
- `fork.fork_at(timestamp=...)` gives the fork active before/after a transition boundary
- For gas amounts, see **Gas Cost Expectations** below — prefer framework cost constructs over reading `fork.gas_costs()` constants directly

## Pinning Intent

Pinning is a necessity, not a nice-to-have. With thousands of tests nobody re-reads them to confirm they still fill for the reason they were written, so the pin is the only thing that notices when one stops.

- **Pin a value that is as close to unique to this case as possible.** It should hold under the rule the test is about and under no other plausible rule, so that a test drifting onto a different rule, or a fork changing which rule applies, fails `fill` instead of quietly producing a new fixture.
- **A pin that restates an input is not a pin.** `cumulative_gas_used` equal to the `gas_limit` the test itself set, a storage slot expected to be zero when zero is also the untouched value, an `Account.NONEXISTENT` that a mis-wired setup would produce anyway: each of these passes just as happily under the wrong behavior. Give the transaction slack above the boundary so the charged amount cannot equal the limit, pre-set the witness slot to a sentinel, and assert the created address you actually expect.
- **The pin has to bite at fill time.** EELS collapses distinctions clients keep apart — both intrinsic-gas rejections map to one error, for instance — so an expectation that only differs under `consume` does not protect the fixture. When the discriminating fact cannot appear in the fixture, assert the premise in the test body: a plain `assert` on which of two thresholds binds, or a helper asserting the preconditions its boundary rests on, fails the fill the moment the assumption stops holding.
- **Derive parameters from what the test asserts.** If a boundary is `len(slots) * COST`, compute it from the same `slots` the expectation checks, so the two cannot drift apart.
- **Pin block premises.** A block that must be exactly full asserts its `gas_used` with `header_verify=Header(...)`.
- **Make a mid-transaction value durable.** A `CALL` result, a `BALANCE`, `GAS` or `EXTCODESIZE` reading only exists while the code runs; `SSTORE` it into a witness slot and assert that slot in `post` (`Storage.store_next(expected)` builds the code and the expectation together).
- **Say which rule the pinned number comes from.** One short comment naming the rule lets the next reader tell a repricing from a regression.
- **Break it once.** After the test fills, mutate the setup so the behaviour under test cannot happen and confirm the fill fails for that reason; then restore it.

## Gas Cost Expectations

Never hand-reconstruct a gas amount by summing `fork.gas_costs()` constants (`NEW_ACCOUNT`, `CALL_VALUE`, `COLD_STORAGE_WRITE`, `VERY_LOW`, ...). Re-deriving the schedule duplicates the framework's own calculation and silently breaks when a future fork reprices. Instead:

- **Read the cost off the bytecode under test.** Set the relevant opcode metadata (`account_new`, `value_transfer`, `address_warm`, `key_warm`/`original_value`/`current_value`/`new_value`, `init_code_size`, `code_deposit_size`, `new_memory_size`, ...) and use `bytecode.gas_cost(fork)` (execution + state), `.execution_cost(fork)`, `.state_cost(fork)`, or `.refund(fork)`. Link the exact opcode to the behavior — e.g. `Op.SELFDESTRUCT(account_new=True).state_cost(fork)`.
- **Transaction-level costs:** `fork.transaction_intrinsic_cost_calculator()`; `fork.transaction_top_frame_state_gas(contract_creation=True)` for the created account's `NEW_ACCOUNT` (under EIP-2780 it is NOT part of the intrinsic — never subtract it from the intrinsic); `fork.transaction_data_floor_cost_calculator()` (pass `contract_creation=True` for a creation transaction — its floor is anchored on a create-shaped base and comes out 9000 gas low without it); `fork.call_value_stipend()`.
- **A gas-limit validity boundary pins one threshold, so name which one.** `fork.transaction_intrinsic_cost_calculator()` returns `max(standard_intrinsic, calldata_floor)`, and on a data-heavy transaction the floor wins by a wide margin. Compute both — `return_cost_deducted_prior_execution=True` for the standard cost, `fork.transaction_data_floor_cost_calculator()` for the floor — set the gas limit from the threshold under test, `assert` it is the greater of the two, and expect that threshold's rejection: `INTRINSIC_GAS_BELOW_FLOOR_GAS_COST` for the floor, `INTRINSIC_GAS_TOO_LOW` for the standard cost (see **Pinning Intent**: EELS maps both to one error, so only the `assert` protects the fixture).
- **A single bare opcode/schedule cost** (e.g. an account-access constant) comes from a metadata-only opcode: `Op.BALANCE.with_metadata(address_warm=False).gas_cost(fork)`.
- **Fork-transition / cross-fork comparisons:** evaluate the same bytecode or intrinsic at each fork (`before = fork.fork_at(timestamp=...)`, `after = ...`) and compare `before` vs `after` costs — do not compare raw schedule constants.
- **Do not add "self-check" asserts** that compare a framework-computed value against a `fork.gas_costs()` decomposition of the same fork; they add no coverage over the runtime behavior the test already exercises and only break on repricing.
- **Exception:** a test whose *subject* is a specific schedule value (e.g. a regression that an opcode's cost is unchanged) may compare a runtime measurement (`CodeGasMeasure`) against `fork.gas_costs().OPCODE_*`. Even then, never hardcode the literal value.

## Transactions

- Rule: omit `gas_limit`. It auto-fills so the transaction executes in full without running out of gas.
- Exception: set `gas_limit` explicitly for gas-sensitive tests (intrinsic-gas boundaries, OOG, code-deposit limits, or gas metering).
- Anti-pattern: the `gas_limit=fork.transaction_gas_limit_cap()` boilerplate is now redundant.
- A transaction that runs out of gas consumes exactly its `gas_limit`, so calling an `Om.OOG` contract pins a transaction's gas used to a chosen value without any cost arithmetic.

## Exception Testing

- Pass `error=TransactionException.INTRINSIC_GAS_TOO_LOW` to `Transaction`
- Common exceptions: `GAS_ALLOWANCE_EXCEEDED`, `NONCE_MISMATCH_TOO_LOW`, `INSUFFICIENT_ACCOUNT_FUNDS`
- Expect the one exception the spec names. A client that reports a different error first is a mapper fix on the client side, not a reason for `exception=[A, B]`.

## Test Organization

- Place tests in `tests/<fork>/eip<number>/` where `<fork>` is the fork that introduced the functionality
- Each EIP directory has `spec.py` with `ReferenceSpec(git_path=..., version=...)` and test files declaring `REFERENCE_SPEC_GIT_PATH` / `REFERENCE_SPEC_VERSION`. `version` is the EIP file's blob SHA (`gh api repos/ethereum/EIPs/contents/EIPS/eip-N.md --jq .sha`); `uv run check_eip_versions --until <Fork> <path>` flags stale pins.
- Put a scenario where it earns the most coverage. Before adding a test to a new EIP's module, look in the module that owns the mechanism for one that already runs the case and only needs tightened expectations or an `is_eip_enabled` branch, and amend it; write a new test in the new module only when the branches would cost more readability than the extra fork coverage buys.
- Use `conftest.py` for shared fixtures within an EIP directory

## Test Docstrings

- Keep the docstring to a short summary of the scenario and the rule it pins — a sentence or two.
- Do not narrate the implementation: parametrized cases, gas decompositions, and case-by-case outcome walkthroughs are already expressed by the code. Prose restating them goes stale when the test changes and adds review burden.
- State only what the code cannot show (e.g. why a boundary value is chosen). Prefer a short inline comment at the relevant line over growing the docstring.
- Never hardcode numeric gas values in docstrings; name the constants instead.

## Parametrization

- `@pytest.mark.parametrize("name", [pytest.param(val, id="label"), ...])` with descriptive `id=` strings
- Stack parametrize decorators for multiple dimensions
- Handle every parametrized case with an explicit `if`/`elif` and `else: raise ValueError(...)`; an `else` that is a real case silently absorbs values added later.
- Parametrize the dimensions that take different code paths in clients (warm/cold, empty/funded, same-tx/pre-deployed), not just the ones the spec names.
- **Cover the family, not just the instance.** Before fixing the subject of a test, ask whether it is one member of a set the framework already parametrizes: call opcodes, create opcodes, precompiles, system contracts, request classes, tx types. If so, use that `with_all_*` marker and narrow it with `selector=lambda value: ...` when only part of the set can reach the behaviour (only `CALL` and `CALLCODE` carry a value, so only they can fail a sender-balance check). The nearest test proving the same rule for one member usually already carries the marker, so read a model test's decorators and not just its body. If the family is real but no marker covers it, propose a covariant marker (`covariant_decorator` in `plugins/forks/forks.py`) rather than hand-writing the list in the test; framework surface lands in its own change.

## Unit Tests (execution_testing package)

Plain pytest. Tests are co-located with each module under `packages/testing/src/execution_testing/` in a sibling `tests/` directory. When adding a guardrail or validation, verify the tests fail without the change and pass with it.

## After Writing Tests

After writing or modifying tests, ask the user: "Would you like me to load the `/fill-tests` skill to verify the new tests fill correctly? (This loads an additional skill into context.)" If they agree, run `/fill-tests`, fill the new tests, then inspect the generated fixture JSON to verify the fixture contents match what the test intends.

## References

See `docs/writing_tests/` and `docs/writing_tests/opcode_metadata.md` for detailed documentation.
