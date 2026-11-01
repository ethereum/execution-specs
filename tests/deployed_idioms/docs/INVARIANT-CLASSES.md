# Invariant classes and the test archetype each one requires

The corpus's unit of work is **not** "a pattern" but "an invariant a deployed contract
relies on, plus a test shape that can express it". These are different: a frozen-budget
survival test cannot express a monotonicity invariant, and a monotonicity test cannot
express a forwarding-prediction invariant. Getting the archetype wrong means writing a
test that passes no matter what the fork does.

**Honest state: 33 invariant classes identified; 30 have proven, mutation-validated archetypes across two waves** — #1–#18 and #20–#25 in `tests/` (24), #28–#33 in `expansion/tests/` (6). Three are not built, each for a stated reason rather than as a gap: **#19** collapses into #1, **#26** is already covered by 5,103 lines of official tests, and **#27** (environment-field semantics) is a recorded candidate.

All mechanism claims below were read out of EELS at the pinned Amsterdam commit and are
**CHECKED** unless marked otherwise. Citations are file:line.

---

## Verified mechanism reference

These are the levers a fork can move. Everything in the table below depends on one of
them.

```text
forwarding            gas = min(requested,
                                max_message_call_gas(gas_left - memory_cost - extra_gas))
                      max_message_call_gas(g) = g - g // 64        amsterdam/vm/gas.py:861
stipend               call_stipend = ZERO if value == 0 else 2300  amsterdam/vm/gas.py:838
                      CALL_STIPEND = 2300                          amsterdam/vm/gas.py:84
                      CALL_VALUE = ACCOUNT_WRITE + CALL_STIPEND    amsterdam/vm/gas.py:86
sstore sentry         check_gas(max(access_cost, CALL_STIPEND+1))  amsterdam/.../storage.py:104
   (Istanbul form)    if gas_left <= CALL_STIPEND: raise OOG       istanbul/.../storage.py:62
refund cap            min(gas_used_before_refund // 5, refund_counter)
                                                                   amsterdam/vm/gas.py:1213
   (London)           // Uint(5)                                   london/fork.py:810
   (Berlin)           // Uint(2)                                   berlin/fork.py:698
state refund (8037)   credit_state_gas_refund: LIFO, gas_left up to
                      the spill, then the reservoir                amsterdam/vm/gas.py:594
reservoir to child    drain_state_gas_reservoir -- entire reservoir,
                      "no all-but-one-64th rule for state gas"     amsterdam/vm/gas.py:689
state gas per byte    COST_PER_STATE_BYTE = 1530                   amsterdam/vm/gas.py:47
                      STATE_BYTES_PER_STORAGE_SET = 64  -> 97,920  amsterdam/vm/gas.py:49
settlement            gas_used_before_refund = tx_gas - gas_left - state_gas_left
                      gas_used = max(after_refund, calldata_floor)
                      execution_gas_used ignores refunds (EIP-7778)
                      settled_state_gas_used = max(0, state_gas_used)
                                                                   amsterdam/vm/gas.py:1211-1222
gas introspection     push(evm.stack, U256(evm.gas_meter.gas_left))
                      -- `GAS` reports gas_left only, never the reservoir
```

Two of these carry a comment showing the spec authors already anticipate repricing:

- `storage.py:104` — *"The `max` guards an access cost repriced above the stipend;
  neither warmth is today."*
- `frontier/vm/gas.py:28` — *"These values may be patched at runtime by a future gas
  repricing utility"* (above `class GasCosts`).

---

## The classes

Columns: **Broken?** = a mainnet fork has already changed this rule under deployed code.
**Witness** = measured population from our lenses. **Status** = does a proven test
archetype exist in this corpus.

### Absolute-budget family

**1. Frozen-budget survival.** A caller forwards a literal and depends on the callee
completing. *Invariant:* the callee's full cost fits inside the literal.
*Assert:* committed effects on both sides of the call.
*Broken?* Yes — EIP-8037 raised a fresh slot from 22,100 to 110,020.
*Witness:* a staking-pod module 140,000 (immutable, live); VRF 200,000; a cross-chain transfer protocol 250,000.
**Status: PROVEN** — `wave1/frozen_budget/`, 66/66 fill, mutation-validated, and the
measured break point is a +30.65% `COST_PER_STATE_BYTE` increase.

**2. Frozen budget *below* the floor — "never needs to write".** For budgets under the
~110,026 Amsterdam floor, the callee cannot create state at all, so survival is the wrong
assertion. *Invariant:* this convention never needs to create new state, and its
read-only work fits.
*Assert:* the callee completes **and** performs no fresh SSTORE.
*Witness:* ERC-7579 `postCheck` exactly 3,229 gas (97.5% of frames short of a slot);
4337 `validatePaymasterUserOp` exactly 50,000 (99.4%); ERC-165 `supportsInterface`
exactly 30,000 (83.9%).
**Status: PROVEN** — `tests/subfloor_budget/`, **132 fill**. Measurement reshaped the
design: for 30,000 and 50,000 the "never writes" guarantee is **new at EIP-8037** — before
it, those budgets had 22,100 available and *could* create a slot. So the class needs four
tests, not one: a read-only arm on all forks, the Amsterdam "cannot write" arm, and both
pre-fork counterparts. Measured (all six forks, CHECKED): 3,229 cannot create a slot on
**any** fork; 30,000 and 50,000 can before Amsterdam and cannot after. Detected by
`cls12-cold-read-5000` (6), `cls2-cpsb-250` (6), `cls2-storage-set-osaka-1000` (3) and
`cls2-storage-set-osaka-60000` (6), with failure counts matching the arithmetic exactly.
`cls12-cold-read-700` survives **correctly**: cheaper reads cut a slot only to
`700 + 10,000 + 97,920 = 108,620`, still 2.2x the largest budget.

**3. Hardcoded cost-equality.** A contract hardcodes an expected gas cost to compute a
fee, an L1 charge, or a quote. *Invariant:* the constant equals the real cost.
*Assert:* the operation's charged cost equals the contract's constant.
*Broken?* Yes, every reprice, by construction.
**Status: PROVEN** — `tests/hardcoded_cost_equality/`, 44 fill. This is one of two classes
where asserting a raw gas number *is* the invariant, so SCHEMA §4.1's prohibition does not
apply. **The result is sharper than expected, because the two deployed constants have
opposite histories:**
- **5,000 is exactly right for five forks.** EIP-2929 split it into `2,100 + 2,900` and
  deliberately preserved the cold total. *An inequality-only corpus would never have
  recorded that an equality held* — which is the argument for pinning equalities at all.
- **20,000 has been wrong since Berlin** by the 2,100 cold surcharge: a 10.5% under-quote
  sitting in deployed code for five forks with no test failing anywhere.
At Amsterdam the gaps are 110,020 vs 20,000 (5.50x) and 12,100 vs 5,000 (2.42x); the second
involves **no state gas at all**, so it also reaches class #2's population.
*Witnesses (verified):* a deployed rollup `Bridge` `<address withheld>` —
`_GAS_REFUND_PER_CACHE_OPERATION = 20_000` flowing through `gasCharged * block.basefee` into
`sendEtherAndVerify`, so an under-quote under-pays relayers in ether; and a deployed rollup
a rollup execution manager `0x2745c248…` — `NUISANCE_GAS_SSTORE = 20000`. **Caveat kept:** the
21/26 identifier counts are occurrence counts with **no measured FP rate**, so they must not
enter a registry record without §7.3 hand-validation, and the 5,000 constant has no
deployed-address witness (asserted as a protocol constant, like the 2,300 stipend).
Detected by `cls3-cold-storage-write-4500`, seen by only this archetype and
`block_vs_sender_accounting` across all 20 — nothing else can observe the pre-8037
`SSTORE_RESET` term.
the invariant, so SCHEMA §4.1 explicitly permits it.

