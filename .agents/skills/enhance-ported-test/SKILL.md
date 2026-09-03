---
name: enhance-ported-test
description: Clean up and future-proof a ported static test.
---

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
  that enables new EIPs). A gas/state-cost change there is the most likely
  future breakage. (Historical note: broken tests used to be parked in a
  `tests/ported_static/amsterdam_skip_list.txt` consumed by a local conftest;
  the list was emptied and both were removed. If a future fork's repricing
  breaks tests en masse, the same parking pattern — a substring-matched skip
  list plus a `pytest_collection_modifyitems` hook — is in git history.)
- **`fill` output:** writes to `./fixtures` (`--clean` resets it), or pass
  `--output <dir>` for a scratch location. Do **not** use `-o` — that is
  pytest's `--override-ini`, not the output dir.

## Ordered steps

Do them roughly in this order. Earlier steps unblock later ones (notably: audit
the bytecode *before* touching gas, since restoring elided opcodes moves the
budget; and max out gas *before* strengthening post-state, so added opcodes
don't hit a gas ceiling).

### 0. Audit the bytecode against its `# Source: yul` comment
The `# Source: yul` blocks are the *filler's* source; the bytecode beside them is
what **solc emitted**, and the optimizer is free to delete operations the test
depends on. A port that faithfully reproduces the compiled bytecode therefore
faithfully reproduces the *hole* the optimizer left. Do this **first** —
restoring elided operations changes gas, so it must precede any budget work
(steps 2 / 10).

**The canonical fold: a self-cancelling `SSTORE` pair.** Refund tests set a slot
then clear it (`sstore(k, 1); sstore(k, 0)`) to earn a refund. In a fresh
`CREATE` frame slot `k` is already zero, so solc folds the pair down to
`sstore(k, 0)` — a no-op that generates **no refund at all**, leaving the test
vacuous while still passing. Validated on `test_create_oog_from_call_refunds`,
where 2 of 24 init codes had lost their `sstore(1, 1)`: the OoG arms assert the
sender's balance reaches exactly zero, which *is* the "refund earned inside a
reverted frame must be discarded" check — and it was asserting nothing.

**How to check.** Disassemble every bytecode blob and diff it against the comment
above it. Comparing opcode *counts* per mnemonic (`sstore(` in the Yul vs.
`SSTORE` in the asm) catches the whole class in one pass. A throwaway script that
`ast`-parses the test, `eval`s each `Op...` assignment against a namespace of the
test's constants, and walks `bytes(...)` through a `PUSH*`-aware opcode table is
enough — there is no disassembler in `execution_testing`.

**Tells in the ported source.** Dense `DUP`/`SWAP` juggling
(`Op.SSTORE(key=Op.DUP2, value=Op.DUP2)`, a bare `Op.PUSH1[0x1] + Op.PUSH1[0x0]`
prologue, a trailing argument-less `Op.RETURN`) is solc's stack reuse — the shape
most likely to hide a fold, and unreadable regardless. Rewrite those from the Yul
into explicit `Op.SSTORE(key=..., value=...)` / `Op.RETURN(offset=..., size=...)`
form: it restores the intent and makes the next audit trivial.

**Benign deviations — do not "fix" them.** solc drops a `POP` before a terminator
(`pop(call(...)); return(0, 1)` compiles without the `POP`, as `RETURN` ignores
leftover stack) and encodes repeated literal zeros as `DUP1` chains
(`Op.CALL(..., args_offset=Op.DUP1, ...)`). Both are semantically identical to
the Yul. Only a **missing or added state-changing operation** is a real
deviation.

**Expect to re-budget afterwards.** Restoring an elided op adds its cost — a
zero->non-zero `SSTORE` is ~22.1k pre-EIP-8037 and ~97.9k of *state* gas on
Amsterdam — so a test with a hardcoded `gas_limit` may now OOG. That is usually
not a regression you introduced: it reveals that the sibling cases which never
lost their op were *already* failing on the future fork for the same reason.
Establish this before re-budgeting by copying the pre-change file aside under a
different test name, filling both, and diffing the failure sets — in the
validated case that separated 12 pre-existing Amsterdam failures from the 3 the
fix added.

**Verify the restoration is observable, not merely green.** Fill before and
after and reconcile the gas delta. Above, consumption moved 77731 -> 97857 (the
added cold `SSTORE`, minus the reset dropping to a warm 100) and the 19900 refund
was capped by EIP-3529 at `97857 // 5 = 19571`, giving the reported 78286 exactly.
A delta you cannot account for means the rewrite changed the program (see
"Re-pinning" below).

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
  do not just strip `gas_limit`. This was the dominant skip-list shape:
  the stored gas value is exactly what EIP-8037 re-prices and breaks.
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
- **Drop the hardcoded subcall `gas` operand — this is a correctness fix, not
  cosmetics.** `Op.CALL`/`CALLCODE`/`DELEGATECALL`/`STATICCALL` default `gas` to
  `Op.GAS` (forward all remaining). Ported fillers hardcode a constant
  (`gas=0xEA60`, `gas=0x186A0`) that was sized for the *old* gas schedule; once
  EIP-8037 inflates the callee's state gas (e.g. a zero→non-zero SSTORE jumps to
  ~97920), that fixed budget no longer covers the callee and the subcall OOGs on
  Amsterdam — a common reason a pure-behavior test lands on the skip list. Omit
  the operand so it forwards everything. **Caveat:** forwarding all gas via
  `Op.GAS` misbehaves on **pre-EIP-150 (Homestead)** — the sweep (step 11) fails
  only there, so such tests floor at **TangerineWhistle**. Keep an explicit `gas`
  operand *only* when the amount forwarded is the subject (an OOG-boundary test).
  **Budget vs. subject:** before dropping the operand, ask *why* the constant
  has its value. A mid-sized constant (`0xEA60`) is a *budget* sized for the old
  schedule — drop it. An absurd or boundary constant (`2**256 - 20`) is the
  *subject*: it exercises the 63/64 clamp on an oversized ask (a client that
  computed e.g. `requested + stipend` in wrapping arithmetic would forward
  almost nothing and fail). Keep it, name it (`OVERSIZED_GAS_ASK`), and state
  the intent in a comment. Validated on `test_make_money`.
