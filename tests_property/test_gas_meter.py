"""
Properties of the [EIP-8037] two-pool gas meter, in one frame and across a
call into a child frame.

State gas draws from a reservoir before spilling into `gas_left`, and
refunds credit the pools in reverse order.

[EIP-8037]: https://eips.ethereum.org/EIPS/eip-8037
"""

from types import ModuleType
from typing import List

import pytest
from ethereum_types.numeric import Uint
from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.stateful import (
    RuleBasedStateMachine,
    initialize,
    invariant,
    precondition,
    rule,
    run_state_machine_as_test,
)

from ethereum_spec_tools.forks import Hardfork

from .forks import requires
from .gas_meter import (
    AMOUNT_BOUND,
    CHARGES,
    CHARGES_AND_REFUNDS,
    MeterFields,
    MeterOp,
    amounts,
    apply_ops,
    fresh_frame,
    meter_fields,
    op_lists,
    pools,
)
from .strategies import aim_at

pytestmark = requires(lambda fork: fork.state_gas_reservoir_enabled())


@pytest.mark.spec_unit
@given(
    gas_left=pools(),
    reservoir=pools(),
    pre_charges=op_lists(CHARGES, max_size=6),
    commit=st.booleans(),
    post_ops=op_lists(CHARGES_AND_REFUNDS),
    refund_counter=st.integers(min_value=-(1 << 20), max_value=1 << 20),
    halt=st.booleans(),
)
def test_restore_returns_to_the_last_commit(
    gas: ModuleType,
    gas_left: int,
    reservoir: int,
    pre_charges: List[MeterOp],
    commit: bool,
    post_ops: List[MeterOp],
    refund_counter: int,
    halt: bool,
) -> None:
    """
    A frame rollback undoes every state charge and refund since the last
    commit, keeps the regular gas spent since then, and leaves the state
    gas charged before the commit in place. A halt then burns `gas_left`.
    """
    frame = fresh_frame(gas, gas_left, reservoir)
    meter = frame.gas_meter
    if commit:
        _, committed, _ = apply_ops(gas, frame, pre_charges)
        # A commit right as the reservoir runs dry splits the spill.
        aim_at(committed, reservoir, "committed state gas near the reservoir")
        gas.commit_state_gas(meter)
        ops_after_commit = post_ops
    else:
        # Without a commit the rollback point is the frame entry.
        committed = 0
        ops_after_commit = pre_charges + post_ops
    at_commit = meter_fields(meter)
    regular_after_commit, _, _ = apply_ops(gas, frame, ops_after_commit)
    meter.refund_counter = refund_counter

    gas.restore_state_gas(meter)
    if halt:
        gas.forfeit_remaining_gas(meter)

    expected_gas_left = (
        0 if halt else at_commit.gas_left - regular_after_commit
    )
    assert meter_fields(meter) == at_commit._replace(
        gas_left=expected_gas_left
    )
    assert gas.tx_state_gas_used(meter, Uint(reservoir)) == committed


@pytest.mark.spec_unit
@given(
    gas_left=pools(),
    reservoir=pools(),
    first_charges=op_lists(CHARGES, max_size=6),
    commit=st.booleans(),
    second_charges=op_lists(CHARGES, max_size=6),
)
def test_restore_to_entry_undoes_the_commit(
    gas: ModuleType,
    gas_left: int,
    reservoir: int,
    first_charges: List[MeterOp],
    commit: bool,
    second_charges: List[MeterOp],
) -> None:
    """
    A failure before dispatch refills every state charge, committed or
    not, so only the regular charges stay paid.
    """
    frame = fresh_frame(gas, gas_left, reservoir)
    meter = frame.gas_meter
    regular_first, _, _ = apply_ops(gas, frame, first_charges)
    if commit:
        gas.commit_state_gas(meter)
    regular_second, _, _ = apply_ops(gas, frame, second_charges)

    gas.restore_state_gas_to_entry(meter, Uint(reservoir))

    assert meter_fields(meter) == meter_fields(
        fresh_frame(
            gas, gas_left - regular_first - regular_second, reservoir
        ).gas_meter
    )
    assert gas.tx_state_gas_used(meter, Uint(reservoir)) == 0