### Relative-forwarding family — "how much gets forwarded matters"

**4. Retained-gas epilogue survival (the 63/64 rule).** `call(gas(), ...)` forwards
all-but-1/64; the caller depends on the retained `avail // 64` being enough for its own
post-call work (unwinding a lock, emitting, writing a result). **No literal is involved**,
which is why a frozen-budget test cannot catch it. *Invariant:* the gas retained by the
63/64 rule covers the caller's epilogue.
*Assert:* the caller's post-call committed effect survives a child that consumes
everything it was given.
*Broken?* Yes — EIP-150 introduced the rule; any reprice of *epilogue* opcodes shrinks the
margin.
*Witness:* L4 `retention-6364` — **245,595 addresses from 183 source files**, FP 0/18
hand-validated. L5 `6364-retention` — 239 transactions that commit *only* because of the
rule, 77 runtimes.
**Status: PROVEN** — `wave1/retained_epilogue/`, 22 fill. The sole detector of the
retention divisor among the pre-existing archetypes, and now corroborated by classes #5
and #6, which detect `retention-128` where this one correctly survives (see
`MUTATION-MATRIX.md`). L2 re-measured the shape at **1,449,863 addresses / 574,625
runtimes**, FP 0/8 — 5.9x L4's source-side count, extended to unverified contracts.

**5. Forwarding-prediction agreement.** A contract reimplements the forwarding formula to
predict what the callee will receive — a deployed oracle network's `callWithExactGas` uses yul
`g - g/64 > gasLimit`. *Invariant:* the contract's prediction equals what the EVM
actually forwards.
*Assert:* predicted == actual delivered gas, across the boundary.
*Broken?* Would break on any change to the retention fraction, to `extra_gas`, or to the
memory-cost term in `calculate_message_call_gas`.
*Witness:* a deployed cross-chain router — and it **documents its own fragility in source**:
`GAS_FOR_CALL_EXACT_CHECK = 5_000; // so that we can redeploy to adjust it should a
hardfork change the gas costs of relevant opcodes in callWithExactGas`.
**Status: PROVEN** — `tests/forwarding_prediction/`, **210 fill**, detected by
`retention-{32,128,256}`, `retention-osaka-256` and `cold-account-{6000,2600}`.
*It produced the corpus's first concrete deployed-insufficiency finding:* a deployed oracle network's
`GAS_FOR_CALL_EXACT_CHECK = 5_000` is **insufficient for three call shapes**, measured as
`gasLimit − delivered` by two independent probes agreeing in every cell — value-bearing
short 4,287 (Berlin→Osaka) and 6,944 (Amsterdam); an EIP-7702 delegated target short 287
(Prague/Osaka) and 1,074 (Amsterdam, two cold accesses in `extra_gas`); and a 16 KiB
return buffer sound through Osaka (4,638 of 5,000) but **breaking at Amsterdam** (5,031,
short 133). The rise is exactly `5,031 − 4,638 = 393 = floor(400 × 63/64)` — EIP-8038's
`COLD_ACCOUNT_ACCESS` 2,600→3,000 propagated through the clamp. Derivation and
measurement agree to the gas (CHECKED). a deployed oracle network's own comment anticipated exactly this.

**6. Compounded depth forwarding.** The leaf of a depth-*n* chain runs on
~`(63/64)^n` of the original. *Invariant:* the deepest frame still completes.
*Assert:* leaf effect commits at realistic depth.
*Witness:* L5 — 38,325 instances, 142 runtimes.
**Status: PROVEN** — `tests/depth_forwarding/`, **308 fill**. Measured: **EIP-8037
shortened the maximum useful forwarding chain** — on the same 4M budget with a leaf
creating two slots, Berlin→Osaka reaches 256 hops while Amsterdam dies between 184 and
187. Compounding ratios are fork-identical to the basis point, and the `(63/64)^n < 1/2`
crossing measures at 44 hops against an ideal 45 (the 19 bp per-frame deficit tips it one
hop early). `cold-account-*` correctly survives, because a self-call warms its own address.

**7. Stipend-funded fallback survival.** A value-bearing `transfer()`/`send()` delivers
exactly 2300, and only when `value != 0` (`gas.py:838`). *Invariant:* the recipient's
fallback completes on 2300.
*Assert:* the recipient's committed effect after a 2300-gas value call.
*Broken?* **Yes, historically and famously** — EIP-1884 raised SLOAD 200→800 and broke
deployed fallbacks. L4 found **EIP-1884 has zero tests from any angle**: no
`istanbul/eip1884*` directory exists, and `generators.py:524` refuses pre-Berlin gas tests.
*Witness:* L5 — 265,056 calls at exactly 2300, of which 63.5% target codeless addresses,
so **~96,865 real** stipend-to-code calls.
Corollary (CHECKED): with the `max(access_cost, CALL_STIPEND+1)` sentry, a stipend-funded
frame can never complete an SSTORE.
**Status: PROVEN** — `tests/stipend_fallback/`, 22 fill, detected by `sload-cold-2300`
(an EIP-1884-shaped access reprice) and `stipend-2000`, with perfect specificity. The
margin is ~195 gas: one cold `SLOAD` costs about 2,105 against a 2,300 stipend, tight by
protocol design rather than by our choice. L1 measured the stipend-send shape at
**2,098,994 addresses / 5,041 runtimes** — the largest population it found, and prior art
had *explicitly excluded* it.

### Refund family — "how much comes back matters"

**8. Refund-cap dependence.** *Invariant:* a transaction that clears N slots settles under
its gas limit given the cap `min(gas_used_before_refund // D, refund_counter)`.
*Assert:* the tx completes and its `gas_used` stays under the limit, with D frozen.
*Broken?* **Yes** — EIP-3529 moved D from 2 (Berlin) to 5 (London). L4: the `//2 → //5`
change is **never tested behaviourally**, only for conformance.
*Witness:* 406,604 addresses / 298,869 runtimes (bulk storage clearing inside a loop), plus
792,199 refunding transactions (30.81%) in a 10,000-block window. Gas tokens (a gas-token contract/a gas-token contract) are
cited as history only — L4's `refund-cap` axis records `instances: 0`, so no count is claimed.
*Measured (CHECKED):* divisor **2 at Berlin, 5 from London**; clear refund
**15,000 / 4,800 / 11,616** at Berlin / London..Osaka / EIP-8037.
**Status: PROVEN** — `tests/refund_cap/`, 28 fill. A refund is invisible to the EVM, so the
test observes it by *balance differencing*: two senders run gas-identical bytecode over
identical storage, one clearing (`1→0`, refund) and its twin writing `1→2` (same charge, no
refund); a third transaction reads both balances with `BALANCE`, and the difference is exactly
the refund. Detected 9/9, both directions, at all three divisor code sites.

