"""
Tests for [EIP-8038: State-access gas cost update](https://eips.ethereum.org/EIPS/eip-8038).

Covers the EIP-8038 ``SSTORE`` *execution* (non-state) gas schedule. The
state-creation charge for a zero-to-nonzero write is owned by EIP-8037
and is asserted separately; here every expectation is taken from the
``execution_cost`` dimension only.

The execution ``SSTORE`` cost is the slot-access cost (``COLD_STORAGE_ACCESS``
when the key is cold, else ``WARM_SLOAD``) plus, on the first change of the
slot in the transaction (``original == current != new``), the write cost
``STORAGE_WRITE`` (modeled as ``COLD_STORAGE_WRITE - COLD_STORAGE_ACCESS``).
"""

import pytest
from execution_testing import (
    AccessList,
    Account,
    Alloc,
    BalAccountExpectation,
    BlockAccessListExpectation,
    Bytecode,
    CodeGasMeasure,
    Fork,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
)
from execution_testing.checklists import EIPChecklist

from .spec import ref_spec_8038

REFERENCE_SPEC_GIT_PATH = ref_spec_8038.git_path
REFERENCE_SPEC_VERSION = ref_spec_8038.version

pytestmark = pytest.mark.valid_from("Amsterdam")


# Each parameter: (key_warm, original, current, new). The id encodes the
# (original, current, new) triple, where ``0`` is the zero value and
# ``x``/``y``/``z`` are distinct non-zero values (1, 2, 3). The suffix marks
# the slot state at the measured write. A clean slot (current == original)
# is ``_cold`` or access-list ``_warm``; a dirty slot (current != original)
# is ``_dirty`` and has necessarily been warmed by the prior in-frame SSTORE.
# No-op writes (new == current) have no row in the EIP's cases table; their
# access-only cost falls out of the three-component formula and is pinned
# here alongside the listed rows.
SSTORE_ROWS = [
    pytest.param(False, 0, 0, 1, id="00x_cold"),
    pytest.param(True, 0, 0, 1, id="00x_warm"),
    pytest.param(True, 0, 1, 0, id="0x0_dirty"),
    pytest.param(True, 0, 1, 2, id="0xy_dirty"),
    pytest.param(False, 1, 1, 0, id="xx0_cold"),
    pytest.param(True, 1, 1, 0, id="xx0_warm"),
    pytest.param(False, 1, 1, 2, id="xxy_cold"),
    pytest.param(True, 1, 1, 2, id="xxy_warm"),
    pytest.param(True, 1, 2, 3, id="xyz_dirty"),
    pytest.param(True, 1, 2, 1, id="xyx_dirty"),
    pytest.param(True, 1, 2, 0, id="xy0_dirty"),
    pytest.param(True, 1, 0, 1, id="x0x_dirty"),
    pytest.param(True, 1, 0, 2, id="x0y_dirty"),
    pytest.param(True, 1, 0, 0, id="x00_dirty"),
    pytest.param(True, 1, 1, 1, id="xxx_warm"),
    pytest.param(False, 1, 1, 1, id="xxx_cold"),
    pytest.param(False, 0, 0, 0, id="000_cold"),
    pytest.param(True, 0, 0, 0, id="000_warm"),
    pytest.param(True, 0, 1, 1, id="0xx_dirty"),
    pytest.param(True, 1, 2, 2, id="xyy_dirty"),
]


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.parametrize("key_warm,original,current,new", SSTORE_ROWS)
def test_sstore_execution_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    key_warm: bool,
    original: int,
    current: int,
    new: int,
) -> None:
    """
    Measure the execution ``SSTORE`` gas for each EIP-8038 row and assert it.

    The final (measured) ``SSTORE`` is wrapped in ``CodeGasMeasure`` so the
    executed execution cost is stored on-chain and asserted against
    ``expected_execution`` (slot access plus write-on-first-change). The same
    value is cross-checked against the framework opcode model's
    ``execution_cost`` as a secondary guard. The state-gas dimension is owned
    by EIP-8037 and funded from the reservoir, so it is excluded here.
    """
    # Move the data off slot 0 so ``CodeGasMeasure`` can store the measured
    # cost in slot 0. The bare (operand-free) opcode carries the metadata so
    # the measure overhead resolves to just the two operand PUSHes, and
    # ``execution_cost``/``gas_cost`` are exact.
    data_slot = 0x42
    result_slot = 0
    measured_bare = Op.SSTORE.with_metadata(
        key_warm=key_warm,
        original_value=original,
        current_value=current,
        new_value=new,
    )
    measured = measured_bare(data_slot, new)

    # Cross-check the oracle agrees with the hand-derived formula.
    expected_execution = measured_bare.execution_cost(fork)

    # Reach ``current`` from ``original`` with an unmeasured prep SSTORE when
    # they differ, then measure the write to ``new``. The slot is warmed for
    # ``key_warm`` rows via the access list (and, where current != original,
    # the prep SSTORE warms it too); cold rows have neither, so the measured
    # write is cold.
    code = Bytecode()
    if current != original:
        code += Op.SSTORE(data_slot, current)
    code += CodeGasMeasure(
        code=measured,
        overhead_cost=measured.gas_cost(fork) - measured_bare.gas_cost(fork),
        extra_stack_items=0,
        sstore_key=result_slot,
    )

    contract = pre.deploy_contract(
        code=code,
        storage={data_slot: original} if original != 0 else {},
    )

    # Warm the slot for ``key_warm`` rows that have no prep to warm it;
    # harmless for prep rows (warmth is set membership). Built after
    # ``deploy_contract`` so the address exists.
    access_list = (
        [AccessList(address=contract, storage_keys=[data_slot])]
        if key_warm
        else None
    )

    # State gas (owned by EIP-8037) is funded from the reservoir so it never
    # disturbs the execution gas this test isolates. ``gas_limit`` is left
    # unset so the reservoir lands above the EIP-7825 cap and ``Op.GAS``
    # measures execution gas only; an explicit gas_limit below the cap would
    # zero the reservoir and spill state gas into the measurement.
    single_set_state_gas = Op.SSTORE(new_value=1).state_cost(fork)
    tx = Transaction(
        to=contract,
        sender=pre.fund_eoa(),
        access_list=access_list,
        state_gas_reservoir=2 * single_set_state_gas,
    )

    # result_slot holds the measured execution cost; data_slot holds ``new``
    # (absent when new == 0, because the slot is cleared).
    expected_storage = {result_slot: expected_execution}
    if new != 0:
        expected_storage[data_slot] = new
    post = {contract: Account(storage=expected_storage)}
    state_test(pre=pre, post=post, tx=tx)


