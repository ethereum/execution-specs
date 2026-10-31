# Candidate class, identity dimension: assignment changes what code does, not what code is

**Invariant, two-sided.**

(a) `EXTCODESIZE` and `EXTCODEHASH` are the raw length and the raw `keccak256`
of the deployed bytes, with no reference to the opcode table. So a contract
whose bytes include `0x4B` or `0x1E` has **exactly** the same size and hash
across the fork that turns those bytes into `SLOTNUM` and `CLZ` — while its
behaviour may change completely. **A code-hash pin is structurally incapable of
noticing an opcode assignment.**

(b) The reverse: `PUSH0` exists only to spell `PUSH1 0x00` in one byte. Two
builds of one routine behave identically, differ in size by exactly 1, and hash
differently. So recompiling unchanged source with a `PUSH0`-capable compiler
breaks every hash pin against it, with no behavioural change to point at.

Together: **the only two observables deployed safety checks have for "is this
the code I audited" are blind in one direction and over-sensitive in the
other.** That asymmetry is the finding, and it is why the brief's question
("does `PUSH0` change the length or hash of otherwise-identical compiled
output?") has a sharper answer than yes.

## Mechanism (CHECKED, pinned EELS Amsterdam commit 168980009)

```text
EXTCODESIZE:  codesize = U256(len(code))      amsterdam/vm/instructions/environment.py:357
EXTCODEHASH:  keccak256 over the account's code bytes
Ops(byte) is resolved lazily at the program counter  amsterdam/vm/interpreter.py:440
  -> there is no code validation, so validity never enters identity
```

## Relation to existing classes (CHECKED)

- **Class #22, code presence as an identity test** (`tests/code_presence_identity/`,
  31 fill) pins `isContract(a) == (a.code.length > 0)` and the EIP-7702
  delegation-designator hazard. It is the nearest neighbour and it is a
  different question: #22 asks *how much* code an account reports, this asks
  whether *which bytes are instructions* can be seen from the outside. #22's
  mutation `extcodesize-hides-delegation` does not reach here and this
  archetype's detectors do not reach #22.
- **Class #23, counterfactual address validity** pins address derivation over
  init code; it never compares two semantically equal builds.
- No gas-shaped class can see either half — nothing is repriced.

## Prior art does not cover it (CHECKED)

- `tests/shanghai/eip3855_push0/test_push0.py` is 162 lines; it asserts
  `PUSH0`'s stack and gas behaviour and **touches neither `EXTCODEHASH` nor
  `EXTCODESIZE`** (0 grep hits). It never compares a `PUSH0` build with its
  `PUSH1 0x00` twin.
- `tests/osaka/eip7939_count_leading_zeros/`,
  `tests/amsterdam/eip7843_slotnum/` and
  `tests/amsterdam/eip8024_dupn_swapn_exchange/` assert nothing about code
  identity.

## Deployed witness

Half (a) has **two** populations and they multiply: the contracts whose bytes
contain a later-assigned byte, and the gates that pin a code hash.

**Contracts whose deployed bytes contain a byte that four EIPs later claimed
(CHECKED).** Measured over **994,414 distinct mainnet runtime code hashes**
backing **7,911,875 distinct addresses** (L2's staged corpus, blocks
51,291–26,259,375; address counts rebuilt from the Sourcify v2 deployment join;
C scanner cross-validated against an independent Python implementation, 0
mismatches on 4,000 runtimes). Full method in
`../undefined_opcode_halt/README.md`.

| byte | runtime hashes | distinct addresses |
|---|---|---|
| `0x1E` CLZ | 874,187 (87.91%) | 3,669,300 (46.38%) |
| `0x4B` SLOTNUM | 764,495 (76.88%) | 2,005,457 (25.35%) |
| `0x5F` PUSH0 | 815,732 (82.03%) | 5,076,634 (64.16%) |
| `0xE6` DUPN | 732,224 (73.63%) | 3,469,609 (43.85%) |
| `0xE7` SWAPN | 735,762 (73.99%) | 2,580,728 (32.62%) |
| `0xE8` EXCHANGE | 777,911 (78.23%) | 4,430,554 (56.00%) |

**466,220 runtime hashes contain all six.** Every one of those keeps its exact
`EXTCODESIZE` and `EXTCODEHASH` across Shanghai, Osaka and Amsterdam — which is
precisely the point of half (a): between 2.0M and 5.1M addresses' worth of
deployed bytes had their instruction set reinterpreted and **no code-hash pin
anywhere could tell.**

