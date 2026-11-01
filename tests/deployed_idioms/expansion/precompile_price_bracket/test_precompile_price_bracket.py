"""
A frozen gas literal forwarded to a precompile, pinned from **both** sides.

This is class #1's shape (a budget that is a literal in immutable code) on a
rule class #1 never touches, and deliberately sharpened: instead of asserting
only that the deployed literal survives, each precompile's price is bracketed
-- `price` suffices and `price - 1` does not -- so a reprice in **either**
direction fails a slot. That matters here more than anywhere else in the
corpus, because precompiles are the one surface where mainnet repricing has
gone both ways:

```text
PRECOMPILE_ECADD              500 ->    150   EIP-1108, Istanbul   3.3x cheaper
PRECOMPILE_ECMUL           40,000 ->  6,000   EIP-1108             6.7x cheaper
PRECOMPILE_ECPAIRING_BASE 100,000 -> 45,000   EIP-1108
PRECOMPILE_ECPAIRING_PER_POINT
                           80,000 -> 34,000   EIP-1108
MODEXP (32-byte operands)   1,360 ->  4,080   EIP-7883, Osaka      3.0x dearer
```

`INVARIANT-CLASSES.md`'s "repricing DOWNWARD" section records that class #1
is *invisible* to a reduction -- an over-provisioned budget still fits -- and
that `cls12-cold-read-700` is survived by all six budget-sufficiency
archetypes. The lower rail of each bracket here is what makes a reduction
observable: if ECADD became 50 gas, a 149-gas forward would start
succeeding.

Honest placement: the *archetype* is not new. It is the two-sided bracket
that `tests/oog_as_signal/` established, applied to precompile pricing, plus
a fork-split pair of arms for the one precompile whose price actually moved
in range. What is new is the rule and the direction coverage, and that is
stated rather than dressed up as a new class.

## Prior art: the same bracket shape exists officially and is blind, MEASURED

`tests/byzantium/eip196_ec_add_mul/test_gas.py::test_gas_costs` already
implements this exact shape -- `gas = precompile_gas if enough_gas else
precompile_gas - 1`, committing 1 or 0 -- and so does
`tests/byzantium/eip197_ec_pairing/test_gas.py`. But both rails come from
`fork.gas_costs()`:

```python
# tests/byzantium/eip196_ec_add_mul/conftest.py:24-31
gas_costs = fork.gas_costs()
match precompile_address:
    case Spec.ECADD:  return gas_costs.PRECOMPILE_ECADD
    case Spec.ECMUL:  return gas_costs.PRECOMPILE_ECMUL
```

so a reprice moves both rails together -- `docs/COVERAGE-GAP.md`'s
structural argument. **That was tested rather than assumed.** A *real*
reprice was simulated by editing **both** gas tables at once (the spec's
`amsterdam/vm/gas.py` and the test framework's own independent copy at
`execution_testing/forks/forks/eips/istanbul/eip_1108.py:21`), setting
`PRECOMPILE_ECADD` 150 -> 50:

```text
tests/byzantium/eip196_ec_add_mul/test_gas.py     24 passed   <- blind
expansion/.../precompile_price_bracket             3 failed   <- detected
```

That is the first *measured* demonstration of the coverage gap on the
precompile-pricing axis, and it carries a methodological warning the whole
corpus needs:

**A mutation-harness "DETECTED" on a fork-derived official test proves
nothing.** The framework keeps its own gas table, so perturbing only
`src/ethereum/forks/.../gas.py` makes the two disagree, and *every*
fork-derived test goes red for that reason alone. Measured: under the
single-table `exp-pre-ecadd-50`, `tests/byzantium/` reports
`3 failed, 1797 passed` -- and those 3 are exactly the `enough_gas_False`
ecadd params, failing because the framework still forwarded 149 while the
spec charged 50. Under the two-table edit the same 3 pass. Only a literal
frozen in the *test's own source* fails under both.

`tests/osaka/eip7883_modexp_gas_increase/` has the same property, by the same
route: `conftest.py:233-239` picks `Spec` or `Spec7883` from
`fork.is_eip_enabled(7883)` and recomputes the budget, and
`test_modexp_gas_usage_contract_wrapper` brackets it +1 / 0 / -1. The shape
is right; the rails move. L4's "conformance-only" rating of the
`precompile-pricing` axis is therefore correct and now has a measurement
behind it.

## Deployed witnesses, with addresses (CHECKED, Sourcify v2)

**1. A frozen literal equal to the price, with zero margin.**
`<address withheld>`
a deployed Groth16 verifier, `contracts/verifiers/...sol:125`:

```solidity
// ecMul
res_ := staticcall(6000, 7, add(pointer_, 64), 96, add(pointer_, 64), 64)
// check that multiplication succeeded
res_ := and(res_, gt(returndatasize(), 0))
```

6,000 is *exactly* `PRECOMPILE_ECMUL`. There is no headroom at all: the
first gas this precompile ever costs above 6,000 breaks this verifier, and
it reads the failure as "multiplication did not succeed" rather than
surfacing an error.

**2. A frozen literal that writes down the price and the date it was
checked.** a deployed zk protocol a deployed zk verifier, three deployments --
`<address withheld>`,
`<address withheld>`,
`<address withheld>` -- a deployed zk verifier.sol:62-65`:

```solidity
// ecMul gas cost is fixed at 6000. Add 33.3% gas for safety buffer.
// Last checked in 2024 Oct, evm codename Cancun
// ref: https://www.evm.codes/precompiled?fork=cancun#0x07
success := staticcall(8000, 7, mIn, 96, mIn, 64)
```

A deployed contract stating the constant it depends on, the margin it chose,
and the fork it verified against. This corpus exists for exactly that
comment.

**3. Two sibling deployments whose literals bracket EIP-7883.** Both compute
a modular inverse by Fermat's little theorem -- `modexp(value, p - 2, p)`
with `p` the secp256r1 field prime, i.e. 32/32/32 byte lengths and a
256-bit exponent -- under a frozen literal:

```text
<address withheld>  a deployed passkey validation module
    Secp256r1.sol:183     staticcall(1500,  0x5, freemem, 0xc0, freemem, 0x20)
<address withheld>  a sibling fallback handler
    LibSecp256r1.sol:366  staticcall(14000, 0x5, freemem, 0xc0, freemem, 0x20)
```

Both wrap the call in `switch success case 0 { revert(0x0, 0x0) }`, so a
budget that stops fitting is a hard revert, not a silent wrong answer.

## The measured result: a live deployed break

Bracketed with `expansion/tests/tools/test_precompile_price_probe.py`, six
forks, six ascending budgets per shape, every answer packed into one word
(CHECKED):

```text
shape                        Berlin..Prague        Osaka, Amsterdam
ECADD, 128 zero bytes        exactly 150           exactly 150
ECMUL, 96 zero bytes         exactly 6,000         exactly 6,000
ECPAIRING, 0 pairs           exactly 45,000        exactly 45,000
ECPAIRING, 1 pair            exactly 79,000        exactly 79,000
MODEXP, 32/32/32, exp=p-2    exactly 1,360         exactly 4,080
MODEXP, base 1024            exactly 5,461         exactly 32,768
MODEXP, exponent 1024        exactly 2,645         exactly 253,952
P256VERIFY, empty input      n/a (empty account)   exactly 6,900
```

Why these are direct measurements and not subtractions: all-zero inputs are
the point at infinity for G1 and G2 and the scalar 0, `py_ecc` returns
`FQ12.one()` for a pairing involving infinity, and a precompile frame runs
no code -- so the precompile's own charge is the frame's *entire* cost and
`forwarded >= cost` is exactly `success`.

The bn128 prices are **identical on all six forks** -- EIP-1108 landed at
Istanbul, before this range -- so a single fork-free test pins them, by the
same argument `oog_as_signal` uses for `COLD_STORAGE_ACCESS`. The pairing
pair separates the two constants: 45,000 is `ECPAIRING_BASE` alone and
79,000 - 45,000 = 34,000 is `ECPAIRING_PER_POINT`, so a mutation to either
is attributable.

And the modexp row locates a break in deployed code:

```text
budget   Berlin..Prague   Osaka, Amsterdam   deployed at
 1,359   fails            fails              --
 1,360   SUCCEEDS         fails              --
 1,500   SUCCEEDS         FAILS              a deployed passkey validation module
 4,079   succeeds         fails              --
 4,080   succeeds         SUCCEEDS           --
14,000   succeeds         succeeds           a sibling fallback handler
```

**a deployed passkey validation module `staticcall(1500, 0x5, ...)` succeeds on
Berlin through Prague and fails from Osaka.** The derivation agrees to the
gas: 32-byte operands give `complexity = 16` and a 256-bit exponent gives
`iterations = 255`, so the cost is `16 x 255 = 4,080`; before EIP-7883 the
same product was divided by `GQUADDIVISOR = 3`, giving 1,360. The literal
1,500 sat 140 gas above the old cost and sits 2,580 below the new one. Its
sibling at 14,000 keeps 3.43x headroom, so the two deployed literals bracket
the change -- the only such pair found on this surface.

Consequence: `primemod` reverts, so passkey (WebAuthn) signature
verification in that module cannot complete. A liveness failure, loud rather
than silent, in an immutable module.

## What a failure means

A deployed frozen budget no longer matches what the precompile charges.
A failing *upper* rail (`..._suffices`) means the price rose and the deployed
contract now reverts or reads "operation failed"; a failing *lower* rail
(`..._does_not_suffice`) means the price fell, which breaks the opposite
population -- probes that read failure as a negative answer (class #12) now
read success.

Do not repair a failure by adjusting a budget: the deployed literals come
from the contracts named above, and the +/-1 rails are the measured price.
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

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-7883.md"
REFERENCE_SPEC_VERSION = "13aa65810336d4f243d4563a828d5afe36035d23"

ECADD = 0x06
ECMUL = 0x07
ECPAIRING = 0x08
MODEXP = 0x05
P256VERIFY = 0x100

# secp256r1 field prime and p-2: the exponent both deployed `primemod`
# wrappers pass, by Fermat's little theorem.
P256_P = 0xFFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF
P256_P_MINUS_2 = P256_P - 2

# Deployed frozen literals, each with its contract. Not ours to change.
ECMUL_GROTH16_EXACT = 6_000  # a deployed Groth16 verifier, zero margin
ECMUL_ZKVERIFIER = 8_000  # a deployed zk verifier, "33.3% safety buffer"
MODEXP_AAMODULE = 1_500  # a deployed passkey validation module
MODEXP_FALLBACK_HANDLER = 14_000  # a sibling fallback handler

# Measured prices (CHECKED; see the module docstring's table).
PRICE_ECADD = 150
PRICE_ECMUL = 6_000
PRICE_ECPAIRING_BASE = 45_000
PRICE_ECPAIRING_ONE_PAIR = 79_000
PRICE_MODEXP_INVERSE_BEFORE_7883 = 1_360
PRICE_MODEXP_INVERSE_FROM_7883 = 4_080
PRICE_P256VERIFY = 6_900

# Large-operand shapes, which reach coefficients the 32-byte inverse cannot:
#   base 1024 / exp 0 / mod 1  -> the `complexity` word term
#       before 7883: words**2 // 3 = 128**2 // 3        = 5,461
#       from   7883: 2 * words**2  = 2 * 128**2         = 32,768
#   base 1 / exp 1024 / mod 1  -> the `iterations` length term
#       before 7883: 1 * (8 * (1024-32)) // 3           = 2,645
#       from   7883: 16 * (16 * (1024-32))              = 253,952
PRICE_MODEXP_BASE_1024_BEFORE_7883 = 5_461
PRICE_MODEXP_BASE_1024_FROM_7883 = 32_768
PRICE_MODEXP_EXP_1024_BEFORE_7883 = 2_645
PRICE_MODEXP_EXP_1024_FROM_7883 = 253_952

# All-zero inputs: the point at infinity for G1 and G2, and the scalar 0.
# `py_ecc` returns `FQ12.one()` for a pairing involving infinity, so each
# call is a valid, successful, minimal-work invocation whose entire cost is
# the precompile's own charge -- which is what makes the bracket a direct
# measurement rather than a subtraction.
LEN_ECADD = 128
LEN_ECMUL = 96
LEN_ECPAIRING_ONE_PAIR = 192


def _call(
    addr: int,
    in_len: int,
    budget: int,
    storage: Storage,
    label: str,
    expect: int,
) -> Bytecode:
    """Forward exactly `budget` to `addr` and commit the success bit."""
    return Op.MSTORE(
        0x3000,
        Op.STATICCALL(
            gas=budget,
            address=Address(addr),
            args_offset=0,
            args_size=in_len,
            ret_offset=0x4000,
            ret_size=0,
        ),
    ) + Op.SSTORE(storage.store_next(expect, label), Op.MLOAD(0x3000))


def _bracket(
    addr: int, in_len: int, price: int, storage: Storage, name: str
) -> Bytecode:
    """`price` suffices and `price - 1` does not: the two-sided rail pair."""
    return _call(
        addr, in_len, price, storage, f"{name}_at_{price}_suffices", 1
    ) + _call(
        addr,
        in_len,
        price - 1,
        storage,
        f"{name}_at_{price - 1}_does_not_suffice",
        0,
    )


def _modexp_inverse_input() -> Bytecode:
    """
    The exact memory image both deployed `primemod` wrappers build.

    Three 32-byte lengths, then base = 1, exponent = p-2, modulus = p --
    `modexp(value, p - 2, p)`, with a 256-bit exponent so `iterations` is
    255 rather than the degenerate 1 a zero exponent would give.
    """
    return (
        Op.MSTORE(0, 32)
        + Op.MSTORE(32, 32)
        + Op.MSTORE(64, 32)
        + Op.MSTORE(96, 1)
        + Op.MSTORE(128, P256_P_MINUS_2)
        + Op.MSTORE(160, P256_P)
    )


MODEXP_INPUT_LEN = 192


def _modexp_lengths(bl: int, el: int, ml: int) -> Bytecode:
    """Declare three modexp operand lengths; the payload stays zero."""
    return Op.MSTORE(0, bl) + Op.MSTORE(32, el) + Op.MSTORE(64, ml)


@pytest.mark.valid_from("Berlin")
def test_bn128_prices_are_pinned_from_both_sides(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Test every alt_bn128 price is bracketed, and the deployed literals fit.

    Four brackets, eight rails, and two deployed ECMUL literals. The upper
    rails detect a reprice upward (the direction class #1 already covers);
    the lower rails detect a reprice downward (the direction
    `INVARIANT-CLASSES.md` records as a blind spot, and the direction
    EIP-1108 actually took on these four constants).

    The pairing pair is the reason this is four brackets and not three:
    `ECPAIRING_BASE` is isolated by a zero-pair call, and
    `ECPAIRING_PER_POINT` only appears as the 34,000 difference between the
    zero-pair and one-pair rails, so a mutation to either is attributable
    from the failure signature alone.
    """
    storage = Storage()
    code = (
        _bracket(ECADD, LEN_ECADD, PRICE_ECADD, storage, "ecadd")
        + _bracket(ECMUL, LEN_ECMUL, PRICE_ECMUL, storage, "ecmul")
        + _bracket(
            ECPAIRING, 0, PRICE_ECPAIRING_BASE, storage, "ecpairing_base"
        )
        + _bracket(
            ECPAIRING,
            LEN_ECPAIRING_ONE_PAIR,
            PRICE_ECPAIRING_ONE_PAIR,
            storage,
            "ecpairing_one_pair",
        )
        # The deployed literals, both on ECMUL.
        + _call(
            ECMUL,
            LEN_ECMUL,
            ECMUL_GROTH16_EXACT,
            storage,
            "groth16_verifier_6000_zero_margin",
            1,
        )
        + _call(
            ECMUL,
            LEN_ECMUL,
            ECMUL_ZKVERIFIER,
            storage,
            "zkverifier_verifier_8000",
            1,
        )
        + Op.SSTORE(storage.store_next(1, "caller_survived"), 1)
        + Op.STOP
    )
    caller = pre.deploy_contract(code)
    tx = Transaction(
        to=caller,
        gas_limit=2_000_000,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
    )
    state_test(pre=pre, post={caller: Account(storage=storage)}, tx=tx)


