# Class #23: counterfactual address validity

**Invariant.** The address a contract derives for a deployment it has not yet made is the
address that deployment actually lands at.

**Status: 179 fill, Berlin→Amsterdam, 0 failures; `pass(27)` at Amsterdam. All 8 `cls23-`
mutations DETECTED, every one of them by this archetype alone — perfect specificity, 8/8.**

A contract commits to that address *in advance* — pre-funds it, writes it into a registry,
grants it permissions, publishes it as a cross-chain identity — and only later puts code
there. Two derivations are in deployed use, and both are reimplemented in **EVM bytecode**
rather than looked up:

```text
CREATE2   keccak256(0xff || deployer || salt || keccak256(initcode))[12:]
          amsterdam/utils/address.py:88-93
CREATE    keccak256(rlp([deployer, nonce]))[12:]
          amsterdam/utils/address.py:60-63
```

**This class is semantic, not gas-shaped.** Nothing in it moves if a price moves; it moves
if a derivation input, the preimage layout, the truncation side, or the nonce-increment rule
changes. `code_presence_identity` is the precedent — EIP-7702 broke the most deployed
identity idiom on Ethereum while repricing nothing.

---

## Deployed witnesses

Read out of `registry/L2-bytecode.jsonl`. **The brief's figures conflated two columns**:
`instances` counts *witnessing program points*, not addresses. Corrected:

```text
shape                runtimes  addresses  program points  FP     confidence
adr.create2_derive      2,723      2,945           3,217  0.0    CHECKED
adr.create_derive         187        205             366  0.25   INFERRED
```

* **`adr.create2_derive`.** The detector's spec is literally the shape these tests build:
  *"a SHA3 site whose preimage length is exactly 85 (0x55)"*. Its registry `invariant` field
  is this class's invariant verbatim. FP 0.0 by deployment-block self-check (0 of 2,723
  runtimes predate Constantinople, so none is a misdecoded data region; earliest genuine
  deployment block 8,588,119). Calibration positive: **a major NFT exchange's conduit derivation**.
  Exemplar `<address withheld>` pc 1870.
* **`adr.create_derive`.** Far rarer, and its **FP rate is 0.25**: 2 of 8 hand-disassembled
  hits hash 23 bytes of non-RLP data (a selector plus a word — a storage-slot computation),
  not an address. The population is therefore stated with the caveat rather than leaned on.
  The *named* witness does not depend on the detector: **a gas-token contract**
  `<address withheld>` derives its children's addresses from its own
  nonce in order to free them (CHECKED by hand).

An independent source-side lens corroborates CREATE2 at a far larger scale: L1's *"CREATE2
address derived in source"* is **8,172 distinct runtimes over 22,270 confirmed source
files**, exact count mode (all 7,989 mainnet-reachable prefilter hits confirmed
individually, 2,650 passed), hand-measured precision 1.0, 13,120 first-party confirmed
addresses.

---

## Prior art, and exactly what it leaves uncovered (CHECKED)

The official suite derives counterfactual addresses **in Python** and asserts the contract
landed there:

```text
tests/amsterdam/eip7997_deterministic_factory_contract/test_factory.py   1,437 lines
tests/amsterdam/eip8037_state_creation_gas_cost_increase/test_state_gas_create.py:675,2805
tests/cancun/eip6780_selfdestruct/test_collision_selfdestruct.py:56
tests/cancun/eip6780_selfdestruct/test_dynamic_create2_selfdestruct_collision.py:124,351,626
tests/berlin/eip2929_gas_cost_increases/test_warm_status_revert.py:185
tests/amsterdam/eip7928_block_level_access_lists/test_block_access_lists.py:4251
tests/amsterdam/eip8246_selfdestruct_no_burn/test_selfdestruct_no_burn.py:571
```

Every one goes through `compute_create2_address(...)` from
`execution_testing.test_types.helpers`. That checks the client against EEST's own Python
reimplementation of the derivation. It does **not** check the deployed idiom, which is a
`keccak256` assembled in EVM memory out of literals a contract committed to years ago.
**Nothing in `tests/` hashes a CREATE2 preimage with `SHA3`** — the only EVM-side `SHA3` in
the 7997 directory hashes the factory's *code* (`test_factory.py:86`,
`test_eip_mainnet.py:46`). So a change on the *contract's* side of the equality is invisible
to the official suite and visible here; `cls23-sha3-opcode-salted` is the mutation that
demonstrates it.

This archetype asserts **both** sides: the in-EVM derivation against the landing site, and
the landing site against the Python helper, so a divergence is attributed rather than merely
detected. It also covers the forks the 7997 directory cannot: those tests are all
`valid_from("EIP7997")`, while CREATE2 derivation has been deployed since Constantinople and
these tests run Berlin→Amsterdam.