**9. Refunds do not fund in-frame execution.** Pre-8037 this is an absolute invariant:
refunds accrue to a counter and settle at the end, so clearing a slot never increases the
gas available to the running frame. Post-8037 it is **false** for state gas:
`credit_state_gas_refund` puts the refund back into `gas_left` (LIFO: `gas_left` up to the
spill, then the reservoir).
*Assert:* on pre-8037 forks, a frame's available gas is unchanged by its own clears.
*Broken?* **Yes — this is the inversion that generated the entire 8037 hunt.**
*Witness:* 265,217 addresses / 208,712 runtimes, whose registry invariant is this class verbatim.
*Measured floor for set+clear+15,000 (CHECKED):* **(37,200 , 37,300] pre-8037** and
**(112,000 , 115,000] at Amsterdam**. Two things measurement corrected: the Amsterdam refill is
**peak**-limited, not total-limited (a naive estimate was ~100,000 gas out), and a 23,000 budget
cannot reach past the clear even though set+clear costs 22,212, because the pre-8037 SSTORE
sentry requires `gas_left > 2,300` on entry.
**Status: PROVEN** — `tests/refund_not_spendable/`, 63 fill. Both arms detected by *different*
mutations; the pre-8037 arm needed a mutation that *adds* a refill, since it is the only shape
that can falsify a rule whose content is “nothing happens”.

**10. Gas monotonicity across a call.** *Invariant:* `gasleft()` after a call is ≤
`gasleft()` before it, so `before - after` cannot underflow. This is what every gas meter
and every gas-refunding relayer relies on.
*Assert:* the subtraction's committed result, or simply that the second reading is not
larger.
*Broken?* **Yes — EIP-8037 M2/M4.** L4: the invariant is asserted **nowhere** on pre-8037
forks; only its Amsterdam violation is tested.
*Witness:* L4 `gas-delta` — **252,006 addresses from 2,499 source files**, FP 0/18.
Includes Safe's `gasUsed.sub(gasleft())`.
**Severity splits by compiler (L4, important for ranking):** under solc ≥ 0.8 / SafeMath
the underflow **reverts** → liveness failure; under plain `-` with solc < 0.8 it **wraps
silently** → the relayer is reimbursed an astronomically wrong amount. The silent case is
a correctness and funds bug, and is *worse* than the DoS.
**Status: PROVEN** — `wave1/gas_monotonicity/`, 44 fill. Four tests, because EIP-8037 has
**two distinct refund paths** and one test reaches only one: `credit_state_gas_refund`
in-frame (M2, `storage.py:151`) and `repay_state_gas_spill` on child merge (M4,
`vm/__init__.py:240`). The mutation matrix found the M2 path unprotected on its first run
and a same-frame set/clear pair closed it. Detected by `m2-no-inframe-refill` and
`m4-no-merge-repay`, perfect specificity.

**11. Halt-versus-revert gas return.** A reverting child returns its remaining gas
(including, under 8037, restored spill); an exceptional halt burns it. *Invariant:* a
caller that tolerates child failure recovers gas on `REVERT` but not on OOG, and its
own completion depends on which.
*Assert:* the caller's post-failure effect, parametrised over revert vs OOG.
*Witness:* L5 — tolerated child failure inside a committing tx, raw 116,823 frames at
**94.12% measured FP** (sql/35). The correct filtered figure is **6,281 frames across 270
runtimes**, taken from the registry's post-filter count; my earlier “~6,870” was the bare
subtraction residual `116,823 − 109,953` and is wrong — use 6,281.
*Measured retained gas on a 200,000 grant (CHECKED):* 197,376 stop / 197,370 revert /
3,080 invalid / 3,080 OOG pre-8037; 196,976 / 196,970 / 3,073 / 3,073 at Amsterdam — so a
halt returns only the 63/64 retention while a revert returns almost everything.
**Status: PROVEN** — `tests/halt_vs_revert/`, 138 fill, 6 mutations over 4 distinct rules.

**12. OOG-as-signal, two-sided.** A capability probe forwards a literal and reads *any*
failure as "no". *Invariant:* **both** directions hold — a capable target completes
within the literal, and an incapable one fails within it.
*Assert:* both arms, in one test.
*Broken?* A reprice can flip either direction, and **neither reverts**, so the caller
commits down the wrong branch with nothing surfacing an error.
*Witness:* a deployed AMM `isV28OrHigher()` under `staticcall(5000,..)`, 2,998 frames, 7 call
sites, two-sided and witnessed on both sides. ERC-165 `supportsInterface` at exactly
30,000 — never OOGs but reverts on **64.36%** of calls, so callers are already
habituated to reading failure as "unsupported".
**Status: PROVEN** — `tests/oog_as_signal/`, 44 fill. Measured bracket, **identical on all
six forks**: at the a deployed AMM literal 5,000, 2 cold reads answer and 3 do not; at the ERC-165
literal 30,000, 14 answer and 15 do not. Both literals are pinned from *both* sides, which
is the tight two-sided form `frozen_budget/README.md` asked for — achievable without a
per-fork table because `COLD_STORAGE_ACCESS` is fork-stable, which the six-fork identity
*demonstrates* rather than assumes.
**This archetype is where the downward-reprice blind spot was closed.**
`cls12-cold-read-700` (cheaper, EIP-1108-scale) is survived by **all six budget-sufficiency
archetypes** — `frozen_budget`, `stipend_fallback`, `gasleft_sufficiency`,
`retained_epilogue`, `depth_forwarding`, `forwarding_prediction` — and detected only by
archetypes asserting an exact value or a two-sided bracket. Before it, **every** mutation in
the corpus made gas dearer.
The halting arm is `INVALID` (solc <=0.4.12 `throw`, what L5 actually witnessed) rather than
an unbounded loop: deliberately *not* repricing-sensitive, so it pins halt semantics while
the overrunning arm carries the cheaper-reprice sensitivity. An infinite loop would have
looked equivalent and taught nothing, because it can never flip.

### Settlement and accounting family

**13. Block-versus-sender accounting divergence (EIP-7778).** `execution_gas_used`
ignores refunds while the sender-facing `gas_used` applies them (`gas.py:1211-1222`).
*Invariant:* anything inferring block fullness, L1 cost, or fee from a receipt must use
the right one. *Assert:* a refunding tx's receipt `gasUsed` differs from its block-gas
contribution, by the refund.
*Broken?* Yes, by EIP-7778 itself.
**Status: PROVEN** — `tests/block_vs_sender_accounting/`, 22 fill. Two tests pin the
**pre-7778 identity** on the forks deployed receipt consumers rely on — and pre-Amsterdam
EELS makes the receipt field and the block counter *literally the same variable*
(`prague/fork.py:941,944` hands `make_receipt` the accumulated `block_gas_used` itself),
so one literal is pinned to both sides and the equality cannot be satisfied by tuning
one. Measured: Berlin 20,512/20,512; London→Osaka **32,820/32,820, one literal across six
forks**; Amsterdam **50,740 receipt vs 63,424 header, gap 12,684**. The Amsterdam pair is
self-checking: `63,424 − 50,740 == 63,424 // 5`, exactly one cap-bound refund (CHECKED).
Detected by `exec-gas-applies-refund` (the direct revert of EIP-7778),
`refund-divisor-4` and `state-free-credit`.

