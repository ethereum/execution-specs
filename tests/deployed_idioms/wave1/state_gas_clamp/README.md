# Archetype 14 — state-gas block accounting is one-sided (EIP-8037)

## The invariant

A transaction is never paid for freeing state. Its block-level state-gas contribution is
the full price of everything it created and **nothing** for anything it destroyed,
floored at zero and never negative. Freeing two slots and freeing four slots, each
alongside one creation, carry the *same* block state-gas figure as freeing none.

**What a failure means in one sentence:** a fork has started crediting freed state into
block accounting (or stopped charging created state into it), which silently changes what
a block-space budget, a state-growth metric, or an EIP-8037-aware fee model is measuring.

## Mechanism citation (CHECKED)

```python
settled_state_gas_used = StateGas(Uint(max(0, state_gas_used)))      # amsterdam/vm/gas.py:1216
execution_gas_used = ExecutionGas(
    max(gas_used_before_refund - settled_state_gas_used, calldata_floor))  #        :1217-1222
block_output.block_state_gas_used += settlement.state_gas_used       # amsterdam/fork.py:1069
block_gas_used = max(block_output.block_gas_used,
                     block_output.block_state_gas_used)              # amsterdam/fork.py:335-338
```

with the settlement docstring explaining the clamp as *"the state gas used (clamped to
zero, since refunds can drive it negative)"*.

`state_gas_used` itself is `reservoir - state_gas_left + spilled + committed_spill`
(`amsterdam/vm/gas.py:584-591`), i.e. a conserved function of state-gas charges minus
state-gas credits.

## The correction this archetype produced

**The one-sidedness is not the `max(0, ...)` clamp.** It is enforced one level earlier, in
the `sstore` refund guard: state gas is credited back only for a slot the *same
transaction* created.

```python
if current_value != new_value and original_value == new_value:
    if original_value == 0:
        # Slot set then cleared: refund the state gas charge.
        credit_state_gas_refund(evm.gas_meter, StateGasCosts.STORAGE_SET)
#                       amsterdam/vm/instructions/storage.py:148-151
```

`original_value == 0` means a slot that was already non-zero when the transaction began
earns **no state-gas credit at all** when it is cleared — only the execution-gas
`REFUND_STORAGE_CLEAR`. So the brief's suggested construction ("clear pre-existing slots
without creating any, and pin the block-level figure at 0") pins a figure that is 0
because nothing ever entered the state dimension, not because the clamp acted.

Ten adversarial constructions were measured for a negative net (CHECKED,
`tests/tools/settlement_probe/test_settlement_probe.py`):

```text
probe                                             state_gas_used (pre-clamp)
clear 3 pre-existing slots, create nothing                                 0
in-frame set then clear, reservoir 0                                       0
DELEGATECALL child clears the parent's fresh slot                          0
  ... same with state_gas_reservoir=300,000                                0
child clears a pre-existing slot while the parent creates one        +97,920
EIP-7702 authorization + two clears                                  +35,190
EIP-7702 authorization + in-frame set/clear                          +35,190
EIP-7702 authorization, parent sets, child clears                    +35,190
CREATE whose child aborts after the NEW_ACCOUNT charge                     0
create 1 and free 2 / free 4                                         +97,920
```

**Not one was negative.** The reason is structural: every `credit_state_gas_refund` is
paired one-for-one with a `charge_state_gas` of the same constant, `commit_state_gas` and
`repay_state_gas_spill` are documented as moving gas between pools without changing the
used counters, and `incorporate_child` plus `repay_state_gas_spill` convert a child's
reservoir surplus back into the parent's spill exactly. The 7702 path was the most
promising route — `commit_state_gas` leaves the spill at zero so later credits route to
the reservoir rather than `gas_left` — and it still lands at exactly the authorization's
own `AUTH_BASE` (23 × 1530 = 35,190).

**Under the reference refund rules the clamp has nothing to clamp; it is defensive.**
That is a result, not a coverage gap, and the mutation table below carries the arithmetic.

## Measurement

Same instrument and command as `tests/block_vs_sender_accounting/README.md`. Amsterdam,
`state_gas_reservoir=0`, `gas_limit=1_000_000`, zero value:

```text
shape                     raw state_gas_used   block state gas   exec    header   receipt
free 3, create 0                           0                 0  51,318   51,318    41,055
free 0, create 1                     +97,920            97,920  27,106   97,920   125,026
free 2, create 1                     +97,920            97,920  51,318   97,920   126,006
free 4, create 1                     +97,920            97,920  75,530   97,920   138,760
set and clear one slot                     0                 0  27,212   27,212    21,770
```

Three readings matter.

1. **`free 3, create 0` contributes 0, and the execution figure is not reduced either.**
   51,318 is `gas_used_before_refund` undiminished: freeing three slots of state bought no
   reduction in *either* block counter.
2. **`free 0 / free 2 / free 4` all carry 97,920** — one `STORAGE_SET`
   (`COST_PER_STATE_BYTE 1530 × STATE_BYTES_PER_STORAGE_SET 64`). At `free 2` and `free 4`
   the transaction is physically net-freeing and is still charged in full.
