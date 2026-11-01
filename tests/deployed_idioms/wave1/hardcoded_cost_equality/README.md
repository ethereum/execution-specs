# Archetype 3: hardcoded cost-equality for a storage write

## The invariant

A contract hardcodes an expected gas cost and uses it to compute a fee, an L1 charge, or a
quote. The invariant is **equality**: the constant equals the charge the EVM actually
takes.

This is one of the two archetypes in the corpus where asserting a raw gas number *is* the
invariant. SCHEMA.md §4.1 permits it explicitly — "must_not_assert: exact gas numbers,
**unless the gas number IS the invariant**". **Do not repair a failure here by rebasing
the constants; the constants are the assertion.** The distinction a future maintainer
needs: a test asserting `gasUsed == 45038` is forbidden because the number is incidental
to what it tests, whereas these numbers are what a deployed contract wrote into immutable
code and then multiplied by a gas price to move ether.

A failure means the cost of a storage write moved, and every deployed contract pricing a
fee off one of these constants is now wrong by the delta — silently, because a bad quote
produces a bad price, not a revert.

## Deployed witnesses (CHECKED — source text read, addresses confirmed `chain_id = 1`)

**a deployed rollup `Bridge`**, `<address withheld>`,
`contracts/bridge/Bridge.sol`. The clearest instance in the corpus, because the constant
flows into an ether transfer:

```solidity
46:  /// @dev The amount of gas not to charge fee per cache operation.
47:  uint256 private constant _GAS_REFUND_PER_CACHE_OPERATION = 20_000;
...
288:  uint256 refund = stats.numCacheOps * _GAS_REFUND_PER_CACHE_OPERATION;
291:  stats.gasUsedInFeeCalc = uint32(
292:      GAS_OVERHEAD + gasStart + _messageCalldataCost(_message.data.length) - gasleft()
294:  );
296:  uint256 gasCharged = refund.max(stats.gasUsedInFeeCalc) - refund;
297:  uint256 maxFee = gasCharged * _message.fee / _message.gasLimit;
298:  uint256 baseFee = gasCharged * block.basefee;
...
303:  msg.sender.sendEtherAndVerify(fee, _SEND_ETHER_GAS_LIMIT);
```

If 20,000 under-states the real charge, `gasCharged` is too small and the relayer is
**under-paid in ether**. The identifier appears in 18 verified source files across **21
distinct mainnet addresses**.

**a deployed rollup a rollup execution manager**, `<address withheld>`,
`contracts/optimistic-ethereum/OVM/execution/a rollup execution manager.sol`:

```solidity
67:  uint256 constant NUISANCE_GAS_SLOAD = 20000;
68:  uint256 constant NUISANCE_GAS_SSTORE = 20000;
...
1686:     _useNuisanceGas(NUISANCE_GAS_SSTORE);   // first write to a slot only
```

Here the same constant drives a sufficiency decision rather than a price. 6 files, **26
distinct mainnet addresses**.

### Witness scope — stated, not glossed

- Counting unit: **distinct mainnet (`chain_id = 1`) addresses whose verified source set
  contains the identifier**, over the Sourcify v2 export. Not runtime code hashes, not
  files.
- The **5,000** constant is **not** separately witnessed by a deployed address here. It is
  asserted on the same footing as `tests/stipend_fallback`'s 2,300: a protocol constant
  rather than a budget this corpus chose. EELS itself still carries the figure under that
  name — `COLD_STORAGE_WRITE: Final[Uint] = Uint(5000)`, `osaka/vm/gas.py:49`, consumed as
  `COLD_STORAGE_WRITE - COLD_STORAGE_ACCESS` in `osaka/vm/instructions/storage.py`.
  Searching Sourcify for a deployed `5000`-for-a-reset constant was **not done**.
- No false-positive rate was measured for the search that produced these two witnesses,
  because no prevalence *count* is being ranked on — the two instances were hand-read.
  The 21 and 26 figures are identifier-occurrence counts, and should not be promoted into
  a registry record without the §7.3 hand-validation.
- One finding about the detection machinery, not acted on because it is not my file:
  `lenses/L4/l4_rule_constants.py` `validate()` (lines 362-368) selects only `txt` from
  `sources` and never joins the address map, so it prints source fragments **without
  addresses** and cannot by itself produce an exemplar. The witnesses above came from
  throwaway scripts reusing its `strip_comments_sql` / `FAST_SRC` / `FAST_MAP` helpers.

### Search commands

```bash
# narrow named-constant probe over comment-stripped mainnet sources, regex:
#   (?i)(sstore|storage_?write|store_?gas|gas_?per_?s|slot_?gas|storage_?gas|write_?gas
#        |storage_?refund|refund_?gas|clear_?refund)[a-z_0-9]*\s*=\s*
#        (20_?000|15_?000|24_?000|22_?100|5_?000|2_?900|4_?800|19_?900)\b
# -> 32 files / 44 compilations / 63 mainnet addresses   (86 s)
```

