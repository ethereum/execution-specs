# Enhance Ported Test

Future-proof and clean up a test under `tests/ported_static/`. These tests were
machine-ported from the legacy `ethereum/tests` static fillers (YAML/JSON) and
carry a lot of boilerplate, hardcoded values, and weak/incomplete post-state
checks. This skill is the ordered methodology for turning one into idiomatic,
robust Python.

This skill is a **living document**: it captures the cases we have validated so
far. Real tests will hit shapes not covered here — that is expected. When you
find one, solve it, then add the new case/step to this file.

## Goal

The end state is a test that **passes on every fork from its `valid_from`
onward** (not just the baseline), expresses its intent explicitly, and has no
fragile hardcoded constants. "Future-proof" = a later fork that re-prices gas,
adds state costs, or changes account rules should not silently break it.

## Core loop (subtractive)

Most of the work is **removing** boilerplate one piece at a time and proving the
test still passes after each removal:

1. **Baseline first.** Before touching anything, fill the test and confirm it is
   green: `uv run fill <path> --fork=<valid_from-fork> -q --clean`.
2. Make **one** change.
3. Fill again (same fast command). Green → keep, move on.
4. **Red → roll back that one change and analyze.** A break is information: it
   tells you the thing you removed was load-bearing. Understand *why* before
   deciding whether to keep it, replace it with a dynamic equivalent, or leave
   it. Never paste a new expected value just to make red go green without
   understanding the change (see "Re-pinning" below).

Do low-risk, independent removals in small batches if you like, but anything
that can plausibly interact (addresses, contracts, gas) goes **one at a time**
so a failure is attributable.

## Verification cadence

- **Iterating:** `--fork=<baseline>` (usually Cancun) — fast.
- **Checkpoint / done:** fill the whole `valid_from` range (omit `--fork`) so all
  deployed forks are exercised.
- **Probe the future fork:** explicitly `--fork Amsterdam` (or the latest fork
  that enables new EIPs). It may **pass**, or be **skipped** (`sss`) if it is
  outside the fillable range — either way you learn the true extent of your
  coverage. A gas/state-cost change there is the most likely future breakage.

## Ordered steps

Do them roughly in this order. Earlier steps unblock later ones (notably: max
out gas *before* strengthening post-state, so added opcodes don't hit a gas
ceiling).

### 1. Remove `env`
Delete the `Environment(...)` block, the `env=env` arg to `state_test`, and any
now-orphaned vars (`coinbase`) and the `Environment` import. The framework
supplies sensible defaults.
**Keep `env` only if** the post asserts on the coinbase/`fee_recipient` balance,
or the bytecode reads block fields (`NUMBER`, `TIMESTAMP`, `PREVRANDAO`,
`BASEFEE`, `GASLIMIT`, `COINBASE`). `fee_recipient=sender` alone is not a reason
to keep it.

### 2. Remove `gas_limit` from the transaction (if gas is not the subject)
This is the common case and belongs early. Omitting `gas_limit` maxes out the
gas the tx receives, so the body executes fully. See `write-test.md` "Transactions".
- **Remove it** when the test is about *behavior* and just needs to run to
  completion. This also lets you delete any per-fork gas band-aids (e.g.
  `fork.is_eip_enabled(8037)` budget bumps) and often the `fork` param itself.
- **Keep it** only for genuinely gas-sensitive tests (OOG boundaries,
  intrinsic-gas, code-deposit limits, or gas metering) — see step 9.
- Do **not** add a comment explaining the absence of `gas_limit`; omission is
  the default.

### 3. Remove hardcoded contract `nonce`
Drop `nonce=0` from `pre.deploy_contract(...)`. If a `compute_create_address(...,
nonce=N)` in the post depends on it, keep them consistent.

### 4. Remove hardcoded addresses (one contract at a time)
Two sub-cases:
- **Value discarded:** a `contract = Address(0x...)` literal that is immediately
  overwritten by `pre.deploy_contract(...)` (no `address=`). Just delete the
  literal; the deploy returns a `fill`-generated address.
- **Value passed to `address=`:** remove both the literal *and* the `address=`
  argument, per contract, filling after each.