@pytest.mark.valid_from("Berlin")
@pytest.mark.valid_until("Prague")
def test_modexp_inverse_budget_before_eip7883(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Test the p-2 modular inverse costs exactly 1,360, and 1,500 fits.

    The invariant arm. `complexity = words**2 = 16`, `iterations = 255`,
    `cost = 16 * 255 // GQUADDIVISOR(3) = 1,360`. a deployed account-abstraction stack's frozen 1,500
    clears it by 140 gas -- which is why the module worked for five forks
    and why nobody noticed how tight it was.
    """
    storage = Storage()
    caller = pre.deploy_contract(
        _modexp_inverse_input()
        + _bracket(
            MODEXP,
            MODEXP_INPUT_LEN,
            PRICE_MODEXP_INVERSE_BEFORE_7883,
            storage,
            "modexp_inverse",
        )
        + _call(
            MODEXP,
            MODEXP_INPUT_LEN,
            MODEXP_AAMODULE,
            storage,
            "aamodule_passkey_1500_still_fits",
            1,
        )
        + _call(
            MODEXP,
            MODEXP_INPUT_LEN,
            MODEXP_FALLBACK_HANDLER,
            storage,
            "fallback_handler_14000_fits",
            1,
        )
        + Op.SSTORE(storage.store_next(1, "caller_survived"), 1)
        + Op.STOP
    )
    tx = Transaction(
        to=caller,
        gas_limit=1_000_000,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
    )
    state_test(pre=pre, post={caller: Account(storage=storage)}, tx=tx)


@pytest.mark.valid_from("Osaka")
def test_modexp_inverse_budget_from_eip7883(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Test the same inverse costs exactly 4,080, and 1,500 no longer fits.

    The violation arm, same deployed bytes. EIP-7883 removed
    `GQUADDIVISOR`, so `16 * 255` is charged in full: 3.0x dearer, to the
    gas. `aamodule_passkey_1500_no_longer_fits` is the slot that states the
    break, and `fallback_handler_14000_still_fits` is the control that keeps
    it from being read as "modexp got expensive for everyone".
    """
    storage = Storage()
    caller = pre.deploy_contract(
        _modexp_inverse_input()
        + _bracket(
            MODEXP,
            MODEXP_INPUT_LEN,
            PRICE_MODEXP_INVERSE_FROM_7883,
            storage,
            "modexp_inverse",
        )
        + _call(
            MODEXP,
            MODEXP_INPUT_LEN,
            MODEXP_AAMODULE,
            storage,
            "aamodule_passkey_1500_no_longer_fits",
            0,
        )
        + _call(
            MODEXP,
            MODEXP_INPUT_LEN,
            MODEXP_FALLBACK_HANDLER,
            storage,
            "fallback_handler_14000_still_fits",
            1,
        )
        + Op.SSTORE(storage.store_next(1, "caller_survived"), 1)
        + Op.STOP
    )
    tx = Transaction(
        to=caller,
        gas_limit=1_000_000,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
    )
    state_test(pre=pre, post={caller: Account(storage=storage)}, tx=tx)


@pytest.mark.valid_from("Berlin")
@pytest.mark.valid_until("Prague")
def test_modexp_large_operand_prices_before_eip7883(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Test the two large-operand modexp coefficients, before EIP-7883.

    The 32-byte inverse above cannot reach either: with `max_length <= 32`
    the word term is a flat constant, and with a 32-byte exponent the
    length term is never evaluated. So two further brackets are needed, one
    per coefficient, or a change to `words**2` or to `8 * (exp_len - 32)`
    would pass unnoticed. Pre-EIP-2565 arithmetic is `// GQUADDIVISOR(3)`.
    """
    storage = Storage()
    caller = pre.deploy_contract(
        _modexp_lengths(1024, 0, 1)
        + _bracket(
            MODEXP,
            96 + 1024 + 0 + 1,
            PRICE_MODEXP_BASE_1024_BEFORE_7883,
            storage,
            "modexp_base_1024",
        )
        + _modexp_lengths(1, 1024, 1)
        + _bracket(
            MODEXP,
            96 + 1 + 1024 + 1,
            PRICE_MODEXP_EXP_1024_BEFORE_7883,
            storage,
            "modexp_exponent_1024",
        )
        + Op.SSTORE(storage.store_next(1, "caller_survived"), 1)
        + Op.STOP
    )
    tx = Transaction(
        to=caller,
        gas_limit=1_000_000,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
    )
    state_test(pre=pre, post={caller: Account(storage=storage)}, tx=tx)


@pytest.mark.valid_from("Osaka")
def test_modexp_large_operand_prices_from_eip7883(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Test the two large-operand modexp coefficients, from EIP-7883.

    Same two brackets on the far side of the fork. The pair of arms measures
    how differently EIP-7883 treated the two terms: the word term went
    `words**2 // 3 -> 2 * words**2`, a 6.0x rise, while the exponent length
    term went `8 * (n-32) // 3 -> 16 * (n-32)` *and* picked up the flat
    `complexity = 16` for small moduli, a **96x** rise (2,645 -> 253,952).
    A contract sized against the old exponent term is therefore far more
    exposed than one sized against the old word term, which only a
    per-coefficient bracket can show.
    """
    storage = Storage()
    caller = pre.deploy_contract(
        _modexp_lengths(1024, 0, 1)
        + _bracket(
            MODEXP,
            96 + 1024 + 0 + 1,
            PRICE_MODEXP_BASE_1024_FROM_7883,
            storage,
            "modexp_base_1024",
        )
        + _modexp_lengths(1, 1024, 1)
        + _bracket(
            MODEXP,
            96 + 1 + 1024 + 1,
            PRICE_MODEXP_EXP_1024_FROM_7883,
            storage,
            "modexp_exponent_1024",
        )
        + Op.SSTORE(storage.store_next(1, "caller_survived"), 1)
        + Op.STOP
    )
    tx = Transaction(
        to=caller,
        gas_limit=2_000_000,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
    )
    state_test(pre=pre, post={caller: Account(storage=storage)}, tx=tx)


@pytest.mark.valid_from("Osaka")
def test_p256verify_price_is_pinned_from_both_sides(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Test `P256VERIFY` costs exactly 6,900 from the fork that introduced it.

    `p256verify` charges unconditionally and *then* validates
    (`p256verify.py:44-47`), so an empty input still pays the full price --
    which makes this the cleanest possible bracket and also the reason the
    presence probe in `unassigned_precompile_identity/` has a gas signature
    at all. Pinned from Osaka because a brand-new precompile's price is the
    one most likely to be adjusted in its first few forks, and nothing in
    the corpus asserts it.
    """
    storage = Storage()
    caller = pre.deploy_contract(
        _bracket(P256VERIFY, 0, PRICE_P256VERIFY, storage, "p256verify")
        + Op.SSTORE(storage.store_next(1, "caller_survived"), 1)
        + Op.STOP
    )
    tx = Transaction(
        to=caller,
        gas_limit=1_000_000,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
    )
    state_test(pre=pre, post={caller: Account(storage=storage)}, tx=tx)
