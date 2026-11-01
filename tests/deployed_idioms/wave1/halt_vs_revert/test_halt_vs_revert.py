"""
Archetype 11: halt-versus-revert gas return.

A child that `STOP`s or `REVERT`s hands its unspent `gas_left` back to
its parent; a child that halts exceptionally -- out of gas, invalid
opcode -- hands back nothing, because `forfeit_remaining_gas` zeroes the
meter first (`amsterdam/vm/interpreter.py:450-462`,
`amsterdam/vm/gas.py:647`). From EIP-8037 the reverting child gives back
*more* than its unspent execution gas: `restore_state_gas` refills the
state-gas spill into `gas_left` before the parent absorbs the meter
(`amsterdam/vm/gas.py:493`), and the halting child still gives back
nothing because the forfeit runs immediately after the same refill.

A caller that tolerates child failure therefore recovers gas on `REVERT`
and not on a halt, and **its own completion depends on which**. That
asymmetry is invisible to the caller's control flow: `CALL` returns `0`
in both cases.

Witnessed (CHECKED, `registry/L5-dynamic.jsonl`, mainnet blocks
26,250,000-26,259,999): *tolerated child failure inside a committing
transaction* -- raw 116,823 frames, but **measured 94.12% false positive
(sql/35)**: 109,953 of those are reverts that consumed under half their
grant, i.e. business-logic failures no repricing can flip. The record's
own post-filter population is **6,281 frames across 270 distinct runtime
code hashes** (the brief's ~6,870 is the bare subtraction residual
116,823 - 109,953; 6,281 is the filtered count and is the figure used
here). Exemplars:

* `<address withheld>` -- KyberSwap executor,
  10,029 self-call frames in 3,981 transactions, 40% of them failing and
  tolerated;
* `<address withheld>` -- 5,413 of 6,852 frames
  (79%) fail and are tolerated;
* `<address withheld>` -- a deployed AMM, where
  **the `StateChangeDuringStaticCall` and out-of-gas arms are both
  tolerated**, which is this discriminator in deployed code.

Statically (CHECKED, `registry/L2-bytecode.jsonl`): *best-effort sub-call
inside a loop* -- 17,435 mainnet addresses from 15,296 distinct runtimes,
rule axes including `exceptional-halt-gas-burn` and `revert-propagation`.

**Shape.** Three frames. `outer` calls `tolerant` on a literal grant and
commits `CALL + 1`, so 2 means `tolerant` finished and 1 means it died --
both a non-zero committed effect. `tolerant` forwards `GAS`, which is the
deployed `call(gas(), ...)` idiom, so it retains exactly the 63/64
remainder; it then discards the result and writes its epilogue. The
epilogue updates three pre-existing slots, which costs more than the
retained remainder and far less than a returned grant, so the epilogue
commits if and only if the child gave its gas back.

Measured, not assumed (`tests/tools/test_refund_probe.py`), gas held by
`tolerant` after the child ends, on a 200,000 grant:

```text
fork             STOP      REVERT   INVALID      OOG
Berlin..Osaka   197,376   197,370     3,080    3,080
Amsterdam       196,976   196,970     3,073    3,073
```

and after a child that creates a slot, burns almost everything down with
`WhileGas`, and then ends -- with the clear (`_spilling_child`) and
without it (`_unrepaid_spill_child`):

```text
                   clears the slot      keeps the spill
fork             REVERT   INVALID     REVERT   INVALID
Berlin..Osaka     6,990     3,080      7,096     3,080
Amsterdam       104,902     3,073    105,008     3,073
```

The two Amsterdam revert figures are nearly equal but arrive by
*different* routes, and the mutation matrix is what showed it: with the
clear, `credit_state_gas_refund` has already moved the spill into
`gas_left`, so the revert merely returns it; without the clear the spill
is still outstanding and `restore_state_gas` is the only thing that can
return it. Only the second shape can see a change to the revert path's
refill.

The epilogue costs 15,000 on Berlin..Osaka (3 x (`COLD_STORAGE_ACCESS`
2,100 + `COLD_STORAGE_WRITE - COLD_STORAGE_ACCESS` 2,900)) and 36,300 on
Amsterdam (3 x (2,100 + `STORAGE_WRITE` 10,000)) -- inside every bracket
above, so one epilogue discriminates on every fork in range.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Fork,
    GasConsumer,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
    WhileGas,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

SLOT_X = 0x01
UNTOUCHED = 0xFF

# The grant `outer` hands `tolerant`. A literal: a deployed caller's
# forwarding ceiling is in its immutable code, never derived from a fork.
GRANT = 200_000

# Gas left in the drained child before it ends, so that what the parent
# gets back on `REVERT` is dominated by the state-gas refill rather than
# by unspent execution gas.
DRAIN_RESERVE = 4_000


def _epilogue(value: int) -> tuple[Storage, Bytecode]:
    """
    Post-failure work, and the storage it leaves behind.

    Three slots, each pre-set to `UNTOUCHED`, each overwritten with 1.
    Overwriting a non-zero slot costs 5,000 on Berlin..Osaka and 12,100
    on Amsterdam, so the three together cost more than the 63/64
    remainder the caller held back and far less than a returned grant.
    """
    expected = Storage()
    slots = [expected.store_next(value, f"epilogue_{i}") for i in range(3)]
    code = Bytecode()
    for slot in slots:
        code += Op.SSTORE(slot, 1)
    return expected, code + Op.STOP


def _plain_child(ending: str, fork: Fork) -> Bytecode:
    """A child that does nothing and then ends one of four ways."""
    if ending == "stop":
        return Op.STOP
    if ending == "revert":
        return Op.REVERT(0, 0)
    if ending == "invalid":
        return Op.INVALID
    if ending == "oog":
        return GasConsumer.out_of_gas(fork) + Op.STOP
    raise ValueError(ending)


def _spilling_child(ending: str, fork: Fork) -> Bytecode:
    """
    A child that creates a slot, burns almost everything, clears, ends.

    By the time it ends, its unspent execution gas is down to roughly
    `DRAIN_RESERVE`, so whatever the parent gets back beyond that came
    from the clear -- which pre-8037 is nothing at all and from EIP-8037
    is the 97,920 state-gas spill returned to `gas_left`.
    """
    return (
        Op.SSTORE(SLOT_X, 1)
        + WhileGas(body=Op.JUMPDEST, fork=fork, extra_gas=DRAIN_RESERVE)
        + Op.SSTORE(SLOT_X, 0)
        + (Op.REVERT(0, 0) if ending == "revert" else Op.INVALID)
    )


def _unrepaid_spill_child(ending: str, fork: Fork) -> Bytecode:
    """
    A child that creates a slot, burns almost everything, then ends.

    No clear, so the state-gas spill is **still outstanding** when the
    frame ends and the only thing that can return it is
    `restore_state_gas` on the revert path. `_spilling_child` cannot
    isolate that, because its clear has already moved the spill into
    `gas_left` through `credit_state_gas_refund` -- the mutation matrix
    is what established the difference; see this directory's README.
    """
    return (
        Op.SSTORE(SLOT_X, 1)
        + WhileGas(body=Op.JUMPDEST, fork=fork, extra_gas=DRAIN_RESERVE)
        + (Op.REVERT(0, 0) if ending == "revert" else Op.INVALID)
    )


def _run(
    state_test: StateTestFiller,
    pre: Alloc,
    *,
    child_code: Bytecode,
    tolerant_survives: bool,
) -> None:
    """Fill one ending and assert both frames' committed effects."""
    child = pre.deploy_contract(child_code)

    # A surviving caller leaves 1 in each epilogue slot; a caller that
    # dies in its epilogue leaves every slot at its pre-transaction
    # value, because the whole frame rolls back.
    epilogue, epilogue_code = _epilogue(1 if tolerant_survives else UNTOUCHED)
    tolerant = pre.deploy_contract(
        Op.POP(Op.CALL(gas=Op.GAS, address=child)) + epilogue_code,
        storage={slot: UNTOUCHED for slot in epilogue},
    )

    status = Storage()
    outer = pre.deploy_contract(
        Op.SSTORE(
            status.store_next(2 if tolerant_survives else 1, "tolerant_ok"),
            Op.ADD(Op.CALL(gas=GRANT, address=tolerant), 1),
        )
        + Op.STOP
    )
    state_test(
        pre=pre,
        post={
            outer: Account(storage=status),
            tolerant: Account(storage=epilogue),
        },
        tx=Transaction(to=outer, sender=pre.fund_eoa(), state_gas_reservoir=0),
    )


