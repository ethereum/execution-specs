"""
Candidate class: **precompile-address assignment semantics.**

An address that holds neither code nor a precompile answers a `CALL` the way
every empty account does: the call **succeeds** (pushes 1) and leaves
**zero-length return data**. Deployed code uses exactly that to decide
whether a precompile exists yet, because *nothing else can tell*:
`EXTCODESIZE`, `EXTCODEHASH` and `BALANCE` report `0`, `0` and `0` for a
live precompile and for a never-assigned address alike (measured below, all
six forks). Assigning a precompile to that address changes the answer while
**moving no gas rule at all**.

## The deployed witness, which documents the hazard in its own source

a widely used contract library `utils/cryptography/P256.sol` (`_tryVerifyNative` /
`_rip7212`). Verified mainnet addresses carrying it, from the Sourcify v2
export (CHECKED, see README for the queries): **35 source files / 78
addresses / 62 runtimes** for `_tryVerifyNative`, and **58 / 176 / 155** for
the `0x...0100` address literal in any spelling. Exemplars:
`<address withheld>` (that library P256.sol as deployed),
`<address withheld>` `ChipAccount`,
`<address withheld>` MetaMask `HybridDeleGator`
(`P256SCLVerifierLib`), `<address withheld>`
`WebAuthnValidator`, `<address withheld>` (a widely used assembly library
`P256.sol`).

The library's own comments state the invariant and the reason it has to be
probed behaviourally:

```solidity
// Given precompiles have no bytecode (i.e. `address(0x100).code.length == 0`),
// we use a valid signature with small `r` and `s` values to check if the
// precompile is present.
...
// RIP-7212 precompiles return empty bytes when an invalid signature is passed,
// making it impossible to distinguish the presence of the precompile.
mstore(0x00, 0) // zero scratch, in case the precompile returns nothing
if iszero(staticcall(gas(), 0x100, ptr, 0xa0, 0x00, 0x20)) { invalid() }
isValid := mload(0x00)
```

Two separate invariants are load-bearing there:

1. **the call must succeed.** `if iszero(staticcall(...)) { invalid() }` — if
   a call to an unassigned address ever returned 0, that library's `P256.verify` would
   execute `INVALID` and burn the caller's entire frame instead of falling
   back to `verifySolidity`.
2. **empty return data must mean "absent".** The probe's `isValid` is read
   out of a pre-zeroed scratch word, so "no return data" and "returned
   `false`" are the same observation.

And `verifyNative` turns the same probe into a hard
`revert Errors.MissingPrecompile(address(0x100))`, so a contract on that
path goes from always-reverting to working at the assignment fork.

## Why this is not an existing class

* **#22 code-presence identity** uses `EXTCODESIZE`/`EXTCODEHASH`, and those
  are **structurally blind** here: measured `0` for `0x05` (a precompile
  since Byzantium), for `0x100`, and for `0x12`, on every fork
  Berlin..Amsterdam. `test_code_inspection_cannot_distinguish_a_precompile`
  pins that blindness, which is *why* a behavioural probe exists at all.
* **#12 two-sided OOG probe** brackets a *gas literal*. Here the literal is
  `gas()` — everything is forwarded — and no price moved. The flip is
  semantic.
* **#27 environment-field semantics** is about what a field *reports*; this
  is about what an *address* is.
* `expansion/tests/undefined_opcode_halt/` is the sibling result in the
  **opcode** space (an undefined byte becoming an instruction). Different
  rule, different mechanism (`InvalidOpcode` halt vs the empty-account call
  convention) and a different observable, so the two do not overlap.

## Prior art: more of this is covered than I first assumed (CHECKED)

A first pass at this archetype claimed "nothing in `tests/` asserts what a
`CALL` to a not-yet-assigned precompile address returns". **That is false**,
and the correction is recorded here rather than quietly dropped. All three
assignment events have an official before-fork test:

```text
tests/cancun/eip4844_blobs/test_point_evaluation_precompile.py:713
    test_precompile_before_fork         valid_at_transition_to("Cancun")
tests/prague/eip2537_bls_12_381_precompiles/
        test_bls12_precompiles_before_fork.py
    pytestmark                         valid_at_transition_to("Prague")
tests/osaka/eip7951_p256verify_precompiles/test_p256verify_before_fork.py
    test_precompile_before_fork         valid_at_transition_to("Osaka")
    docstring: "The call must succeed but the output must be empty."
tests/berlin/eip2929_gas_cost_increases/test_precompile_warming.py
    the warm/cold channel, via BALANCE across a transition
```

So the bare-call channel and the warm/cold channel are both covered, and
neither is rebuilt here. What those tests cannot state, and what this
archetype adds:

1. **The deployed idiom, not the bare call.** They assert `call_succeeds`
   and `expected_output` at the transaction level, using each precompile's
   own vectors. None runs a *presence probe from inside a contract* and
   commits the boolean the contract derives. that library's probe has three features
   that carry the invariant and a bare call does not: the pre-zeroed scratch
   word (so "no data" and "returned false" are the same observation), the
   return buffer aliased onto that word, and the `invalid()` guard that
   makes a failed call destroy the caller's frame.
   `test_lib_p256_probe_*` reproduces all three.
2. **Scope.** Every official before-fork test is
   `valid_at_transition_to(X)` — it exists at exactly one fork boundary. The
   arms here are `valid_from("Berlin")` with `valid_until("Shanghai")` or
   `valid_until("Prague")`: every fork on which the deployed convention
   held. The never-assigned controls run through Amsterdam, so a fork that
   changed empty-account call semantics *without* introducing a precompile
   would be caught here and nowhere else.
3. **Never-assigned addresses as the subject.** `0x12` and `0x200` have no
   scheduled assignment, so asserting them pins the *convention* rather than
   one address's history. (The warming test does reach addresses above the
   highest precompile — but via `BALANCE`, for warmth only.)
4. **The code-inspection blindness, asserted beside the call channel.**
   Nothing official states that `EXTCODESIZE`, `EXTCODEHASH` and `BALANCE`
   are identical for a live precompile and an empty account — and that is
   what forces the behavioural probe to exist, and what makes class #22's
   instrument structurally unable to cover this class.
5. **Three assignment events in one archetype**, which is what reveals that
   they have *different break shapes*. Each official suite tests its own EIP
   in isolation and so cannot state the contrast.

One further structural point: those tests derive their gas from the fork
(`fork.transitions_to().gas_costs().PRECOMPILE_P256VERIFY`,
`gas_map[addr](len(input_data))`), so per `docs/COVERAGE-GAP.md` they cannot
fail under a reprice — the same reason this corpus exists.

## Measured (CHECKED), `expansion/tests/tools/`

`STATICCALL(50_000, addr, 0, 0, 0, 0)`, reported as
success / returndatasize / caller-frame gas delta:

```text
addr    Berlin      London      Cancun      Prague      Osaka       Amsterdam
0x05    1/0/350     1/0/350     1/0/350     1/0/350     1/0/650     1/0/650
0x0a    1/0/2650    1/0/2650    0/0/50150   0/0/50150   0/0/50150   0/0/50150
0x0b    1/0/2650    1/0/2650    1/0/2650    0/0/50150   0/0/50150   0/0/50150
0x100   1/0/2650    1/0/2650    1/0/2650    1/0/2650    1/0/7050    1/0/7050
0x12    1/0/2650    1/0/2650    1/0/2650    1/0/2650    1/0/2650    1/0/3050
0x200   1/0/2650    1/0/2650    1/0/2650    1/0/2650    1/0/2650    1/0/3050
```

Every cell decomposes exactly, which is why these are CHECKED rather than
inferred: 2,650 = `COLD_ACCOUNT_ACCESS` 2,600 + 50 of probe overhead;
3,050 = 3,000 + 50 (EIP-8038 raised the cold charge); 7,050 = warm 100 +
`PRECOMPILE_P256VERIFY` 6,900 + 50; 350/650 = warm 100 + modexp's
`max(200|500, ...)` floor + 50; 50,150 = warm 100 + the whole 50,000
forwarded, burned by an exceptional halt, + 50.

Three assignment events, **three different break shapes**:

* **0x0a at Cancun** and **0x0b at Prague**: the precompile rejects the
  probe's input length *before* charging gas (`point_evaluation` raises
  `KZGProofError` on `len != 192`; `bls12_g1_add` raises `InvalidParameter`
  on `len != 256`), so `CALL` returns **0** and the forwarded budget is
  burned entirely. Under that library's guard this is `invalid()`.
* **0x100 at Osaka**: `p256verify` charges 6,900 and returns *empty* output
  for anything it does not verify, so success stays **1** and
  returndatasize stays **0** for a malformed probe. The boolean channel is
  unchanged; only a *well-formed* probe sees the difference.

that library's own wycheproof vector through that library's own probe (CHECKED):

```text
fork       success  returndatasize  isValid   that library reads
Berlin     1        0               0         absent -> verifySolidity
London     1        0               0         absent
Cancun     1        0               0         absent
Prague     1        0               0         absent
Osaka      1        32              1         present, signature valid
Amsterdam  1        32              1         present
```

So **`success` is 1 on all six forks and only `RETURNDATASIZE` moves.** That
is the sharpest statement available about this surface: call success is not a
channel that distinguishes a precompile from an empty account, and a
contract that treats "the call succeeded" as "the operation was performed"
is wrong on every fork, before and after assignment.

## What a failure means

The probe answered the wrong question about an address. On the
`..._before_assignment` arms: a contract that should take its software
fallback takes the native path, or `invalid()`s and burns the frame. On the
`..._after_assignment` arms: a contract that should use the precompile keeps
running a software implementation, or `verifyNative` keeps reverting.

**Fork-scoping is the point.** The `before` arms are `valid_until(...)` and
would fail if run on a later fork — that is the invariant being pinned, not
staleness. Do not "repair" a failure by widening a fork window.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytecode,
    Conditional,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

# Addresses, and the fork at which each stops being an empty account.
POINT_EVALUATION = 0x0A  # EIP-4844, Cancun
BLS12_G1_ADD = 0x0B  # EIP-2537, Prague
P256VERIFY = 0x100  # EIP-7951, Osaka
MODEXP = 0x05  # EIP-198, Byzantium: a precompile on every fork here
UNASSIGNED_LOW = 0x12  # first address above the EIP-2537 block
UNASSIGNED_HIGH = 0x200  # above every assigned address

# A bounded literal rather than `gas()`, so an exceptional halt in the
# probed frame burns a known amount and the prober survives to commit.
FORWARD = 50_000

# a widely used contract library `utils/cryptography/P256.sol::_tryVerifyNative`
# presence probe -- "a valid signature with small `r` and `s` values", from
# C2SP/wycheproof `ecdsa_secp256r1_sha256_p1363_test.json#L1173-L1204`.
# These five words are the deployed constant; they are not ours to change.
LIB_PROBE = (
    0xBB5A52F42F9C9261ED4361F59422A1E30036E7C32B270C8807A419FECA605023,
    0x0000000000000000000000000000000000000000000000000000000000000005,
    0x0000000000000000000000000000000000000000000000000000000000000001,
    0xA71AF64DE5126A4A4E02B7922D66CE9415CE88A4C9D25514D91082C8725AC957,
    0x5D47723C8FBE580BB369FEC9C2665D8E30A435B9932645482E7C9F11E872296B,
)


def _bare_probe(
    addr: int, storage: Storage, label: str, expect: int
) -> Bytecode:
    """
    Call `addr` with no input and commit `success | returndatasize << 1`.

    An empty account answers 1 (success, zero-length return data). A
    precompile that rejects the input answers 0 and burns the whole
    forwarded literal; one that accepts it answers `1 | n << 1`. Both
    channels land in one labelled slot, so a mutation failure names which
    one moved.
    """
    return Op.MSTORE(
        0xA0,
        Op.STATICCALL(
            gas=FORWARD,
            address=Address(addr),
            args_offset=0,
            args_size=0,
            ret_offset=0,
            ret_size=0,
        ),
    ) + Op.SSTORE(
        storage.store_next(expect, label),
        Op.ADD(Op.MLOAD(0xA0), Op.SHL(1, Op.RETURNDATASIZE)),
    )


def _lib_rip7212(
    storage: Storage, expect_valid: int, expect_rds: int
) -> Bytecode:
    """
    a widely used P256 library transcribed opcode for opcode.

    Faithful in all three details that carry the invariant: the scratch word
    is zeroed first so empty return data reads as `false`; the return buffer
    is the scratch word, not fresh memory; and a failed call executes
    `invalid()`, which burns the frame.
    """
    code = Bytecode()
    for i, word in enumerate(LIB_PROBE):
        code += Op.MSTORE(0x100 + 0x20 * i, word)
    code += Op.MSTORE(0x00, 0)
    code += Op.MSTORE(
        0x200,
        Op.STATICCALL(
            gas=Op.GAS,
            address=Address(P256VERIFY),
            args_offset=0x100,
            args_size=0xA0,
            ret_offset=0x00,
            ret_size=0x20,
        ),
    )
    code += Op.SSTORE(
        storage.store_next(expect_rds, "lib_probe_returndatasize"),
        Op.RETURNDATASIZE,
    )
    code += Op.SSTORE(
        storage.store_next(expect_valid, "lib_probe_is_valid"), Op.MLOAD(0x00)
    )
    # that library: `if iszero(staticcall(...)) { invalid() }`.
    code += Conditional(
        condition=Op.MLOAD(0x200), if_true=Bytecode(), if_false=Op.INVALID
    )
    # Unreachable if the call returned 0, because INVALID discards the frame
    # and with it every SSTORE above.
    code += Op.SSTORE(storage.store_next(1, "lib_guard_not_tripped"), 1)
    return code


@pytest.mark.valid_from("Berlin")
@pytest.mark.valid_until("Shanghai")
def test_unassigned_addresses_answer_like_empty_accounts(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Test every not-yet-assigned precompile address answers (1, 0).

    The window is the one where all three of `0x0a`, `0x0b` and `0x100` are
    still empty accounts, so the arm states the convention a widely used contract library's
    probe is written against, with two never-assigned addresses as controls
    and `0x05` as a positive control for "this really is a precompile".
    """
    storage = Storage()
    code = Bytecode()
    for addr, label in (
        (POINT_EVALUATION, "point_evaluation_0x0a"),
        (BLS12_G1_ADD, "bls_g1add_0x0b"),
        (P256VERIFY, "p256verify_0x100"),
        (UNASSIGNED_LOW, "unassigned_0x12"),
        (UNASSIGNED_HIGH, "unassigned_0x200"),
        # `0x05` is a precompile on every fork in range, and must answer
        # identically for an empty input -- which is exactly why this
        # channel cannot distinguish the two.
        (MODEXP, "live_precompile_0x05_indistinguishable"),
    ):
        code += _bare_probe(
            addr, storage, f"{label}_succeeds_with_no_returndata", 1
        )
    code += Op.SSTORE(storage.store_next(1, "prober_survived"), 1) + Op.STOP

    prober = pre.deploy_contract(code)
    tx = Transaction(to=prober, state_gas_reservoir=0, sender=pre.fund_eoa())
    state_test(pre=pre, post={prober: Account(storage=storage)}, tx=tx)