@pytest.mark.spec_unit
@given(
    gas_left=pools(),
    reservoir=pools(),
    prefix=op_lists(CHARGES_AND_REFUNDS),
)
def test_restore_child_gas_undoes_withhold_and_drain(
    gas: ModuleType,
    gas_left: int,
    reservoir: int,
    prefix: List[MeterOp],
) -> None:
    """Handing back a child's unused grants restores the parent exactly."""
    frame = fresh_frame(gas, gas_left, reservoir)
    apply_ops(gas, frame, prefix)
    meter = frame.gas_meter
    before = meter_fields(meter)

    child_gas = gas.withhold_create_gas(meter)
    child_reservoir = gas.drain_state_gas_reservoir(meter)
    gas.restore_child_gas(meter, child_gas, child_reservoir)

    assert meter_fields(meter) == before


@pytest.mark.spec_unit
@given(
    gas_left=pools(),
    reservoir=pools(),
    parent_ops=op_lists(CHARGES_AND_REFUNDS, max_size=6),
    grant=pools(),
    child_ops=op_lists(CHARGES_AND_REFUNDS),
    child_refund_counter=st.integers(min_value=-(1 << 20), max_value=1 << 20),
    outcome=st.sampled_from(["success", "revert", "halt"]),
)
def test_child_gas_returns_exactly(
    spec: Hardfork,
    gas: ModuleType,
    gas_left: int,
    reservoir: int,
    parent_ops: List[MeterOp],
    grant: int,
    child_ops: List[MeterOp],
    child_refund_counter: int,
    outcome: str,
) -> None:
    """
    A returning child leaves its parent short by its net charges on
    success, by its regular charges after a revert and by its whole grant
    after a halt. A successful merge leaves no spill the reservoir could
    repay, and the parent settles to the state gas the same operations use
    in one frame.
    """
    parent = fresh_frame(gas, gas_left, reservoir)
    apply_ops(gas, parent, parent_ops)
    before = meter_fields(parent.gas_meter)

    # A call charges the child's grant to the parent and lends the child
    # the whole reservoir.
    child_gas = min(grant, before.gas_left)
    gas.charge_gas(parent, Uint(child_gas))
    gas.drain_state_gas_reservoir(parent.gas_meter)
    child = fresh_frame(gas, child_gas, before.state_gas_left)
    child_applied: List[MeterOp] = []
    regular, state, refunded = apply_ops(gas, child, child_ops, child_applied)
    child.gas_meter.refund_counter = child_refund_counter
    exceptions = spec.module("vm.exceptions")
    if outcome == "revert":
        gas.restore_state_gas(child.gas_meter)
        child.error = exceptions.Revert()
    elif outcome == "halt":
        gas.restore_state_gas(child.gas_meter)
        gas.forfeit_remaining_gas(child.gas_meter)
        child.error = exceptions.OutOfGasError()

    spec.module("vm").incorporate_child(parent, child)

    after = meter_fields(parent.gas_meter)
    if outcome == "success":
        held = before.gas_left + before.state_gas_left
        assert after.gas_left + after.state_gas_left == (
            held - regular - (state - refunded)
        )
        assert after.state_gas_left == 0 or after.state_gas_spilled == 0
        assert after.refund_counter == (
            before.refund_counter + child_refund_counter
        )
        assert after.state_gas_baseline == before.state_gas_baseline
    else:
        spent = regular if outcome == "revert" else child_gas
        assert after == before._replace(gas_left=before.gas_left - spent)

    # A rolled-back child leaves no state gas used behind it.
    one_frame = fresh_frame(gas, gas_left, reservoir)
    apply_ops(gas, one_frame, parent_ops)
    if outcome == "success":
        replayed = apply_ops(gas, one_frame, child_applied)
        assert replayed == (regular, state, refunded)
    assert gas.tx_state_gas_used(parent.gas_meter, Uint(reservoir)) == (
        gas.tx_state_gas_used(one_frame.gas_meter, Uint(reservoir))
    )


