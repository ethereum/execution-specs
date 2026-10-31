"""
Candidate class: **precompile input admissibility** -- the accepted input
*domain* of a precompile, as distinct from its price.

A contract passes a precompile an input whose size is derived from runtime
values. The invariant it relies on is not "the call is affordable" but "this
input is *admissible*". EIP-7823 (Osaka) added upper bounds to `MODEXP`:
a base, exponent or modulus declared longer than 1,024 bytes is now
**rejected**, where before it was computed. The rejection happens *before*
`charge_gas` (`osaka/vm/precompiled_contracts/modexp.py:32-41`), so it is an
exceptional halt: `CALL` returns 0 and the entire forwarded budget is burned,
and the caller cannot tell it apart from an out-of-gas.

```python
base_length = U256.from_be_bytes(buffer_read(data, U256(0), U256(32)))
if base_length > U256(1024):
    raise ExceptionalHalt("Mod-exp base length is too large")
```

## Why this is a different class, and the test that proves it

Every budget class in the catalogue -- #1 frozen budget, #12 two-sided OOG
probe, #18 dynamic-cost prediction -- asks "can the caller afford it?" and
is therefore satisfiable by raising the budget. **This one is not.**
`test_oversized_modexp_is_unaffordable_at_any_price` forwards 2,000,000 gas,
about 360x the pre-Osaka cost of the very same call, and the call still
fails. No price exists at which an inadmissible input succeeds, so no
affordability test can express this invariant and no affordability fix can
repair a contract that hits it.

It is also distinct from #18 in the direction of the dependence: #18's
contracts *size* an operation to fit a budget, so the hazard is a changed
coefficient. Here the size is dictated by the data (an RSA modulus, a VDF
accumulator) and the hazard is a changed *admissible set* -- a cliff, not a
slope.

## The witness, stated honestly

**CHECKED:** six mainnet-verified `BigNumber`/`BigNumbers` sources pass
`MODEXP` operands whose byte length comes from runtime values and impose
**no upper bound of their own**. The only length `require`s in them are
32-byte alignment (`require(val.length % 32 == 0)`) and a lower bound
(`require(_size >= _byteLength, "Number too large to represent")`).
Measured population (Sourcify v2, distinct mainnet addresses whose verified
compilation contains such a source): **6 files / 52 addresses / 48
runtimes**. Exemplars, each hand-read:

```text
<address withheld>  ForexToken          (BigNumbers)
<address withheld>  Lottery      BigNumbers.sol
<address withheld>  PolicyProposals  VDF/BigNumber
<address withheld>  VDFVerifier      VDF/BigNumber
<address withheld>  FactoringChallenge  BigNumber.sol
<address withheld>  FactoringChallenge  BigNumber.sol
```

These libraries multiply via `(a*b) = ((a+b)**2 - (a-b)**2) / 4`, and the
modulus for each squaring comes from
`_powModulus(a, e)`, which sets `mod_index := a.bitlen * e` -- so the
operand length **doubles with every multiplication, with no cap**. From a
512-byte operand one multiplication reaches 1,024 bytes (exactly the new
bound) and a second reaches 2,048 (rejected from Osaka).

**INFERRED, not measured:** that a specific deployed call has in fact passed
more than 1,024 bytes. I have no transaction-level evidence for that and do
not claim it. What is CHECKED is that nothing in these contracts prevents
it, which is the property a regression test can defend.

## Prior art: thorough, and most of this surface is already covered

A first pass claimed the official suite "never states the pre-Osaka half".
**That is wrong and the correction is kept here rather than dropped.**
`tests/osaka/eip7823_modexp_upper_bounds/` (357 + 96 + 228 lines) covers:

```text
test_modexp_upper_bounds              valid_from("Osaka")
  all three fields at 1,024 accepted  (base/exp/mod/base+mod "boundary")
  all three fields at 1,025 rejected  ("excess_length_{base,exponent,modulus}")
  plus exp=1025 with 0/1024/1025-byte bases, 0xff exponents, ...
test_modexp_upper_bounds_fork_transition
                                      valid_at_transition_to("Osaka")
  blockchain_test at timestamps 14,999 / 15,000 / 15,001 with
  expected_results = [True, False, False] -- so the pre-fork SUCCESS of a
  1,025-byte base IS asserted, for the base field, at one boundary
test_eip_mainnet                      valid_at("Osaka"), mainnet
```

So the bound is well covered and most of what this archetype asserts is
**not new**. The honest residue, in order of value:

1. **`test_oversized_modexp_is_unaffordable_at_any_price` is new, and it is
   the assertion that defines the class.** Every official test derives
   `precompile_gas` from the fork and runs under `gas_limit=6_000_000`; none
   demonstrates that *no* budget suffices. Without that assertion,
   "inadmissible" is indistinguishable from "expensive", and the class
   collapses into #1/#12/#18.
2. **Per-field before-fork coverage across the whole pre-Osaka window.** The
   official before-fork assertion is one vector (base only) at one
   transition. These arms cover base, exponent *and* modulus on every fork
   Berlin..Prague, as `state_test`s rather than a transition
   `blockchain_test` -- a different fixture shape that clients consume
   differently.
3. **The 1,024-accepted side pinned from Berlin** rather than from Osaka.
   Thin: before Osaka there is no bound to lower, so this only matters to a
   fork that introduced a bound earlier than EIP-7823 did. Recorded as thin
   rather than presented as a gap.

The *class* is still worth recording in `INVARIANT-CLASSES.md`: an
admissible-set change is a different kind of rule from a price, and the
catalogue has no entry for it. But the test surface was largely built
already, and saying so is the result.

## Measured (CHECKED), `expansion/tests/tools/test_precompile_address_probe.py`

`success` / `returndatasize` / caller-frame gas delta, 2,000,000 forwarded:

```text
shape (base/exp/mod bytes)   Berlin..Prague        Osaka, Amsterdam
1024 /    0 /    1           1 / 1    /   6,488    1 / 1    /    33,795
1025 /    0 /    1           1 / 1    /   6,574    0 / 0    / 2,001,027
   1 /    0 / 1024           1 / 1024 /   6,488    1 / 1024 /    33,795
   1 /    0 / 1025           1 / 1025 /   6,574    0 / 0    / 2,001,027
   1 / 1024 /    1           1 / 1    /   3,672    1 / 1    /   254,979
   1 / 1025 /    1           1 / 1    /   3,675    0 / 0    / 2,001,027
```

Three facts this nails down:

1. **The bound is per field, and all three fields moved together.** 1,024 is
   accepted and 1,025 rejected for base, exponent *and* modulus.
2. **No gas rule caused it.** Pre-Osaka the rejected `1025/0/1` shape costs
   **5,547** gas: 6,574 minus 1,027 of probe overhead (warm account access,
   memory expansion to the probe's scratch area, and the probe's own
   opcodes), and that 1,027 comes out **identical in all six rows above**,
   which is what makes the subtraction trustworthy. The shape was never
   expensive; it is now simply not allowed. The precompile prices
   themselves are pinned directly, without any subtraction, in
   `precompile_price_bracket/`.
3. **The whole forwarded budget is burned.** 2,001,027 against 2,000,000
   forwarded: an exceptional halt, so a caller with a frozen budget loses
   all of it and reads the result as an out-of-gas.

## What a failure means

A contract passed the precompile an input size the chain no longer accepts
(or newly accepts). On the `..._before_eip7823` arm, a `BigNumbers`
multiplication chain that completed now reverts or returns garbage; on the
`..._from_eip7823` arm, an input the chain must reject was computed instead.
Neither is a pricing problem and neither can be fixed by sending more gas.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytecode,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-7823.md"
REFERENCE_SPEC_VERSION = "c8321494fdfbfda52ad46c3515a7ca5dc86b857c"

MODEXP = 0x05

# EIP-7823's bound, as a deployed-facing constant pair. The bound itself is
# the invariant, so these two literals are the test (SCHEMA.md 4.1's
# exception for "the number IS the invariant").
PERMITTED = 1024
OVERSIZED = 1025

# Comfortably above every measured cost in range: the largest shape here
# costs 253,952 at Osaka.
AMPLE = 400_000

# ~360x the pre-Osaka cost of the rejected call. Used to show that the
# rejection is not an affordability failure.
EXTRAVAGANT = 2_000_000

# (base_length, exponent_length, modulus_length) with one field at the
# tested size and the others minimal, so each field's bound is separable.
FIELDS = ("base", "exponent", "modulus")


def _lengths(field: str, size: int) -> tuple:
    """Put `size` in one length field and 1 (or 0) in the others."""
    if field == "base":
        return (size, 0, 1)
    if field == "exponent":
        return (1, size, 1)
    return (1, 0, size)


def _modexp(
    bl: int,
    el: int,
    ml: int,
    budget: int,
    storage: Storage,
    label: str,
    expect: int,
) -> Bytecode:
    """
    Declare the three lengths in memory and call `MODEXP` under `budget`.

    Memory beyond the three length words is never written, so base,
    exponent and modulus are all zero. A zero modulus makes the precompile
    return `modulus_length` zero bytes, which keeps the arithmetic trivial
    while the *declared lengths* -- the only thing EIP-7823 inspects -- are
    exactly as written. Commits `success | returndatasize << 1`, so one
    labelled slot carries both channels.
    """
    return (
        Op.MSTORE(0, bl)
        + Op.MSTORE(32, el)
        + Op.MSTORE(64, ml)
        + Op.MSTORE(
            0x3000,
            Op.STATICCALL(
                gas=budget,
                address=Address(MODEXP),
                args_offset=0,
                args_size=96 + bl + el + ml,
                ret_offset=0x4000,
                ret_size=0,
            ),
        )
        + Op.SSTORE(
            storage.store_next(expect, label),
            Op.ADD(Op.MLOAD(0x3000), Op.SHL(1, Op.RETURNDATASIZE)),
        )
    )


def _accepted(bl: int, el: int, ml: int) -> int:
    """`success | returndatasize << 1` for an accepted call."""
    # modexp returns `modulus_length` bytes; with `modulus == 0` they are
    # all zero, but the length is what we observe.
    return 1 + (ml << 1)


@pytest.mark.valid_from("Berlin")
def test_modexp_accepts_the_largest_permitted_operands(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Test 1,024-byte base, exponent and modulus are admissible on every fork.

    The lower side of the bracket, and the half that must hold *forever*:
    EIP-7823 chose 1,024 precisely so that existing RSA-8192 and
    BLS-style callers keep working. Pinned from Berlin rather than from
    Osaka so that a future fork lowering the bound fails here, which the
    official `valid_from("Osaka")` suite cannot see.
    """
    storage = Storage()
    code = Bytecode()
    for field in FIELDS:
        bl, el, ml = _lengths(field, PERMITTED)
        code += _modexp(
            bl,
            el,
            ml,
            AMPLE,
            storage,
            f"{field}_at_1024_is_admissible",
            _accepted(bl, el, ml),
        )
    code += Op.SSTORE(storage.store_next(1, "caller_survived"), 1) + Op.STOP

    caller = pre.deploy_contract(code)
    tx = Transaction(
        to=caller,
        gas_limit=8_000_000,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
    )
    state_test(pre=pre, post={caller: Account(storage=storage)}, tx=tx)