@pytest.mark.valid_from("Cancun")
def test_point_evaluation_assignment_inverts_the_probe(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Test `0x0a` stops answering like an empty account from Cancun.

    EIP-4844 put `point_evaluation` there, and it raises on any input whose
    length is not 192 **before** charging gas, so the same `STATICCALL` that
    returned 1 on Berlin and London now returns 0 and burns the entire
    forwarded literal. The never-assigned control must still answer 1, so a
    blanket change to call semantics cannot satisfy both slots.
    """
    storage = Storage()
    prober = pre.deploy_contract(
        _bare_probe(
            POINT_EVALUATION, storage, "point_evaluation_0x0a_now_fails", 0
        )
        + _bare_probe(
            UNASSIGNED_HIGH, storage, "control_0x200_still_succeeds", 1
        )
        + Op.SSTORE(storage.store_next(1, "prober_survived"), 1)
        + Op.STOP
    )
    tx = Transaction(to=prober, state_gas_reservoir=0, sender=pre.fund_eoa())
    state_test(pre=pre, post={prober: Account(storage=storage)}, tx=tx)


@pytest.mark.valid_from("Prague")
def test_bls_g1add_assignment_inverts_the_probe(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Test `0x0b` stops answering like an empty account from Prague.

    `0x0b` is the sharpest of the three because it was a *candidate P256
    address*: a widely used assembly library deployed `P256.sol` says "we don't support EIP-7212's
    precompile at 0x0b as it has not been finalized". EIP-2537 then assigned
    it to `bls12_g1_add`, which rejects any input that is not 256 bytes
    before charging gas.
    """
    storage = Storage()
    prober = pre.deploy_contract(
        _bare_probe(BLS12_G1_ADD, storage, "bls_g1add_0x0b_now_fails", 0)
        + _bare_probe(
            UNASSIGNED_LOW, storage, "control_0x12_still_succeeds", 1
        )
        + Op.SSTORE(storage.store_next(1, "prober_survived"), 1)
        + Op.STOP
    )
    tx = Transaction(to=prober, state_gas_reservoir=0, sender=pre.fund_eoa())
    state_test(pre=pre, post={prober: Account(storage=storage)}, tx=tx)


@pytest.mark.valid_from("Berlin")
@pytest.mark.valid_until("Prague")
def test_lib_p256_probe_reads_absent_before_assignment(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Test a widely used contract library's presence probe reads "absent" before Osaka.

    The invariant arm. On every fork before EIP-7951, `0x100` is an empty
    account: the call succeeds (so that library's `invalid()` guard is not tripped),
    returns no data, and the pre-zeroed scratch word still reads `false` --
    which that library interprets as "precompile absent" and routes to
    `verifySolidity`.
    """
    storage = Storage()
    prober = pre.deploy_contract(_lib_rip7212(storage, 0, 0) + Op.STOP)
    tx = Transaction(to=prober, state_gas_reservoir=0, sender=pre.fund_eoa())
    state_test(pre=pre, post={prober: Account(storage=storage)}, tx=tx)


@pytest.mark.valid_from("Osaka")
def test_lib_p256_probe_reads_present_after_assignment(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Test a widely used contract library's presence probe reads "present" from Osaka.

    The violation arm, with the same deployed bytes. `p256verify` accepts
    that library's wycheproof vector and returns 32 bytes of 1, so the scratch word
    reads `true` and that library switches to the native path. `success` is 1 on both
    sides of the fork -- only `RETURNDATASIZE` moves -- so the pair of arms
    is what makes the boundary observable at all.
    """
    storage = Storage()
    prober = pre.deploy_contract(_lib_rip7212(storage, 1, 32) + Op.STOP)
    tx = Transaction(to=prober, state_gas_reservoir=0, sender=pre.fund_eoa())
    state_test(pre=pre, post={prober: Account(storage=storage)}, tx=tx)


@pytest.mark.valid_from("Berlin")
def test_code_inspection_cannot_distinguish_a_precompile(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Test no code-inspection idiom can see a precompile.

    `EXTCODESIZE`, `EXTCODEHASH` and `BALANCE` report the same values for a
    precompile that has existed since Byzantium (`0x05`), an address that
    becomes one at Osaka (`0x100`), and one never assigned (`0x12`). This is
    the reason a widely used contract library probes behaviourally, quoted in its source, and
    it is what makes class #22's instrument structurally unable to cover
    this class. A deployed contract is included as a positive control, so
    the test cannot be satisfied by an `EXTCODESIZE` that simply stopped
    working.
    """
    storage = Storage()
    real_contract = pre.deploy_contract(Op.STOP)
    code = Bytecode()
    for addr, label in (
        (MODEXP, "live_precompile_0x05"),
        (P256VERIFY, "becomes_precompile_at_osaka_0x100"),
        (UNASSIGNED_LOW, "never_assigned_0x12"),
    ):
        code += Op.SSTORE(
            storage.store_next(0, f"{label}_extcodesize"),
            Op.EXTCODESIZE(Address(addr)),
        )
        code += Op.SSTORE(
            storage.store_next(0, f"{label}_extcodehash"),
            Op.EXTCODEHASH(Address(addr)),
        )
        code += Op.SSTORE(
            storage.store_next(0, f"{label}_balance"),
            Op.BALANCE(Address(addr)),
        )
    code += Op.SSTORE(
        storage.store_next(1, "control_real_contract_has_code"),
        Op.EXTCODESIZE(real_contract),
    )
    code += Op.SSTORE(
        storage.store_next(1, "control_real_contract_has_a_codehash"),
        Op.ISZERO(Op.ISZERO(Op.EXTCODEHASH(real_contract))),
    )
    code += Op.STOP

    prober = pre.deploy_contract(code)
    tx = Transaction(to=prober, state_gas_reservoir=0, sender=pre.fund_eoa())
    state_test(pre=pre, post={prober: Account(storage=storage)}, tx=tx)
