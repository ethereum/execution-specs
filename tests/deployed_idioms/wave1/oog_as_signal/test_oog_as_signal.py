"""
Archetype 12: the two-sided OOG-as-signal capability probe.

A caller asks an unknown contract a yes/no question under a hardcoded gas
literal and treats **any** failure as "no". Nothing reverts, so a repricing
that moves a target across the literal does not produce an error -- it
produces a *wrong answer*, and the caller commits effects down the wrong
branch. This is the quietest failure shape in the corpus.

Two deployed witnesses, both CHECKED by lens L5 over mainnet blocks
26,250,000-26,259,999 (10,000 blocks, 2,571,532 transactions):

**a deployed AMM** `<address withheld>` (Sourcify:
`a deployed AMM`, solc 0.4.26) asks converters `isV28OrHigher()` (selector
`0xd260529c`) under a hard cap, in assembly, with the bet written in the
comment -- `a deployed AMM.sol:1398-1415`:

```solidity
success := staticcall(
    5000,          // isV28OrHigher consumes 190 gas, but just for extra safety
    _converter, add(data, 32), mload(data), ret, 32)
...
return success && ret[0] != 0;        // ANY failure => "not v28+", silently
```

and **seven** call sites branch on the result (lines 1120, 1134, 1282, 1293,
1305, 1313, 1364). Both arms are witnessed in the same window
(`lenses/L5/sql/23-ammprobe-isv28-probe.sql`):

```text
succeeded  2,529 frames  818 txs  93 targets  avg 293.9 of 5,000  max 1,155
reverted     459 frames  230 txs   6 targets  avg 1,430.8         max 1,823
OUT OF GAS     10 frames    6 txs   3 targets
```

Resolved against Sourcify: the succeeding targets are `StandardPoolConverter`
(solc 0.6.12); the out-of-gas targets are a deployed AMM contract (solc
0.4.21/0.4.23) -- genuinely pre-v28 converters, so the probe is currently
**correct**. The erosion is the useful number: the comment says 190 gas, the
measured cost today is 293, so headroom has already fallen from 26x to 17x
purely from intervening repricings.

**ERC-165** `supportsInterface(bytes4)` at exactly 30,000 is the same shape
with the literal written into a *standard* ("must use less than 30,000 gas",
and the reference caller does `staticcall(30000, ...)`), so it is not one
contract's choice. L3 counts 163,050 implementing addresses;
`lenses/L5/sql/25-erc165-30000.sql` measured at the ceiling:

```text
reverted   17,657 calls / 15,723 txs / 197 callers / 63 targets
                                 max gas used 29,588  <- 412 from the cap
succeeded   9,904 calls /  2,575 txs / 166 callers / 262 targets
                                 max gas used  8,476
```

**64.36% of live `supportsInterface` calls fail**, so callers are already
habituated to reading failure as "unsupported" and would not notice a
repricing converting a compliant implementation into an unsupported one.

## Why both arms, and why the second one is not hypothetical

The invariant is two-sided and a reprice can flip either direction:

* **reads get dearer** -> a capable target stops answering -> "supported"
  becomes "unsupported". Every historical gas reprice but EIP-1108 pushed
  this way (EIP-1884 SLOAD 200->800; EIP-2929 cold 2,100).
* **reads get cheaper** -> an incapable target starts answering ->
  "unsupported" becomes "supported". This is the direction catalogues forget.
  It is witnessed: of the fifteen gas constants that changed value across the
  fifteen mainnet forks, **five moved down**, and EIP-1108 cut
  `PRECOMPILE_ECMUL` 40,000 -> 6,000 -- a **6.7x reduction**. A target whose
  work sits just over a literal is exactly what such a cut converts into a
  false "yes".

A one-sided test would therefore protect only half of a shape whose whole
danger is that neither half announces itself.

## The bracket, measured not assumed

`tests/tools/test_capability_arms_probe.py` (CHECKED; Berlin, London, Cancun,
Prague, Osaka, Amsterdam -- identical on all six). The only repricing-
sensitive mechanism in each target is the cold storage read, which is 2,100
gas and unchanged across that whole range (`COLD_STORAGE_ACCESS`,
amsterdam/vm/gas.py:78), so the brackets below are fork-stable:

```text
literal   cold reads that ANSWER   cold reads that DO NOT   boundary cost
 5,000    2   (~ 4,210 gas)        3   (~ 6,315 gas)        5,000
30,000    14  (~29,470 gas)        15  (~31,575 gas)        30,000
```

Each literal is pinned from both sides, so **any** reprice of a storage read
moves at least one arm. That is the tight two-sided form
`tests/frozen_budget/README.md` asks for in its "Known limitation" section,
here achieved without a per-fork table because the mechanism is fork-stable.

Headroom honesty, since the two literals differ in how faithful the bracket
is to production:

* the **30,000** arm is faithful: L5's tightest witnessed success is 29,588
  of 30,000, and the modelled capable target costs ~29,470. Production
  breaks on the first reprice of a read, and so does this test.
* the **5,000** arm is *tighter* than production: a deployed AMM's live
  implementations use 294 gas on average (max 1,155), so production breaks at
  roughly a 4x read reprice whereas this arm fires at ~1.2x. It is an
  early-warning canary at that literal, deliberately, and is reported as such
  rather than presented as a faithful break point.

## What a failure means

The probe derived the wrong boolean about a target's capability, and no
transaction reverted to say so. For a deployed AMM that selects the legacy swap path
on a modern converter at seven call sites; for ERC-165 it silently disables
every interface-gated hook on a compliant implementation.

Do not repair a failure by changing `PROBE_LITERALS` or the read counts. The
literals are deployed constants -- one of them is in a standard -- and the
read counts are the measured bracket.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

# (gas literal, cold reads that fit, cold reads that do not). Both literals
# are deployed constants; both read counts are measured brackets.
PROBE_LITERALS = {
    # a deployed AMM <address withheld>,
    # a deployed AMM.sol:1398-1415, `staticcall(5000, ...)`.
    "ammprobe_isv28orhigher_5000": (5_000, 2, 3),
    # ERC-165 `supportsInterface`: the 30,000 ceiling is in the standard and
    # in its reference caller.
    "erc165_supportsinterface_30000": (30_000, 14, 15),
}


def _answering_target(cold_reads: int) -> Bytecode:
    """
    A target that does `cold_reads` storage reads and then answers "yes".

    Bounded work, not a loop: the point is a target whose cost sits a
    known distance from the literal, so the test locates a cliff rather
    than returning a boolean. Reads use distinct keys so every one is cold.
    """
    body = Op.MSTORE(0, 1)
    for k in range(cold_reads):
        body += Op.POP(Op.SLOAD(k + 1))
    return body + Op.RETURN(0, 32)


# A legacy implementation that does not have the function at all. solc
# <= 0.4.12 compiles `throw` to `INVALID`, which consumes the entire frame
# and is reported by tracers as "Out of gas" -- which is precisely what L5
# observed against the three a deployed AMM contract targets (solc 0.4.21/0.4.23).
LEGACY_HALTING_TARGET = Op.INVALID


def _prober(target: object, literal: int, slot: int) -> Bytecode:
    """
    Derive a deployed AMM's boolean: `success && returned_word != 0`.

    `STATICCALL` is used because that is what both witnesses use, and because
    it guarantees the probed frame cannot have committed anything -- so the
    only thing crossing the boundary is the answer.

    The call must execute before either `MLOAD`: `Op.X(a, b)` emits `b`
    first, so folding the call into the `AND` would read the return buffer
    before the call had filled it. Frame memory starts zeroed, so a failed
    call leaves the buffer at zero and the answer is "no".
    """
    return Op.MSTORE(
        0x20,
        Op.STATICCALL(gas=literal, address=target, ret_offset=0, ret_size=32),
    ) + Op.SSTORE(
        slot, Op.AND(Op.MLOAD(0x20), Op.ISZERO(Op.ISZERO(Op.MLOAD(0))))
    )


@pytest.mark.parametrize(
    "literal,reads_in,reads_out",
    [pytest.param(*v, id=k) for k, v in PROBE_LITERALS.items()],
)
@pytest.mark.valid_from("Berlin")
def test_capability_probe_answers_both_ways_within_its_literal(
    state_test: StateTestFiller,
    pre: Alloc,
    literal: int,
    reads_in: int,
    reads_out: int,
) -> None:
    """
    Test a gas-capped probe derives the right boolean on both sides.

    One prober, one transaction, three targets under the same deployed
    literal, and a fourth marker proving the prober itself survived all
    three answers:

    * a **capable** target whose work fits the literal must answer "yes";
    * a **legacy halting** target (solc `throw` -> `INVALID`, which burns
      the whole forwarded frame) must answer "no" without aborting the
      prober;
    * an **overrunning** target, whose work exceeds the literal by one cold
      read, must also answer "no".

    Asserting the three together is what makes this a *two-sided* test. A
    reprice upward flips the first marker; a reprice downward flips the
    third; and because the prober never reverts, the only observable
    difference is the committed boolean itself, which is exactly what is
    asserted here.
    """
    storage = Storage()
    prober = pre.deploy_contract(
        _prober(
            pre.deploy_contract(_answering_target(reads_in)),
            literal,
            storage.store_next(1, "capable_target_answered_yes"),
        )
        + _prober(
            pre.deploy_contract(LEGACY_HALTING_TARGET),
            literal,
            storage.store_next(0, "halting_target_answered_no"),
        )
        + _prober(
            pre.deploy_contract(_answering_target(reads_out)),
            literal,
            storage.store_next(0, "overrunning_target_answered_no"),
        )
        # Reached only if no probed failure propagated. A capability probe
        # that reverts is a different (and safer) pattern -- the error
        # surfaces -- so the prober's survival is part of the invariant.
        + Op.SSTORE(storage.store_next(1, "prober_survived"), 1)
        + Op.STOP
    )

    tx = Transaction(to=prober, state_gas_reservoir=0, sender=pre.fund_eoa())
    state_test(pre=pre, post={prober: Account(storage=storage)}, tx=tx)
