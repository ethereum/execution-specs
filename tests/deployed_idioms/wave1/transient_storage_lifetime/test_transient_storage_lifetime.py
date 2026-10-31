"""
Class #24: transient-storage lifetime, and its **state-gas immunity**.

`TSTORE`/`TLOAD` as an in-transaction lock or scratch slot. L2 measured
three shapes of it: a transient reentrancy lock at **2,315 runtimes /
4,528 addresses** (FP 0.0), transient storage written before an external
call at **4,091 / 14,167** (FP 0.0), and a transient slot written and
never cleared at **2,005 / 5,478** (FP 0.125). L5 separately counted
`TSTORE` at 3,938,758 occurrences across 12,603 runtimes in a 10,000-block
window.

The invariant is two-sided and the two halves have very different
coverage:

**(a) lifetime** -- the slot is visible for the whole transaction and
gone at its end; a nested frame sees its caller's write, a reverted
frame's write is discarded, and a successful write survives to the end of
the transaction. **This half is already covered by the official suite**:
`tests/cancun/eip1153_tstore/` is 11 files and 2,698 lines, including
`test_tstore_clear_after_tx`, `test_tstore_rollback_on_callcode_revert`,
`test_tload_calls`, `test_tstore_reentrancy` and 430 lines of execution
contexts. Per SCHEMA's prior-art rule it is **not rebuilt here**; only
the deployed consequence that no official test expresses -- a lock
round-tripping inside a *frozen* budget -- is asserted, in
`test_a_transient_lock_round_trips_inside_a_frozen_budget` and
`test_a_reverted_attempt_does_not_brick_an_unreleased_transient_lock`.

**(b) state-gas immunity** -- transient storage carries **no state gas**,
so it is structurally immune to every state-gas repricing in this
catalogue. `tstore` charges `GasCosts.OPCODE_TSTORE` through `charge_gas`
and never calls `charge_state_gas`
(`amsterdam/vm/instructions/storage.py:189-216`, CHECKED), whereas
`sstore` calls both (`storage.py:156-157`). **Nothing asserted this.**
It is the load-bearing half: a fork that gave transient storage a state
cost would break this entire population at once, silently, and the
official EIP-1153 suite cannot notice because it derives every gas
expectation from the fork -- `Op.TLOAD.gas_cost(fork)`
(`test_basic_tload.py:244`), `bytecode.gas_cost(fork)`
(`test_tstorage.py:212`), `callee_bytecode.gas_cost(fork) - 1`
(`test_tstorage_execution_contexts.py:203`) -- and mentions neither state
gas nor the reservoir anywhere (0 grep hits, CHECKED). That is
`docs/COVERAGE-GAP.md`'s keystone result applied to this class.

Prior art worth citing rather than repeating: a widely used reentrancy guard uses 1/2 rather than 0/1, so its slot never holds zero
and no zero-boundary refund rule touches it. L2 measured that shape --
its `sto.lock12` record, **6,785 runtimes**, FP 0/8 -- and it is used
here as the negative control, because a *persistent* 1/2 lock turns out
to be state-gas immune too, for a completely different reason: `sstore`
charges `StateGasCosts.STORAGE_SET` only inside
`if original_value == 0` (`storage.py:143-146`). A 0/1 lock is **not**
immune, and that is what makes the control informative.

Every number in this file was measured with
`tests/tools/test_cls24_tstore_probe.py`; the tables are in README.md.
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

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-1153.md"
REFERENCE_SPEC_VERSION = "N/A"

# ---------------------------------------------------------------------
# Frozen literals. None of these is derived from the fork; that is the
# property that separates this corpus from the official suite
# (`frozen_budget/README.md` rule 1).
# ---------------------------------------------------------------------

# StateGasCosts.STORAGE_SET == STATE_BYTES_PER_STORAGE_SET(64)
#                            * COST_PER_STATE_BYTE(1530)   gas.py:47-51
ONE_SLOT_STATE_GAS = 97_920
# One single state byte. Used as the immunity threshold: the cheapest
# conceivable state pricing for a 32-byte key and a 32-byte value is at
# least one byte, and the measured transient-write delta is 117.
ONE_STATE_BYTE = 1_530
RESERVOIR_ONE_BYTE_SHORT = ONE_SLOT_STATE_GAS - ONE_STATE_BYTE  # 96,390

# Deployed frozen budgets, from L3's measured per-frame figures
# (HANDOFF.md 3.3): ERC-7579 `postCheck` is exactly 3,229 gas in 96.8% of
# frames; ERC-165 `supportsInterface` exactly 30,000; EIP-4337
# `validatePaymasterUserOp` exactly 50,000 over 610k frames.
ERC7579_POSTCHECK = 3_229
ERC165_SUPPORTS_INTERFACE = 30_000
ERC4337_VALIDATE_PAYMASTER = 50_000

# Measured: with a reservoir of exactly one slot, a frame doing two
# TSTOREs and one fresh SSTORE needs an execution literal in
# (12,315 , 12,318]. 13,320 leaves ~1,002 gas of slack -- deliberately
# chosen so that a state charge of more than ~500 gas per TSTORE is
# caught while a doubling of TSTORE's *execution* price is not.
RESERVOIR_LITERAL = 13_320

LOCK = 0x11
PERSISTENT_LOCK = 0x12
CONTROL_SLOT = 0x7F


def _attacker(pre: Alloc) -> Address:
    """
    A callee that re-enters whoever called it.

    Returns `1 | (reentry_succeeded << 1)`, so "the callee ran at all" and
    "the re-entry got through the guard" are distinguishable from a zero
    word -- which is what a frame that never ran leaves behind.
    """
    return pre.deploy_contract(
        Op.MSTORE(
            0x40,
            Op.OR(
                1,
                Op.SHL(1, Op.CALL(gas=Op.GAS, address=Op.CALLDATALOAD(0))),
            ),
        )
        + Op.RETURN(0x40, 0x20)
    )


# ----------------------------------------------------------------------
# (a) the deployed lock shape, inside a frozen budget
# ----------------------------------------------------------------------


@pytest.mark.parametrize(
    "budget,outer_ok,callee_ran,reentry_ok,second_ok",
    [
        # Measured floor for this shape: (3,250 , 3,260] on
        # Cancun/Prague/Osaka and (3,640 , 3,660] at EIP-8037, so
        # ERC-7579's 3,229 is below it on every fork. The guard is not
        # reached, nothing commits, and the caller sees a bare failure.
        pytest.param(ERC7579_POSTCHECK, 0, 0, 0, 0, id="erc7579_postcheck"),
        pytest.param(
            ERC165_SUPPORTS_INTERFACE, 1, 1, 0, 1, id="erc165_30000"
        ),
        pytest.param(
            ERC4337_VALIDATE_PAYMASTER, 1, 1, 0, 1, id="erc4337_50000"
        ),
    ],
)
@pytest.mark.valid_from("Cancun")
def test_a_transient_lock_round_trips_inside_a_frozen_budget(
    state_test: StateTestFiller,
    pre: Alloc,
    budget: int,
    outer_ok: int,
    callee_ran: int,
    reentry_ok: int,
    second_ok: int,
) -> None:
    """
    Test the transient reentrancy lock works on a frozen forwarded literal.

    The whole deployed shape in one frame: read the lock, reject if set,
    set it, make the external call that opens the reentrancy window,
    clear it. The callee re-enters and must be rejected, and a *second*
    legitimate call in the same transaction must succeed, which is what
    proves the lock was released rather than merely never set.

    The budget is a frozen literal from deployed code, not
    `bytecode.gas_cost(fork)`. That is the whole point: the official
    EIP-1153 suite derives its budgets from the fork, so no reprice of
    anything the lock touches can make it fail, while this test fails the
    moment the shape stops fitting.

    `erc7579_postcheck` is the lower side of the bracket and is a
    measured finding rather than a construction: a transient guard that
    makes an external call does **not** fit ERC-7579's 3,229-gas
    convention on any fork.

    A failure means either that transient storage stopped being visible
    across the call boundary -- in which case 4,528 deployed addresses'
    reentrancy guards no longer guard anything -- or that the shape
    stopped fitting a budget it used to fit.
    """
    attacker = _attacker(pre)
    guarded = pre.deploy_contract(
        Conditional(
            condition=Op.TLOAD(LOCK),
            if_true=Op.REVERT(0, 0),
            if_false=(
                Op.TSTORE(LOCK, 1)
                + Op.MSTORE(0, Op.ADDRESS)
                + Op.POP(
                    Op.CALL(
                        gas=Op.GAS,
                        address=attacker,
                        args_offset=0,
                        args_size=0x20,
                        ret_offset=0x20,
                        ret_size=0x20,
                    )
                )
                + Op.TSTORE(LOCK, 0)
                + Op.RETURN(0x20, 0x20)
            ),
        )
    )

    storage = Storage()
    parent = pre.deploy_contract(
        Op.MSTORE(
            0x40,
            Op.CALL(
                gas=budget, address=guarded, ret_offset=0, ret_size=0x20
            ),
        )
        + Op.SSTORE(
            storage.store_next(outer_ok, "outer_call_succeeded"),
            Op.MLOAD(0x40),
        )
        + Op.SSTORE(
            storage.store_next(callee_ran, "callee_ran"),
            Op.AND(Op.MLOAD(0), 1),
        )
        + Op.SSTORE(
            storage.store_next(reentry_ok, "reentry_got_through_the_guard"),
            Op.AND(Op.SHR(1, Op.MLOAD(0)), 1),
        )
        + Op.SSTORE(
            storage.store_next(second_ok, "second_call_succeeded"),
            Op.CALL(gas=budget, address=guarded),
        )
        + Op.STOP
    )
    tx = Transaction(to=parent, state_gas_reservoir=0, sender=pre.fund_eoa())
    state_test(pre=pre, post={parent: Account(storage=storage)}, tx=tx)


@pytest.mark.valid_from("Cancun")
def test_a_reverted_attempt_does_not_brick_an_unreleased_transient_lock(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test the lifetime boundary the "written and never cleared" idiom uses.

    L2's third shape -- a transient slot written and never cleared, 2,005
    runtimes / 5,478 addresses -- relies on the *transaction* releasing
    the lock rather than the contract. Two facts make that safe, and they
    pull in opposite directions, so a single assertion cannot express
    them:

    1. a frame that **reverts** must leave no trace of its write, or one
       failed attempt would brick the function for the rest of the
       transaction;
    2. a frame that **succeeds** must leave its write in place, or the
       lock would not be a lock at all.

    Three calls in one transaction, to a guard that never clears:
    attempt 1 sets the lock and then reverts, attempt 2 must therefore
    succeed, and attempt 3 must therefore fail.

    A failure in either direction means a deployed "set once per
    transaction" guard either self-denies after a tolerated failure or
    stops excluding the second entry.
    """
    guarded = pre.deploy_contract(
        Conditional(
            condition=Op.TLOAD(LOCK),
            if_true=Op.REVERT(0, 0),
            if_false=Op.TSTORE(LOCK, 1)
            + Conditional(
                # non-empty calldata == "this attempt fails"
                condition=Op.CALLDATASIZE,
                if_true=Op.REVERT(0, 0),
                if_false=Op.STOP,
            ),
        )
    )

    storage = Storage()
    parent = pre.deploy_contract(
        Op.MSTORE(0, 1)
        + Op.SSTORE(
            storage.store_next(0, "failed_attempt_reverted"),
            Op.CALL(
                gas=Op.GAS,
                address=guarded,
                args_offset=0,
                args_size=0x20,
            ),
        )
        + Op.SSTORE(
            storage.store_next(1, "next_attempt_is_not_bricked"),
            Op.CALL(gas=Op.GAS, address=guarded),
        )
        + Op.SSTORE(
            storage.store_next(0, "third_attempt_hits_the_live_lock"),
            Op.CALL(gas=Op.GAS, address=guarded),
        )
        + Op.STOP
    )
    tx = Transaction(to=parent, state_gas_reservoir=0, sender=pre.fund_eoa())
    state_test(pre=pre, post={parent: Account(storage=storage)}, tx=tx)


