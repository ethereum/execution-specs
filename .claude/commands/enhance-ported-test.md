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
  that enables new EIPs). A ported test listed in `amsterdam_skip_list.txt` will
  always show `sss` there — to see its *real* behavior, temporarily remove its
  entry from that file, fill, then restore (or, once fixed, remove it for good —
  see Finishing). A gas/state-cost change there is the most likely future
  breakage.
- **`fill` output:** writes to `./fixtures` (`--clean` resets it), or pass
  `--output <dir>` for a scratch location. Do **not** use `-o` — that is
  pytest's `--override-ini`, not the output dir.

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
  intrinsic-gas, code-deposit limits, or gas metering) — see step 10.
- **Gas-snapshot tests are gas-sensitive.** If the post asserts a stored `GAS`
  reading or a `SUB(@gas_before, GAS)` delta (legacy slots `0` / `0x64`), the
  test *measures gas* — handle it under step 10 (preserve via `CodeGasMeasure`),
  do not just strip `gas_limit`. This is the dominant `amsterdam_skip_list.txt`
  shape: the stored gas value is exactly what EIP-8037 re-prices and breaks.
- **EIP-8037 caveat:** when you omit `gas_limit` on a test that *measures* an
  operation incurring **state gas** (account creation, storage writes), add
  `state_gas_reservoir=0` to the tx, or that state gas is silently dropped from
  the measurement on EIP-8037 forks (see step 10). Pure-execution opcodes
  (e.g. `PUSH0`, arithmetic) have no state gas and do not need it.
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
- **Self-reference:** a contract that hardcodes its *own* deploy address (e.g.
  `Op.BALANCE(0xF172…)` where `0xF172…` is its own `address=`). Threading a
  `fill`-generated address in is impossible (chicken-and-egg), so replace the
  self-reference with the opcode that yields it at runtime — `Op.BALANCE(Op.
  ADDRESS)`. Don't substitute a *different* opcode that happens to be shorter
  (e.g. `Op.SELFBALANCE`) if it changes what the test exercises.
- **Remove `@pytest.mark.pre_alloc_mutable`** once the test no longer hardcodes
  addresses/nonces or assigns `pre[...]` directly — i.e. all allocation now goes
  through `fund_eoa` / `deploy_contract` / `nonexistent_account`. Fill to confirm.

### 5. Remove easy boilerplate values
Independent and usually safe (batchable): `pre.fund_eoa(amount=...)` → `fund_eoa()`;
tx `value`; tx `data` when it is empty (`Bytes("")`); explicit gas price fields.
Keep any of these that the post actually checks or that triggers the behavior
under test.
- **Drop opcode args that just pass their default.** Ported bytecode often spells
  out zero operands that are already the default, e.g. `Op.CALL(..., args_offset=0,
  args_size=0, ret_offset=0, ret_size=0)` — all four are `0` by default. Removing
  them is a no-op on the assembled bytecode (verify once with
  `bytes(a) == bytes(b)`) and cuts noise. Applies to any opcode arg equal to its
  default.
- **Drop a stale `# noqa: F841`** on `contract = pre.deploy_contract(...)` once the
  variable is actually used (in `to=` / the post); leaving it triggers `RUF100`.

### 6. (Parametrized tests) Analyze what the `data` parameter is
Look at `tx.data` / `tx.to`:
- **Scenario A — data is a target contract address:** the tx lands in a thin
  entry-point contract that just `CALL`s the address from calldata. Usually you
  can **delete the entry-point** and call the target directly, and the N targets
  are near-identical → replace N bytecode copies with a **dynamic generator**
  parameterized by the small difference. When the targets are *gas-measurement*
  contracts differing only by the measured opcode, the dedup collapses all the
  way to a single `CodeGasMeasure(code=opcode)` parametrized on the opcode
  (step 10) — the entry-point's `CALL` was only a delivery mechanism. Validated
  on `test_push0_gas2` (PUSH0 vs PUSH1 0x00).
- **Scenario B — data is initcode:** spotted by **`to=None`**. Decide whether
  running inside initcode is *required* by the test (e.g. the test is about
  initcode-context behavior, per its title/docstring) or just an artifact of the
  static-filler format (most common — then the logic can move to a normal
  deployed contract). If required, convert the `tx_data` array into an
  `initcode(d)` **generator function**: even when variants are genuinely
  different programs, the function form lets each branch be labeled by intent,
  surfacing the one thing that varies.

### 7. (Parametrized tests) Simplify `expect_entries_` / `resolve_expect_post`
**First, identify which index actually discriminates — it is *not* always `d`.**
Ported tests also key on `g` (gas) or `v` (value); check both the
`expect_entries_` `indexes` (which axis is non-`-1`) and which of
`tx_data[d]`/`tx_gas[g]`/`tx_value[v]` is the list with >1 entry. The other two
indexes are pinned/wildcard. (Example: `test_add_non_const` varies `v` —
`d`/`g` are fixed at 0 and the `indexes` match on `"value"`.)
**Precondition** (to collapse to a per-case form): every entry's `network` is
implied by `valid_from` and there is no `expect_exception`. Then the post is a
pure function of the discriminating index.
- Convert `expect_entries_` into a plain **list of `result` dicts indexed by the
  discriminator** — duplicating identical entries (e.g. data `[0,1]` → two
  slots) is fine and preferred; an explicit flat list is easiest to reason about.