Negative results worth keeping: the `gasleft() > 20000` family (47 mainnet addresses) is
**not** this pattern — every hit read was a loop-continuation budget (`VestingRouter.sol`,
`BasicJurisdiction`, `AdManager`), sized at roughly one storage write but never stating
that attribution. And `SSTORE2_CHUNK_SIZE = 24_000` is the EIP-170 code-size budget, not
the SELFDESTRUCT refund; it belongs to the `codesize-24576` axis.

## Measurement

Instrument: `tests/tools/test_storage_cost_probe.py`. It asserts 0, so the mismatch
message prints the real value.

```bash
cd /home/devops/toni/datanalysis/eip-8037/engine/eels
for F in Berlin London Cancun Prague Osaka Amsterdam; do
  for W in create update clear; do
    ./.venv/bin/fill ../../wave1/instruments --from $F --until $F \
        -k "storage_cost and state_test and write_$W" --output /tmp/sc-$F-$W \
        -q --tb=long -p no:cacheprovider | grep -oE "got 0x[0-9a-f]+ \(dec:[0-9]+\)"
done; done
```

Result (CHECKED; raw readings include 17 gas of instrument overhead, netted out below):

```text
fork            create a slot    replace a value     clear a value
Berlin                 22,100              5,000             5,000
London                 22,100              5,000             5,000
Cancun                 22,100              5,000             5,000
Prague                 22,100              5,000             5,000
Osaka                  22,100              5,000             5,000
Amsterdam             110,020             12,100            12,100
```

The two constants have opposite histories, which is the reason this directory has three
tests rather than one:

- **5,000 is exactly right for five consecutive forks.** EIP-2929 split the flat 5,000
  into `COLD_STORAGE_ACCESS 2,100` plus `COLD_STORAGE_WRITE 5,000 - COLD_STORAGE_ACCESS
  2,100` and deliberately preserved the cold total, so a contract holding 5,000 survived
  the largest access-cost reprice in Ethereum's history unchanged. A corpus that only
  asserted inequalities would never have recorded that this equality held.
- **20,000 has been wrong since Berlin**, by the 2,100 cold surcharge EIP-2929 added on
  top of `STORAGE_SET` — a 10.5% under-quote sitting in deployed code for five forks with
  no test failing anywhere, because nothing asserts the equality. a deployed rollup under-pays its
  relayers by that margin today.

At EIP-8037 both break at once:

```text
constant   real cost (Amsterdam)   under-quote   decomposition
20,000              110,020             5.50x    2,100 + 10,000 + 64*1,530
 5,000               12,100             2.42x    2,100 + 10,000
```

The second row involves **no state gas at all**, so it is not reachable by reasoning about
the reservoir, and it is the row that reaches archetype 2's population: a contract that
only ever updates values it already created is still mispriced by 7,100 gas per write.

The 17-gas instrument overhead is derived, then cross-checked rather than fitted: after
the first `GAS` is charged, `PUSH1 3 + MSTORE (3+3 expansion) + PUSH1 3 + PUSH1 3 + GAS 2`
= 17, and `2,100 + 20,000 + 17 = 22,117` is exactly the Osaka reading.

## Fill

```bash
./.venv/bin/fill ../../wave1/hardcoded_cost_equality --until Amsterdam \
    --output /tmp/c3 -q --tb=no -p no:cacheprovider
```

**44 passed**, exit 0 (CHECKED). Berlin through Amsterdam, three tests, 12 fixtures across
3 formats.

## Mutation result

`python3 tools/mutate.py -k cls3-` and `-k cls2-` (full 20-archetype matrix, CHECKED).
Baseline `pass(6)` at Amsterdam.

| mutation | verdict | which test it kills |
|---|---|---|
| `cls3-cold-storage-write-4500` (Osaka `COLD_STORAGE_WRITE` 5000→4500) | **DETECTED(3)** | test 1 — the cold total EIP-2929 preserved moves, so the 5,000 equality stops holding |
| `cls2-storage-set-osaka-60000` / `cls2-storage-set-osaka-1000` | **DETECTED(3)** each | test 2 — the pre-8037 creating-write charge moves off 22,100 |
| `cls3-storage-write-9000` (Amsterdam `STORAGE_WRITE` 10000→9000) | **DETECTED(6)** | test 3, both params — the execution term of every storage write moves |
| `cls2-cpsb-250` (`COST_PER_STATE_BYTE` 1530→250) | **DETECTED(3)** | test 3's creating param — the state term moves |
| `cls12-cold-read-5000` / `cls12-cold-read-700` | **DETECTED(6)** each | both Amsterdam params — the access term is in both charges |

All three tests are killed. The valuable row is `cls3-cold-storage-write-4500`: across the
whole 20-archetype corpus it is detected by **only** this archetype and
`block_vs_sender_accounting`. Nothing else can see the pre-EIP-8037 `SSTORE_RESET` term,
which is the specificity result that justifies the archetype existing — the reset price is
a rule with real deployed dependents and, before this directory, no test in the corpus
could observe it at all.

The two `cls12-cold-read-*` mutations being detected in **both** directions is the other
property worth recording: an equality assertion is the only test shape that fails when a
cost goes *down*. Every budget-sufficiency archetype in the corpus survives a cheaper
reprice by construction.
