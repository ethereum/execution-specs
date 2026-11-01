# Coverage gap — rule axes vs the official test suite

Owner: lens **L4**. Companion to `docs/RULE-AXES.md` (60 axes). This file answers
one question per axis: **if a future fork broke a deployed contract that depends on
this axis, would any existing official test fail?**

Target of the survey: `/home/devops/toni/datanalysis/eip-8037/engine/eels/tests`
(pinned EELS 16898000) — 2,666 Python files, 80,464 lines in the per-fork/per-EIP
tree plus `ported_static/` at 329,053 lines across 2,102 files. **CHECKED**:

```sh
cd engine/eels/tests && find . -name '*.py' | wc -l           # 2666
find . -name '*.py' | xargs wc -l | tail -1                   # 80464 (excl. ported_static depth)
for d in */; do echo "$(find $d -name '*.py' -exec cat {} + | wc -l) $d"; done | sort -rn
```

## 0. The central finding

**No frozen-budget survival test exists for any *repriced* operation.** That is the
precise claim, and it is the one the corpus rests on.

The weaker phrasing "the suite has no frozen-budget tests" is wrong and invites
rebuttal. Frozen-budget tests that assert *survival* do exist — the precompile
directories are the clearest case: they hand a precompile a hardcoded gas figure and
assert it returns the right answer. But they target operations whose gas has never
moved, so they are **structurally incapable of firing on a repricing**. The set
{frozen budget} ∩ {asserts survival} ∩ {targets a repriced operation} is empty.

That this is a *design property* rather than an oversight is **INFERRED** — the
docstrings below say what the tests do and instruct maintainers not to hardcode, but
attributing the intent to specific EIP work without reading the PRs stays INFERRED.
A conformance suite that froze budgets would turn every intentional repricing into
noise, so the design is defensible on its own terms; it simply leaves the
deployed-code question unasked.

Five independent pieces of evidence, all **CHECKED**:

1. **Every budget is derived from the fork.** 267 test files call a fork-derived gas
   helper. In the EIP-8037 suite specifically,
   `fork.transaction_intrinsic_cost_calculator()` appears 168 times,
   `fork.transaction_gas_limit_cap()` 45, `fork.transaction_data_floor_cost_calculator()`
   18, `fork.max_refund_quotient()` 14, `fork.call_value_stipend()` 10,
   `fork.max_code_size()` 8. A repricing moves the expectation in lockstep with the
   rule, so the assertion cannot break.

   ```sh
   grep -rlE "gas_costs\(|memory_expansion_gas_calculator|transaction_intrinsic_cost_calculator" --include='*.py' . | wc -l   # 267
   grep -rhoE "fork\.[a-z_]+\(\)" amsterdam/eip8037_state_creation_gas_cost_increase/ | sort | uniq -c | sort -rn
   ```

2. **Even the tests named for a fixed gas budget derive it.** The closest thing in the
   suite to this project's `fixed-gas-budget` axis is the EIP-8037 "fixed-gas probe"
   family, and the probe is computed from the fork:

   ```python
   # tests/amsterdam/eip8037_state_creation_gas_cost_increase/test_state_gas_sstore.py:1284
   probe_gas = Op.SSTORE(0, 1).gas_cost(fork) - 1
   ```
   `test_call_frame_credit_repays_spill_before_fixed_gas_probe`
   (`test_state_gas_cross_frame_refund.py:609`) and
   `test_fixed_gas_probe_after_clearing_frame` (`:675`) both use this form. They assert
   that a probe one gas short of an SSTORE fails — a statement about the *mechanism*,
   which stays true under any repricing. They do not assert that a budget a real
   contract hardcoded still suffices.