**14. Net-negative state gas is clamped.** `settled_state_gas_used = max(0,
state_gas_used)`. A transaction that frees more state than it creates receives **no**
block-level credit for the surplus. *Invariant:* net-freeing transactions are not paid
for freeing. *Assert:* block state-gas accounting for a net-clearing tx is exactly 0,
not negative.
**Status: PROVEN, but the invariant had to be reframed — and my brief for it was wrong.**
`tests/state_gas_clamp/`, 15 fill. I asked for the clamp to be asserted against a
deliberately over-generous refund. **The clamp is unreachable under the reference rules,**
and the one-sidedness lives one level earlier than `max(0, …)`: `sstore` credits state gas
only inside `if original_value == 0` (`storage.py:148-151`, CHECKED), so clearing a slot
that pre-dates the transaction earns **no state-gas refund at all**. Ten adversarial
shapes were measured for a negative net — in-frame set/clear, a DELEGATECALL child
clearing the parent's fresh slot with and without a reservoir, EIP-7702 (the only
`commit_state_gas` path), a CREATE aborting after `NEW_ACCOUNT` — and **every one came out
exactly 0 or +97,920. None negative.** Reframed to the observable hazard: create-1/free-0,
free-2 and free-4 all carry the **identical** block state-gas figure of 97,920, so
physically net-freeing transactions pay full price for creation and get nothing back.
`state-clamp-off` therefore **survives correctly** (`max(0,x) == x` for every measured
`x >= 0`), while an over-generous freeing rule is hidden from `block_state_gas_used` by
the clamp yet **leaks into the execution dimension** via `gas_used_before_refund`
(51,318 → 32,958). Detected by `state-free-credit` (9), `state-clamp-min` (6) and
`exec-gas-no-state-subtraction` (6, which only this archetype sees).

**15. Calldata-floor binding.** `gas_used = max(gas_used_after_refund, calldata_floor)`.
When the floor binds, a refund becomes invisible in `gas_used`. *Invariant:* a
calldata-heavy, execution-light tx pays the floor regardless of refunds.
*Broken?* EIP-7623 introduced it; EIP-7976 raised it.
**Status: PROVEN** — `tests/calldata_floor_refund/`, 12 fill, and it **asserts no gas
number at all**: two senders with equal balances send transactions differing only in the
callee's pre-state, and a third transaction commits `EQ(BALANCE(a), BALANCE(b))` to
storage — 1 when the floor binds, 0 on the `floor_has_slack` arm. Non-duplicative with
`eip7976_increase_calldata_floor_cost/`, which is `valid_from("EIP7976")` (Amsterdam only)
and derives every expectation from the fork, whereas the floor shipped at **Prague**.
Per-token cost verified independently: **64 gas/byte at Amsterdam** (`TX_DATA_TOKEN_FLOOR`
16 × 4 tokens/byte, base 15,000) and 40 at Prague/Osaka (base 21,000). Detected by
`floor-not-a-max` and `floor-token-7`; `floor-token-8` survives correctly, and the pair
locates the cliff at `TX_DATA_TOKEN_FLOOR = 7.74`.

### Reservoir family (EIP-8037-specific, forward-looking)

**16. Reservoir allocation is not subject to 63/64.** `drain_state_gas_reservoir` gives
the child the **entire** reservoir — the docstring states "there is no all-but-one-64th
rule for state gas". *Invariant:* a parent cannot retain state gas across a child call,
asymmetrically with execution gas. *Assert:* parent's post-call state-gas-funded work
fails where the equivalent execution-gas work would succeed.
**Status: PROVEN** — `tests/reservoir_allocation/`, 30 fill, all `valid_from("EIP8037")`.
Detected by `reservoir-6364` and `reservoir-half` with **perfect specificity — they fire
on this archetype alone**. The execution-gas half is pinned to a single gas: the threshold
is `tx.gas = 7,059,812 = 64 × 110,028 + 3,020 + 15,000`, every component named, predicted
and measured identical (CHECKED; note 110,028 falls inside the independently measured
fresh-slot floor bracket of (110,020 , 110,040]). Listed late because it pins a *new*
rule rather than an old one, which is exactly the kind of asymmetry a later fork might
"fix" and thereby break contracts written against Amsterdam.

### Intrinsic and prediction family (added after the first archetype round)

**17. Hardcoded intrinsic transaction cost.** A relayer reimburses a charge it cannot
observe: the intrinsic cost is deducted before the first opcode, `GAS` never sees it, and
no opcode reports it, so deployed meta-transaction code hardcodes **21,000**.
*Invariant:* the constant equals the charge actually levied.
*Broken?* **Yes, and not by a simple reduction.** EIP-2780 *decomposes* the flat charge:
`base_execution_gas = TX_BASE + recipient_execution_gas` (`transactions.py:777`), where
the recipient term is 0 for a self-transfer, `COLD_ACCOUNT_ACCESS` (3,000) for a normal
call, `+ TX_VALUE_COST` (6,000) if value-bearing, or `CREATE_ACCESS + init_code_cost` for
a create. `TX_BASE` itself went 21,000 -> 12,000.
*Measured (CHECKED):* Berlin..Osaka a flat 21,000 for any shape; Amsterdam **15,000**
zero-value and **21,000** value-bearing — so the hardcoded figure stays exactly right for
value-bearing calls and over-states by 6,000 for the common zero-value case.
*Witness:* Safe `execTransaction` reimbursement, GSN relay hubs, 4337 paymaster postOp.
**Status: PROVEN** — `tests/intrinsic_cost/`, 44 fill, detected by `tx-base-11000` (both
arms) and `tx-value-cost-5000` (value arm only), with perfect specificity.