class ReservoirModel:
    """
    Reference model of the two pools, following the EIP-8037 charge and
    refund rules and the `commit_state_gas` docstring.
    """

    def __init__(self, gas_left: int, reservoir: int) -> None:
        self.gas_left = gas_left
        self.reservoir = reservoir
        self.spilled = 0
        self.committed_spill = 0
        self.baseline = reservoir
        self.refund_counter = 0
        self.net_state = 0

    def charge_regular(self, amount: int) -> None:
        """Take a regular charge from `gas_left` only."""
        self.gas_left -= amount

    def charge_state(self, amount: int) -> None:
        """Take from the reservoir first and spill the rest."""
        from_reservoir = min(amount, self.reservoir)
        remainder = amount - from_reservoir
        self.reservoir -= from_reservoir
        self.gas_left -= remainder
        self.spilled += remainder
        self.net_state += amount

    def credit_refund(self, amount: int) -> None:
        """Credit `gas_left` up to the spill, then the reservoir."""
        from_gas_left = min(amount, self.spilled)
        self.gas_left += from_gas_left
        self.spilled -= from_gas_left
        self.reservoir += amount - from_gas_left
        self.net_state -= amount

    def commit(self) -> None:
        """Make the spill permanent and move the baseline down."""
        self.committed_spill += self.spilled
        self.spilled = 0
        self.baseline = self.reservoir

    def fields(self) -> MeterFields:
        """Return the model in the same shape as `meter_fields`."""
        return MeterFields(
            gas_left=self.gas_left,
            state_gas_left=self.reservoir,
            state_gas_baseline=self.baseline,
            refund_counter=self.refund_counter,
            state_gas_spilled=self.spilled,
            state_gas_committed_spill=self.committed_spill,
        )