---

## The four tests

```text
test_create2_counterfactual_address_is_where_the_contract_lands   4 params, Berlin+
test_counterfactual_prefunding_survives_the_deployment            1 param,  Berlin+
test_create_from_nonce_counterfactual_address                     3 params, Berlin+
test_deterministic_factory_counterfactual_address                 1 param,  EIP7997+
```

**The CREATE2 preimage, built in memory exactly as deployed assembly builds it.** 85 bytes
at `0x0b`, so the 20-byte deployer sits right-aligned in the word at `0x00`:

```text
0x00 .. 0x1f   MSTORE(0x00, ADDRESS)        deployer right-aligned at 0x0c..0x1f
0x0b           MSTORE8(0x0b, 0xff)          the domain-separation byte, written after
0x20 .. 0x3f   MSTORE(0x20, CALLDATALOAD 0) the salt
0x40 .. 0x5f   MSTORE(0x40, SHA3(initcode)) the init-code hash, computed on chain
               AND(SHA3(0x0b, 0x55), 2**160 - 1)
```

The init code arrives in calldata and is hashed with `SHA3`, so the preimage is assembled
from runtime values rather than constants. Parameters cover a zero salt, a salt with the top
bit set (a sign-extension bug in the preimage would show), the maximum salt, and **empty
init code** — whose `keccak256(b"")` is the one preimage component a contract cannot read out
of its own calldata.

**The CREATE preimage.** 23 bytes at `0x0a`: `0xd6 0x94 || deployer(20) || nonce(1)`, where
`0xd6 = 0xc0 + 22` is the RLP list header for a 22-byte payload, `0x94 = 0x80 + 20` the
string header for the address, and a single-byte nonce in `[0x01, 0x7f]` is its own RLP
encoding. A contract's nonce is 1 at deployment (EIP-161) and each `CREATE` increments it, so
the test burns `nonce - 1` throwaway creates first.

**Parametrising the nonce pins the increment rule, not just the preimage.** Both halves of
that rule have moved before: Spurious Dragon moved the increment to *before* the init code
runs, and EIP-2681 capped the nonce at `2**64 - 1` (visible in `generic_create`'s preflight,
`vm/instructions/system.py:96`). `cls23-create-nonce-not-incremented` is the mutation that
exercises it, and the result is **graded** — see below.

**The pre-funding test is where the class stops being a hashing curiosity.** The factory
derives the address, sends ether to **an account that does not exist**, and only then
deploys. Six markers: the derived address, the address `CREATE2` returned, their equality, the
success of the value-bearing call to a codeless address, the balance while the address is
still codeless, and the balance afterwards — and the factory then calls the derived address
so the deployed runtime's own `SSTORE` is asserted too. The
deployment succeeds at an address that already holds a balance because `account_deployable`
tests nonce and code only (`state_tracker.py:362-370`, CHECKED).

---

## Mutation result

Eight mutations in `tools/mutations/cls-18-23.json`. **Direction is not a meaningful axis
for a semantic equality** — there is no "cheaper" way to be wrong about an address — so the
two-sidedness this class can offer is different, and it is provided deliberately in two
forms:

1. **Every input of every derivation is mutated separately**: prefix byte, salt, init-code
   hash, truncation side, nonce value, nonce presence, nonce increment. A derivation is a
   function of several arguments, and pinning each one individually is the analogue of
   bracketing a budget from both sides.
2. **Three of the eight are *loosenings*, not substitutions** — the closest semantic
   analogue of a cheaper reprice, in that the rule becomes *less* discriminating rather than
   differently discriminating. `cls23-create2-salt-ignored`, `cls23-create-no-nonce` and
   `cls23-create-nonce-not-incremented` each collapse many distinct derived addresses onto
   one. That direction matters for the same reason EIP-1108's reductions matter to class #12:
   a rule that stops separating things breaks a *different* population from one that
   separates them differently.

A third axis is available here and nowhere else in the corpus: one mutation perturbs the
**contract's** side of the equality rather than the EVM's.

From `mutate.py -k cls23- --md` over **all 24 archetypes** (the unrestricted column).
**Every one of the eight has exactly one detector: this archetype. Perfect specificity, 8
for 8** — no other test shape in the corpus can observe an address derivation.

```text
mutation                             counterfactual_address   what it pins
(baseline)                           pass(27)
cls23-create2-prefix-fe              DETECTED(18)             the 0xff domain separator
cls23-create2-salt-ignored           DETECTED(18)             the salt as an input
cls23-create2-raw-initcode           DETECTED(18)             the inner keccak
cls23-create2-high-20-bytes          DETECTED(18)             which end the hash truncates
cls23-create-nonce-plus-one          DETECTED( 9)             the nonce value in the RLP
cls23-create-no-nonce                DETECTED( 9)             the nonce as an input
cls23-create-nonce-not-incremented   DETECTED( 6)             the increment rule  <- graded
cls23-sha3-opcode-salted             DETECTED(27)             the contract's own hash
```