**18. Dynamic-cost affordability prediction.** Costs that depend on a runtime value:
memory expansion (quadratic in size), copy per word, `EXP` per byte, `KECCAK256` per word,
`LOG` per byte, init code per word, access list per entry. A contract that *sizes* an
operation to fit a budget must predict a **formula**, not a constant.
*Invariant:* the predicted cost of the chosen size is affordable.
*Why distinct from #3:* a reprice changes the formula's coefficient, so the prediction
error scales with size — a contract correct at small sizes fails at large ones.
*Broken?* `OPCODE_EXP_PER_BYTE` went 10 -> 50 (EIP-160); EIP-3860 added an init-code word
charge; EIP-7981 raised access-list cost.
*Witnesses (corrected against `registry/L2-bytecode.jsonl` — the figures circulated earlier
read the `instances` column, which counts witnessing program points, as addresses):*
`mem.mcopy` **108,056 runtimes / 145,049 addresses / 730,841 program points**, FP 0.0003,
10.87% of every mainnet runtime scanned; `pre.call.a4` (the identity precompile as a memcpy,
the pre-`MCOPY` form) **3,367 / 24,448 / 92,537**, FP 0.0, witnessed on a major NFT exchange
**Status: PROVEN** — `tests/dynamic_cost_prediction/`, **869 fill** Berlin→Amsterdam,
`pass(135)` at Amsterdam. Three arms, because one instrument cannot reach all seven
coefficients: a *prediction equality* (the contract evaluates its formula in EVM bytecode on
a calldata length and the result is compared with the measured `GAS` delta, one coefficient
per test), a *two-sided affordability bracket* (a frozen budget buys N words and not N+1),
and *differencing* (two `CREATE2`s one word apart, the only way to see the 8 gas of
`KECCAK256_PER_WORD` + `CODE_INIT_PER_WORD` against a measured 195,624-gas charge). All 14
`cls18-` mutations are
DETECTED — **eight dearer and six cheaper**, with `cls18-exp-per-byte-10` restoring the
pre-EIP-160 value exactly rather than inventing one — and every failure count was predicted
from the arithmetic before the run and came back identical.
*The result that distinguishes this class from #3 is measured, not argued:*
`cls18-memory-quadratic-256` fails 5 of 8 memory sizes and **survives the other three for an
exact arithmetic reason** — `floor(w**2/512) == floor(w**2/256) == 0` for every `w <= 15` —
so the 480-byte and 512-byte params locate the cliff to a single word. The cheaper divisor
(`512 -> 1024`) has a *different* cliff, at `w = 32`, because `floor(256/512) ==
floor(256/1024) == 0`: a contract is more exposed to memory getting dearer than cheaper, by
one octave of size. The `MCOPY` bracket sits exactly on its budget, 100,000 of 100,000, with
the quadratic term accounting for 65,296 of it.
*Specificity (unrestricted column, 24 archetypes):* **11 of the 14 have exactly one
detector** — nothing else in the corpus can see a copy, keccak, log, exp, init-code or
identity-precompile coefficient, nor the memory quadratic divisor in its dearer direction.
The three shared rows are correct cross-checks: `MEMORY_PER_WORD` is literally one word of
expansion inside `hardcoded_cost_equality`'s documented 17-gas instrument, and
`forwarding_prediction` reimplements `calculate_message_call_gas`'s memory-cost term, which
#5 predicted it would. That sharing is **graded by direction** — the cheaper memory
mutations fire `forwarding_prediction` and the dearer one does not.
*Deliberately not covered, with the reason:* **access-list cost per entry**. It is levied in
`calculate_intrinsic_cost` before the first opcode and no opcode reports it (the instrument
for that dimension lives in `tests/intrinsic_cost/`), and more decisively the class premise
fails — an access list is sized by the transaction sender off chain, so no deployed contract
predicts it and there is no idiom to pin.
*Prior art is structurally incapable of covering this (CHECKED):*
`tests/cancun/eip5656_mcopy/test_mcopy_memory_expansion.py:106` sets the transaction limit to
`callee_bytecode.gas_cost(fork)`, and `tests/shanghai/eip3860_initcode/test_initcode.py:553`
sets `expected_gas_usage = create_code.gas_cost(fork) + initcode.gas_cost(fork)` — the
budget *is* the cost, so a coefficient change moves both sides together.

**19. Loop-bound per-item affordability gate.** `while (i < n && gasleft() > PER_ITEM)`.
Ubiquitous in batch processors, liquidation loops, and keeper/automation contracts.
*Invariant:* `PER_ITEM` correctly bounds one iteration's cost.
*Witness:* L5 measured per-item sibling fan-out at 435,998 frames across 30 runtimes
(corrected for a 23.11% precompile-loop FP rate).
**Status: PARTLY REDUNDANT, and saying so is the result.** Its *budget* invariant
("`PER_ITEM` >= cost of one item") is mechanically identical to #1 with the threshold as
the budget — the difference is only who chose the number, which is sociological rather
than behavioural. Building a separate survival test here would duplicate #1. Its
genuinely distinct content is the *gate* itself, and that turned out to be a different
invariant, split out as #20 below.

**20. `gasleft()` as a sufficient statistic for affordability.** The gate above assumes
that if `gasleft()` is below the cost of some work, the frame cannot do that work.
*Invariant:* `gasleft()` tells a frame what it can afford.
*Why rule-dependent:* `GAS` pushes `gas_meter.gas_left` only, never the reservoir
(`vm/instructions/control_flow.py:143`), while state charges draw from the reservoir
first; `drain_state_gas_reservoir` gives a child the entire reservoir with no 63/64 rule.
*Broken?* **Yes, by EIP-8037.** Measured: with a 200,000 reservoir and 26,000 forwarded
execution gas, a frame reports `gasleft() < 97,920` and completes a 97,920-state-gas
write anyway.
*Failure direction — the one nothing else here covers:* not an out-of-gas but an
**unnecessary refusal**. The gate declines work the frame could have performed, the batch
silently does less, and nothing reverts.
**Status: PROVEN** — `tests/gasleft_sufficiency/`, 25 fill, three arms (pre-8037 sound /
Amsterdam-without-reservoir control / Amsterdam-with-reservoir violated), detected by
`drain-no-reservoir` and `gas-reports-reservoir` with perfect specificity.

### Semantic-identity family (found by L2; the taxonomy above could not reach it)

**Structural correction.** Classes 1–20 are all gas-shaped: each asks "what happens when
a price moves". L2's bytecode sweep of 994,414 distinct mainnet runtimes surfaced 24
high-prevalence records that map to **none** of them, and they are not a miscellany —
they form a coherent family whose invariants are about **meaning, not cost**. A fork can
change semantics without changing any price, and EIP-7702 is the proof: it broke the
single most deployed identity idiom on Ethereum while repricing nothing.

The mission scope was always "gas accounting, pricing, **or execution semantics**"; the
catalogue had drifted gas-only. Prevalence figures below are L2's, counted as distinct
runtime code hashes and addresses, each with a measured FP rate.

**21. Return-data pass-through fidelity.** A proxy or router copies a child's revert data
out verbatim and re-reverts with it.
*Invariant:* the caller's caller observes the original revert payload, unchanged.
*Rule-dependent on:* `RETURNDATASIZE`/`RETURNDATACOPY` semantics, and — the gas-shaped
half — the memory-expansion and copy cost of a large payload, since bubbling is only
possible if the copy is affordable.
*Witness:* **723,118 runtimes / 4,755,135 addresses**, FP 0.0 — the largest measured
population in the entire corpus. Plus `proxy return-data pass-through` at 76,218
runtimes.
**Status: PROVEN** — `tests/returndata_fidelity/`, 88 fill. Two independent arms, and the
mutations separate them cleanly: `returndatasize-halved` breaks all 12 (semantics) while
`rdcopy-per-word-2000` breaks only the 3 frozen-budget tests (cost).

**22. Code presence as an identity test.** `isContract(a) == (a.code.length > 0)`.
*Invariant:* an account reporting code is a contract, and one reporting none is not.
*Broken?* **Yes, already shipped.** A delegated EOA stores
`EOA_DELEGATION_MARKER || address` where the marker is `b"\xef\x01\x00"`
(`vm/eoa_delegation.py:36`), giving 23 bytes, and `EXTCODESIZE` pushes
`U256(len(code))` with no delegation resolution
(`vm/instructions/environment.py:357`). So from Prague, `isContract(an EOA)` is true for
any EOA that has ever signed an authorization.
*Witness:* **618,693 runtimes / 2,417,615 addresses**, FP 0.0.
**Status: PROVEN** — `tests/code_presence_identity/`, 31 fill.

