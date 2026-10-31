# Candidate class: an undefined opcode byte halts, and deployed code relies on it

**Invariant.** A byte with no instruction assigned to it aborts the frame
exceptionally the moment the program counter reaches it, so nothing behind it
ever executes. Deployed code uses that as a guaranteed halt.

**Why this is not any of the 26 existing classes.** Assigning an opcode byte
moves **no price**. Every constant in `vm/gas.py` is untouched; the frame simply
stops being a halt and starts being a success, and the code behind the byte
starts running. Classes #1–#20 are all gas-shaped and structurally cannot see
it. The semantic-identity family (#21–#25) is about *meaning*, which is the
right family, but none of its five members is about *instruction-set
membership*: #21 is return-data, #22 code presence, #23 address derivation, #24
transient-storage lifetime, #25 caller identity. #26 is `SELFDESTRUCT` and #27
(candidate) is environment fields. Nothing covers "is this byte an
instruction". **CHECKED against `docs/INVARIANT-CLASSES.md` in full.**

## Mechanism (CHECKED, pinned EELS Amsterdam commit 168980009)

```text
try:    op = Ops(evm.code[evm.pc])
except ValueError as e:
        raise InvalidOpcode(evm.code[evm.pc]) from e
                                        amsterdam/vm/interpreter.py:440-442
InvalidOpcode is an ExceptionalHalt, so:
        restore_state_gas(evm.gas_meter)
        forfeit_remaining_gas(evm.gas_meter)
        evm.output = b""                amsterdam/vm/interpreter.py:455-458
```

Two consequences worth stating because deployed code depends on both:

* resolution is **lazy, one byte at a time, at the program counter**. There is
  no code validation. An undefined byte anywhere else in the code is inert.
* `0xFE` is **not a named member of `Ops`** on any fork from Berlin to Amsterdam
  (CHECKED: `grep -c '= 0xFE$'` returns 0 in all 8 forks'
  `vm/instructions/__init__.py`; EEST's `Op.INVALID` is a convenience name on the
  test side only). The designated-INVALID byte and a merely
  unassigned byte halt through the identical path. That is why the idiom works
  at all, and why it is only safe for the one byte that is reserved forever.

## The surface: five bytes claimed by four EIPs

Measured by filling a throwaway parametrised probe fork by fork; the passing
param of `test_undefined_byte_flip` is the answer
(`expansion/tests/tools/test_exp_undefined_opcode_probe.py`). **CHECKED, all 64
cells:**

```text
byte                  Berl  Lond  Pari  Shan  Canc  Prag  Osak  Amst
0x5F PUSH0            HALT  HALT  HALT  EXEC  EXEC  EXEC  EXEC  EXEC   EIP-3855
0x1E CLZ              HALT  HALT  HALT  HALT  HALT  HALT  EXEC  EXEC   EIP-7939
0x4B SLOTNUM          HALT  HALT  HALT  HALT  HALT  HALT  HALT  EXEC   EIP-7843
0xE6 DUPN     +imm    HALT  HALT  HALT  HALT  HALT  HALT  HALT  EXEC   EIP-8024
0xE7 SWAPN    +imm    HALT  HALT  HALT  HALT  HALT  HALT  HALT  EXEC   EIP-8024
0xE8 EXCHANGE +imm    HALT  HALT  HALT  HALT  HALT  HALT  HALT  EXEC   EIP-8024
0xFE (reserved)       HALT  HALT  HALT  HALT  HALT  HALT  HALT  HALT   control
0x0C (unclaimed)      HALT  HALT  HALT  HALT  HALT  HALT  HALT  HALT   control
```

Three observables were asserted together in every cell — the guarded `SSTORE`
behind the byte, the caller's `CALL` status, and whether the child consumed more
than half its grant — and **all three flip at the same fork in all 64 cells**,
so the semantic flip and the gas forfeit are one event, not two.

### The result the official suites do not state: the flip is depth-conditional

Once the byte is an instruction it can still halt, on *stack underflow*. That is
accidental protection, not the invariant, and it splits the five bytes in two.
Measured over stack depths 0, 1, 2, 3, 16, 17, 18, on Shanghai..Amsterdam
(**CHECKED**: 5 forks x 8 bytes x 7 depths x 2 expectations = 560 params of
`test_undefined_byte_stack_depth`, of which exactly 280 pass and 280 fail, so
every cell is unambiguous):

```text
byte          stops guarding at stack depth
0x4B SLOTNUM  0      -- pops nothing, so a guard is broken unconditionally
0x5F PUSH0    0      -- same
0x1E CLZ      1      -- any non-empty stack
0xE8 EXCHANGE 3      (immediate 0x8E, decoding to the pair (1, 2))
0xE6 DUPN     17     (immediate 0x80, decoding to index 17 -- the minimum)
0xE7 SWAPN    18
```

So **EIP-7843's and EIP-3855's assignments are the dangerous ones** for this
idiom and EIP-8024's are mostly shielded by their own stack requirement. The
underflow behaviour itself is already swept exhaustively by
`tests/amsterdam/eip8024_dupn_swapn_exchange/test_dupn.py:246` and
`test_swapn.py:301`, so it is **cited, not rebuilt**; what is recorded here is
the consequence for the guard idiom, which those sweeps do not draw.

## Deployed witness — measured

**Population, stated once and used for every percentage below (CHECKED):**
**994,414 distinct mainnet runtime code hashes** backing **7,911,875 distinct
addresses**, from L2's staged corpus
(`lenses/L2/work/rt/shard=*`, blocks 51,291–26,259,375), with the
deployment↔runtime-hash join rebuilt from the Sourcify v2 export so address
counts are distinct addresses rather than deployment rows. Scanner written in C
and **cross-validated against an independent Python implementation: 0 mismatches
on 4,000 runtimes** (linear scan) and **0 mismatches on 2,500 runtimes x 7
bytes** (reachability classifier).

### (a) The byte is *present* somewhere in deployed code — the unreachable-bytes invariant

| byte | runtime hashes | distinct addresses |
|---|---|---|
| `0x1E` CLZ | 874,187 (87.91%) | 3,669,300 (46.38%) |
| `0x4B` SLOTNUM | 764,495 (76.88%) | 2,005,457 (25.35%) |
| `0x5F` PUSH0 | 815,732 (82.03%) | 5,076,634 (64.16%) |
| `0xE6` DUPN | 732,224 (73.63%) | 3,469,609 (43.85%) |
| `0xE7` SWAPN | 735,762 (73.99%) | 2,580,728 (32.62%) |
| `0xE8` EXCHANGE | 777,911 (78.23%) | 4,430,554 (56.00%) |
| `0xFE` (reserved) | 976,263 (98.17%) | 6,143,274 (77.65%) |

**The "~100%" guess in an earlier draft of this file was wrong and the
measurement corrected it.** The figure needs a length condition: among runtimes
of 4 KiB or more (696,658 hashes) each byte is present in **85.4%–99.5%**, and
**466,220 runtime hashes contain all seven bytes**; the sub-100% tail is
minimal proxies and EIP-1167 clones, too short to contain much. So the
unreachable-bytes invariant's population is between 2.0M and 5.1M addresses
depending on the byte, not "every contract".

### (b) The byte at a *reachable* position — the halt-as-a-guard idiom

Jumpdest-style walk (skip `n` bytes after `PUSH1`..`PUSH32`), CBOR metadata tail
stripped, then classified by the terminator-free run containing the byte.
`jd_named` = a `JUMPDEST` opens the run *and* some `PUSH` immediate names it;
`entry_fallthrough` = the run starts at pc 0. Unit: runtime hashes.

| byte | at a code position outside the tail | `jd_named` | `entry_fallthrough` |
|---|---|---|---|
| `0x1E` | 4,741 (0.48%) | 48 | **0** |
| `0x4B` | 11,158 (1.12%) | 43 | **0** |
| `0x5F` | 287,846 (28.95%) | 3,827 | 274,358 |
| `0xE6` | 5,854 (0.59%) | 3 | **0** |
| `0xE7` | 4,764 (0.48%) | 2 | **0** |
| `0xE8` | 7,475 (0.75%) | 10 | **0** |
| `0xFE` | 962,502 (96.79%) | 176,900 | 3,502 |

**The clean negative, hand-measured: 0 of 11 disassembled candidates is an
undefined byte in a reachable position.** All 119 `jd_named` candidates for the
five non-`PUSH0` bytes were inspected, and an exhaustive pass over 30,868
candidate runtimes requiring `jd_named` *and* no other undefined byte in the run
left **93 survivors, of which 92 are `0x1E` genuinely executing as `CLZ`
post-Osaka** (a defined opcode there) and the last one —
`<address withheld>`, `0xE8` — is hand-refuted as 30
bytes of zero padding followed by data. The refuted hits are ASCII `_` in revert
strings and embedded ABI JSON, ASCII `K` in base64 IPFS tables, and bytes inside
a solc CBOR blob.

**So: no deployed contract in this population uses an undefined byte other than
`0xFE` as a deliberate guaranteed halt.** That is the finding, and it explains
why the idiom survived four EIPs: compilers picked the one byte reserved
forever. **Scope caveat, stated:** the corpus is Sourcify-*verified* mainnet
deployments. Unverified contracts — hand-written assembly, obfuscated MEV bots —
are exactly where a deliberate non-`0xFE` halt is most plausible and are **not**
in this population.

### (c) `0xFE`, the calibration positive — real, ubiquitous, with addresses

| condition | runtime hashes | distinct addresses |
|---|---|---|
| `0xFE` at a code position outside the tail | 962,502 (96.79%) | 4,676,967 (59.11%) |
| …plausibly reachable (`jd_named` or better) | **180,402 (18.14%)** | **2,466,439 (31.17%)** |

**The predecessor opcode of the best hit is `JUMPI` in 177,918 of those 180,402
runtimes** — the solc `assert`/`throw` guard, identified by its own signature
rather than assumed. Hand-disassembled, identical in all three:

```text
Tether a major stablecoin          <address withheld>  blk 4,634,748
  10788 PUSH2 0x2a29 / 10791 JUMPI / 10792 INVALID / 10793 JUMPDEST
a major DEX router  <address withheld>  blk 10,207,858
    462 PUSH2 0x01d3 /   465 JUMPI /   466 INVALID /   467 JUMPDEST
a widely deployed smart-account wallet    <address withheld>  blk 12,504,268
  11876 PUSH2 0x2e69 / 11879 JUMPI / 11880 INVALID / 11881 JUMPDEST
```

Also present: a deployed oracle network LINK `<address withheld>`,
a major DEX UNI `<address withheld>`, a deployed CDP protocol LUSD
`<address withheld>`. a canonical wrapped-ether contract and the a major stablecoin proxy have no
`0xFE` code position at all. Of the 780,537 runtimes whose only `0xFE` is
unreachable, 460,740 sit immediately before the metadata — solc's
code/metadata separator, correctly classified as dead. So the 96.79% splits into
"one inert separator byte" (~81%) and "the real `assert` idiom" (180,402 hashes
/ 2,466,439 addresses).

This is why the archetype's control test pins `0xFE`: **2.47M addresses rely on
that byte halting, and the only reason they are safe is that it is reserved.**

### (d) The corpus validates the fork boundary on its own

Of the 274,358 runtime hashes with `0x5F` in a definitely-reachable
`entry_fallthrough` position, the **minimum deployment block is 17,230,795 —
after Shanghai at 17,034,870. Zero pre-Shanghai** (CHECKED). And 6,614 runtime
hashes / 172,628 addresses deployed *before* Shanghai do contain `0x5F` at a
non-PUSH-data code position outside the tail, of which only **13 hashes / 16
addresses** survive the reachability filter — all `jd_named`, none
`entry_fallthrough`, and all hand-refuted as ASCII in strings or ABI JSON. So
not one contract deployed before `PUSH0` existed reaches a `0x5F` byte. The
fork table in the section above is not merely asserted by the spec; the deployed
corpus agrees with it.

Independently, all 48 `0x1E` `jd_named` candidates have minimum deployment block
≥ 24,119,272, tightly clustered and increasing, with zero earlier occurrences —
the signature of a fork activation. **INFERRED:** Osaka activated at or before
block 24,119,272. The mainnet activation height was not independently verified.

### (e) The reverse direction, witnessed by incident

In 2023 solc 0.8.20 defaulted to the Shanghai target and emitted `PUSH0`;
contracts deployed to chains that had not forked hit `0x5F` and bricked. Same
invariant, observed from the side where code assumes the byte *is* valid.
**INFERRED** from public record, not measured here.

## Deliberately not built, with the reason

**"A contract that validates other contracts' bytecode by scanning for invalid
opcodes."** This was on the brief and is not here. Such a contract would carry a
hardcoded table of valid opcode bytes, which a fork invalidates by construction,
so the invariant is sound — but **no deployed address witness was established**
(the corpus sweep above looked for code *containing* undefined bytes, not for
code *inspecting* them, and found no scanner), and SCHEMA §1.2 is explicit that
zero instances puts a pattern out of scope
("Witnessed. At least one deployed instance exists, with an address. Rarity is
fine — a pattern with 3 instances is in scope. Zero instances is not"). Building
a test for an idiom with no witness would be padding, and `docs/` already records
one class (#19) and one deliberate non-build (#26) resolved exactly this way.
If a witness is later found, the archetype shape is already here: deploy the
scanner, `EXTCODECOPY` a target whose code contains the byte, and assert the
verdict flips at the assignment fork.

**The EIP-8024 jumpdest-in-immediate question** is also not built: it is already
covered officially and thoroughly, by
`tests/amsterdam/eip8024_dupn_swapn_exchange/test_fork_transition.py:99`
(`test_jumpdest_in_immediate_at_fork_transition`),
`test_eip_vectors.py:319,793` and `test_swapn.py:392,439`. Confirmed from the
reference implementation: `get_valid_jump_destinations` skips only PUSH data and
advances one byte past anything it cannot decode
(`amsterdam/vm/runtime.py:55-66`), so an EIP-8024 immediate byte holding `0x5B`
**remains a valid jump destination** at Amsterdam. Cited, not rebuilt.

## The tests

Four, and the fork scoping is the product rather than a problem.

| test | scope | asserts |
|---|---|---|
| `test_undefined_byte_is_a_guaranteed_halt` | per-param `valid_from("Berlin")` + `valid_until` the fork before assignment | the guarded slot still holds its sentinel; the caller's `CALL` returned 0 |
| `test_assigned_byte_no_longer_guards` | per-param `valid_from` the assignment fork | the guarded slot now holds the forbidden value; `CALL` returned 1 |
| `test_bytes_that_never_got_assigned_still_halt` | `valid_from("Berlin")` | `0xFE` and `0x0C` halt on every fork — the arm that stays green |
| `test_unreachable_undefined_bytes_leave_the_code_runnable` | `valid_from("Berlin")` | a contract carrying all eight bytes in a jumped-over region still commits |

The first two are the same deployed bytecode asserted from both sides. The first
**would fail if run unscoped on a later fork**, which is correct: that is the
break, and it is asserted by the second rather than tuned away — the split
`wave1/gas_monotonicity/` uses.

The guarded slot is pre-seeded with a sentinel (`0x5AFE`) rather than left at
zero, so "the write did not happen" is a positive assertion. Asserting `0` would
also be satisfied by a slot that was never written for an unrelated reason.

Support code forwards `Op.GAS`, never a literal — a literal gas operand in
support code is itself a frozen budget, and the Amsterdam floor for one fresh
slot is ~110,026 (class #1). This corpus has eaten that mistake once already
(`tests/code_presence_identity/README.md`).

## Reproduce

```bash
cd tests/deployed_idioms
# the archetype
python3 tools/locked_fill.py \
    /home/devops/toni/datanalysis/eip-8037/expansion/undefined_opcode_halt \
    --until Amsterdam --output /tmp/a1 -q -p no:cacheprovider     # 198 passed

# the whole expansion wave, one summary
python3 tools/verify_corpus.py --wave expansion

# the measurement that designed it (its FAILURES are the measurement)
python3 tools/locked_fill.py \
    /home/devops/toni/datanalysis/eip-8037/expansion/instruments \
    --from Berlin --until Amsterdam \
    -k "undefined_byte_flip and state_test and not blockchain" \
    --output /tmp/uop -q --tb=no -p no:cacheprovider

# mutations
python3 tools/mutate.py --wave expansion -k exp-op --archetype undefined_opcode_halt
```

## Mutation result

See `expansion/docs/MUTATIONS-exp-opcodes.md` for the full table. Summary:

- `exp-op-undefined-is-a-noop-{paris,prague,osaka,amsterdam}` — an undefined
  byte stops halting. This is the only shape that can falsify an invariant whose
  content is "nothing after this byte ever runs", the same problem class #9 hit
  (it needed a mutation that *adds* a refill). Scoped per fork so each one meets
  the arms that are valid there.
- `exp-op-{slotnum,dupn,swapn,exchange,clz,push0}-moved-off-*` — the byte is
  assigned to a different, free byte, so the original is undefined again. These
  break the violation arms and are **graded by byte**: each one can only reach
  its own params, so the failure count identifies which assignment moved.
- `exp-op-code-validated-at-frame-entry` — EOF-style static validation
  (EIP-3670) applied to legacy code.

## What a failure means

The invariant arm failing means a fork has claimed a byte that deployed code was
using as a guaranteed halt: a frame that used to abort now runs on, and whatever
sits behind the byte commits. Nothing reverts, no gas number moves, and no
code-hash pin changes.

The control arm failing means a fork has claimed `0xFE` or `0x0C` — for `0xFE`
that is every solc-`<0.8` `assert()` on the chain losing its abort at once.

`test_unreachable_undefined_bytes_leave_the_code_runnable` failing means legacy
bytecode acquired static validation, which would brick essentially every
deployed contract, because every one of them carries a metadata blob of
arbitrary bytes.