# ----------------------------------------------------------------------
# (b) the state-gas immunity -- the half nothing asserted
# ----------------------------------------------------------------------

MEASURED_OPS = {
    "tstore": Op.TSTORE(LOCK, 1),
    "tload": Op.POP(Op.TLOAD(LOCK)),
    "tstore_then_tload": Op.TSTORE(LOCK, 1) + Op.POP(Op.TLOAD(LOCK)),
    # positive control: a fresh persistent slot. Its charge is the thing
    # transient storage is immune to, so if the apparatus cannot see it
    # here the immunity arms above are passing vacuously.
    "fresh_sstore": Op.SSTORE(CONTROL_SLOT, 1),
}


@pytest.mark.parametrize(
    "op,costs_less_than_one_state_byte",
    [
        pytest.param("tstore", 1, id="tstore"),
        pytest.param("tload", 1, id="tload"),
        pytest.param("tstore_then_tload", 1, id="tstore_then_tload"),
        pytest.param("fresh_sstore", 0, id="fresh_sstore_control"),
    ],
)
@pytest.mark.valid_from("Cancun")
def test_a_transient_write_costs_no_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    op: str,
    costs_less_than_one_state_byte: int,
) -> None:
    """
    Test a transient write costs less than a single state byte.

    The reservoir is pinned to **zero**, which is what makes this
    observable at all: with an empty reservoir every state charge has to
    spill out of `gas_left` (`charge_state_gas_from_meter`,
    amsterdam/vm/gas.py:413), so the in-frame `GAS` difference is the
    whole cost of the operation, state gas included. With a positive
    reservoir a state charge would be invisible to `GAS` -- the reservoir
    arm below is the one that covers that case.

    The threshold is one state byte, `COST_PER_STATE_BYTE = 1,530`, and
    it is asserted as an **inequality**, not an equality: this test is
    not pinning TSTORE's price, it is pinning that TSTORE has no *state*
    price. Measured deltas, **identical on Cancun, Prague, Osaka and
    EIP-8037**: 117 for a TSTORE, 116 for a TLOAD, 222 for both. Over the
    same four forks a persistent update moved 5,017 -> 12,117 and a fresh
    slot 22,117 -> 110,037, so the immunity is not an artefact of a quiet
    fork range: the transient numbers did not move across the change that
    multiplied a fresh slot by 4.97x. A transient write would have to
    become 13x dearer before this fired spuriously, while
    the cheapest possible state charge -- one byte of the 64 a storage
    slot is billed for -- trips it immediately.

    `fresh_sstore` is the two-sided half: the same apparatus answers 0
    for an operation that *does* carry state gas, so a mutation that
    merely blinded `GAS` would be caught rather than read as immunity.

    A failure means transient storage has acquired a state cost, and
    every one of the 14,167 addresses that writes it before an external
    call is now running on a different budget than it was written for.
    """
    storage = Storage()
    subject = pre.deploy_contract(
        Op.MSTORE(0, Op.GAS)
        + MEASURED_OPS[op]
        + Op.MSTORE(0x20, Op.GAS)
        + Op.MSTORE(0x40, Op.SUB(Op.MLOAD(0), Op.MLOAD(0x20)))
        + Op.SSTORE(
            storage.store_next(
                costs_less_than_one_state_byte, "below_one_state_byte"
            ),
            Op.LT(Op.MLOAD(0x40), ONE_STATE_BYTE),
        )
        # guards against a vacuous pass: a delta of zero would satisfy
        # the inequality above without measuring anything.
        + Op.SSTORE(
            storage.store_next(1, "apparatus_measured_something"),
            Op.GT(Op.MLOAD(0x40), 0),
        )
        + Op.STOP
    )
    if op == "fresh_sstore":
        # the control's own write is part of the post state
        storage[CONTROL_SLOT] = 1
    tx = Transaction(to=subject, state_gas_reservoir=0, sender=pre.fund_eoa())
    state_test(pre=pre, post={subject: Account(storage=storage)}, tx=tx)


