# Archetype 22: code presence as an identity test

**Invariant.** An account reporting code is a contract; an account reporting none is not.
`isContract(a) == (a.code.length > 0)`.

**Why this class exists at all.** Classes 1–20 of this catalogue are gas-shaped — each
asks what happens when a price moves. This one is not, and **no repricing breaks it**.
A fork can change *meaning* without changing any cost, and EIP-7702 did exactly that: it
broke the most widely deployed identity idiom on Ethereum while repricing nothing. The
corpus needed a non-gas axis and did not have one until L2's sweep surfaced this family.

**Mechanism** (CHECKED):

```text
EOA_DELEGATION_MARKER = b"\xef\x01\x00"            vm/eoa_delegation.py:36
  full designator = 3-byte marker + 20-byte address = 23 bytes
EXTCODESIZE: codesize = U256(len(code))            vm/instructions/environment.py:357
  -- the raw code length, with NO delegation resolution
```

So from Prague onward, for any EOA that has ever signed an authorization:

```
EXTCODESIZE(eoa) == 23   ->   isContract(eoa) == true
```

The account is still externally owned — it sends transactions and holds a nonce. Every
deployed `require(!isContract(x))`, every "reject contract callers" gate, and every "this
must be a wallet" check silently changed meaning.

**Deployed witness.** L2's `EXTCODESIZE`-gate detector: **618,693 distinct runtime code
hashes across 2,417,615 addresses**, FP **0/8** hand-validated — the second-largest
measured population in the corpus, behind only revert bubbling.

**Two tests, split by fork.** The first asserts the *sound* form on every fork from Berlin
(a plain EOA is not a contract, a contract is), so the discriminator is pinned rather than
assumed. The second asserts the violation from Prague, pinning both the boolean (the harm)
and the exact 23-byte designator length (the format that produces it).

**Reproduce**

```bash
cd engine/eels
./.venv/bin/fill ../../wave1/code_presence_identity --until Amsterdam \
    --output /tmp/cpi -q -p no:cacheprovider          # 31 passed
cd ../../patterns && python3 tools/mutate.py -k extcodesize
```

**Mutation.** `extcodesize-hides-delegation` makes `EXTCODESIZE` report 0 for a
delegation designator — i.e. it *repairs* the hazard — which flips both assertions in the
Prague test.

**A note on this corpus eating its own dog food.** The first version of the control test
forwarded a literal `100_000` to a probe that creates one storage slot. It passed Berlin
through Osaka and failed on Amsterdam, because 100,000 is below the measured ~110,026
floor — archetype 1's exact finding, applied accidentally to this corpus's own test code.
The control now forwards `GAS`. Worth remembering when writing any test here: a literal
gas operand in *support* code is itself a frozen budget.

**What a failure means.** Either the delegation designator format changed, or
`EXTCODESIZE` started resolving delegations. In the second case, 2.4 million addresses'
worth of deployed identity gates change behaviour again — this time back.