@pytest.mark.parametrize(
    "ending,tolerant_survives",
    [
        pytest.param("stop", True, id="child_stops"),
        pytest.param("revert", True, id="child_reverts"),
        pytest.param("invalid", False, id="child_hits_invalid_opcode"),
        pytest.param("oog", False, id="child_runs_out_of_gas"),
    ],
)
@pytest.mark.valid_from("Berlin")
def test_a_tolerant_caller_recovers_gas_on_revert_but_not_on_a_halt(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    ending: str,
    tolerant_survives: bool,
) -> None:
    """
    Test the caller's post-failure work commits on `REVERT`, not on a halt.

    The same caller, the same grant and the same tolerated `CALL`; only
    the child's ending changes. On `STOP` and `REVERT` the ~197,000 gas
    the child did not spend comes back and the epilogue commits. On an
    invalid opcode or a genuine out-of-gas the caller is left with the
    3,07x the 63/64 rule held back, which is below the epilogue's cost,
    so the caller dies too and `outer` records 1.

    All four points are asserted together on purpose: without the halting
    pair the test would not distinguish "gas came back" from "the
    epilogue was affordable anyway", and without the returning pair it
    would not distinguish "gas was burnt" from "the construction never
    worked".
    """
    _run(
        state_test,
        pre,
        child_code=_plain_child(ending, fork),
        tolerant_survives=tolerant_survives,
    )