@pytest.mark.parametrize(
    "reservoir,tstores,committed",
    [
        pytest.param(ONE_SLOT_STATE_GAS, 0, 1, id="exact_reservoir_no_tstore"),
        pytest.param(
            ONE_SLOT_STATE_GAS, 2, 1, id="exact_reservoir_two_tstores"
        ),
        pytest.param(
            RESERVOIR_ONE_BYTE_SHORT, 2, 0, id="one_state_byte_short"
        ),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_a_transient_write_does_not_draw_on_the_state_gas_reservoir(
    state_test: StateTestFiller,
    pre: Alloc,
    reservoir: int,
    tstores: int,
    committed: int,
) -> None:
    """
    Test transient writes leave the state-gas reservoir untouched.

    The zero-reservoir arm above cannot see this: once a reservoir
    exists, a state charge is paid out of it and never touches `gas_left`
    at all, so `GAS` reports the same number either way. The only
    observable is **exhaustion**. So the transaction carries a reservoir
    of exactly one slot, the child does N transient writes and then
    exactly one fresh `SSTORE`, and the forwarded execution literal is
    tight enough that any shortfall spilling out of it is fatal.

    `one_state_byte_short` is the calibration, and it is the reason this
    arm can be trusted: with the reservoir reduced by a single state byte
    -- 1,530 of 97,920, 1.6% -- the identical child no longer commits.
    So the arm is sensitive to a per-TSTORE state charge above about
    half a state byte, measured rather than argued. The slack is ~1,002
    gas against a measured floor in (12,315 , 12,318], which also means
    a doubling of TSTORE's *execution* price would not trip it: that
    costs 200, not 1,530.

    A failure in the `exact_reservoir` arms means transient storage has
    started drawing on the reservoir, so every Amsterdam-era contract
    that sized a reservoir around its persistent writes is now short.
    """
    body = Bytecode()
    for i in range(tstores):
        body += Op.TSTORE(LOCK + i, 1)

    storage = Storage()
    child = pre.deploy_contract(
        body
        + Op.SSTORE(storage.store_next(committed, "fresh_slot_funded"), 1)
        + Op.STOP
    )
    caller = pre.deploy_contract(
        Op.POP(Op.CALL(gas=RESERVOIR_LITERAL, address=child)) + Op.STOP
    )
    # No explicit `gas_limit`: EIP-8037 defines the reservoir as the part
    # of `tx.gas` above TX_MAX_GAS_LIMIT, so passing both silently yields
    # a zero reservoir (MUTATION-MATRIX.md, "harness gotchas").
    tx = Transaction(
        to=caller, state_gas_reservoir=reservoir, sender=pre.fund_eoa()
    )
    state_test(pre=pre, post={child: Account(storage=storage)}, tx=tx)


# ----------------------------------------------------------------------
# the negative control: L2's `sto.lock12`, a persistent 1/2 lock
# ----------------------------------------------------------------------


def _flavoured_lock(
    pre: Alloc, flavour: str, callee: Address
) -> Address:
    """Build a lock in one of the three deployed flavours."""
    if flavour == "transient":
        acquire, release, prestate = (
            Op.TSTORE(LOCK, 1),
            Op.TSTORE(LOCK, 0),
            {},
        )
    elif flavour == "persistent_1_2":
        # a widely used contract library ReentrancyGuard: NOT_ENTERED=1, ENTERED=2, so the
        # slot never holds zero. L2's `sto.lock12`: 6,785 runtimes,
        # FP 0/8.
        acquire, release, prestate = (
            Op.SSTORE(PERSISTENT_LOCK, 2),
            Op.SSTORE(PERSISTENT_LOCK, 1),
            {PERSISTENT_LOCK: 1},
        )
    else:  # persistent_0_1
        acquire, release, prestate = (
            Op.SSTORE(PERSISTENT_LOCK, 1),
            Op.SSTORE(PERSISTENT_LOCK, 0),
            {},
        )
    return pre.deploy_contract(
        acquire
        + Op.POP(Op.CALL(gas=Op.GAS, address=callee))
        + release
        + Op.STOP,
        storage=prestate,
    )


@pytest.mark.parametrize(
    "flavour", ["transient", "persistent_1_2"], ids=lambda f: f
)
@pytest.mark.valid_from("Cancun")
def test_lock_flavours_that_carry_no_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    flavour: str,
) -> None:
    """
    Test both state-gas-immune lock flavours survive a sub-floor budget.

    Two flavours, immune for two unrelated reasons, which is why this is
    the right negative control rather than a duplicate:

    `transient`       `tstore` never calls `charge_state_gas` at all
                      (storage.py:189-216).
    `persistent_1_2`  `sstore` charges `StateGasCosts.STORAGE_SET` only
                      inside `if original_value == 0`
                      (storage.py:143-146), and a 1/2 lock's slot never
                      holds zero, so the charge is never reached.

    Both therefore complete inside EIP-4337's frozen 50,000-gas
    `validatePaymasterUserOp` budget on every fork, even though that
    budget is far below the ~110,026 Amsterdam cost of creating one slot.
    The 0/1 flavour is **not** immune, and the pair of fork-split tests
    below measures exactly where it stops fitting.

    The 1/2 convention predates EIP-8037 by years, and the prior result
    this corpus already recorded for it was about *refunds* -- the slot
    never holds zero, so no zero-boundary refund rule touches it. That it
    also buys state-gas immunity is a consequence of the same property,
    measured here; no claim is made about what a widely used contract library intended.
    A failure here means one of the two immunity mechanisms is gone.
    """
    callee = pre.deploy_contract(Op.STOP)
    guarded = _flavoured_lock(pre, flavour, callee)

    storage = Storage()
    parent = pre.deploy_contract(
        Op.SSTORE(
            storage.store_next(1, "lock_round_trip_fitted_50000"),
            Op.CALL(gas=ERC4337_VALIDATE_PAYMASTER, address=guarded),
        )
        + Op.STOP
    )
    tx = Transaction(to=parent, state_gas_reservoir=0, sender=pre.fund_eoa())
    state_test(pre=pre, post={parent: Account(storage=storage)}, tx=tx)


@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Osaka")
def test_a_fresh_zero_one_lock_still_fitted_50000_before_eip8037(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test the 0/1 lock fitted the same budget before EIP-8037.

    The pre-fork half of the control. A 0/1 lock's first acquire is a
    genuine `0 -> 1` transition, so it pays for creating state: 22,100
    before EIP-8037 and 110,020 after. 50,000 covers the first and not
    the second, which is the measured difference between a lock that is
    state-gas immune and one that is not -- and the reason the
    `transient` and `persistent_1_2` arms above are worth a test.
    """
    callee = pre.deploy_contract(Op.STOP)
    guarded = _flavoured_lock(pre, "persistent_0_1", callee)

    storage = Storage()
    parent = pre.deploy_contract(
        Op.SSTORE(
            storage.store_next(1, "lock_round_trip_fitted_50000"),
            Op.CALL(gas=ERC4337_VALIDATE_PAYMASTER, address=guarded),
        )
        + Op.STOP
    )
    tx = Transaction(to=parent, state_gas_reservoir=0, sender=pre.fund_eoa())
    state_test(pre=pre, post={parent: Account(storage=storage)}, tx=tx)


@pytest.mark.valid_from("EIP8037")
def test_a_fresh_zero_one_lock_no_longer_fits_50000_at_eip8037(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test the 0/1 lock stopped fitting the same budget at EIP-8037.

    The post-fork half. Identical bytecode, identical frozen literal,
    opposite outcome: the acquire now needs 97,920 of state gas, the
    transaction carries no reservoir, so the charge spills into a 50,000
    budget that cannot absorb it.

    This is the control that gives the immunity arms their meaning. A
    state-gas reprice is not hypothetical for locks in general -- it has
    already moved one deployed flavour from working to out-of-gas. The
    transient and 1/2 flavours sat through the same change untouched.
    """
    callee = pre.deploy_contract(Op.STOP)
    guarded = _flavoured_lock(pre, "persistent_0_1", callee)

    storage = Storage()
    parent = pre.deploy_contract(
        Op.SSTORE(
            storage.store_next(0, "lock_round_trip_fitted_50000"),
            Op.CALL(gas=ERC4337_VALIDATE_PAYMASTER, address=guarded),
        )
        + Op.STOP
    )
    tx = Transaction(to=parent, state_gas_reservoir=0, sender=pre.fund_eoa())
    state_test(pre=pre, post={parent: Account(storage=storage)}, tx=tx)