- **A codeless / absent call target is `pre.nonexistent_account()`**, not
  `pre.fund_eoa(amount=0)`. It yields an address guaranteed to hold no code and
  no state, which is what "call an empty contract" tests mean.
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

### 7b. Consolidate near-identical sibling files
Ported fillers often arrive as a fan of files with near-identical names that
differ in one axis — `test_non_zero_value_{call,callcode,delegatecall}` ×
`{,_to_empty,_to_one_storage_key,…}`. Once enhanced to the same shape, **join
them into one parametrized test** (`parametrize("opcode, target_kind", …)` with
ids matching the old filenames), set up the varying piece (call op, target
pre-state) from the params, and merge every source into a single `ported_from`
list. One readable file replaces N. Validated: 10 `NonZeroValue_*` files →
`test_non_zero_value.py`.

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
- **Zero source data makes offset tests vacuous.** A test that asserts an
  out-of-bounds read yields zeros proves nothing if the *in-bounds* data is
  also all zeros — any offset, right or wrong, reads zero. Supply non-zero
  source bytes (e.g. `data=bytes(range(1, 33))` for a CALLDATACOPY test) so a
  client reading from a wrong in-bounds offset produces a visible mismatch.
  Ported fillers often ship all-zero calldata; the rewrite is the moment to
  fix it. Validated on `test_copy_offset`.
- **Preserve every assertion the legacy filler made — count its slots.** A
  ported post often pins *two* observables (e.g. the ask fillers stored both
  the callee-observed gas *and* the caller's net gas, which proves unused
  forwarded gas is credited back). When reframing, it is easy to carry over
  the headline assertion and silently drop the second. Diff the old post's
  slots against the new one and re-express each dropped slot dynamically (or
  justify its removal explicitly). Validated on `test_raw_call_gas_ask` (the
  caller reports its remaining gas up the stack as a second return word).
- **Add a canary.** Write a distinctive non-zero sentinel to an extra slot as the
  *final* step (e.g. `Op.SSTORE(0x2, 0xC0DE)`), and assert it. If creation
  reverts or the code doesn't run to completion, the slot stays zero and the
  test fails loudly instead of silently passing on a coincidentally-matching
  (often empty) account.