**The gates that pin a code hash** are class #22's lens measurement: **618,693
distinct runtime code hashes across 2,417,615 addresses, FP 0/8 hand-validated**
(`docs/INVARIANT-CLASSES.md` #22). Cited, not re-measured, and not claimed as
this archetype's own.

**Half (b)'s witness is the compiler, not a contract:** every runtime emitted by
solc >= 0.8.20 under default settings differs from its pre-Shanghai build by
this exact substitution. Corroborated from the data: of the 274,358 runtime
hashes with `0x5F` at a definitely-reachable entry position, the minimum
deployment block is **17,230,795 — after Shanghai at 17,034,870, with zero
earlier** (CHECKED). The 2023 "solc 0.8.20 targets Shanghai" deployment breakage
on chains that had not forked is the same mechanism observed from the execution
side; **INFERRED** from public record.

## The tests

| test | scope | asserts |
|---|---|---|
| `test_code_identity_does_not_move_when_a_byte_is_assigned` | `valid_from("Berlin")` | the contract still runs and commits; `EXTCODESIZE` equals the exact byte count; `EXTCODEHASH` equals a **single Python-computed `keccak256` literal, the same on all eight forks** |
| `test_push0_changes_identity_without_changing_behaviour` | `valid_from("Shanghai")` | both builds run and commit the same value; `EXTCODESIZE(push1) - EXTCODESIZE(push0) == 1`; the hashes differ; each equals the `keccak256` of its own bytes |

Fork-identity in the first test is **demonstrated, not assumed**: one hash
literal, eight forks, no per-fork table — the same technique class #12 used to
show `COLD_STORAGE_ACCESS` is fork-stable rather than asserting it.

The first test also *calls* the target rather than only reading its metadata.
That is what gives this archetype a detector at all (see below) and it is one
`CALL` of overlap with `undefined_opcode_halt`'s unreachable-bytes test, stated
rather than hidden.

## Reproduce

```bash
cd tests/deployed_idioms
python3 tools/locked_fill.py \
    /home/devops/toni/datanalysis/eip-8037/expansion/opcode_assignment_code_identity \
    --until Amsterdam --output /tmp/a3 -q -p no:cacheprovider      # 37 passed

python3 tools/mutate.py --wave expansion -k exp-op \
    --archetype opcode_assignment_code_identity
```

## Mutation result

Full table in `expansion/docs/MUTATIONS-exp-opcodes.md`.

- `exp-op-push0-moved-off-5f-shanghai` — **DETECTED**, and it is the honest
  detector of half (b): un-assigning `0x5F` makes the `PUSH0` build halt, so
  the behavioural-equality assertion fails. The Amsterdam variant of the same
  mutation detects it too but is **not specific** (see the docs file: Amsterdam's
  pre-deployed system contracts are themselves compiled with `PUSH0`, so every
  blockchain-format fixture dies).
- `exp-op-code-validated-at-frame-entry` — **DETECTED**, the detector of half
  (a): with EIP-3670-style validation the target refuses to run, so `target_ran`
  goes to 0 while its size and hash are unchanged. That is the hazard stated
  exactly: identity is fine, execution is gone.

**Explained survival, and it is the point of the archetype.** Every
`exp-op-*-moved-off-*` mutation other than `push0` **survives**, and so does
every `exp-op-undefined-is-a-noop-*`. That is not a coverage gap: assigning or
un-assigning `0x4B`, `0x1E`, `0xE6`, `0xE7` or `0xE8` **cannot** change
`EXTCODESIZE` or `EXTCODEHASH`, because neither consults the opcode table. The
survival *is* the invariant being asserted. Recorded here explicitly so it is
never mistaken for a weak test, following the `state-clamp-off` /
`floor-token-8` precedent in `docs/MUTATION-MATRIX.md`: a mutation that survives
for a stated reason is a result.

## What a failure means

Test 1 failing means either code identity started depending on opcode validity
(so an audited-hash allowlist would start rejecting contracts it previously
accepted), or legacy code acquired static validation and the contract stopped
being runnable while its hash stayed put.

Test 2 failing means `PUSH0` stopped being a one-byte spelling of
`PUSH1 0x00` — either its byte moved, or its behaviour diverged. In the first
case every contract compiled by a modern solc stops working.