3. **The header reports the state dimension in all three creating rows** because
   `max(block_gas_used, block_state_gas_used)` picks 97,920 over the execution figure
   (27,106 / 51,318 / 75,530). `frees` therefore stops at 4: at `frees=6` the execution
   figure would cross 97,920, the header would stop reporting the state counter, and the
   test would silently change meaning.

## Fill

```bash
cd /home/devops/toni/datanalysis/eip-8037/engine/eels
./.venv/bin/fill ../../wave1/state_gas_clamp \
    --until Amsterdam --output /tmp/c14 -q --tb=no -p no:cacheprovider
# 15 passed  CHECKED   (5 Amsterdam tests x 3 fixture formats)
```

Amsterdam only — `valid_from("EIP8037")`, since state gas does not exist earlier.

## Mutation result (CHECKED, `python3 tools/mutate.py`)

```text
mutation                        state_gas_clamp
(baseline)                      pass(15)
exec-gas-no-state-subtraction   DETECTED(6)
state-clamp-min                 DETECTED(6)
state-free-credit               DETECTED(9)
exec-gas-applies-refund         DETECTED(4)
refund-divisor-4                DETECTED(9)
state-clamp-off                 survives     <-- correctly; arithmetic below
floor-not-a-max                 survives
floor-token-8 / -7              survives
```

**`state-free-credit` is the mutation this invariant is defined against.** It makes
clearing state that pre-dates the transaction earn a state-gas credit — a fork that
decided to *pay* for freeing state — at a sixteenth of a storage set (6,120) so the
resulting negative net stays representable:

```text
free 3, create 0 under state-free-credit:
  raw state_gas_used = 0 - 3 x 6,120            = -18,360
  settled_state_gas_used = max(0, -18,360)      =       0     <- the clamp absorbs it
  gas_used_before_refund = 51,318 - 18,360      =  32,958     <- but the credit leaks here
  execution_gas_used = max(32,958, 15,000)      =  32,958  != 51,318
```

This is the asymmetry in sharp form, and it confirms the hazard precisely: the clamp hides
an over-generous freeing rule from the **state** dimension while the same gas reappears in
the **execution** dimension through `gas_used_before_refund`. A state-growth metric reading
`block_state_gas_used` would see nothing change. **DETECTED.**

**`state-clamp-min`** inverts the clamp (`max` → `min`). For `free 2, create 1` the raw net
is +97,920, so `min(0, 97,920) = 0`, the `- settled_state_gas_used` term vanishes, and the
header becomes `max(149,238, 0) = 149,238` instead of 97,920. **DETECTED.** This is what
proves the archetype sees the clamp's *orientation*, not merely its presence.

**`state-clamp-off`** (`max(0, x)` → `x`) **survives, and correctly.** The arithmetic is an
identity: `state_gas_used` is 0 or +97,920 in every shape this archetype uses and in all
ten adversarial probes, and `max(0, x) == x` for every `x >= 0`. The clamp is unreachable
under the reference refund rules. It becomes reachable only in combination with a more
generous freeing rule, and `tools/mutate.py` applies one mutation at a time, so no single
entry can express the composite — `state-free-credit` is the honest substitute, since it
mutates the rule that makes the clamp matter at all.

`exec-gas-no-state-subtraction` (drop `- settled_state_gas_used`) is detected only here:
for `free 0, create 1` the header becomes `max(125,026, 97,920) = 125,026` instead of
97,920, i.e. state gas counted in both block dimensions at once.

`refund-divisor-4` is detected because this archetype also pins receipts (9 = the three
refunding tests × three fixture formats). That is wanted, not noise: the receipt pins are
what stop "the header did not move" from being satisfied by three transactions that did
the same work.

The two partial counts are both informative rather than sloppy, and both were checked
against the arithmetic:

- `state-free-credit` reads DETECTED(**9**) of 15 because its extra branch is guarded on
  `original_value != 0`: it cannot fire for `free 0, create 1` (nothing pre-existing is
  cleared) or for the set-then-clear test (its slot starts at 0). Exactly the three tests
  that clear pre-existing state move, in all three formats.
- `exec-gas-applies-refund` reads DETECTED(**4**) of 15 because in the three creating
  rows the state dimension still wins the header maximum: subtracting the refund takes
  `free 2`'s execution figure to 28,086, and `max(28,086, 97,920)` is still 97,920. Only
  the two rows whose header *is* the execution figure — `free 3, create 0` and the
  set-then-clear — move, in the two blockchain-derived formats each. The state dimension
  masking an execution-side rule change is itself worth knowing.

## Rules this archetype adds to the corpus

1. **Pin a figure that is invariant across a parametrised axis, and pin the varying side
   too.** `frees ∈ {0, 2, 4}` share one header literal; their receipts are three different
   literals. The shared literal carries the invariant, the differing ones prove the
   parameter did something.
2. **State the crossover that bounds the parametrisation.** The header is a `max`; a
   parameter range that silently crosses it changes what the test measures without
   failing.
3. **A clamp that cannot be reached is a finding.** Report the measured range of the
   clamped quantity and the mutation that makes the clamp reachable, rather than shipping
   a test that claims to cover a branch it never enters.