**Every count was predicted before the run and came back identical.** The Amsterdam fill is
27 tests — `12` CREATE2-derivation (4 params) + `3` pre-funding + `9` CREATE-from-nonce (3
params) + `3` deterministic-factory, each param in three fixture formats — and the counts
partition it exactly:

* **18 = 12 + 3 + 3** for every CREATE2 mutation: the three CREATE2-based tests fail and the
  CREATE-from-nonce arm is untouched.
* **9** for every CREATE mutation: only the nonce arm fails, and the three CREATE2-based
  tests are untouched.
* **27** for the opcode mutation: all four tests fail, because the contract's own hash moved.

So the two derivations are **cleanly discriminated by the failure signature**, not merely
both covered. A failure pattern of 18 says the CREATE2 preimage moved; 9 says the RLP form
moved; 27 says `KECCAK256` itself moved.

**`cls23-create2-high-20-bytes` is scoped to the CREATE2 function only, and the count proves
it.** The line
`canonical_address = computed_address[-20:]` appears in *both* derivation functions in
`utils/address.py`, so the mutation's `find` spans three lines to hit one of them. That makes
the mutation discriminate the two derivations instead of breaking both at once.

**`cls23-create-nonce-not-incremented` is the graded one, and the grading was predicted then
measured.** It fails **6 of the 9** nonce tests, not 9: with the increment removed the
`nonce_1` param is unaffected — the first create still lands where nonce 1 says — while
`nonce_2` and `nonce_3` collide onto the nonce-1 address, `CREATE` pushes 0, and the
derivation disagrees. `6 = 2 params x 3 formats`, exactly. The failure *pattern* therefore
locates the rule, the way `retention-128` versus `retention-256` does for the forwarding
divisor. A single-nonce test would have reported "survives" and recorded a coverage gap that
was not one.

**`cls23-sha3-opcode-salted` is the mutation no Python-side test can have, and it fires on
all 27.** It perturbs the `KECCAK256` opcode (`vm/instructions/keccak.py:57`) and leaves
`utils/address.py` alone, so the *contract's* derivation moves while the landing site stays
put. Every official counterfactual test computes the expected address in Python and is
structurally blind to this direction. It is also the reason these tests assert the derived
address, the returned address **and** their equality separately: the three markers
distinguish "the EVM moved", "the contract moved", and "they disagree".

Worth noting what it says about the rest of the corpus too: **no other archetype detects it
either**. Twenty-three of the twenty-four survive a `KECCAK256` opcode that returns the wrong
hash. That is not a gap in those archetypes — none of them hashes anything — but it does mean
this archetype is the corpus's only check that the hash function the EVM exposes to contracts
is the hash function the protocol itself uses.

### The archetype row (`mutate.py --archetype counterfactual_address`, all 83 mutations)

This archetype detects **9 of the 83 registered mutations**: its own 8, plus
`cls11-no-child-gas-return` at DETECTED(9) — which is exactly the CREATE-from-nonce arm, the
CREATE2 arms surviving. That mutation removes `gas_meter.gas_left += child_meter.gas_left`
(`vm/__init__.py`), so a child's unspent gas never returns to the parent. **CHECKED:** the
count is 9 of 27, so it is the nonce arm alone. **INFERRED:** the cause is budgetary rather
than semantic — the nonce arm's post-create storage writes no longer fit once a create's
forwarded `all-but-1/64` is permanently lost, while the CREATE2 arms retain just enough
slack. It is not a false signal, but it is a *support-code* sensitivity rather than a
derivation one, and it is recorded here so nobody reads it as evidence about address
derivation.

The other 74 mutations survive, which is the expected shape: this class is semantic, and
nothing in it depends on a price.

---

## Reproduce

```bash
cd engine/eels
# never fill while a mutate.py run holds the lock
python3 ../../tools/locked_fill.py ../../wave1/counterfactual_address \
    --from Berlin --until Amsterdam --output /tmp/cfa -q -p no:cacheprovider

cd ../../patterns
python3 tools/mutate.py -k cls23- --archetype counterfactual_address   # the row
python3 tools/mutate.py -k cls23- --md                                 # the column
```

**What a failure means.** Funds already sent to a counterfactual address are stranded at an
address no deployment will ever reach, and every registry entry, allowlist and cross-chain
address mapping that pinned the old derivation points at the wrong account. Nothing reverts —
the factory's own `CREATE2` succeeds — so the loss is silent.