- **No-op case:** `to=None` creation tests often have no hardcoded address at all
  (the created address is `compute_create_address(sender, nonce=0)`). Confirm by
  grepping for `Address(0x` / `address=`.
- **On break:** some bytecode hardcodes that address as a CALL/CREATE target (or
  the tx `to`/`data`). Thread the dynamic address through the caller and the tx
  entry point instead.

### 5. Remove easy boilerplate values
Independent and usually safe (batchable): `pre.fund_eoa(amount=...)` → `fund_eoa()`;
tx `value`; tx `data` when it is empty (`Bytes("")`); explicit gas price fields.
Keep any of these that the post actually checks or that triggers the behavior
under test.

### 6. (Parametrized tests) Analyze what the `data` parameter is
Look at `tx.data` / `tx.to`:
- **Scenario A — data is a target contract address:** the tx lands in a thin
  entry-point contract that just `CALL`s the address from calldata. Usually you
  can **delete the entry-point** and call the target directly, and the N targets
  are near-identical → replace N bytecode copies with a **dynamic generator**
  parameterized by the small difference.
- **Scenario B — data is initcode:** spotted by **`to=None`**. Decide whether
  running inside initcode is *required* by the test (e.g. the test is about
  initcode-context behavior, per its title/docstring) or just an artifact of the
  static-filler format (most common — then the logic can move to a normal
  deployed contract). If required, convert the `tx_data` array into an
  `initcode(d)` **generator function**: even when variants are genuinely
  different programs, the function form lets each branch be labeled by intent,
  surfacing the one thing that varies.

### 7. (Parametrized tests) Simplify `expect_entries_` / `resolve_expect_post`
**Precondition** (must all hold to collapse to a per-`d` form): every entry's
`network` is implied by `valid_from`, `gas`/`value` indexes are wildcards (`-1`),
and there is no `expect_exception`. Then the post is a pure function of `d`.
- Convert `expect_entries_` into a plain **list of `result` dicts indexed by
  `d`** — duplicating identical entries (e.g. data `[0,1]` → two slots) is fine
  and preferred; an explicit flat list is easiest to reason about.
- Cascade: delete the `resolve_expect_post` import, the `_exc` it returned, and
  the tx's `error=_exc`.
- **Optionally merge** the data-generator and the post-list into **one
  `if/elif/else` on `d`** that sets both `initcode` and `post` per case. This
  co-locates each case's bytecode with its expected state — the strongest
  readability win, and it tends to *reveal* incomplete verification. Use a final
  `else` so every branch binds both vars; declare `initcode: Bytecode` and
  `post: dict` above the switch. Prefer the array form when cases are many or
  the switch would be unwieldy; this is a judgment call.
- **Clean up the `parametrize` signature.** The ported `"d, g, v"` triple is
  usually overkill: once gas/value indexing is gone (steps 2/5), drop the unused
  `g`/`v` from both the `parametrize` and the function signature. Rename `d` to
  something meaningful and parametrize on that:
  - **String values** (e.g. `parametrize("opcode", ["calldataload",
    "calldatacopy", "codecopy"])`) read best when the cases are distinct
    programs; pytest derives the test ids straight from the strings (matching the
    old `id=`s), and the switch branches become `if opcode == "calldataload"`.
  - **`Op` values** (e.g. `parametrize("opcode", [Op.SLOAD, Op.TLOAD])`) are
    cleaner *only* when the opcode plugs directly into a shared bytecode template;
    avoid forcing it when each case needs structurally different code.
  - Drop the verbose `pytest.param(..., id=...)` wrapping when the bare values
    already give good ids.

### 8. Strengthen post-state verification
Co-locating bytecode and post (step 7) often exposes that the ported test barely
verifies anything. Improve coupling and observability:
- **Couple the expectation to the bytecode.** If a contract returns its own code
  (`CODECOPY`+`RETURN`), assert `code=initcode` instead of a hand-copied
  `bytes.fromhex(...)` — change the bytecode and the expectation follows.