@pytest.mark.valid_from("Berlin")
@pytest.mark.valid_until("Prague")
def test_modexp_accepts_oversized_operands_before_eip7823(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Test 1,025-byte operands are admissible before Osaka.

    The invariant arm: for the five forks before EIP-7823 there was no upper
    bound at all, and a `BigNumbers` multiplication chain that walked past
    1,024 bytes simply paid more gas. This arm would fail if run on Osaka,
    and that is correct -- it is the statement of what EIP-7823 changed.
    """
    storage = Storage()
    code = Bytecode()
    for field in FIELDS:
        bl, el, ml = _lengths(field, OVERSIZED)
        code += _modexp(
            bl,
            el,
            ml,
            AMPLE,
            storage,
            f"{field}_at_1025_was_admissible",
            _accepted(bl, el, ml),
        )
    code += Op.SSTORE(storage.store_next(1, "caller_survived"), 1) + Op.STOP

    caller = pre.deploy_contract(code)
    tx = Transaction(
        to=caller,
        gas_limit=8_000_000,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
    )
    state_test(pre=pre, post={caller: Account(storage=storage)}, tx=tx)


@pytest.mark.valid_from("Osaka")
def test_modexp_rejects_oversized_operands_from_eip7823(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Test 1,025-byte operands are inadmissible from Osaka, on all three fields.

    The violation arm. Each field is tested separately, so the failure
    signature says *which* bound moved rather than only that one did: a
    mutation touching only the base check leaves the other two slots green.
    `caller_survived` matters because the rejection is an exceptional halt
    in the *child*, which must not propagate -- the caller reads a 0 and
    carries on, which is precisely why the break is quiet.
    """
    storage = Storage()
    code = Bytecode()
    for field in FIELDS:
        bl, el, ml = _lengths(field, OVERSIZED)
        code += _modexp(
            bl, el, ml, AMPLE, storage, f"{field}_at_1025_is_rejected", 0
        )
    code += Op.SSTORE(storage.store_next(1, "caller_survived"), 1) + Op.STOP

    caller = pre.deploy_contract(code)
    tx = Transaction(
        to=caller,
        gas_limit=8_000_000,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
    )
    state_test(pre=pre, post={caller: Account(storage=storage)}, tx=tx)


@pytest.mark.valid_from("Osaka")
def test_oversized_modexp_is_unaffordable_at_any_price(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Test the rejection is a domain rule and not a price.

    The same `1025/0/1` call that cost **5,547** gas before Osaka is
    forwarded 2,000,000 here -- 360x -- and still fails, while its
    `1024/0/1` neighbour succeeds on the same budget. This is the assertion
    that separates this class from every affordability class in the
    catalogue: no budget satisfies an inadmissible input, so a frozen-budget
    or two-sided-bracket test cannot express the invariant and raising a
    deployed contract's gas cap cannot repair it.
    """
    storage = Storage()
    caller = pre.deploy_contract(
        _modexp(
            PERMITTED,
            0,
            1,
            EXTRAVAGANT,
            storage,
            "base_at_1024_succeeds_on_the_same_budget",
            _accepted(PERMITTED, 0, 1),
        )
        + _modexp(
            OVERSIZED,
            0,
            1,
            EXTRAVAGANT,
            storage,
            "base_at_1025_fails_on_360x_its_old_cost",
            0,
        )
        + Op.SSTORE(storage.store_next(1, "caller_survived"), 1)
        + Op.STOP
    )
    tx = Transaction(
        to=caller,
        gas_limit=8_000_000,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
    )
    state_test(pre=pre, post={caller: Account(storage=storage)}, tx=tx)