@pytest.mark.parametrize(
    "ending",
    [pytest.param("revert", id="revert"), pytest.param("invalid", id="halt")],
)
@pytest.mark.valid_from("Berlin")
@pytest.mark.valid_until("Osaka")
def test_a_drained_child_returns_nothing_either_way_before_eip8037(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    ending: str,
) -> None:
    """
    Test a drained child's revert is worth no more than its halt, pre-8037.

    The child creates a slot, burns itself down to ~4,000 gas, clears the
    slot and ends. Clearing moves 19,900 into the refund counter and
    nothing into `gas_left`, so the revert returns ~3,900 where the halt
    returns 0 -- and 3,900 is not the difference between a 3,080-gas
    remainder and a 15,000-gas epilogue. Both endings kill the caller.

    This is the pre-fork half of the pair below. It is what makes the
    EIP-8037 result a *change* rather than an isolated observation, and a
    fork that routed storage refunds into `gas_left` would turn the
    `revert` point green here.
    """
    _run(
        state_test,
        pre,
        child_code=_spilling_child(ending, fork),
        tolerant_survives=False,
    )


@pytest.mark.parametrize(
    "ending,tolerant_survives",
    [
        pytest.param("revert", True, id="revert"),
        pytest.param("invalid", False, id="halt"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_a_drained_child_returns_its_restored_spill_on_revert_from_eip8037(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    ending: str,
    tolerant_survives: bool,
) -> None:
    """
    Test the reverting child now hands back its restored state-gas spill.

    Identical bytecode to the test above. The child still ends holding
    ~4,000 gas of its own, but the clear has already returned the 97,920
    state-gas spill to its `gas_left`, so `REVERT` hands the caller
    ~104,900 and the 36,300-gas epilogue commits. The halting child
    reaches the same point and gives back nothing, because
    `forfeit_remaining_gas` runs immediately after the same refill.

    So from EIP-8037 the gap between revert and halt is no longer only
    the child's unspent execution gas -- it includes state gas the child
    was charged for and the halt destroys.
    """
    _run(
        state_test,
        pre,
        child_code=_spilling_child(ending, fork),
        tolerant_survives=tolerant_survives,
    )


@pytest.mark.parametrize(
    "ending,tolerant_survives",
    [
        pytest.param("revert", True, id="revert"),
        pytest.param("invalid", False, id="halt"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_a_revert_returns_an_outstanding_spill_and_a_halt_destroys_it(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    ending: str,
    tolerant_survives: bool,
) -> None:
    """
    Test the revert path's spill refill in isolation, with no clear.

    The child creates a slot and burns itself down to ~4,000 gas without
    clearing it, so its 97,920-gas spill is still outstanding when it
    ends. On `REVERT`, `restore_state_gas` refills the spill into
    `gas_left` and the caller receives ~105,000 -- measured -- so the
    36,300-gas epilogue commits. On an invalid opcode the same refill
    happens and `forfeit_remaining_gas` immediately destroys it, so the
    caller receives nothing.

    This exists because the mutation matrix found the test above could
    not see `restore_state_gas` at all: a clear converts the spill into
    `gas_left` before the revert, so removing the revert's refill changed
    nothing. Here there is no clear, and nothing else can return the
    spill.
    """
    _run(
        state_test,
        pre,
        child_code=_unrepaid_spill_child(ending, fork),
        tolerant_survives=tolerant_survives,
    )