3. **The legacy frozen budgets were deliberately de-frozen during the port, and the
   maintainers' instruction is explicit.** From
   `tests/ported_static/stEIP150Specific/test_call_and_callcode_consume_more_gas_then_transaction_has.py:7-15`:

   > `@manually-enhanced: Do not overwrite. The post-state asserts storage[8] = 0x8D5B6
   > captured by Op.GAS, which depends on the exact post-intrinsic execution budget. The
   > original hardcoded gas_limit of 600_000 was built against Cancun's TX_BASE of 21_000;
   > EIP-2780 lowers the intrinsic for non-self non-value txs, so gas_limit is derived as
   > 600_000 + (intrinsic - 21_000) from transaction_intrinsic_cost_calculator to shift by
   > the fork intrinsic delta and keep the Op.GAS assertion correct. ... Do not hardcode
   > the literal gas_limit.`

   ```python
   intrinsic = fork.transaction_intrinsic_cost_calculator()()   # :103
   gas_limit = 600_000 + (intrinsic - 21_000)                   # :104
   post = {target: Account(storage={0: 18, 8: 0x8D5B6, 9: 1, 10: 1})}   # :113
   ```

   This is correct for a *conformance* suite — a frozen budget would turn every
   intentional repricing into noise. But it means the legacy EIP-150 tests, which were
   originally the closest thing to a fixed-budget tripwire, no longer act as one. When
   EIP-2780 moved the intrinsic, the response was to **re-baseline the budget** so the
   exact `Op.GAS` assertion stayed true.

4. **The gas-test generator refuses to run before Berlin, naming CALL gas changes as
   the reason.** `packages/testing/src/execution_testing/tools/utility/generators.py:522-524`:

   ```python
   if fork < Berlin:
       raise ValueError(
           "Gas tests before Berlin are not supported due to CALL gas changes"
       )
   ```

   So the forks that introduced the 63/64 retention (Tangerine Whistle, EIP-150) and
   that carried the EIP-1884 repricings (Istanbul) cannot be gas-tested by this tooling
   at all. Every axis whose breaking change predates Berlin is therefore tested, if at
   all, only in its *post-Berlin* form.

5. **Even the code-deposit cost is reached through a fork-derived accessor.**
   `packages/testing/src/execution_testing/forks/forks/forks.py:119` sets
   `CODE_DEPOSIT_PER_BYTE=200` once, in the Frontier gas schedule, and `:734` computes
   `gas_costs.CODE_DEPOSIT_PER_BYTE * code_deposit_size`. There are 4 occurrences in the
   whole forks package and none of them is a per-fork override, so a test's expected
   deposit cost is always whatever the fork object reports.

   ```sh
   grep -rn CODE_DEPOSIT_PER_BYTE packages/testing/src/execution_testing/forks/ | wc -l   # 4
   ```

**Why this is the gap this project fills.** The suite asks "is the rule implemented as
specified?" A regression corpus derived from deployed code asks "does the contract that
depends on the old rule still work?" Those come apart exactly when a repricing is
intentional — which is every repricing. `SCHEMA.md` §4.1 forbids asserting raw gas
numbers for precisely the reason the suite asserts them: an exact-number assertion
protects nothing and is re-baselined on contact.

### 0.6 A large slice of the frozen-budget legacy corpus retires at Prague

**CHECKED.** 109 files under `tests/ported_static/` (110 across all of `tests/`) carry
`@pytest.mark.valid_until("Prague")`, so they do not run on Amsterdam:

```sh
grep -rl 'valid_until("Prague")' tests/ported_static/ | wc -l        # 109
grep -rl 'valid_until("Prague")' tests/ported_static/ | cut -d/ -f3 | sort | uniq -c | sort -rn
#   26 stStaticCall   17 stRandom   13 stRandom2   13 stQuadraticComplexityTest
#    8 stSystemOperationsTest   4 stDelegatecallTestHomestead   4 stCallCreateCallCodeTest ...
```

The legacy corpus is where the genuinely frozen budgets lived, inherited from the old
JSON fillers. Two things are happening to it at once: the tests that survive are being
rebased to fork-relative expressions (§0.3), and 109 of them are being retired outright
at Prague. Both directions remove frozen-budget coverage going into Amsterdam. Why each
specific directory was retired is **INFERRED** — the markers state the bound, not the
reason.

### Corollary: where the suite *does* assert exact gas, it is a brittle tripwire

