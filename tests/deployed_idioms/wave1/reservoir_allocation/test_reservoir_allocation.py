"""
Class #16: reservoir allocation is NOT subject to the 63/64 rule.

EIP-8037 splits a transaction's gas into an execution-gas grant and a
state-gas reservoir (`allocate_evm_gas`, amsterdam/vm/gas.py:1105: the
reservoir is whatever `tx.gas` exceeds `TX_MAX_GAS_LIMIT = 16,777,216`).
The two dimensions are handed to a child frame by *different rules*:

    execution gas   gas = min(requested, gas_left - gas_left // 64)
                    -- the parent always keeps `gas_left // 64` back
                                            amsterdam/vm/gas.py:801-861

    state gas       drain_state_gas_reservoir: the child receives the
                    parent's **entire** reservoir
                    "there is no all-but-one-64th rule for state gas"
                                            amsterdam/vm/gas.py:689

So a parent cannot reserve any state gas for its own later work, while it
always retains a 64th of its execution gas however hostile the child is.
That asymmetry is this class's invariant.

This pins a *new* rule rather than an old one, which is deliberate: a
later fork that "fixed" the asymmetry by giving state gas its own 63/64
rule would change what every Amsterdam-era contract receives, and nothing
else in the corpus would notice. These tests are the tripwire.

Why the reservoir is observable at all: a state charge the reservoir
cannot cover *spills* into `gas_left` (`charge_state_gas_from_meter`,
amsterdam/vm/gas.py:412), so a frame with plenty of execution gas never
notices an empty reservoir. Every test here therefore forwards a **tight
execution-gas literal** to the frame doing the state-creating work, which
is both the only way to make the reservoir visible and the shape deployed
callers actually use.

`valid_from("EIP8037")` throughout: a positive reservoir raises on earlier
forks (`transaction_types.py:697`), and there is nothing to test without
one.

Every number here was measured with
`tests/tools/test_cls16_reservoir_probe.py`; the tables are in README.md.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    GasConsumer,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

# STATE_BYTES_PER_STORAGE_SET(64) * COST_PER_STATE_BYTE(1530)
# == StateGasCosts.STORAGE_SET, amsterdam/vm/gas.py:47-51.
ONE_SLOT_STATE_GAS = 97_920

# Measured: with the whole of `ONE_SLOT_STATE_GAS` in hand, a frame
# creates one fresh slot on an execution-gas literal in (12,100 , 12,110].
# The two values bracket it.
LITERAL_TOO_TIGHT = 12_100
LITERAL_EXACT = 12_110
LITERAL_COMFORTABLE = 20_000

# Measured: with *no* reservoir the same frame needs (110,020 , 110,040],
# because the 97,920 has to spill out of `gas_left`.
LITERAL_WITHOUT_RESERVOIR = 110_040

# Execution gas a frame needs to create one fresh slot and get out, with
# an empty reservoir:
#   2,100  COLD_STORAGE_ACCESS
#  10,000  STORAGE_WRITE
#  97,920  STORAGE_SET, spilled out of `gas_left`
#       8  POP + two PUSH1
EPILOGUE_EXECUTION_GAS = 110_028

# What the caller spends before the EVM computes the child's grant:
#   3,000  COLD_ACCOUNT_ACCESS on the burner
#      18  six PUSH operands
#       2  GAS
CALLER_PRE_CALL_GAS = 3_020

# Amsterdam intrinsic cost of a zero-value call to a contract
# (EIP-2780 decomposes 21,000 into TX_BASE + recipient_execution_gas).
INTRINSIC_ZERO_VALUE_CALL = 15_000


def _retention_budget(multiple: int) -> int:
    """`tx.gas` whose retained 64th is exactly `multiple/64` epilogues."""
    return (
        multiple * EPILOGUE_EXECUTION_GAS
        + CALLER_PRE_CALL_GAS
        + INTRINSIC_ZERO_VALUE_CALL
    )


# --------------------------------------------------------------------------
# 1. The child receives the whole reservoir, not 63/64 of it
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "reservoir,literal,committed",
    [
        pytest.param(
            ONE_SLOT_STATE_GAS,
            LITERAL_TOO_TIGHT,
            0,
            id="exact_reservoir_12100",
        ),
        pytest.param(
            ONE_SLOT_STATE_GAS, LITERAL_EXACT, 1, id="exact_reservoir_12110"
        ),
        pytest.param(
            ONE_SLOT_STATE_GAS,
            LITERAL_COMFORTABLE,
            1,
            id="exact_reservoir_20000",
        ),
        pytest.param(0, LITERAL_COMFORTABLE, 0, id="no_reservoir_20000"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_child_receives_the_entire_reservoir(
    state_test: StateTestFiller,
    pre: Alloc,
    reservoir: int,
    literal: int,
    committed: int,
) -> None:
    """
    Test a child funds a whole fresh slot from a reservoir of exactly one.

    The transaction's reservoir is exactly `StateGasCosts.STORAGE_SET`, and
    the child creates exactly one fresh slot. If the child receives 100% of
    the reservoir the state charge is covered with nothing left over and
    nothing spilled, so a 12,110-gas execution literal suffices. If it
    received `63/64` instead -- 96,390 -- the remaining 1,530 would have to
    spill out of that literal, which would then need ~13,636 and the write
    would not happen.

    The `no_reservoir` param is the control: the identical child on the
    identical literal commits nothing, because the full 97,920 must then
    come out of execution gas. The gap between 12,110 and 110,040 is what
    the reservoir carries.

    A failure means the rule for handing state gas to a child has changed,
    and every Amsterdam-era caller that sized a forwarded gas literal
    against it is now wrong.
    """
    child_storage = Storage()
    child = pre.deploy_contract(
        Op.SSTORE(child_storage.store_next(committed, "child_committed"), 1)
        + Op.STOP
    )
    caller = pre.deploy_contract(
        Op.POP(Op.CALL(gas=literal, address=child)) + Op.STOP
    )
    # No explicit `gas_limit`: EIP-8037 defines the reservoir as the part
    # of `tx.gas` above TX_MAX_GAS_LIMIT, so the harness has to set
    # `tx.gas = cap + reservoir` itself. Passing both silently yields a
    # zero reservoir.
    tx = Transaction(
        to=caller,
        state_gas_reservoir=reservoir,
        sender=pre.fund_eoa(),
    )
    state_test(pre=pre, post={child: Account(storage=child_storage)}, tx=tx)


# --------------------------------------------------------------------------
# 2. A parent cannot hold any of the reservoir back across a child call
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "drained,literal,committed",
    [
        pytest.param(False, LITERAL_COMFORTABLE, 1, id="not_drained"),
        pytest.param(True, LITERAL_COMFORTABLE, 0, id="drained"),
        pytest.param(
            True, LITERAL_WITHOUT_RESERVOIR, 1, id="drained_but_funded"
        ),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_a_reservoir_spent_by_a_child_is_gone_for_the_next(
    state_test: StateTestFiller,
    pre: Alloc,
    drained: bool,
    literal: int,
    committed: int,
) -> None:
    """
    Test the parent retains no state gas once a child has spent it.

    One caller, one reservoir of exactly one slot, two children. The first
    either spends the reservoir on a slot of its own or does nothing; the
    second always tries to create a slot on the same forwarded literal.

    `not_drained`       the reservoir reaches the second child intact, so
                        20,000 execution gas is plenty.
    `drained`           the first child took 100% of it. The parent kept
                        nothing back for the second, which now needs
                        110,028 execution gas and has 20,000.
    `drained_but_funded` the same drained call with 110,040 forwarded does
                        commit, which identifies the shortfall as exactly
                        the state-gas charge and not something else.

    Had the reservoir followed the execution-gas rule, the parent would
    have kept `97,920 // 64 = 1,530` back -- still not a slot -- so note
    what this test does **not** claim: a 63/64 rule would not rescue the
    `drained` arm. The arithmetic that makes the asymmetry bite at scale is
    in the third test below and in README.md.

    A failure means a contract that creates state after calling out can no
    longer predict whether its own write will fit.
    """
    drain_storage = Storage()
    if drained:
        drain_code = (
            Op.SSTORE(drain_storage.store_next(1, "drain_committed"), 1)
            + Op.STOP
        )
    else:
        drain_code = Op.STOP
    drain = pre.deploy_contract(drain_code)

    epilogue_storage = Storage()
    epilogue = pre.deploy_contract(
        Op.SSTORE(
            epilogue_storage.store_next(committed, "epilogue_committed"), 1
        )
        + Op.STOP
    )
    caller = pre.deploy_contract(
        Op.POP(Op.CALL(gas=LITERAL_COMFORTABLE, address=drain))
        + Op.POP(Op.CALL(gas=literal, address=epilogue))
        + Op.STOP
    )
    tx = Transaction(
        to=caller,
        state_gas_reservoir=ONE_SLOT_STATE_GAS,
        sender=pre.fund_eoa(),
    )
    state_test(
        pre=pre,
        post={
            drain: Account(storage=drain_storage),
            epilogue: Account(storage=epilogue_storage),
        },
        tx=tx,
    )


# --------------------------------------------------------------------------
# 3. The execution-gas half of the asymmetry, to one gas
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "gas_limit,committed",
    [
        pytest.param(_retention_budget(63), 0, id="63_epilogues"),
        pytest.param(_retention_budget(64) - 1, 0, id="64_epilogues_minus_1"),
        pytest.param(_retention_budget(64), 1, id="64_epilogues"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_execution_gas_retention_is_exactly_one_64th(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_limit: int,
    committed: int,
) -> None:
    """
    Test the parent keeps back exactly `gas_left // 64` of execution gas.

    Same shape as the retained-gas epilogue archetype, but the budget is
    built as a *multiple of the epilogue's own cost*, which turns a loose
    survival test into a one-gas measurement of the divisor. The child
    consumes everything it is given, so the parent's epilogue runs purely
    on what the 63/64 rule withheld:

        63 epilogues' worth of budget  ->  retains 108,465, write fails
        64 epilogues' worth, minus 1   ->  retains 110,027, write fails
        64 epilogues' worth            ->  retains 110,028, write succeeds

    Measured threshold `tx.gas = 7,059,812` exactly, and the 64-epilogue
    param passes with **zero** margin, so any tightening of the divisor,
    any rise in the cost of creating a slot, and any rise in the call's own
    charge all flip it.

    This is the half of class #16's asymmetry that *does* have a fraction.
    Its state-gas counterpart has no analogue: there is no multiple of the
    reservoir at which the parent keeps a slot's worth back, because it
    keeps nothing back at all.
    """
    burner = pre.deploy_contract(GasConsumer(gas=None, fork=fork))
    storage = Storage()
    caller = pre.deploy_contract(
        Op.POP(Op.CALL(gas=Op.GAS, address=burner))
        + Op.SSTORE(storage.store_next(committed, "epilogue_committed"), 1)
        + Op.STOP
    )
    tx = Transaction(
        to=caller,
        gas_limit=gas_limit,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
    )
    state_test(pre=pre, post={caller: Account(storage=storage)}, tx=tx)
