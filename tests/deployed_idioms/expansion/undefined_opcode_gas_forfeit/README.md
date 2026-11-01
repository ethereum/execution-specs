# Candidate class, gas dimension: the halt on an undefined byte forfeits the whole grant

**Invariant.** A caller that caps a sub-call forfeits the **entire** cap when the
callee reaches an undefined opcode byte — the halt burns the frame, exactly as
`INVALID` does. A caller budgeting around a guaranteed-halt callee, or metering
one, depends on that figure.

**What is new here, precisely.** Class #11 (`tests/halt_vs_revert/`, 138 fill)
already pins halt-versus-revert gas return, and its halting arm is `Op.INVALID`
"deliberately *not* repricing-sensitive, so it pins halt semantics"
(`docs/INVARIANT-CLASSES.md` #12/#11). `INVALID` is `0xFE`, reserved forever, so
in class #11 the **trigger cannot move**. Here it does: five bytes that halted
identically have been claimed by four EIPs, and on the assignment fork the same
deployed bytecode stops burning the grant and starts handing it back. Same rule,
a trigger that a fork can flip. That is the gap this archetype fills, and it is
the gap the brief named.

## Mechanism (CHECKED, pinned EELS Amsterdam commit 168980009)

```text
except ExceptionalHalt as error:
        restore_state_gas(evm.gas_meter)
        forfeit_remaining_gas(evm.gas_meter)   amsterdam/vm/interpreter.py:455-457
forfeit_remaining_gas:  gas_meter.gas_left = ExecutionGas(Uint(0))
                                               amsterdam/vm/gas.py:663
except Revert as error:
        restore_state_gas(evm.gas_meter)       -- and NOT forfeit
                                               amsterdam/vm/interpreter.py:461-465
```

`InvalidOpcode` is an `ExceptionalHalt`, and `0xFE` is **not** a named member of
`Ops` on any fork in range (CHECKED), so the designated-INVALID byte and a
merely unassigned byte take literally the same path. The answer to "does an
undefined byte burn all gas the way `INVALID` does?" is **yes, through the
identical code, measured identical to the gas**.

## Measurement (CHECKED)

`expansion/tests/tools/test_exp_undefined_opcode_probe.py`,
`test_undefined_byte_cost` / `test_undefined_byte_warm_cost` — both always fail
on purpose, so the mismatch prints the figure. Caller's `GAS` delta across a
`CALL` with a 400,000-gas grant. The left column is **quantised to 1024** (the
probe divides, so the figure fits a readable storage diff); the right column is
exact:

```text
                            child's work behind the byte
                            fresh slot (// 1024)   warm 1->2 update (exact)
halted (byte undefined)     393                    402,634   Berlin..Osaka
                                                   403,034   Amsterdam
executed (byte assigned)     24   Shanghai..Osaka    7,642 .. 7,648
                            110   Amsterdam         15,142 .. 15,197
```

Identical for `0xFE`, for the never-claimed `0x0C`, and for all six
later-assigned bytes before their assignment fork. The halted figure is the
grant plus the `CALL`'s own charge — the whole cap, gone. After assignment the
caller pays **1/16th (fresh slot) to 1/27th (warm update)** of that for the same
bytecode.

The `110` cell is a cross-check against class #1: it is the EIP-8037 fresh-slot
floor of ~110,026 plus overhead, re-measured independently here.

## What breaks, in both directions

* **A capability probe** that reads "the child consumed everything" as "not
  supported" starts reading "supported". This is class #12's inversion reached
  through *semantics* rather than a reprice, and class #12 cannot see it.
* **A metering or reimbursement caller** that charges from the observed
  consumption starts charging ~6% of the right amount. A funds leak, not a
  liveness failure — the quieter and worse direction, as class #10 found for
  `gasleft()` wrap-around.

## Deployed witness — measured

Population, stated once: **994,414 distinct mainnet runtime code hashes** backing
**7,911,875 distinct addresses** (L2's staged corpus, blocks 51,291–26,259,375;
address counts rebuilt from the Sourcify v2 deployment join so they are distinct
addresses, not deployment rows). Full tables and method in
`../undefined_opcode_halt/README.md`.

**The byte that reaches this forfeit today: `0xFE`, at 180,402 runtime hashes
(18.14%) / 2,466,439 distinct addresses (31.17%)** with the byte at a reachable
code position outside the metadata tail — and the **predecessor opcode is
`JUMPI` in 177,918 of those 180,402**, which is the solc `assert`/`throw` guard
identified by its own signature rather than assumed. Named, hand-disassembled
witnesses: Tether a major stablecoin `<address withheld>`, a major DEX router `<address withheld>`, a widely deployed smart-account wallet
`<address withheld>`.

**The clean negative, hand-measured: zero deployed contracts in that population
use a non-`0xFE` undefined byte as a reachable halt.** An exhaustive pass over
30,868 candidate runtimes left 93 survivors, 92 of which are `0x1E` genuinely
executing as `CLZ` post-Osaka and the last of which is hand-refuted as data.
Scope caveat: Sourcify-*verified* deployments only; hand-written assembly and
obfuscated bots are not in the population and are where a non-`0xFE` halt would
be most plausible.

So the forfeit's **witnessed** population is `0xFE`-shaped, and the hazard this
archetype pins is counterfactual-but-cheap: the rule is identical for every
byte, and four EIPs have now claimed five of them. The forfeit-on-halt rule's
own deployed population belongs to class #11 (tolerated child failure inside a
committing transaction: **6,281 frames across 270 runtimes**, post-filter, from
`docs/INVARIANT-CLASSES.md` #11 — the raw 116,823 figure carries 94.12% measured
FP and must not be used).