**23. Counterfactual address validity.** A contract derives an address it has not yet
deployed to — `keccak256(0xff || deployer || salt || keccak256(initcode))[12:]` for
CREATE2, or the RLP-and-nonce form for CREATE — and commits to it in advance.
*Invariant:* the derived address equals where the contract will actually land.
*Rule-dependent on:* the address-derivation rules themselves, and on EIP-7997's
deterministic factory.
*Witness (corrected against `registry/L2-bytecode.jsonl` — the figures circulated earlier
read the `instances` column, which counts witnessing program points, as addresses):*
`adr.create2_derive` **2,723 runtimes / 2,945 addresses / 3,217 program points**, FP 0.0,
CHECKED, calibration positive a major NFT exchange's conduit derivation; `adr.create_derive`
**187 / 205 / 366**, FP **0.25**, INFERRED, with one named hand-checked witness, a gas-token contract
`<address withheld>`. Corroborated source-side by L1's *"CREATE2
address derived in source"* at **8,172 runtimes / 22,270 confirmed files**, exact count mode,
hand-measured precision 1.0.
**Status: PROVEN** — `tests/counterfactual_address/`, **179 fill** Berlin→Amsterdam,
`pass(27)` at Amsterdam. Four tests: the CREATE2 derivation built **in EVM memory** against
where `CREATE2` lands, the escrow pre-funding commitment (value sent to an account that does
not exist yet, then deployed over, then called), the RLP-and-nonce form parametrised over
nonce 1/2/3, and the EIP-7997 factory's canonical address as a bytecode literal.
*All 8 `cls23-` mutations are DETECTED with **perfect specificity — 8 for 8, one detector
each**.* No other archetype can observe an address derivation. The failure counts partition
the 27 exactly and were predicted before the run: **18** for every CREATE2-preimage mutation
(the three CREATE2-based tests, nonce arm untouched), **9** for every CREATE mutation (the
nonce arm only), **27** for the opcode mutation. So the two derivations are *discriminated by
signature*, not merely both covered.
*Three results worth keeping.* (a) `cls23-create-nonce-not-incremented` is **graded**: 6 of 9,
because `nonce_1` is unaffected while `nonce_2`/`nonce_3` collide — a single-nonce test would
have read "survives" and logged a coverage gap that was not one. (b)
`cls23-sha3-opcode-salted` perturbs the `KECCAK256` **opcode** and leaves `utils/address.py`
alone, so the *contract's* side of the equality moves while the landing site stays put; **no
other archetype in the corpus detects it**, which makes this the only test that the hash the
EVM exposes to contracts is the hash the protocol uses. Every official counterfactual test
derives in Python and is structurally blind to that direction. (c) Direction is not a
meaningful axis for a semantic equality, so the two-sidedness here is provided differently:
each *input* of each derivation is mutated separately, and **three of the eight are
loosenings** (salt dropped, nonce dropped, nonce not incremented) that collapse many derived
addresses onto one.
*Prior art does not cover it (CHECKED):* seven official files derive counterfactual addresses
via `compute_create2_address(...)` in Python — `eip7997_deterministic_factory_contract/
test_factory.py` (1,437 lines), `eip8037_state_creation_gas_cost_increase/
test_state_gas_create.py:675,2805`, `eip6780_selfdestruct/test_collision_selfdestruct.py:56`
and `test_dynamic_create2_selfdestruct_collision.py:124,351,626`,
`eip2929_gas_cost_increases/test_warm_status_revert.py:185`,
`eip7928_block_level_access_lists/test_block_access_lists.py:4251`,
`eip8246_selfdestruct_no_burn/test_selfdestruct_no_burn.py:571`. **Nothing in `tests/` hashes
a CREATE2 preimage with `SHA3`**; the only EVM-side `SHA3` in the 7997 directory hashes the
factory's own code (`test_factory.py:86`). The 7997 tests are also all
`valid_from("EIP7997")`, while this derivation has been deployed since Constantinople.

**24. Transient-storage lifetime, and its state-gas immunity.** `TSTORE`/`TLOAD` used as
an in-transaction lock or scratch slot.
*Invariant, two-sided:* the slot is visible for the whole transaction and is gone at its
end — and, separately, **transient storage carries no state gas**, so it is structurally
immune to every state-gas repricing in this catalogue.
*Why worth pinning:* the immunity is load-bearing for a large population. A fork that
gave transient storage a state cost would break all of it at once, and nothing currently
asserts that it has none. (This mirrors a prior result: a widely used reentrancy guard
uses 1/2 rather than 0/1, so its slot never holds zero and no zero-boundary refund rule
touches it.)
*Witness:* transient reentrancy lock 2,315 runtimes / 4,528 addresses (FP 0.0); written
before an external call 4,091 / 14,167 (FP 0.0); written and never cleared 2,005 / 5,478
(FP 0.125). L5 separately: `TSTORE` 3,938,758 occurrences / 12,603 runtimes.
**Status: PROVEN — `tests/transient_storage_lifetime/`, 141 fill, Cancun→Amsterdam.**
Half (a), the lifetime semantics, is **deliberately not rebuilt**: it is already covered by
`tests/cancun/eip1153_tstore/`, 11 files and 2,698 lines. Half (b), the immunity, had
**zero** coverage and structurally so — that suite derives every gas expectation from the
fork (`Op.TLOAD.gas_cost(fork)`, `bytecode.gas_cost(fork)`,
`callee_bytecode.gas_cost(fork) - 1`) and mentions neither state gas nor the reservoir
(0 grep hits, CHECKED).
*Measured (CHECKED):* the in-frame gas delta across a `TSTORE` is **117 on Cancun,
Prague, Osaka and Amsterdam alike**, while over the same four forks a fresh slot moved
22,117 → 110,037 and a persistent update 5,017 → 12,117. Two observables are needed,
because each is blind where the other works: with a **zero reservoir** a state charge
spills into `gas_left` and shows up in `GAS`; with a **positive reservoir** it does not,
and only exhaustion is visible. The second arm carries a calibration param — a reservoir
reduced by one single state byte (97,920 → 96,390, 1.6%) stops funding the same write —
so the immunity is measured to within half a state byte rather than asserted.
*The negative control is L2's `sto.lock12` as suggested, and it paid off twice:* a
persistent **1/2** lock is state-gas immune too, by a different mechanism (`sstore`
charges `STORAGE_SET` only inside `if original_value == 0`, `storage.py:145`), while a
**0/1** lock is not and has **already moved from working to out-of-gas** inside EIP-4337's
frozen 50,000-gas budget. Detected by `cls24-tstore-charges-state-gas` (18),
`cls24-tstore-charges-one-state-byte` (9), `cls24-tload-always-zero` (9) and
`cls24-transient-revert-not-rolled-back` (3), all four with **perfect specificity**. The
archetype detects 15 mutations in total and **both reprice directions**, including
`cls12-cold-read-700`, the downward reprice that all six budget-sufficiency archetypes
survive.
*Also measured:* the lock round-trip's frozen-budget floor is **(3,250 , 3,260]** on
Cancun/Prague/Osaka and **(3,640 , 3,660]** at EIP-8037, so ERC-7579's 3,229-gas
`postCheck` convention cannot host a transient reentrancy guard that makes an external
call **on any fork**.