- **When the discriminator is a real quantity** (the tx `value` or `gas`),
  parametrize *directly on that quantity* (`parametrize("tx_value", [0, 1])`)
  rather than an opaque index, feed it straight into the `Transaction`, and
  express the post as a function of it. A clean closed form is ideal —
  e.g. `Account(storage={0: 2 * tx_value})` for a contract that stores
  `ADD(BALANCE, BALANCE)` of a balance equal to the sent value (this is the
  "encode relationships" idea from step 9 applied to the post).
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
  usually overkill: drop the pinned/unused indexes from both the `parametrize`
  and the function signature, keep the discriminator, and rename it to something
  meaningful (and `fork` too, if no longer used). Parametrize on the renamed axis:
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
- **Post-state derived from gas/fees.** When the asserted value is a function of
  the gas charge (e.g. an origin `BALANCE` read mid-execution equals
  `sender_balance - gas_limit * effective_gas_price`), express it as that formula
  rather than a hardcoded number. Such a test is gas-sensitive — keep an explicit
  `gas_limit` (step 10), since the observable depends on it. Validated on
  `test_sender_balance` (EIP-1559 effective-vs-max price).

### 10. (Gas-subject / gas-snapshot tests) Replace hardcoded gas with dynamic calculation
Covers both tests that *assert* a gas amount and the dominant
`amsterdam_skip_list.txt` shape: a legacy `GAS` snapshot / `SUB(@gas_before,
GAS)` delta stored to slot `0`/`0x64`. That stored value is *why* EIP-8037
breaks the test, but it is real coverage — **preserve and fork-robustify it, do
not drop it.**

**The `CodeGasMeasure` workflow:**
- **Isolate** the bytecode under measurement into a variable
  (`call_code = Op.CALL(...)`). This often reveals the legacy measured window
  bundled extra ops — e.g. it wrapped an `SSTORE`, inflating the value by a cold
  `SSTORE` (~22100). Isolating the opcode measures only it (a large but
  *explainable* re-pin — see Re-pinning).
- **Wrap** it: `CodeGasMeasure(code=call_code, extra_stack_items=N, sstore_key=K)`.
  It self-calibrates (subtracts its own `GAS` ops and `overhead_cost`) so the
  stored value is the opcode's real cost. `extra_stack_items` = items the
  measured code leaves on the stack (`CREATE`/`CALL` leave 1) — wrong value
  corrupts the result. `sstore_key` = the slot the post asserts.
- **Apply opcode metadata from the test's context** so `gas_cost(fork)` is
  correct (see `docs/writing_tests/opcode_metadata.md`). For `CALL`:
  `address_warm` (is the target pre-accessed?), `value_transfer` (value > 0?),
  `account_new` (target absent/empty and receiving value → created?). Use
  `pre.nonexistent_account()` for a target that must stay **cold + non-existent**
  so `account_new` holds — a `fund_eoa()` target already exists (warm/created) and
  would change the cost.
- **Express the expected value dynamically** from the same metadata-bearing
  variable: `call_code.gas_cost(fork)` (add `fork: Fork`). Both the bytecode and
  the expectation are now fork-aware.

**CALL value-transfer stipend.** A value-bearing `CALL` whose callee consumes
nothing (empty account / EOA) measures `gas_cost(fork) -
fork.gas_costs().CALL_STIPEND`: `gas_cost` counts the full value cost, but the
2300 stipend is forwarded to the callee and returned unused. Confirm the
`- CALL_STIPEND` holds on *every* fork (it is a fork-stable relationship, not a
coincidence).

**EIP-8037 state-gas reservoir — critical.** Omitting `gas_limit` (step 2) on an
EIP-8037 fork *maxes the state-gas reservoir*, so state gas (e.g. account
creation) is **not** charged against what the `GAS` opcode sees — the measurement
silently loses it (observed 192921 → 9321) and only the future fork breaks. Fix:
keep `gas_limit` omitted **and** add an explicit `state_gas_reservoir=0` to the
`Transaction`. That pins the gas limit to exactly the cap (no reservoir) so state
gas is charged and measurable, and is a no-op on pre-EIP-8037 forks (a *positive*
reservoir there raises; `0` does not, and it must be set explicitly — the default
is treated as "unset"). This keeps a `CodeGasMeasure` test clean (no magic
`gas_limit`) yet correct on Amsterdam.

