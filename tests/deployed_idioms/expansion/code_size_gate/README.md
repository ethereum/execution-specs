# code_size_gate — the hardcoded 24,576, against EIP-7954

**Invariant.** Every contract that can exist has `EXTCODESIZE <= 24,576`, so a
validator or factory holding that literal never refuses a live contract.
EIP-7954 falsifies it: `MAX_CODE_SIZE` moves from `0x6000` (24,576) to `0x10000`
(65,536) (`amsterdam/vm/interpreter.py:80`), and from that fork a 24,577-byte
contract is a perfectly valid deployment that every such validator rejects.

The gas number IS the invariant here (SCHEMA §4.1): both 24,576 and 65,536 are
pinned as absolutes, from both sides.

## Deployed witness (CHECKED, with addresses)

L1-source pattern **P26**, "EIP-170/3860 code-size limit encoded as a
constant" (`registry/L1-source.jsonl`):

```text
prevalence      338 mainnet addresses / 120 distinct runtime code hashes
counting unit   address = distinct contract_deployments.address whose verified
                compilation references a matching source file
count mode      exact -- all 1,815 mainnet-reachable prefilter hits confirmed
                individually, 70 passed
precision       1.0 hand-measured (3/3 sampled hits read as source)
first-party     332 addresses after removing vendored dependency paths
```

Named exemplars, read as source:

| address | site | why |
| --- | --- | --- |
| `<address withheld>` | a deployed Vyper contract:38` | `def deployFromBytecode(_bytecode: Bytes[24576]) -> address` — a factory whose **input buffer is the EIP-170 limit** |
| `<address withheld>` | a deployed Vyper contract:38` | same runtime, second deployment |
| `<address withheld>` | `DexConstraintPoly.sol:201` | the 49,152 EIP-3860 initcode form |
| `<address withheld>` | `FastExitHandler.sol:1088` | the 49,152 form, assembly |

The hand-read verdict recorded in L1's `hand_verdicts.json` notes all three
sampled hits are **data-as-code size limits via SSTORE2**, which sharpens the
harm rather than weakening it: an SSTORE2-style store that sizes its chunking by
24,576 simply cannot use the extra 40,960 bytes EIP-7954 grants, and a deployed Vyper contract's
`Bytes[24576]` parameter makes a larger deployment unrepresentable at the ABI
boundary.

## Measured (CHECKED)

Instrument: `expansion/tests/tools/test_exp_codesize_gate_probe.py`. A factory
`CREATE`s initcode returning `n` bytes, then asks a gate holding the literal
24,576 about the result. `gas_limit` is **omitted** throughout, since an
explicit one yields a zero state-gas reservoir.

```text
60,000,000-gas block
n        Osaka: size / gate      Amsterdam: size / gate
24,576   24,576 / accept         24,576 / accept
24,577   0      / accept         24,577 / REJECT       <- the violation
65,536   0      / accept         0      / accept       <- see below
65,537   0      / accept         0      / accept

120,000,000-gas block, Amsterdam
65,536   65,536 / REJECT
65,537   0      / accept
```

Two results.

**1. The gate rejects a live contract.** At Amsterdam a 24,577-byte contract
deploys — `EXTCODESIZE` reports 24,577, it is callable — and the deployed gate
commits 0. Both effects are asserted in the same transaction, and the 24,576
param is carried alongside as the control, so the failure is localised to the
single byte that crossed the old limit. Nothing reverts.

**2. The EIP-7954 maximum is unreachable in a mainnet-sized block.** This is a
cross-EIP result that no single-EIP suite can see, because neither EIP is wrong
on its own. EIP-8037 reprices the code deposit from 200 execution gas per byte
to `COST_PER_STATE_BYTE` = 1,530 **state** gas per byte
(`amsterdam/vm/interpreter.py:375-378`), and state gas above the EIP-7825 cap
comes only from the reservoir, which is `tx.gas − 2²⁴` and is itself bounded by
the block's state-gas budget (`check_tx_fits_block`, `amsterdam/vm/gas.py:1084`):

```text
code deposit   65,536 x 1,530 = 100,270,080 state gas
new account       120 x 1,530 =     183,600
                               -----------
                               100,453,680

largest reservoir in a 60,000,000-gas block
               60,000,000 - 16,777,216 =  43,222,784
plus at most one execution grant of spill  ~16,762,000
                                         ------------
                                          ~59,985,000   short by ~40%
```

Measured: deployable at a 120,000,000-gas block limit, **not** deployable at
60,000,000 — today's mainnet figure. The `CREATE` returns zero and the gate then
"accepts" an empty address, so a factory sees success-shaped nothing. The exact
minimum block gas limit is **not measured**; arithmetic puts it near 100.8M
(INFERRED), and the measured statement is the bracket `(60M, 120M]`.

Both arms of result 2 are asserted deliberately: a one-sided test would read as
"the new limit does not work", when the truth is "it works, but not in a block
this size" — which has the opposite implication for whether this is an EIP bug
or a parameter choice.

## Non-duplicative with the official suite (CHECKED)