class GasMeterMachine(RuleBasedStateMachine):
    """
    Drive a frame's `GasMeter` against `ReservoirModel` in the order real
    callers use: charges and at most one commit, then dispatch, after which
    refunds and refund counter changes may happen.
    """

    gas: ModuleType
    model: ReservoirModel

    @initialize(gas_left=pools(), reservoir=pools())
    def start_frame(self, gas_left: int, reservoir: int) -> None:
        """Enter a frame."""
        self.frame = fresh_frame(self.gas, gas_left, reservoir)
        self.model = ReservoirModel(gas_left, reservoir)
        self.grant_gas = gas_left
        self.grant_state = reservoir
        self.regular_total = 0
        self.dispatched = False
        self.committed = False

    @rule(data=st.data())
    def charge_regular(self, data: st.DataObject) -> None:
        """Make an affordable regular charge."""
        available = self.model.gas_left
        amount = data.draw(
            st.one_of(
                st.sampled_from(sorted({0, available})),
                st.integers(min_value=0, max_value=available),
            )
        )
        self.gas.charge_gas(self.frame, Uint(amount))
        self.model.charge_regular(amount)
        self.regular_total += amount

    @rule(data=st.data())
    def charge_state(self, data: st.DataObject) -> None:
        """
        Make an affordable state charge, often exactly at the reservoir,
        one past it, or the two pools combined.
        """
        available = self.model.gas_left + self.model.reservoir
        edges = {
            0,
            available,
            min(self.model.reservoir, available),
            min(self.model.reservoir + 1, available),
        }
        amount = data.draw(
            st.one_of(
                st.sampled_from(sorted(edges)),
                st.integers(min_value=0, max_value=available),
            )
        )
        self.gas.charge_state_gas(self.frame, Uint(amount))
        self.model.charge_state(amount)

    @rule(data=st.data())
    def check_regular(self, data: st.DataObject) -> None:
        """
        A regular gas check passes exactly when `gas_left` covers it,
        whatever the reservoir holds, and changes nothing.
        """
        gas_left = self.model.gas_left
        reservoir = self.model.reservoir
        amount = data.draw(
            st.one_of(
                st.sampled_from(
                    sorted({0, gas_left, gas_left + 1, gas_left + reservoir})
                ),
                st.integers(min_value=0, max_value=gas_left + reservoir + 1),
            )
        )
        if amount > gas_left:
            with pytest.raises(self.gas.OutOfGasError):
                self.gas.check_gas(self.frame, Uint(amount))
        else:
            self.gas.check_gas(self.frame, Uint(amount))

    @rule(excess=amounts())
    def overcharge_regular(self, excess: int) -> None:
        """An unaffordable regular charge raises and changes nothing."""
        amount = self.model.gas_left + 1 + excess
        with pytest.raises(self.gas.OutOfGasError):
            self.gas.charge_gas(self.frame, Uint(amount))

    @rule(excess=amounts())
    def overcharge_state(self, excess: int) -> None:
        """An unaffordable state charge raises and changes nothing."""
        amount = self.model.gas_left + self.model.reservoir + 1 + excess
        with pytest.raises(self.gas.OutOfGasError):
            self.gas.charge_state_gas(self.frame, Uint(amount))

    @precondition(lambda self: not self.dispatched and not self.committed)
    @rule()
    def commit(self) -> None:
        """Commit once before dispatch, as the top frame does."""
        self.gas.commit_state_gas(self.frame.gas_meter)
        self.model.commit()
        self.committed = True

    @precondition(lambda self: not self.dispatched)
    @rule()
    def dispatch(self) -> None:
        """Start running the frame's code."""
        self.dispatched = True

    @precondition(lambda self: self.dispatched)
    @rule(data=st.data())
    def credit_refund(self, data: st.DataObject) -> None:
        """
        Credit a refund, often at or next to the current spill. A refund
        may exceed the frame's own charges.
        """
        spilled = self.model.spilled
        edges = sorted({0, spilled, spilled + 1, max(spilled - 1, 0)})
        amount = data.draw(
            st.one_of(
                st.sampled_from(edges),
                st.integers(min_value=0, max_value=AMOUNT_BOUND),
            )
        )
        self.gas.credit_state_gas_refund(self.frame.gas_meter, Uint(amount))
        self.model.credit_refund(amount)

    @precondition(lambda self: self.dispatched)
    @rule(delta=st.integers(min_value=-(1 << 16), max_value=1 << 16))
    def bump_refund_counter(self, delta: int) -> None:
        """Change the refund counter, as `SSTORE` does."""
        self.frame.gas_meter.refund_counter += delta
        self.model.refund_counter += delta

    @invariant()
    def meter_matches_model(self) -> None:
        """Every meter field agrees with the model."""
        assert meter_fields(self.frame.gas_meter) == self.model.fields()

    @invariant()
    def settlement_matches_net_state_gas(self) -> None:
        """`tx_state_gas_used` is state charges minus state refunds."""
        assert (
            self.gas.tx_state_gas_used(
                self.frame.gas_meter, Uint(self.grant_state)
            )
            == self.model.net_state
        )

    @invariant()
    def regular_gas_never_drifts(self) -> None:
        """
        The frame's regular gas always splits into `gas_left`, the spill
        and the regular charges, so none leaks into the reservoir.
        """
        meter = self.frame.gas_meter
        assert (
            int(meter.gas_left)
            + int(meter.state_gas_spilled)
            + int(meter.state_gas_committed_spill)
            + self.regular_total
            == self.grant_gas
        )


@pytest.mark.spec_unit
def test_gas_meter_matches_model(gas: ModuleType) -> None:
    """The gas meter agrees with the reference model on every sequence."""
    machine = type("GasMeterMachine", (GasMeterMachine,), {"gas": gas})
    run_state_machine_as_test(
        machine, settings=settings(stateful_step_count=40)
    )