## The tests

| test | scope | asserts |
|---|---|---|
| `test_halt_on_an_undefined_byte_forfeits_the_grant` | per-param `valid_from("Berlin")` + `valid_until` the fork before assignment, plus `0x0C` on all forks | `CALL` returned 0; `consumed > grant/2`; `not (consumed < grant/8)` |
| `test_assigned_byte_hands_the_grant_back` | per-param `valid_from` the assignment fork | `CALL` returned 1; `consumed < grant/8`; `not (consumed > grant/2)` |

**No gas number is asserted** (SCHEMA §4.1). The instrument is two booleans over
a grant the test chooses itself, with measured slack of 2.01x on the halting
side and 3.29x (Amsterdam) / 6.5x (earlier forks) on the executing side — stated
so a future reprice that eats the margin is a known risk rather than a surprise.
The child's committed effect is a **warm** `1 -> 2` update precisely to keep the
executing arm off the ~110,026 fresh-slot cliff.

The `0x0C` param is the arm that stays green on all eight forks, and it is the
one that fires if a fork ever makes an exceptional halt return gas.

## Reproduce

```bash
cd tests/deployed_idioms
python3 tools/locked_fill.py \
    /home/devops/toni/datanalysis/eip-8037/expansion/undefined_opcode_gas_forfeit \
    --until Amsterdam --output /tmp/a2 -q -p no:cacheprovider     # 154 passed

python3 tools/locked_fill.py \
    /home/devops/toni/datanalysis/eip-8037/expansion/instruments \
    --from Berlin --until Amsterdam \
    -k "undefined_byte_warm_cost and state_test and not blockchain" \
    --output /tmp/uw --tb=short -p no:cacheprovider     # failures ARE the numbers

python3 tools/mutate.py --wave expansion -k exp-op \
    --archetype undefined_opcode_gas_forfeit
```

## Mutation result

Full table in `expansion/docs/MUTATIONS-exp-opcodes.md`. Two families reach it,
and they are complementary:

- `exp-op-halt-keeps-its-gas-{paris,prague,amsterdam}` — the halt stops
  forfeiting. **Detected by this archetype alone**; `undefined_opcode_halt` and
  `opcode_assignment_code_identity` both survive it, correctly, because neither
  observes gas. Perfect specificity, and the failure counts are every live param
  at each fork.
- `exp-op-undefined-is-a-noop-*` and the six `exp-op-*-moved-off-*` byte moves —
  the semantic trigger, from both sides.

`exp-op-code-validated-at-frame-entry` **survives, correctly and for a stated
reason**: a code-validation refusal is still an `ExceptionalHalt`, so it still
forfeits the grant and the two booleans do not move. The observable is
unchanged, so there is nothing for this archetype to see.

## What a failure means

The forfeit arm failing means a fork has made an exceptional halt return gas, or
has claimed a byte deployed code was halting on. Either way a caller's
sub-budget stops being spent, every `consumed`-derived fee under-bills, and
every "it burned everything, so it failed" inference inverts. Nothing reverts
and no gas constant changed.