- **Make no-op results observable.** Storing `0` is indistinguishable from not
  storing (and `storage={}` already asserts "all slots zero" — see
  `Storage.must_be_equal`). To genuinely prove a read returned zero, store a
  derived non-zero value (e.g. `Op.ADD(Op.CALLDATALOAD(0), 1)` → assert `1`).
- **Add a canary.** Write a distinctive non-zero sentinel to an extra slot as the
  *final* step (e.g. `Op.SSTORE(0x2, 0xC0DE)`), and assert it. If creation
  reverts or the code doesn't run to completion, the slot stays zero and the
  test fails loudly instead of silently passing on a coincidentally-matching
  (often empty) account.
- Adding `SSTORE`s costs gas — this is why step 2 (max out gas) comes first.

### 9. Introduce variables that encode relationships
Whenever a literal carries intent or two literals are logically linked, lift them
into named variables that express the *relationship*, not just the value. E.g.
`create_value = 0xB` fed to both `Op.CREATE(value=create_value, ...)` and the tx
`value=create_value - 1` documents an intentional off-by-one (insufficient
balance) and keeps the two coupled so a future edit can't desync them. Same idea
ties a `CREATE`'s `size` operand to the memory/gas math that depends on it.

### 10. (Gas-subject tests only) Replace hardcoded gas with dynamic calculation
For tests that genuinely assert a gas amount:
- Prefer the **`CodeGasMeasure`** helper over hand-rolled `GAS … SUB(@0, GAS)`
  framing: `CodeGasMeasure(code=<op>, extra_stack_items=N, sstore_key=K)`. It
  self-calibrates (subtracts its own `GAS` ops and `overhead_cost`) so the stored
  value is the opcode's real cost. `extra_stack_items` = items the measured code
  leaves on the stack (`CREATE`/`CALL` leave 1) — wrong value corrupts the
  result. `sstore_key` should match the slot the post asserts.
- **Decompose the constant empirically first** (throwaway script against the
  fork): pin each term to the known-good number, then assemble. Map terms to
  fork-derived helpers: opcode base+pushes → `bytecode.gas_cost(fork)`; memory
  growth → `fork.memory_expansion_gas_calculator()(new_bytes=, previous_bytes=)`;
  EIP-3860 init-code words → `fork.gas_costs().CODE_INIT_PER_WORD * ceil(size/32)`.
- Lift the opcode into a variable so you can call `.gas_cost` / `.regular_cost`
  / `.state_cost` on exactly the measured bytecode, and couple its operands to
  the gas inputs (step 9).
- **Error paths are tricky.** A failed `CREATE`/`CALL` still charges some costs
  (memory, init-code words) but forwards no gas — so the delta is gas-limit
  independent. Whether the *state* portion (EIP-8037) is charged on a failure
  path may be unverifiable until a fork enabling it is fillable; flag it.

## Re-pinning expected values

When a measurement rewrite (step 10) or bytecode change shifts a stored value,
the workflow is: change → `fill` → read the `KeyValueMismatchError` (`want … got
…`) → update the expected value to the `got` → `fill` again.
**Sanity gate:** the shift must be *small and explainable* (e.g. exactly the gas
of removed framing ops). A large or inexplicable jump means the rewrite changed
*what* is being measured — stop and investigate, don't just paste the number.

## `@manually-enhanced` markers

A docstring `@manually-enhanced: Do not overwrite` marks a deliberate prior fix.
Respect it by default. It may be removed only when a *better* enhancement makes
the workaround it documents obsolete (e.g. maxing out gas removes a per-fork gas
budget hack) — and only under explicit direction.

## Known gaps (extend me)

Not yet covered by a validated walkthrough; figure out and append when hit:
- Scenario-A (call-target) dedup into a dynamic generator — described but not yet
  exercised end-to-end here.
- Tests where `gas`/`value` parametrization indexes are non-trivial (so
  `resolve_expect_post` can't collapse to a simple `[d]`).
- Multi-block / `blockchain_test` ported tests.
- Confirming EIP-8037 error-path state-gas behavior once a fork enabling it fills.

## Finishing

When done, offer to run `/lint`. Note that pydantic coercion warnings
(`dict→Alloc/Storage`, `Bytecode→Bytes`, unfilled optional `Transaction` params)
are false positives from the type checker, not real issues.