A minority of ported tests persist an `Op.GAS` reading into storage and assert the exact
value (`storage[8] = 0x8D5B6` above). These *do* fail under a repricing, but they fail
unconditionally and uninformatively — they cannot distinguish "a real idiom broke" from
"the number moved as intended". They are re-baselined, not investigated. Counted as
`conformance-only` below, never as `impact`.

## 1. How to read the matrix

| column | meaning |
|---|---|
| **kind** | `conformance` = asserts exact gas/mechanics; `impact` = asserts a behavioural invariant a deployed contract would rely on; `both` |
| **verdict** | `well-covered` / `conformance-only` / `thin` / `absent` |
| **L4** | `CHECKED` = I read the test bodies and assertions cited; `INFERRED` = verdict from directory/grep evidence only; `not surveyed` = no claim |

`files=N` is the count of test files matching the axis grep, which over-counts
(incidental mentions) and is a locator, not a measure.

## 2. Matrix

### A. Gas metering, introspection and settlement

| axis | covering tests | kind | verdict | L4 | evidence |
|---|---|---|---|---|---|
| `gas-introspection` | 8037 suite; `compute/instruction` | both | conformance-only | CHECKED | 8037 tests read `Op.GAS` into storage and assert computed figures (`SLOT_PROBE_RESULT: probe_cost + probe_spill`, `test_state_gas_cross_frame_refund.py:1199`); the expected value is fork-derived |
| `gas-monotonicity` | `eip8037_.../test_state_gas_cross_frame_refund.py` (1,318 ln) | both | **well-covered** | CHECKED | the only axis where the suite genuinely tests the invariant: module docstring states "The measured windows subtract `gas_left` readings with `SUB`, so a window repaid more than it cost reads below zero"; `test_same_frame_refund_increases_gas_left`, `test_cross_frame_refund_repays_spill_at_merge` |
| `gas-forwarding-6364` | `ported_static/stEIP150*`, `stMemExpandingEIP150Calls`, `tangerine_whistle/eip150_operation_gas_costs` | conformance | conformance-only | CHECKED | budgets de-frozen (see §0.3); `stEIP150Specific` is `valid_from("Cancun")`/`valid_from("Berlin")`, so it does not even run on the fork that introduced the rule |
| `call-stipend` | files=52; `eip2200_net_gas_metering`, `eip7708_eth_transfer_logs` | conformance | thin | INFERRED | `fork.call_value_stipend()` used 10x in the 8037 suite — derived, not frozen. No test found asserting "a 2300-gas hook that does real work still completes" |
| `fixed-gas-budget` | files=24, all fork-derived | — | **absent** | CHECKED | see §0.1-0.3. No test pins a frozen absolute budget and asserts a caller still succeeds. **This is the largest gap in the suite and the dominant family in the prior art (56 findings).** |
| `state-gas-reservoir` | `eip8037_...` 17 files / 20,376 ln | both | **well-covered** | CHECKED | reservoir/spill/baseline/commit all exercised: `test_state_gas_reservoir.py` (2,195 ln), `test_state_gas_cross_frame_refund.py`, `test_create_oog_full_burn_no_state_credit` |
| `exceptional-halt-gas-burn` | files=31; `create/test_create_oog_*`, `eip2780_.../test_top_frame_charges.py` | both | thin | INFERRED | `test_create_oog_full_burn_no_state_credit` is impact-shaped; broad coverage of "which failures burn" not found |
| `refund-cap` | files=20; `eip7778_...`, `eip7976_.../test_refunds.py` | conformance | conformance-only | CHECKED | `fork.max_refund_quotient()` (14 uses) — the quotient is read from the fork, so changing //5 to //10 moves test and spec together |
| `storage-refunds` | `ported_static/stRefundTest` (16 `valid_from("Cancun")`, 6 Berlin), `stSStoreTest` (24+2) | conformance | conformance-only | CHECKED | `stRefundTest` is 15 of the 267 fork-derived-gas files; refund amounts asserted against fork-derived expectations |
| `selfdestruct-refund` | within `stRefundTest`, `eip6780_selfdestruct` | conformance | thin | INFERRED | the refund was deleted at London; no deployed-idiom survival test found |
| `intrinsic-gas` | `eip2780_reduce_intrinsic_tx_gas` (11 fork-derived files), `eip7623_...` | conformance | conformance-only | CHECKED | EIP-2780 is the fork change that forced the §0.3 re-baselining — the suite adapted rather than flagged |
| `calldata-floor` | `prague/eip7623_...`, `amsterdam/eip7976_...` (627 ln in 8037 suite) | both | well-covered | INFERRED | dedicated dirs for both the introduction and the repricing |
| `tx-gas-limit-cap` | `osaka/eip7825_transaction_gas_limit_cap` | both | well-covered | INFERRED | dedicated dir; `fork.transaction_gas_limit_cap()` 45 uses |
| `block-gas-accounting` | `amsterdam/eip7778_...`, `eip8037_.../test_block_2d_gas_accounting.py` (1,462 ln) | both | well-covered | INFERRED | dedicated dirs |
| `block-gas-limit-field` | incidental | — | **absent** | INFERRED | no test found for `block.gaslimit`-relative loop bounds |