@EIPChecklist.GasCostChanges.Test.OutOfGas()
@pytest.mark.parametrize("key_warm", [False, True], ids=["cold", "warm"])
@pytest.mark.parametrize(
    "sufficient_gas", [True, False], ids=["sufficient", "insufficient"]
)
def test_sstore_stipend_sentry_boundary(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    key_warm: bool,
    sufficient_gas: bool,
) -> None:
    """
    The EIP-2200 stipend sentry, not the slot's access cost, sets the
    minimum gas an ``SSTORE`` needs.

    The measured write is a *no-op* (``new == current``), so it is
    charged the access cost alone and nothing else, ``WARM_ACCESS`` or
    ``COLD_STORAGE_ACCESS``, both under ``CALL_STIPEND``. The sentry
    nevertheless demands
    more than the stipend before any state is touched, so the boundary
    sits at ``CALL_STIPEND + 1`` in both warmths rather than at the
    cost actually charged. Pinning both warmths shows the floor does not
    move with the access cost.
    """
    slot = 0x42

    # No-op write: original == current == new, so only the access cost is
    # charged and no state gas or refund arises.
    sstore_noop = Op.SSTORE.with_metadata(
        key_warm=key_warm, original_value=1, current_value=1, new_value=1
    )
    child_code = sstore_noop(slot, 1)
    child = pre.deploy_contract(code=child_code, storage={slot: 1})

    # Everything the child spends before reaching the SSTORE itself.
    operand_pushes = child_code.execution_cost(
        fork
    ) - sstore_noop.execution_cost(fork)

    # The sentry requires strictly more than the stipend to remain, so
    # the child needs its pushes plus CALL_STIPEND + 1 — regardless of
    # the access cost it will actually be charged.
    forwarded = operand_pushes + fork.call_value_stipend()
    if sufficient_gas:
        forwarded += 1

    storage = Storage()
    caller_code = Op.SSTORE(
        storage.store_next(1 if sufficient_gas else 0, "sstore_result"),
        Op.CALL(gas=forwarded, address=child),
    )
    caller = pre.deploy_contract(code=caller_code)

    tx = Transaction(
        to=caller,
        sender=pre.fund_eoa(),
        access_list=[AccessList(address=child, storage_keys=[slot])]
        if key_warm
        else None,
        state_gas_reservoir=0,
    )

    # The no-op leaves the slot at its original value either way, so the
    # CALL's success flag is what separates the two arms.
    post = {
        caller: Account(storage=storage),
        child: Account(storage={slot: 1}),
    }
    state_test(
        pre=pre,
        post=post,
        tx=tx,
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                child: BalAccountExpectation(
                    storage_reads=[slot] if sufficient_gas else [],
                    storage_changes=[],
                )
            }
        ),
    )


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
def test_sstore_cold_then_warm_same_slot(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    A first ``SSTORE`` on a cold slot warms it; the second in-frame
    ``SSTORE`` of the same slot is charged only ``WARM_SLOAD``.

    The slot starts non-zero (original 1) and is left unlisted, so the
    first write is cold and is its first change (original == current !=
    new), costing ``COLD_STORAGE_ACCESS + STORAGE_WRITE``.
    That write warms the slot, so the second write -- which moves the slot
    again without being a first change -- costs only ``WARM_SLOAD``,
    with no further ``STORAGE_WRITE``. Slot 0 records the cold first write
    and slot 1 the warm second write; the data slot keeps its final value.
    """
    data_slot = 0x42

    # First write: cold, first change of a non-zero-original slot. The
    # bare (operand-free) opcode carries the same metadata so that the
    # CodeGasMeasure overhead resolves to just the two operand PUSHes.
    first_bare = Op.SSTORE.with_metadata(
        key_warm=False,
        original_value=1,
        current_value=1,
        new_value=2,
    )
    first = first_bare(data_slot, 2)
    # Second write: same slot, now warm; not a first change, so the
    # write cost is not re-charged and only the warm access applies.
    second_bare = Op.SSTORE.with_metadata(
        key_warm=True,
        original_value=1,
        current_value=2,
        new_value=3,
    )
    second = second_bare(data_slot, 3)

    expected_first = first_bare.execution_cost(fork)
    expected_second = second_bare.execution_cost(fork)

    # Each measured write stores its own runtime cost; the overhead
    # subtraction strips the two operand PUSHes so the stored value is the
    # bare SSTORE cost. The second write finds the slot warm.
    code = CodeGasMeasure(
        code=first,
        overhead_cost=first.gas_cost(fork) - first_bare.gas_cost(fork),
        extra_stack_items=0,
        sstore_key=0,
    ) + CodeGasMeasure(
        code=second,
        overhead_cost=second.gas_cost(fork) - second_bare.gas_cost(fork),
        extra_stack_items=0,
        sstore_key=1,
    )

    contract = pre.deploy_contract(code=code, storage={data_slot: 1})

    tx = Transaction(to=contract, sender=pre.fund_eoa())

    # Slots 0/1 hold the two measured writes; the data slot ends at its
    # final written value.
    post = {
        contract: Account(
            storage={0: expected_first, 1: expected_second, data_slot: 3}
        )
    }
    state_test(pre=pre, post=post, tx=tx)