**Decompose the constant empirically** when no single helper applies (throwaway
script against the fork): pin each term to the known-good number, then assemble.
Map terms to fork-derived helpers: opcode base+pushes → `bytecode.gas_cost(fork)`;
memory growth → `fork.memory_expansion_gas_calculator()(new_bytes=,
previous_bytes=)`; EIP-3860 init-code words → `fork.gas_costs().CODE_INIT_PER_WORD
* ceil(size/32)`. You can also call `.gas_cost` / `.regular_cost` / `.state_cost`
on exactly the measured bytecode.

**Nested / callee-side measurements.** When the measured op is a `CALL` whose
callee does real work, the measured cost = `call_code.gas_cost(fork) +
callee_code.gas_cost(fork)` (the CALL's own cost plus what the callee consumed).
Attach the callee's opcode metadata (e.g. SSTORE `key_warm`/`original_value`/
`new_value`) so its `gas_cost` is right, and decompose against the callee's
*actual* bytecode rather than a reconstruction — a value supplied by `GAS` costs
2, not a `PUSH`'s 3, and that off-by-3 is a real trap. A callee-side gas snapshot
(`SSTORE(k, GAS)`) stores `forward_gas - Op.GAS.gas_cost(fork)`. Forward enough
gas that the callee's state op commits on every fork — under EIP-8037 a cold
zero->non-zero SSTORE can cost ~100k — and set `state_gas_reservoir=0` so that
state gas is captured. Validated on `test_raw_call_gas`.

**Error paths are tricky.** A failed `CREATE`/`CALL` still charges some costs
(memory, init-code words) but forwards no gas — so the delta is gas-limit
independent. Whether the *state* portion (EIP-8037) is charged on a failure path
may be unverifiable until confirmed; flag it.

### 11. Lower `valid_from` to extend coverage
The ported `valid_from` (often `Cancun`) is usually higher than necessary — lower
it to widen coverage. Find the true floor empirically: temporarily delete the
`valid_from` marker and fill with no `--fork` (the framework then runs from
Frontier up); the earliest fork that *passes* is your floor. Set
`@pytest.mark.valid_from("<that fork>")` — the marker is mandatory, so this is a
lowering, never a true removal.
- **Gas tests floor at the EIP that introduced their metadata.** A test using
  `address_warm` / cold-access metadata + `gas_cost(fork)` is only valid from
  **Berlin (EIP-2929)**: earlier forks have no warm/cold distinction, so
  `gas_cost` over-predicts by `cold − flat` (2600 − 700 = 1900) and every
  pre-Berlin fork fails the measurement. Same shape elsewhere — EIP-3860
  init-code metering floors at Shanghai, etc. The floor is whichever EIP the
  test's behavior/metadata depends on, which the empirical sweep reveals directly.

## Re-pinning expected values

When a measurement rewrite (step 10) or bytecode change shifts a stored value,
the workflow is: change → `fill` → read the `KeyValueMismatchError` (`want … got
…`) → update the expected value to the `got` → `fill` again.
**Sanity gate:** the shift must be *explainable* — either small (the gas of
removed framing ops) or large-but-precisely-accounted (e.g. isolating an opcode
in `CodeGasMeasure` drops a cold `SSTORE` ~22100 the legacy window had bundled).
A jump you cannot account for means the rewrite changed *what* is being measured
— stop and investigate, don't just paste the number.

## `@manually-enhanced` markers

A docstring `@manually-enhanced: Do not overwrite` marks a deliberate prior fix.
Respect it by default. It may be removed only when a *better* enhancement makes
the workaround it documents obsolete (e.g. maxing out gas removes a per-fork gas
budget hack) — and only under explicit direction.
**Add the marker as the closing step** once a test's enhancements are intentional
(genuinely-verifying post, dynamic addresses/gas) so future auto-porting won't
regress them; briefly state what was enhanced. Place it in the **module
docstring**, after the `Ported from:` block (blank line before), as a single
line: `@manually-enhanced: Do not overwrite. <what changed>.` (keep it ≤79
chars).

## Known gaps (extend me)

Not yet covered by a validated walkthrough; figure out and append when hit:
- Tests where **more than one** parametrize index varies at once (a genuine 2-D
  `data` × `value`/`gas` matrix) — single-axis `d`/`g`/`v` discrimination is now
  handled (step 7), but a multi-axis post is not yet exercised.
- Multi-block / `blockchain_test` ported tests.
- Confirming EIP-8037 *error-path* state-gas behavior. (Success-path account-
  creation state gas is now handled — measure with `state_gas_reservoir=0`, step
  10. Validated end-to-end on `test_non_zero_value_call`.)

## Finishing

**Remove the skip-list entry.** Once the test passes on the future fork, delete
its line from `tests/ported_static/amsterdam_skip_list.txt` and decrement both
its per-directory count header (`# stXxx (N)`) and the `# Total entries:` count.
Confirm with a full-range fill (`--fork` omitted) with the entry gone — that is
the definition of done.

When done, offer to run `/lint`. Note that pydantic coercion warnings
(`dict→Alloc/Storage`, `Bytecode→Bytes`, unfilled optional `Transaction` params)
are false positives from the type checker, not real issues.