### B. Access accounting

| axis | covering tests | kind | verdict | L4 | evidence |
|---|---|---|---|---|---|
| `warm-cold-storage-access` | `berlin/eip2929_gas_cost_increases`, `amsterdam/eip8038_...` (11 files) | conformance | conformance-only | INFERRED | `eip2929_.../test_warm_status_revert.py` found; gas-cost oriented |
| `warm-cold-account-access` | `eip2929_...`, `shanghai/eip3651_warm_coinbase`, `amsterdam/eip7981_...` (7 files) | conformance | conformance-only | INFERRED | three dedicated dirs across three forks |
| `access-list-prewarm` | `berlin/eip2930_access_list`, `ported_static/stEIP2930` | conformance | conformance-only | INFERRED | — |
| `block-level-access-lists` | `amsterdam/eip7928_block_level_access_lists` (7 files) | both | well-covered | INFERRED | dedicated dir; no deployed dependent expected (see RULE-AXES.md) |

### C. Opcode and precompile pricing

Pricing axes are, by construction, the suite's strongest conformance area and its
weakest impact area: a dedicated per-EIP directory exists for nearly every repricing,
and every one of them asserts the new number rather than a contract's survival.

| axis | covering tests | kind | verdict | L4 |
|---|---|---|---|---|
| `storage-write-pricing` | `eip8037_.../test_state_gas_sstore.py` (1,793 ln), `stSStoreTest` | both | conformance-only | CHECKED (probe is `Op.SSTORE(0,1).gas_cost(fork)-1`) |
| `storage-read-pricing` | files=50; `eip2929_...`; **nothing for EIP-1884** | conformance | **thin** | CHECKED — no test dir exists for EIP-1884 (`ls tests/istanbul/` → `eip1344`, `eip152`, `eip2200` only). The repricing that provably broke deployed contracts has no dedicated test. |
| `account-query-pricing` | `eip1052_extcodehash`, `eip2929_...` | conformance | conformance-only | INFERRED |
| `call-base-pricing` | `stCallCodes`, `stCallCreateCallCodeTest` | conformance | conformance-only | INFERRED |
| `memory-expansion-pricing` | `stMemoryTest`, `stQuadraticComplexityTest` (13 of the 109 `valid_until("Prague")` files) | conformance | conformance-only | CHECKED — fork-*bounded*: stops running after Prague (see §0.6) |
| `copy-word-pricing` | `cancun/eip5656_mcopy`, `stCodeCopyTest` | conformance | conformance-only | INFERRED |
| `log-pricing` | `stLogTests`, `vmLogTest` | conformance | conformance-only | INFERRED |
| `keccak-pricing` | `compute/instruction` | conformance | thin | INFERRED |
| `exp-pricing` | `vmArithmeticTest` | conformance | thin | INFERRED |
| `create-pricing` | `shanghai/eip3860_initcode`, `eip8037_.../test_state_gas_create.py` (3,656 ln) | both | well-covered | INFERRED |
| `code-deposit-pricing` | files=24; `create/test_create_deposit_oog.py` | both | thin | INFERRED — the 200/byte → 1530/byte state-gas move is large; no deployed-deploy-budget test found |
| `precompile-pricing` | `eip196/197/198`, `eip1108`-era, `eip2537`, `eip7883`, `eip7951`, `eip4844` | conformance | conformance-only | INFERRED |