`tests/amsterdam/eip7954_increase_max_contract_size/` is 1,666 lines and
thorough about the protocol boundary. Every size in it is derived from the fork:
`DEPLOY_CODE_SIZE_PARAMS` (test_max_code_size.py:38-42) is four lambdas over
`Osaka.max_code_size()` and `f.max_code_size()`, and `conftest.py` pads to
`fork.max_code_size() - len(logic)`. The literal `24576` appears nowhere in the
directory (grep, CHECKED).

So nothing in it can observe:

- **a contract making the wrong decision about a valid deployment** — the
  deployed harm, which needs the limit as a PUSH immediate inside EVM bytecode
  rather than a Python fork lookup;
- the EIP-7954 × EIP-8037 reachability interaction, since it never varies the
  block gas limit (it omits `gas_limit` and uses the default 120,000,000 block,
  which happens to be large enough to hide the problem).

That second point is the one worth escalating: the official suite passes
*because* the default test block is twice mainnet's size.

This class is **not** in `docs/INVARIANT-CLASSES.md`. Its closest relative is #3
(hardcoded cost-equality), which pins a gas constant a contract holds; this pins
a **size** constant a contract holds, and the failure mode is an unnecessary
refusal rather than a mis-quote — the same direction as #20's "unnecessary
refusal", and equally silent.

## Reproduce

```bash
cd tests/deployed_idioms
python3 tools/locked_fill.py \
    expansion/tests/code_size_gate --until Amsterdam \
    --output /tmp/csg --clean -q -p no:cacheprovider          # 56 passed

python3 tools/locked_fill.py \
    expansion/tests/tools/test_exp_codesize_gate_probe.py \
    --from Osaka --until Amsterdam --output /tmp/csgp --clean -q --tb=no \
    -p no:cacheprovider      # failures ARE the measurement

python3 tools/mutate.py --wave expansion -k exp-tx --archetype code_size
```

## Mutation result (CHECKED)

`python3 tools/mutate.py --wave expansion -k exp-tx`, run over all **9**
expansion archetypes. Baseline `pass(18)` at Amsterdam (the full Berlin→Amsterdam
fill is 56).

| mutation | this archetype | elsewhere in the expansion wave |
| --- | --- | --- |
| `exp-tx-max-code-size-24576` | DETECTED(9) | all 8 survive |
| `exp-tx-max-code-size-doubled` | DETECTED(3) | all 8 survive |
| `exp-tx-code-deposit-free` | DETECTED(3) | all 8 survive |
| `exp-tx-osaka-max-code-size-32768` | DETECTED(3) | all 8 survive |
| `exp-tx-reservoir-gets-all-evm-gas` | DETECTED(18) | detected by all 8 as well |
| `exp-tx-osaka-cap-halved` | DETECTED(6) | also 4 others |

**Six detections, four with perfect specificity.** No other archetype in the wave
can observe a code-size limit or the price of depositing code.

**Both directions, and the counts partition the file exactly.**

- `exp-tx-max-code-size-24576` (EIP-7954 reverted, **tighter**) fails **9 of 18**:
  the whole of arm 2's `one_byte_over_eip170` param plus both params of arm 3,
  since 24,577 and 65,536 stop deploying. Arm 2's 24,576 control and arm 4 are
  untouched, which is what makes the failure read as "the limit moved" rather than
  "everything broke".
- `exp-tx-max-code-size-doubled` (**looser**, 131,072) fails exactly **3** — only
  arm 3's `one_byte_over_eip7954` param, because 65,537 becomes deployable. A
  single param locating the upper boundary to one byte.
- `exp-tx-code-deposit-free` (**cheaper**, EIP-8037's 1,530 state gas/byte
  removed) fails exactly **3** — only arm 4's `mainnet_60M_cannot_deploy_it`
  param, because the maximum-size contract now fits in a 60,000,000-gas block.
  This is the mutation that proves arm 4 is measuring the *deposit price* and not
  some incidental gas shortage, and it is the only one in the wave that touches
  it.
- `exp-tx-osaka-max-code-size-32768` raises the limit on a **pre**-EIP-7954 fork
  and fails exactly **3** — arm 1's `one_byte_over_eip170` param. Without it the
  `valid_until("Osaka")` arm would never be exercised, since `mutate.py` fills
  only the fork it mutated.

So each of the four size/price mutations has a **distinct failure signature**
(9 / 3 / 3 / 3 on different params), which means the matrix does not merely detect
a regression here but identifies *which* of the four rules moved.

**One blunt row, flagged.** `exp-tx-reservoir-gets-all-evm-gas` fires on all nine
archetypes; it is a valid detection with low diagnostic value, since a vast
reservoir perturbs every transaction's gas accounting. `exp-tx-osaka-cap-halved`
is similar at 5 of 9.

## What a failure means

The deployable code-size limit moved, or the price of depositing code moved. 338
mainnet addresses are now either refusing valid contracts or sizing a buffer
against the wrong number — and if the deposit price moved, the headline
capability of EIP-7954 just became reachable or unreachable without any test in
either EIP's own suite changing its verdict.
