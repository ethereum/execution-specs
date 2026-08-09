"""
Tests for [EIP-8038: State Access Gas Cost Increase](https://eips.ethereum.org/EIPS/eip-8038).

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
    Bytecode,
    CodeGasMeasure,
    Fork,
    Op,
    StateTestFiller,
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
SSTORE_ROWS = [
    pytest.param(False, 0, 0, 1, id="00x_cold"),
    pytest.param(True, 0, 0, 1, id="00x_warm"),
    pytest.param(True, 0, 1, 0, id="0x0_dirty"),
    pytest.param(True, 1, 1, 0, id="xx0_warm"),
    pytest.param(False, 1, 1, 2, id="xxy_cold"),
    pytest.param(True, 1, 1, 2, id="xxy_warm"),
    pytest.param(True, 1, 2, 3, id="xyz_dirty"),
    pytest.param(True, 1, 2, 1, id="xyx_dirty"),
    pytest.param(True, 1, 1, 1, id="xxx_warm"),
    pytest.param(False, 1, 1, 1, id="xxx_cold"),
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