### D. Control-flow and failure semantics

| axis | covering tests | kind | verdict | L4 |
|---|---|---|---|---|
| `return-data-semantics` | `byzantium/eip211_return_data`, `stReturnDataTest` | both | well-covered | INFERRED |
| `revert-propagation` | `stRevertTest`, `byzantium` | both | well-covered | INFERRED |
| `call-depth-limit` | `stDelegatecallTestHomestead`, `stSystemOperationsTest` | impact | thin | INFERRED |
| `static-context-enforcement` | `byzantium/eip214_staticcall`, `stStaticCall` (259 files), `stStaticFlagEnabled` | both | well-covered | INFERRED |
| `stack-depth-limit` | `stStackTests`, `amsterdam/eip8024_dupn_swapn_exchange` | both | well-covered | INFERRED |
| `jumpdest-validity` | `vmIOandFlowOperations`, `stBadOpcode` | conformance | thin | INFERRED |

### E. State and account model

| axis | covering tests | kind | verdict | L4 |
|---|---|---|---|---|
| `account-existence-empty` | `spurious_dragon/eip161_state_trie_clearing`, `stEIP158Specific`, `frontier/touch` | both | well-covered | INFERRED |
| `new-account-charge` | files=78; `eip8037_.../test_state_gas_call.py` (2,630 ln) | both | conformance-only | INFERRED — the 25,000 → 183,600 move is the biggest multiplier in EIP-8037 and the prior art's `fixed-limit-token-senders` / `ccip-token-release-fresh-receiver` family turns on it; no frozen-budget fresh-recipient test found |
| `selfdestruct-semantics` | files=252; `cancun/eip6780_selfdestruct`, `amsterdam/eip8246_selfdestruct_no_burn`, `eip8037_.../test_state_gas_selfdestruct.py` (1,049 ln) | both | well-covered | INFERRED |
| `transient-storage-lifetime` | `cancun/eip1153_tstore`, `stEIP1153_transientStorage` | both | well-covered | INFERRED — `test_tstorage_reentrancy_contexts.py` is impact-shaped |
| `original-value-tracking` | `istanbul/eip2200_net_gas_metering`, `stSStoreTest` | conformance | conformance-only | INFERRED |
| `created-account-storage` | `create/test_create_collision.py`, `stCreate2`, `stRecursiveCreate` | both | well-covered | INFERRED |
| `code-size-limit` | `stCodeSizeLimit`, `shanghai/eip3860_initcode`, `amsterdam/eip7954_...` | both | well-covered | INFERRED |
| `code-prefix-reserved` | `ported_static` (EIP-3541 era) | conformance | thin | INFERRED — no SSTORE2/data-contract survival test found |
| `address-derivation` | `constantinople/eip1014_create2`, `stCreate2`, `amsterdam/eip7997_...` | both | well-covered | INFERRED |
| `nonce-semantics` | `frontier/eip2681_limit_account_nonce` | both | well-covered | INFERRED |
| `eoa-delegation` | files=177; `prague/eip7702_set_code_tx`, `eip8037_.../test_state_gas_set_code.py` (2,425 ln) | both | well-covered | INFERRED — but see gap note below |
| `protocol-logs` | `amsterdam/eip7708_eth_transfer_logs` | both | well-covered | INFERRED |

Gap note on `eoa-delegation`: coverage of the *mechanism* is extensive, but I found no
test asserting the deployed idiom that the change falsifies — `extcodesize(a) == 0` used
as an "is an EOA" guard. That idiom is measured at corpus scale by L4's
`extcodesize-iscontract` probe.

### F. Block and environment

