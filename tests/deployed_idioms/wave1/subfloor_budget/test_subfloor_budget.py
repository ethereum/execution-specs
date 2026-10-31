"""
Archetype 2: a frozen budget *below* the storage-slot floor -- the
conventions that never need to write.

Archetype 1 (`tests/frozen_budget/`) asserts that a frozen gas operand is
still large enough for the callee to create a storage slot. For the budgets
L3 actually measured on mainnet that assertion would be **false**, and
writing it would be worse than writing nothing: the test would fail for a
correct implementation and get "repaired" by raising the budget, which is
how the legacy corpus lost its canaries.

```text
convention                        granted gas   frames short of one slot
ERC-7579  postCheck               exactly  3,229   (96.8% of frames)  97.5%
ERC-165   supportsInterface       exactly 30,000   (p50 and p90)      83.9%
EIP-4337  validatePaymasterUserOp exactly 50,000   (610k frames)      99.4%
```
(L3, CHECKED; `tests/frozen_budget/README.md` and `registry/L3-abi.jsonl`.)

All three sit under the measured Amsterdam floor of `(110,020 , 110,040]`
for creating one storage slot, so **the callee cannot create state at all**.
The invariant these conventions rely on is therefore not survival-with-a-
write. It is two-sided:

1. the convention's read-only work **fits** the budget, and
2. the budget is **genuinely insufficient** to create new state, so the
   convention's "never writes" contract is enforced by the gas schedule
   rather than merely by its implementers' good manners.

Both sides must be pinned, because a reprice can break either one, and the
two break in opposite directions:

* reads get dearer -> arm 1 fails -> the hook stops answering, and callers
  that read failure as a negative answer (ERC-165: 64.36% of live calls
  already fail, L5 `sql/25`) take the wrong branch with nothing reverting;
* writes get cheaper -> arm 2 fails -> a budget that was a hard read-only
  guarantee silently becomes write-capable. That direction is not
  hypothetical: five of the fifteen gas constants that changed across the
  fifteen mainnet forks moved **down** (EIP-1108 cut `PRECOMPILE_ECMUL`
  40,000 -> 6,000, a 6.7x reduction).

Measured, not assumed (`tests/tools/test_subfloor_probe.py`, CHECKED, six
forks; see README.md for the commands):

```text
budget    read-only hook fits?        callee can create one slot?
          Berlin..Amsterdam           Berlin..Osaka    Amsterdam
 3,229    yes                         NO               NO
30,000    yes                         yes              NO
50,000    yes                         yes              NO
```

The middle column is the reason tests 3 and 4 exist. For 30,000 and 50,000
the "never needs to write" guarantee is **new at EIP-8037**: before it, a
`supportsInterface` implementation had enough gas to create a slot, and an
ERC-165 caller's static-call context was the only thing stopping it. Pinning
the pre-fork behaviour alongside the post-fork behaviour keeps the pair
honest -- if a later fork restores the old floor, test 4 keeps passing and
test 2 fails, which is the signal we want rather than silence.

Mechanism, read out of EELS at the pinned commit (CHECKED):

```text
COLD_STORAGE_ACCESS = 2100, unchanged Berlin..Amsterdam  amsterdam/vm/gas.py:78
STORAGE_WRITE       = 10000  (Amsterdam execution part)  amsterdam/vm/gas.py:82
STORAGE_SET         = 20000  (Osaka, flat)                   osaka/vm/gas.py:48
COST_PER_STATE_BYTE = 1530; STATE_BYTES_PER_STORAGE_SET = 64
                    -> 97,920 state gas per fresh slot   amsterdam/vm/gas.py:47
  fresh slot, Osaka      =  2,100 + 20,000             =  22,100
  fresh slot, Amsterdam  =  2,100 + 10,000 + 97,920    = 110,020
```

Note on `STATICCALL`: ERC-165 probes are static calls, under which a write
is impossible by *context* rather than by *gas*. These tests use `CALL` for
both arms deliberately, so what is being measured is the gas boundary and
not the static-context check -- ERC-7579 `postCheck` and EIP-4337
`validatePaymasterUserOp` are ordinary calls, and for them gas is the only
thing standing between the budget and a state write.

A failure here means one of two real things happened: a sub-floor
convention's read-only work no longer fits the budget deployed callers
forward (test 1), or a budget that provably could not create state now can
(tests 2-4). Do not repair either by changing `SUB_FLOOR_BUDGETS`; those are
measured deployed values, not parameters.
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

# Gas budgets measured by L3 on live mainnet frames. Each is a literal that
# deployed callers forward, so none of them can be rebased by a fork.
SUB_FLOOR_BUDGETS = {
    # ERC-7579 modular-account hook. L3 measured `postCheck` reached with
    # exactly 3,229 gas in 96.8% of frames (registry/L3-abi.jsonl,
    # "ERC-7579 module lifecycle hooks, including a 3,229-gas postCheck").
    # The tightest budget in the corpus, and below the slot floor on every
    # fork from Berlin onwards.
    "erc7579_post_check_3229": 3_229,
    # ERC-165 `supportsInterface`. The 30,000 ceiling is written into the
    # standard itself ("must use less than 30,000 gas") and into its
    # reference caller's `staticcall(30000, ...)`, so it is not one
    # contract's choice. L3 measured it as both the p50 and the p90 of
    # granted gas; L5 `sql/25` measured 27,561 live probe calls at exactly
    # this literal.
    "erc165_supports_interface_30000": 30_000,
    # EIP-4337 paymaster validation sub-budget. L3 measured exactly 50,000
    # over 610k frames (registry/L3-abi.jsonl, "ERC-4337 paymaster
    # validation and postOp on reserved sub-budgets").
    "erc4337_validate_paymaster_50000": 50_000,
}

_ABOVE_THE_PRE_8037_FLOOR = ["erc165_supports_interface_30000",
                             "erc4337_validate_paymaster_50000"]

# Read-only convention body: one cold SLOAD of the hook's own configuration,
# a comparison, and a 32-byte answer returned to the caller. Sized by the
# smallest budget in the table -- it must fit 3,229 gas, which bounds it to
# one cold storage access (2,100) plus arithmetic.
READ_ONLY_HOOK = Op.MSTORE(0, Op.ISZERO(Op.SLOAD(0))) + Op.RETURN(0, 32)

# The same convention, implemented by someone who did reach for state. This
# is the callee whose failure proves the budget is a real guarantee.
WRITING_HOOK = Op.SSTORE(0, 1) + Op.STOP


def _answer_recorder(
    read_only: object, budget: int, storage: Storage
) -> Bytecode:
    """
    Build a caller that records whether the hook answered inside `budget`.

    Both `CALL` status and the returned word are folded into one marker, so
    "the hook answered" is distinguished from "the call returned 0" -- the
    distinction that matters for a convention whose callers read failure as
    a negative answer.
    """
    return (
        # The CALL must execute before either MLOAD. `Op.X(a, b)` emits `b`
        # first, so folding the CALL into the AND would read the return
        # buffer before the call had filled it.
        Op.MSTORE(
            0x20,
            Op.CALL(
                gas=budget, address=read_only, ret_offset=0, ret_size=32
            ),
        )
        + Op.SSTORE(
            storage.store_next(1, "hook_answered"),
            Op.AND(Op.MLOAD(0x20), Op.MLOAD(0)),
        )
    )


def _run_read_only_arm(
    state_test: StateTestFiller, pre: Alloc, budget: int
) -> None:
    """Fill arm 1: the read-only body completes inside the budget."""
    read_only = pre.deploy_contract(READ_ONLY_HOOK)
    prober_storage = Storage()
    prober = pre.deploy_contract(
        _answer_recorder(read_only, budget, prober_storage) + Op.STOP
    )
    tx = Transaction(to=prober, state_gas_reservoir=0, sender=pre.fund_eoa())
    state_test(
        pre=pre,
        post={prober: Account(storage=prober_storage)},
        tx=tx,
    )


def _run_boundary(
    state_test: StateTestFiller,
    pre: Alloc,
    budget: int,
    write_succeeds: bool,
) -> None:
    """
    Fill the two-sided boundary: the hook answers, and the writer's fate.

    Both arms live in one transaction on purpose. Asserting them together
    distinguishes "the budget is too small to run at all" from "the budget
    is large enough to run but too small to write" -- exactly the boundary
    this archetype exists to pin, and which neither arm establishes alone.
    """
    read_only = pre.deploy_contract(READ_ONLY_HOOK)
    writer = pre.deploy_contract(WRITING_HOOK)

    prober_storage = Storage()
    prober = pre.deploy_contract(
        _answer_recorder(read_only, budget, prober_storage)
        + Op.SSTORE(
            prober_storage.store_next(int(write_succeeds), "writer_succeeded"),
            Op.CALL(gas=budget, address=writer),
        )
        + Op.STOP
    )

    writer_storage = Storage()
    writer_storage.store_next(
        int(write_succeeds),
        "fresh_slot_created" if write_succeeds else "fresh_slot_absent",
    )

    tx = Transaction(to=prober, state_gas_reservoir=0, sender=pre.fund_eoa())
    state_test(
        pre=pre,
        post={
            prober: Account(storage=prober_storage),
            writer: Account(storage=writer_storage),
        },
        tx=tx,
    )


@pytest.mark.parametrize(
    "budget",
    [pytest.param(v, id=k) for k, v in SUB_FLOOR_BUDGETS.items()],
)
@pytest.mark.valid_from("Berlin")
def test_subfloor_budget_lets_the_read_only_hook_answer(
    state_test: StateTestFiller,
    pre: Alloc,
    budget: int,
) -> None:
    """
    Test a read-only convention body completes inside its deployed budget.

    This is arm 1 of the invariant, and the only arm archetype 1 could have
    expressed -- except that archetype 1 would have demanded a storage write
    too, which none of these budgets can afford. The assertion here is that
    the hook *answered*: the caller records `CALL` status AND the returned
    word, so "the call returned 0" is distinguished from "the callee ran out
    of gas and the caller read that as a negative answer".

    Held on every fork from Berlin to Amsterdam (measured). It is the cheap
    arm, and the one a read-side reprice breaks: one cold storage access is
    2,100 of the 3,229 that ERC-7579 `postCheck` is given.
    """
    _run_read_only_arm(state_test, pre, budget)


@pytest.mark.parametrize(
    "budget",
    [pytest.param(v, id=k) for k, v in SUB_FLOOR_BUDGETS.items()],
)
@pytest.mark.valid_from("EIP8037")
def test_subfloor_budget_cannot_create_state_from_eip8037(
    state_test: StateTestFiller,
    pre: Alloc,
    budget: int,
) -> None:
    """
    Test none of the three deployed sub-floor budgets can create a slot.

    Arm 2: the "never needs to write" contract is enforced by the gas
    schedule. The writing callee's `CALL` returns 0 and its slot is still
    absent, while the read-only callee in the same transaction answered
    normally -- so the budget is demonstrably sufficient to *run* and
    insufficient to *write*, which is the whole boundary.

    A fresh slot costs `2,100 + 10,000 + 97,920 = 110,020` at Amsterdam, so
    all three budgets are short by at least 60,020. The margin is large,
    which makes this arm a coarse detector: it only fires on a large
    reduction in state-gas pricing. That is the intended trade -- a tight
    bracket here would be a bracket on the floor, which
    `tests/frozen_budget/` already owns.
    """
    _run_boundary(state_test, pre, budget, write_succeeds=False)


@pytest.mark.valid_from("Berlin")
@pytest.mark.valid_until("Osaka")
def test_tightest_subfloor_budget_never_could_create_state(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test the 3,229-gas budget is below the slot floor on the old forks too.

    ERC-7579's `postCheck` is the only one of the three that was *always*
    sub-floor: the pre-EIP-8037 floor is `2,100 + 20,000 = 22,100`, so
    3,229 was never enough. Its read-only guarantee is therefore the oldest
    and the most robust, and asserting it on the forks where it already held
    is what makes test 2's Amsterdam result a continuation rather than a
    coincidence.
    """
    _run_boundary(
        state_test,
        pre,
        SUB_FLOOR_BUDGETS["erc7579_post_check_3229"],
        write_succeeds=False,
    )


@pytest.mark.parametrize(
    "budget",
    [
        pytest.param(SUB_FLOOR_BUDGETS[k], id=k)
        for k in _ABOVE_THE_PRE_8037_FLOOR
    ],
)
@pytest.mark.valid_from("Berlin")
@pytest.mark.valid_until("Osaka")
def test_subfloor_budget_could_still_write_before_eip8037(
    state_test: StateTestFiller,
    pre: Alloc,
    budget: int,
) -> None:
    """
    Test 30,000 and 50,000 *were* enough to create a slot before EIP-8037.

    The uncomfortable half of the pair, and the reason this archetype is
    two-sided rather than a one-sided "cannot write" claim. On Berlin
    through Osaka a `supportsInterface` or `validatePaymasterUserOp`
    implementation given its standard budget had ample gas to create a
    storage slot: 22,100 of the 30,000. The read-only guarantee those
    conventions are documented to provide was, on those forks, not enforced
    by gas at all.

    EIP-8037 is what makes it enforced. Asserting the old behaviour here
    means the boundary's *movement* is pinned, not just its current
    position: a fork that restores the old floor fails this test's
    counterpart above instead of silently re-enabling writes.
    """
    _run_boundary(state_test, pre, budget, write_succeeds=True)