**25. Caller identity as an EOA test.** `tx.origin == msg.sender` used to assert "called
directly by a wallet, with no contract in between".
*Invariant:* the equality holds exactly when no frame that **rewrites the caller**
intervenes. The brief said "no contract frame", and measurement forced the correction:
`DELEGATECALL` passes its own caller through (`caller=evm.caller`, `system.py:866`, the
only call-like instruction that does), so the equality has held through a contract frame
since Homestead, by design. Every deployed proxy depends on that, so it is pinned here as
a control rather than reported as a break.
*Broken?* Weakened by EIP-7702 (a delegated EOA executes code while remaining the origin)
and by account abstraction, where the entry point is the sender.
*Witness:* 8,097 runtimes / 6,126 addresses, FP 0.0; L1 independently 24,044 addresses /
19,017 runtimes on a related shape.
**Status: PROVEN — `tests/eoa_caller_identity/`, 106 fill (of 114 collected; the engine fixture format is not generated before Paris), Berlin→Amsterdam.**
*Measured (CHECKED), `ORIGIN==CALLER` / `EXTCODESIZE(CALLER)`:* direct 1/0; one relay
frame 0/35; 4337 entryPoint→account 0/35; DELEGATECALL proxy 1/0; **7702 self-sponsored
1/23**; 7702 sponsored by a relayer 0/23.
*The result:* for a delegated EOA the two deployed "is this an EOA" idioms answer
**oppositely for the same account in the same block** — `code.length > 0` says contract
(class #22), `tx.origin == msg.sender` says wallet. This class is the caller-side half of
that break. The test makes the delegated code call the gate **twice in one transaction**,
both passing, so the concrete harm is asserted and not merely described. The sponsored
arm is the boundary that keeps it honest: the hazard needs the delegated EOA to be the
*origin*, not merely delegated.
*The other direction is live today with no fork change:* under ERC-4337 the bundler is
the origin and the smart account is the sender, so the gate **rejects a real human**. A
false negative, and the reason the equality was never a usable wallet test.
Detected by `cls25-origin-is-the-current-caller` (9), `cls25-caller-is-the-tx-origin` (9),
`cls25-delegation-length-24` (6) and `cls25-delegatecall-rewrites-the-caller` (3), all four
with **perfect specificity**. The archetype detects **no gas mutation at all** — correctly:
it also detects `extcodesize-hides-delegation`, which until now had exactly one detector,
so the 23-byte designator is now pinned from **both** sides of a call.

**26. SELFDESTRUCT destroys the contract.** A contract calls `SELFDESTRUCT` to retire
itself, and the deployed idiom assumes code and storage are gone afterwards.
*Invariant:* after `SELFDESTRUCT`, the account has no code and no storage.
*Broken?* **Yes, at Cancun.** EIP-6780 deletes the account **only if it was created in the
same transaction** — `if originator in tx_state.created_accounts:`
(`amsterdam/vm/instructions/system.py:771`). For any pre-existing contract the balance
still sweeps but **the code and storage remain**, so a "retired" contract stays callable.
It also interacts with class #22: `SELFDESTRUCT` no longer zeroes code, so `isContract`
keeps returning true for a destroyed contract.
*Witness:* L1 — selfdestruct reliance at **175,573 addresses / 8,050 runtimes**, plus
246,967 addresses / 39,361 runtimes carrying comments about selfdestruct behaviour
(FP 0.0, hand-validated).
**Status: DELIBERATELY NOT BUILT — already covered by the official suite, and duplicating
it would violate SCHEMA's prior-art rule.** `tests/cancun/eip6780_selfdestruct/` is
**7 files and 5,103 lines**; it probes `EXTCODESIZE`/`EXTCODEHASH` after the call
(`test_selfdestruct.py:280,285`), uses `blockchain_test` for cross-transaction
observation, and includes `test_selfdestruct_clears_nonce_and_storage` and
`test_selfdestruct_in_delegate_context`. L4 independently rated the
`selfdestruct-semantics` axis "well-covered — the strongest impact coverage outside
eip8037". The class is recorded here so the deployed population is on file for phase-3
ranking, not because a test is owed. **This is what a correct "do not build" verdict looks
like: cite the coverage, state the population, move on.**

Also surfaced, mapping to existing classes rather than new ones: `MCOPY` for memory
movement (108,056 runtimes / **145,049 addresses** / 730,841 program points, FP 0.0003)
and the identity precompile used as a memory copy (3,367 / **24,448** / 92,537, FP 0.0)
both belong to **#18**
(dynamic-cost prediction); `BASEFEE` in committed fee arithmetic (861 runtimes),
`CHAINID`, `BLOCKHASH` and `BALANCE` branch tests are environment-field dependencies.
One curiosity worth keeping: **`gasleft()` mixed into a hash preimage** (14 runtimes,
FP 0.25) is a universal gas canary — *any* repricing anywhere changes its output.

**A ready-made negative control, from L2.** Its `sto.lock12` record (6,785 runtimes,
FP 0/8) is a 1/2-valued lock whose slot never holds zero, so no zero-boundary refund rule
can touch it. That is the correct negative control for class #9 and should be used as
one rather than written from scratch.

**27. Environment-field semantics (CANDIDATE, surfaced by the phase-2 merge).** A
contract branches on, or commits arithmetic over, an environment field: `BALANCE`,
`CHAINID`, `BLOCKHASH`, `BLOBHASH`, `PREVRANDAO`, `block.basefee`.
*Invariant:* the field means what the contract assumed when it was written.
*Broken?* **Yes, historically:** EIP-4399 turned `DIFFICULTY` into `PREVRANDAO` — same
opcode, entirely different meaning — and EIP-2935 changed the blockhash window.
*Witness:* `BALANCE` in a branch 46,677 addresses / 12,713 runtimes (FP 0.0); `CHAINID` in
a branch 12,150 / 11,662 (FP 0.0); `BLOCKHASH` in a branch 633 / 421 (FP 0.1667);
`block.basefee` read 8,276 / 2,412; `BLOBHASH` read 879 (FP 0.6303 — weak);
`PREVRANDAO` mixed into a hash 38 / 22.
**Status: CANDIDATE, deliberately unassigned.** It is neither a gas rule nor a
semantic-identity rule, so it does not belong to either existing family, and
force-fitting it into #18 would mislabel it. Recorded rather than absorbed, per the rule
that "maps to no class" is a finding to chase. Note L4 rated the `block-fields` axis
well-covered officially, so check `tests/paris/`, `tests/cancun/eip4844_blobs/` and
`tests/prague/eip2935_historical_block_hashes/` before building anything here.

---

## Cross-cutting blind spot: repricing DOWNWARD

Every class above was written assuming costs **rise**. That is wrong, and measurably so.
Diffing every `Final[...] = Uint(n)` constant in `vm/gas.py` across all 15 semantically
distinct mainnet forks yields 15 constants that changed value, and **five moved down**:

```text
TX_BASE                      21,000 -> 12,000    (Amsterdam, EIP-2780)
TX_DATA_PER_NON_ZERO             68 -> 16        (Istanbul, EIP-2028)
PRECOMPILE_ECMUL             40,000 -> 6,000     (Istanbul, EIP-1108)  6.7x cheaper
PRECOMPILE_ECADD                500 -> 150       (Istanbul, EIP-1108)
PRECOMPILE_ECPAIRING_BASE   100,000 -> 45,000    (Istanbul, EIP-1108)
  (and PRECOMPILE_ECPAIRING_PER_POINT 80,000 -> 34,000)
```

A reduction is not a milder version of an increase; it breaks a **different population**:

- #1 frozen-budget survival is *unaffected* by a reduction — an over-provisioned budget
  still fits. Reductions are invisible to the entire archetype.
- #12 two-sided OOG probe inverts: a target that *should* fail the probe now returns
  inside the literal, so "incapable" reads as "capable". EIP-1108 is a real 6.7x
  reduction, so this arm is witnessed, not hypothetical.
- #17 over-reimburses rather than reverting: a funds leak, not a liveness failure.
- #8 refund cap: *loosening* the divisor breaks anything treating post-refund `gas_used`
  as stable, which is the opposite population from the one EIP-3529's tightening killed.
- #14 `settled_state_gas_used = max(0, state_gas_used)` clamps only the negative side, so
  a change making clears *more* generous is absorbed silently and never reaches block
  accounting.

**Rule for every archetype from here on: state which direction it detects, and mutate in
both.** A test that only fires on an increase covers half its rule.

---

## What this changes about the plan

1. **Phase 4 is not one test generator but ~15.** `PLAN.md` phase 4 says "generate EEST
   tests"; it should say "generate tests per archetype", because the archetypes have
   incompatible shapes. A single generator would silently emit archetype-1 tests for
   archetype-2 and archetype-10 patterns and assert false things.
2. **Priority order**, by (historical precedent) x (witnessed population) x (failure
   severity), not by how easy the test is:
   - **#7 stipend-funded fallback** — the only class with a famous historical break
     (EIP-1884) *and* zero official coverage from any angle. ~96,865 real witnesses.
   - **#10 gas monotonicity** — worst failure mode (silent wrap → wrong reimbursement),
     252,006 addresses, asserted nowhere on pre-8037 forks.
   - **#4 retained-gas epilogue** — 245,595 addresses, FP 0/18, no literal involved so
     nothing else can catch it.
   - **#12 two-sided probe** — quietest failure; commits down the wrong branch silently.
   - **#8 refund cap** — proven break (`//2 → //5`), never tested behaviourally.
3. **Archetype 2 must exist before we touch the sub-floor budgets** that L3 measured, or
   we will assert survival for budgets that provably cannot survive.
4. Each archetype needs its own mutation list in phase 5. Archetype 1 mutates
   `COST_PER_STATE_BYTE`; archetype 4 must mutate the retention divisor **and** an
   epilogue opcode cost; archetype 10 must mutate whether a clear credits `gas_left`;
   archetype 8 must mutate the refund divisor. A mutation that the archetype cannot
   detect is a sign the archetype is wrong, not that the rule is safe.

---

## Expansion-wave classes (#28–#33)

Built in the separate wave at `expansion/`, on rule surfaces the classes above
never touched. Compact entries: each archetype's README carries the full invariant,
witness, measurements and mutation table.

**28. An undefined opcode byte halts, and deployed code relies on it.**
*Broken?* Yes, repeatedly — `0x5F`→`PUSH0` (Shanghai), `0x1E`→`CLZ` (Osaka),
`0x4B`→`SLOTNUM` and `0xE6/0xE7/0xE8`→`DUPN/SWAPN/EXCHANGE` (Amsterdam). Assignment turns a
guaranteed halt into successful execution and **moves no price at all**.
*Measured:* the semantic flip and the gas forfeit are **one event** — all three observables
flip together in all 64 fork×byte cells; an undefined byte burns all gas exactly as
`INVALID` does (402,634 vs 7,642 consumed on a 400,000 grant, a 16–27x swing with no
constant moved); and the flip is **depth-conditional**, `0x4B`/`0x5F` breaking a guard at
stack depth 0 while `0xE6`/`0xE7` need 17/18 — EIP-8024's assignments are accidentally
shielded by their own stack requirements.
*Witness:* the `0xFE` idiom at **180,402 runtimes / 2,466,439 addresses** (a major stablecoin, a major DEX router, a widely deployed smart-account wallet hand-disassembled). **Clean hand-measured negative: 0 of 11
sampled and 0 of 93 exhaustive survivors use a *non*-`0xFE` undefined byte reachably** — the
idiom survived four EIPs because compilers picked the one reserved byte.
**PROVEN** — `undefined_opcode_halt/` (198), `undefined_opcode_gas_forfeit/` (154),
`opcode_assignment_code_identity/` (37); 16/16 mutations detected.

**29. An unassigned precompile address returns success with empty return data.**
*Broken?* Yes — 0x0a (Cancun), 0x0b (Prague), 0x100 `P256VERIFY` (Osaka), each with a
**different break shape**: 0x0a and 0x0b flip success 1→0 and burn the forwarded budget,
while 0x100 does not move the success channel at all — only `RETURNDATASIZE`, 0→32.
*Measured:* a widely used P256 library presence probe returns `success = 1` on all
six forks, and `EXTCODESIZE`/`EXTCODEHASH`/`BALANCE` read `0/0/0` for a live precompile, a
future one and a never-assigned address alike — so **class #22's instrument is structurally
blind here**, exactly as that library's own source comment says.
**PROVEN** — `unassigned_precompile_identity/` (75); 4 detecting mutations, **none of which
changes a gas constant**.

**30. A precompile input size that used to be admissible is rejected.** EIP-7823's modexp
bounds. *Largely covered officially* (`test_modexp_upper_bounds_fork_transition`); the
genuinely new assertion is that an oversized input stays unaffordable at **any** price
(2,000,000 gas, 360× the old cost, still fails) — admissibility is not affordability.
**PROVEN** — `precompile_input_admissibility/` (50).

**31. A hardcoded precompile budget.** Class #1's shape on a new rule, and it produced a
**live deployed break located to the gas**: a deployed passkey validation module
`<address withheld>` does `staticcall(1500, 0x5, …)` for
`modexp(value, p-2, p)`, which costs **1,360 on Berlin→Prague and 4,080 from Osaka**
(EIP-7883 dropped `GQUADDIVISOR` 20→3). It worked for five forks and **fails from Osaka**,
reverting passkey verification in an immutable module. Its sibling a sibling fallback handler
`0x2e7f1dae…` at `staticcall(14000, …)` survives, so the two deployed literals bracket the
change. **PROVEN** — `precompile_price_bracket/` (72); 22 mutations, 10 dearer and **9
cheaper**.

**32. A per-transaction gas ceiling.** EIP-7825 caps `tx.gas` at 2²⁴.
*Measured:* asking for 17,777,216 gas is **granted on Prague, rejected on Osaka, and
silently truncated on Amsterdam** to 16,762,214 — identical to the at-cap grant, so 8M extra
gas buys zero execution and nothing reverts. The cap and EIP-8037's reservoir are the **same
boundary to one gas**: the reservoir begins at exactly `2²⁴ + 97,920`.
**PROVEN** — `tx_gas_cap_ceiling/` (106).

**33. A hardcoded maximum code size, and newly-emitted transfer logs.**
*Measured:* at Amsterdam a 24,577-byte contract deploys while a validator holding the
literal 24,576 commits a rejection (witness: 338 addresses / 120 runtimes, precision 1.0).
And a **cross-EIP result neither EIP is wrong about alone** — EIP-7954's new 65,536-byte
maximum is **undeployable in a 60M-gas block**, because EIP-8037 prices code deposit at
1,530 *state* gas/byte (100,453,680 state gas); the official 7954 suite passes only because
its default test block is twice mainnet's size.
**PROVEN** — `code_size_gate/` (56), `transfer_log_count/` (47). The zero-value-no-log rule
is **doubly guarded** (call site *and* `emit_transfer_log`), so no single-site mutation can
falsify it; both were written and both survive, registered as an explained-survival pair.