| axis | covering tests | kind | verdict | L4 |
|---|---|---|---|---|
| `block-fields` | files=84; `eip7516_blobgasfee`, `london/eip1559_...`, `amsterdam/eip7843_slotnum` | both | well-covered | INFERRED |
| `blockhash-window` | files=25; `prague/eip2935_historical_block_hashes_from_state` | both | well-covered | INFERRED |
| `beacon-root` | `cancun/eip4788_beacon_root` | both | well-covered | INFERRED |
| `blob-semantics` | `cancun/eip4844_blobs`, `osaka/eip7594_peerdas`, `eip7918_...`, `amsterdam/eip8070_...` | both | well-covered | INFERRED |
| `chain-id` | `istanbul/eip1344_chainid` | both | thin | INFERRED — no cached-domain-separator test found |
| `system-contracts` | `eip4788`, `eip2935`, `eip7002`, `eip7251`, `eip7997`, `eip8282` | both | well-covered | INFERRED |
| `precompile-set` | `stPreCompiledContracts`, `stPreCompiledContracts2` | both | well-covered | INFERRED |
| `block-size-limit` | `osaka/eip7934_block_rlp_limit` | both | well-covered | INFERRED |

### G. Transaction validity

| axis | covering tests | kind | verdict | L4 |
|---|---|---|---|---|
| `tx-type-validity` | `stTransactionTest`, `berlin/eip2930`, `london/eip1559`, `cancun/eip4844`, `prague/eip7702` | both | well-covered | INFERRED |
| `sender-code-restriction` | `ported_static/stEIP3607` | both | well-covered | INFERRED |
| `authorization-semantics` | `prague/eip7702_set_code_tx`, `eip8037_.../test_state_gas_set_code.py` | both | well-covered | INFERRED |

## 3. Summary

Of 60 axes: **2 absent** (`fixed-gas-budget`, `block-gas-limit-field`), **3 thin-to-absent
on the axes history already broke** (`storage-read-pricing`, `call-stipend`,
`selfdestruct-refund`), **17 conformance-only**, the rest adequately covered for
conformance purposes.

Prioritisation for the corpus, highest value first:

1. **`fixed-gas-budget`** — absent, and the dominant deployed family. Every test must
   use a *frozen* integer budget, which is the one thing the official suite forbids
   itself. This is the project's reason to exist.
2. **`storage-read-pricing` + `call-stipend`** — the EIP-1884 break. No EIP-1884 test
   directory exists at all.
3. **`new-account-charge`** — conformance-only, largest EIP-8037 multiplier, large
   deployed family.
4. **`code-deposit-pricing`** — thin, 7.65x move, deploy-budget idioms.
5. **`gas-monotonicity`** — already well-covered upstream; the corpus should add the
   *deployed witnesses* (Safe `gasUsed.sub(gasleft())`) rather than new mechanism tests.
6. **`eoa-delegation` / `code-prefix-reserved` / `chain-id`** — mechanism covered,
   deployed idiom not.

## 4. What this survey did not do

- Verdicts marked `INFERRED` rest on directory names, dedicated-EIP-dir existence and
  grep counts, **not** on reading the assertions. 13 of 60 axes are `CHECKED`.
- `ported_static/` (329k lines) was sampled, not read. Fork bounds were checked only for
  the 7 directories listed in §0/§C.
- No attempt was made to run the suite under a mutated fork to confirm empirically which
  tests fail under which repricing. That is phase 5 (mutation validation) and would turn
  every `INFERRED` here into a measurement. **Recommended**: the mutation harness makes
  this matrix cheap to verify — patch `GasCosts.SLOAD`/`STORAGE_WRITE` and record which
  tests fail. Until then, treat §2 as a prioritisation aid, not a proof.


## Correction to the refund-cap verdict (CHECKED)

L4 reported the EIP-3529 //2→//5 change as having no behavioural coverage. Too strong. `tests/amsterdam/eip8038_state_access_gas_cost_increase/test_sstore_refunds.py:76` hardcodes `min(gross // 5, code.refund(fork))`, but line 59 pins `valid_from("Amsterdam")`, so it covers Amsterdam alone. `tests/london/` holds only `eip1559_fee_market_change` and `validation`; 20 files read the quotient from `fork.max_refund_quotient()` rather than pinning it. The genuinely uncovered region is the **quotient on Berlin/London/Osaka** plus the **clear-refund amount on every fork**.