- Adding `SSTORE`s costs gas — this is why step 2 (max out gas) comes first.
- **Spot a *degraded* port and restore its stated intent.** A ported test whose
  name/source promises a scenario its values don't actually exercise is a bug in
  the port, not something to preserve faithfully. Classic tell: a
  `*_after_value_transfer` / `*_with_value` test that sends `value=0`, so the
  observable it names (a callee's `CALLVALUE`, a recipient's balance) is
  vacuously zero and would pass even if the behavior were broken. Fix it by
  supplying the missing ingredient (a non-zero tx `value`) and asserting the
  now-meaningful result (`CALLVALUE == transferred`, recipient balance moved) —
  note the restoration in the `@manually-enhanced` line. Validated on
  `test_deleagate_call_after_value_transfer` (DELEGATECALL preserves the
  enclosing frame's value). Read the test's *name and source comment* against
  what it actually checks; the gap is the enhancement. The compiler-optimized
  init code of step 0 is the same family, one level down: there the *bytecode*
  stopped matching the scenario its own Yul comment describes.

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
  `gas_limit` (step 10), since the observable depends on it, but **derive that
  `gas_limit` too** — `fork.transaction_intrinsic_cost_calculator()() +
  code.gas_cost(fork) + buffer` (conservative metadata so it can't undershoot) —
  so it is neither a magic number nor fork-fragile. Validated on
  `test_sender_balance` (EIP-1559 effective-vs-max price).
- **But first ask whether the gas-derived value is the *subject* or just
  noise.** A ported test often pins the `sender` balance to `initial − value −
  gas_used * price` — pure filler bookkeeping, not what the test is about. If the
  real subject is a gas-*independent* fact (a value flow `tx → caller → callee`,
  a storage write, a created account), drop the `gas_limit` (step 2), drop the
  fragile `sender`-balance assertion, and instead assert the gas-independent
  facts, encoding them as a relationship (`caller: INITIAL + tx_value -
  call_value`, `callee: INITIAL + call_value`). Only reach for the "derive the
  fee formula" machinery above when the fee itself is the observable. Validated
  on `test_make_money`.
- **A budget bounded on *both* sides needs a guard, not just a comment.** When a
  test's OOG mechanism is itself gas-priced — the classic being an oversized code
  deposit, `return(0, 5000)` — raising `gas_limit` to fit the *successful* cases
  can quietly fund the *failing* ones, flipping them to success. That direction
  fails silently, because a passing test is the failure mode. Name the quantity
  (`oversized_code_size = 5000`), feed it to both the `Op.RETURN` operands and a
  guard: `assert tx_gas[g] < oversized_code_size *
  fork.gas_costs().CODE_DEPOSIT_PER_BYTE`. That constant is the last-resort form
  (see step 10's `code_deposit_size` note); it is legitimate *here* only because
  it understates the deposit on 8037 forks, keeping an "is this unaffordable?"
  guard conservative. Prefer `Op.RETURN`'s metadata whenever the comparison can
  be expressed against the init code's own `gas_cost(fork)`. Couple the sender's
  balance to the budget in
  the same breath — `balance=tx_gas[g] * tx_gas_price` — whenever the post asserts
  it reaches exactly zero; a hardcoded `0x3D0900` silently desyncs the moment the
  budget moves, and "burned the whole allowance" stops meaning anything. Validated
  on `test_create_oog_from_call_refunds`.

### 10. (Gas-subject / gas-snapshot tests) Replace hardcoded gas with dynamic calculation
Covers both tests that *assert* a gas amount and the dominant broken-port
shape: a legacy `GAS` snapshot / `SUB(@gas_before,
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
- **`extra_stack_items=1` silently discards a call's success flag — keep it
  observable.** `CodeGasMeasure` SWAP/POPs the extra item, and gas alone
  cannot replace it: a wrongly *failed* call refunds the child gas + stipend,
  so it measures identically to a *success* into an empty callee, and for
  `CALLCODE`/`DELEGATECALL` no balance moves either — the whole post-state is
  then blind to the failure. When the measured op is a call whose success is
  not otherwise observable, fold the flag into the measured window:
  `store_code = Op.SSTORE(flag_slot, call_code, key_warm=False,
  original_value=0, new_value=1)` with `extra_stack_items=0`, assert
  `flag_slot: 1` in the post, and expect `store_code.gas_cost(fork)` (the
  SSTORE's cost is now part of the measurement — and a failed call would
  store 0, shifting the measured gas too, so the failure is doubly loud).
  Validated on `test_non_zero_value`.
- **Apply opcode metadata from the test's context** so `gas_cost(fork)` is
  correct (see `docs/writing_tests/opcode_metadata.md`). For `CALL`:
  `address_warm` (is the target pre-accessed?), `value_transfer` (value > 0?),
  `account_new` (target absent/empty and receiving value → created?). Use
  `pre.nonexistent_account()` for a target that must stay **cold + non-existent**
  so `account_new` holds — a `fund_eoa()` target already exists (warm/created) and
  would change the cost.
  - For `CREATE`/`CREATE2`: `new_memory_size` (the init-code window the offset/
    size operands touch, e.g. `size=0x20` → `new_memory_size=0x20`) **and**
    `init_code_size` (drives the EIP-3860 per-word cost, Shanghai+). Omitting
    `init_code_size` silently under-predicts by `CODE_INIT_PER_WORD *
    ceil(size/32)` (2/word) — a small, easily-missed miss. `CREATE` leaves the
    created address on the stack → `extra_stack_items=1`.
  - **A runtime address threaded via `SLOAD`** (the create-then-call idiom:
    store `CREATE`'s result, then `CALL(address=Op.SLOAD(slot))`) must mark that
    `SLOAD` `key_warm=True` — the slot was just written so it is warm at runtime,
    but the metadata default is cold and `gas_cost(fork)` would over-predict by
    `cold − warm` (2000). An account freshly made by `CREATE` is **warm + already
    existing**: `address_warm=True, account_new=False` on the following `CALL`.
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

**Absolute `GAS` readings are unsalvageable — convert to a delta.** A test that
stores a *raw* `GAS` value (not a `SUB(before, GAS)` delta) — e.g. `SSTORE(0,
GAS)` right after entry — pins `gas_limit - intrinsic - overhead`. Amsterdam
re-priced the **intrinsic transaction cost** (EIP-2780: base 21000 → 15000), so
that stored value shifts by a fixed amount (observed 578998 → 584998, a 6000
jump) *independent of any state gas* — `state_gas_reservoir=0` does **not** fix
it. The only robust move is to stop storing absolute readings: wrap the measured
op in `CodeGasMeasure` (which stores the *delta* between two `GAS` reads, immune
to intrinsic) and assert `code.gas_cost(fork)`. A legacy `[[0]](GAS) …
[[100]](GAS)` snapshot pair *is* such a delta in disguise — the pair brackets one
operation (e.g. a `CREATE`); collapse it to a single `CodeGasMeasure` around that
op and drop both raw slots. Validated on the `CREATE_EmptyContract*` family.

**Look for opcode metadata before hand-rolling a gas formula.** Opcodes carry
kwargs that fold fork-dependent charges into `gas_cost(fork)` — `Op.RETURN`'s
`code_deposit_size`, `Op.CREATE`'s `init_code_size`/`new_memory_size`,
`Op.CALL`'s `address_warm`/`value_transfer`/`account_new`, `Op.SSTORE`'s
`key_warm`/`original_value`/`new_value`. A formula assembled out of
`fork.gas_costs()` constants has to be re-audited at every repricing; the
metadata tracks it for you. Check the opcode's `Metadata` docstring block in
`packages/testing/src/execution_testing/vm/opcodes.py` before reaching for
constants — a `fork.gas_costs()` reference in a derivation is a smell that the
metadata was missed.

**Decompose the constant empirically** when no single helper applies (throwaway
script against the fork): pin each term to the known-good number, then assemble.
Map terms to fork-derived helpers: opcode base+pushes → `bytecode.gas_cost(fork)`;
memory growth → `fork.memory_expansion_gas_calculator()(new_bytes=,
previous_bytes=)`; EIP-3860 init-code words → `fork.gas_costs().CODE_INIT_PER_WORD
* ceil(size/32)`. You can also call `.gas_cost` / `.regular_cost` / `.state_cost`
on exactly the measured bytecode.

**Reservoir-less sub-calls pay state gas from their regular grant.** With
the tx reservoir at 0, a sub-frame's state charges spill from its own
`gas_left` — a delegate that does one first-set SSTORE needs its *whole*
~111k inside the forwarded grant on Amsterdam, not just the ~13k regular
part. Size derived sub-call budgets from the callee composite's full
`gas_cost(fork)`. Corollaries: (a) a *failed* sub-frame contributes its
entire forfeited grant to the parent's measured window, not its "cost";
(b) `SSTORE(flag, <call>)` silently degrades to a ~3k no-op store when
the call fails — the flag reads 0 and no state gas is charged, which can
mask a broken callee behind a plausible-looking measurement. Validated on
`test_new_gas_price_for_codes` (delegate budget derived; failed value
calls return their stipends: subtract one `CALL_STIPEND` per failed
value-bearing call from window measurements).

**Nested / callee-side measurements.** When the measured op is a `CALL` whose
callee does real work, the measured cost = `call_code.gas_cost(fork) +
callee_code.gas_cost(fork)` (the CALL's own cost plus what the callee consumed).
Attach the callee's opcode metadata (e.g. SSTORE `key_warm`/`original_value`/
`new_value`) so its `gas_cost` is right, and decompose against the callee's
*actual* bytecode rather than a reconstruction — a value supplied by `GAS` costs
2, not a `PUSH`'s 3, and that off-by-3 is a real trap. A callee-side gas snapshot
(`SSTORE(k, GAS)`) stores `forward_gas - Op.GAS.gas_cost(fork)`. Derive the
forwarded gas dynamically — `forward_gas = callee_store.gas_cost(fork) + buffer`
— rather than a magic number; under EIP-8037 a cold zero->non-zero SSTORE can
cost ~100k, so a fixed value is both fork-fragile and brittle. (Size the SSTORE
with a placeholder `new_value`: its cost depends only on the zero->non-zero
transition, not the magnitude — which also breaks the `forward_gas`/`new_value`
circularity.) Set `state_gas_reservoir=0` so the state gas is captured.
Validated on `test_raw_call_gas`.

**An expensive store after a callee that eats all forwarded gas — pre-write
the slot.** When a frame must SSTORE a result *after* a subcall that
deliberately consumes its whole 63/64 grant (an OOG-probe callee), the frame
retains only 1/64 — under EIP-8037 that cannot afford a cold zero→nonzero
store (~111k), and pre-8037 it often couldn't afford the cold 2.2k either
(making the ported `{slot: 0}` expectation vacuous: caller-OOG and
callee-failure were indistinguishable). Fix: write a sentinel to the slot
*before* the call (paying cold + state with the full budget), then store
`BASE + result` after it — now a dirty-warm write (100 gas) the retention
always covers, and the three outcomes (success `BASE+1`, failure `BASE`,
caller OOG `sentinel`) are all distinct. Validated on
`test_static_execute_call_that_ask_fore_gas_then_trabsaction_has`.
**Caveat — EIP-2200's stipend rule caps this trick.** Any SSTORE (even a
100-gas dirty-warm one) exceptionally halts unless `gas_left > 2300`
(Istanbul+), so the 1/64 retention must exceed ~2400, i.e. the pre-call
budget must exceed ~154k. When the scenario *requires* a smaller budget
(e.g. a starved arm whose forwarded gas must undercut the callee's cost),
no post-call SSTORE is possible at all: write the sentinel *before* the
call and put nothing but a `POP` after it — frame completion (the account
persists with the sentinel) plus the callee-side observable already
separate the outcomes. Validated on
`test_contract_creation_make_call_that_ask_more_gas_then_transaction_provided`.

**Refund-cap derivations need the EIP-7623 kwarg.** The EIP-3529 cap's
base is the gas deducted before execution, which excludes the calldata
floor: pass `return_cost_deducted_prior_execution=True` to the intrinsic
calculator whenever the tx has calldata, or the derived `executed` (and
the cap) overstate. Validated on `test_refund_suicide50procent_cap`.

**A CREATE address collision burns the child's gas allowance** (the
EIP-684 path): the withheld child grant is consumed, nothing is created,
and under EIP-8037 the new-account state charge is refunded. Useful to
build always-failing creator frames with predictable consumption.
Validated on `test_revert_depth_create_address_collision`.

**Loop-to-depth-1024 cannot replace loop-to-OOG.** With 63/64
attenuation, reaching depth 1024 needs ~e^16 × the terminal gas — no
legal budget gets there. For call-loop depth tests the honest shape is a
fixed named budget with per-gas-schedule-era pinned depth counts, each
shift explained (±1 frame ≈ 64·ln(cost ratio)). Validated on
`test_loop_calls_depth_then_revert`.

**Framework wart: the SSTORE dirty-rewrite composite prices 100 on every
fork**, but Constantinople/Petersburg charge 5,000 for a dirty re-store —
a derived budget that must survive pre-Istanbul forks needs an explicit
headroom constant for it (named, commented). Observed on
`test_revert_depth_create_address_collision`'s ConstantinopleFix sweep.

**EIP-8037 repriced the code deposit's regular part — boundaries beware.**
On 8037 forks the deposit charges only the keccak word cost
(`OPCODE_KECCAK256_PER_WORD * ceil32(len)/32`, ~6 gas) as regular gas plus
`len * 1530` state; `fork.gas_costs().CODE_DEPOSIT_PER_BYTE` (200) is the
*pre-8037* constant. Using 200/byte in a *sufficiency* budget merely
overshoots (safe); using it in a one-gas-short *boundary* silently funds
the deposit on Amsterdam. Branch on `fork.is_eip_enabled(8037)` for exact
deposit boundaries. Validated on
`test_create_oo_gafter_init_code_returndata_size`.

**Match the intrinsic calculator's kwargs to the transaction's shape.**
`fork.transaction_intrinsic_cost_calculator()()` defaults to
`sends_value=False`; under EIP-2780 a value-bearing transaction's intrinsic
includes the folded value-transfer cost (~5.9k), so a derived budget or
GAS-observation formula silently skews by that amount on Amsterdam only.
Pass `sends_value=True` when the tx carries value — or drop an incidental
tx `value` entirely (step 5) so the default holds. Validated on
`test_store_gas_on_create`.

**A creation transaction's top frame pays new-account state gas
(EIP-8037) — but only for a fresh target.** When deriving a create-tx
budget, the intrinsic calculator does not include the created account's
state gas — add
`fork.transaction_top_frame_state_gas(contract_creation=True)` (183,600 on
Amsterdam, 0 before) or the whole creation silently OOGs only on the
future fork. Exception: `prepare_dispatch` charges it only when the
target's *pre-state* account is `EMPTY_ACCOUNT` — a prefunded create
address pays nothing (validated on
`test_out_of_gas_prefunded_contract_creation`, whose budgets omit the
term). A nested CREATE's new-account state is charged to the parent
before the 63/64 withhold and refunded if the child fails, so a derived
budget must cover its *peak* (use the composite `gas_cost(fork)`), even
on paths where the net is zero.

**Measuring forwarded gas / the EIP-150 63/64 rule (the `*_gas_ask` shape).**
Ported fillers probe "how much gas does a subcall receive when it asks for more
than is available" by pinning an absolute forwarded amount — fork-fragile,
because "available" moves with the EIP-2780 intrinsic change. Make it robust
with three moves: (1) **cap the caller frame's gas to a known budget** with an
*outer* call (`entry → CALL(gas=CALLER_GAS) → caller`); because `CALLER_GAS` is
far below the outer frame's 63/64, the caller receives exactly `CALLER_GAS`
independent of the tx gas limit. (2) **Return the observed `GAS` up the stack**
(`MSTORE(0, GAS) + RETURN(0, 32)` in the callee, `RETURN` again in the caller,
`SSTORE` only in the top frame) instead of `SSTORE`-ing in a lower frame —
avoids the EIP-8037 state-gas trap. (3) **Derive the expectation from the fork:**
```
available    = CALLER_GAS - caller_call_code.gas_cost(fork)
forwarded    = available - available // 64      # NOT available * 63 // 64
expected_gas = forwarded + stipend - Op.GAS.gas_cost(fork)
```
where `stipend = fork.gas_costs().CALL_STIPEND` for a value-bearing call (0
otherwise). **The `// 64` form is the trap:** `available - available // 64` and
`available * 63 // 64` differ by exactly 1 whenever `available % 64 != 0` (the
EVM uses the former). One parametrize over `(opcode, value, memory)` covers the
whole CALL/CALLCODE/DELEGATECALL family; floor **Berlin** (the call metadata).
Validated on `test_raw_call_gas_ask` (10 RawCall*GasAsk fillers).

**Error paths charge regular gas only — assert `regular_cost(fork)`.** A failed
`CREATE`/`CALL` still charges its regular costs (base, memory, init-code words)
but creates no account, so **no state gas is charged** under EIP-8037. For a
success/failure parametrize, that is exactly the `gas_cost(fork)` vs
`regular_cost(fork)` split: success measures `code.gas_cost(fork)` (regular +
state), failure measures `code.regular_cost(fork)` (regular only). On pre-8037
forks `state_cost` is 0 so the two coincide — one expression, correct on every
fork. Drive a `CREATE` down the balance-failure path by funding the creator one
wei short of the transferred `value` (`balance = value - 1`); the created
address is then `Account.NONEXISTENT`. Validated end-to-end on
`test_raw_create_gas` (6 RawCreate*Gas fillers consolidated).

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
- **Behavioral floors show up as non-gas mismatches in the sweep.** A CREATE
  test asserting the created account has `nonce=1` floors at **SpuriousDragon
  (EIP-161)** — earlier forks start contract nonces at 0, so Frontier/Homestead/
  TangerineWhistle fail on the nonce, not the gas. Read *what* the sweep's
  earliest-passing fork is gated on; it is not always a gas-schedule change.
- **A `bad v` / `INVALID_SIGNATURE_VRS` failure is a signature floor, not a
  real one — don't raise `valid_from` for it.** The default `Transaction` is
  EIP-155-protected, which pre-SpuriousDragon forks reject. Instead set
  `protected=fork.supports_protected_txs()` (add `fork: Fork`): it goes
  unprotected on Frontier/Homestead/TangerineWhistle and protected from
  SpuriousDragon on. This keeps the floor at the *behavior's* real EIP (e.g.
  Homestead for `DELEGATECALL`) instead of masking it at SpuriousDragon.
  Validated on `test_delegatecall_emptycontract`.

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

## Finishing

**Confirm with a full-range fill** (`--fork` omitted) — every deployed fork
green is the definition of done. (If a skip list is ever reintroduced for a
future fork, also delete the test's entry and keep its count headers
accurate.)

**Final sweep checklist** — each of these has been missed in practice; check
them one by one before calling the test done:
- `@pytest.mark.pre_alloc_mutable` removed if no hardcoded addresses/
  nonces/`pre[...]` remain (it silently skips the test in execute mode).
- No machine-port placeholder docstrings left (`Test_<filename>.`) — the
  module and function docstrings say what the test verifies, in
  imperative mood ("Verify/Measure ...", not "Gas cost of ...").
- Docstrings re-read against the *final* architecture: collapsing a
  delivery CALL or moving value onto the tx makes "inherited from the
  enclosing CALL"-style prose stale.
- Inline magic operands named (`FORWARDED_GAS`, `GAS_SLOT`, ...) —
  consistent with sibling files in the same directory.
- Pinned budget constants guarded: anything like
  `available = BUDGET - code.gas_cost(fork)` gets an
  `assert available > 0, ...` so a future repricing that outgrows the
  budget fails loudly at fill time instead of producing a garbage
  expectation.
- The old post's slots all accounted for (see step 8's "count its
  slots").

When done, offer to run `/lint`. Note that pydantic coercion warnings
(`dict→Alloc/Storage`, `Bytecode→Bytes`, unfilled optional `Transaction` params)
are false positives from the type checker, not real issues.
