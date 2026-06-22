"""
Tests for [EIP-8038: State Access Gas Cost Increase](https://eips.ethereum.org/EIPS/eip-8038).

Covers the EIP-8038 ``SSTORE`` *regular* (non-state) gas schedule. The
state-creation charge for a zero-to-nonzero write is owned by EIP-8037
and is asserted separately; here every expectation is taken from the
``regular_cost`` dimension only.

The regular ``SSTORE`` cost is the slot-access cost (``COLD_STORAGE_ACCESS``
when the key is cold, else ``WARM_SLOAD``) plus, on the first change of the
slot in the transaction (``original == current != new``), the write cost
``STORAGE_WRITE`` (modeled as ``COLD_STORAGE_WRITE - COLD_STORAGE_ACCESS``).
"""

import pytest
from execution_testing import (
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

from .helpers import opcode_overhead
from .spec import ref_spec_8038

REFERENCE_SPEC_GIT_PATH = ref_spec_8038.git_path
REFERENCE_SPEC_VERSION = ref_spec_8038.version

pytestmark = pytest.mark.valid_from("Amsterdam")


# Each parameter: (key_warm, original, current, new). ``current`` differs
# from ``original`` only when a prior in-frame SSTORE moves the slot there.
SSTORE_ROWS = [
    pytest.param(False, 0, 0, 1, id="00x_cold"),
    pytest.param(True, 0, 0, 1, id="00x_warm"),
    pytest.param(True, 0, 1, 0, id="0x0"),
    pytest.param(True, 1, 1, 0, id="xx0"),
    pytest.param(False, 1, 1, 2, id="xxy_cold"),
    pytest.param(True, 1, 1, 2, id="xxy_warm"),
    pytest.param(True, 1, 2, 3, id="xyz"),
    pytest.param(True, 1, 2, 1, id="xyx"),
    pytest.param(True, 1, 1, 1, id="xxx"),
    pytest.param(False, 1, 1, 1, id="xxx_cold"),
]


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.parametrize("key_warm,original,current,new", SSTORE_ROWS)
def test_sstore_regular_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    key_warm: bool,
    original: int,
    current: int,
    new: int,
) -> None:
    """
    Assert the regular ``SSTORE`` gas for each EIP-8038 row.

    The expectation is derived purely from ``gas_costs`` (slot access
    plus write-on-first-change) and cross-checked against the framework
    opcode model's ``regular_cost``. The state-gas dimension is owned by
    EIP-8037 and excluded here.
    """
    gas_costs = fork.gas_costs()
    very_low = gas_costs.VERY_LOW

    # EIP-8038 regular formula: slot access, plus the write cost on the
    # first change of the slot (original == current != new).
    access_cost = (
        gas_costs.WARM_SLOAD if key_warm else gas_costs.COLD_STORAGE_ACCESS
    )
    storage_write = (
        gas_costs.COLD_STORAGE_WRITE - gas_costs.COLD_STORAGE_ACCESS
    )
    write_cost = (
        storage_write if (original == current and current != new) else 0
    )
    expected_regular = access_cost + write_cost

    # Bare opcode regular cost = with-metadata regular cost minus the two
    # PUSH wrappers (key, value). Cross-check the oracle agrees.
    metered = Op.SSTORE.with_metadata(
        key_warm=key_warm,
        original_value=original,
        current_value=current,
        new_value=new,
    )(0, new)
    bare_regular = metered.regular_cost(fork) - 2 * very_low
    assert bare_regular == expected_regular

    # Build a contract that reaches ``current`` from ``original`` (a prior
    # SSTORE when they differ), then performs the measured write to
    # ``new``. The access list is left empty so the first touch is cold;
    # the warm rows rely on the prior SSTORE having warmed the slot.
    slot = 0
    code = Bytecode()
    if current != original:
        # Move original -> current first; this also warms the slot.
        code += Op.SSTORE(slot, current)
    code += Op.SSTORE(slot, new)

    contract = pre.deploy_contract(
        code=code,
        storage={slot: original} if original != 0 else {},
    )

    # State gas (owned by EIP-8037) is sourced from the reservoir so it
    # never disturbs the regular-gas accounting this test isolates. Size
    # it to cover up to two zero-to-nonzero sets (prep + measured),
    # derived from the fork rather than hardcoded.
    single_set_state_gas = Op.SSTORE(new_value=1).state_cost(fork)
    tx = Transaction(
        to=contract,
        sender=pre.fund_eoa(),
        state_gas_reservoir=2 * single_set_state_gas,
        gas_limit=1_000_000,
    )

    post = {contract: Account(storage={slot: new})}
    state_test(pre=pre, post=post, tx=tx)


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
def test_sstore_cold_then_warm_same_slot(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    A first ``SSTORE`` on a cold slot warms it; the second in-frame
    ``SSTORE`` of the same slot is charged only ``WARM_SLOAD`` (100).

    The slot starts non-zero (original 1) and is left unlisted, so the
    first write is cold and is its first change (original == current !=
    new), costing ``COLD_STORAGE_ACCESS + STORAGE_WRITE`` (3000 + 10000).
    That write warms the slot, so the second write -- which moves the slot
    again without being a first change -- costs only ``WARM_SLOAD`` (100),
    with no further ``STORAGE_WRITE``. Slot 0 records the cold first write
    and slot 1 the warm second write; the data slot keeps its final value.
    """
    data_slot = 0x42

    # First write: cold, first change of a non-zero-original slot. The
    # bare (operand-free) opcode carries the same metadata so that
    # ``opcode_overhead`` resolves to just the two operand PUSHes.
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

    expected_first = first.regular_cost(fork) - 2 * fork.gas_costs().VERY_LOW
    expected_second = second.regular_cost(fork) - 2 * fork.gas_costs().VERY_LOW

    # Each measured write stores its own runtime cost; ``opcode_overhead``
    # strips the two operand PUSHes so the stored value is the bare SSTORE
    # cost. The first block must not STOP so the (now warm) second runs.
    code = CodeGasMeasure(
        code=first,
        overhead_cost=opcode_overhead(first, first_bare, fork),
        extra_stack_items=0,
        sstore_key=0,
        stop=False,
    ) + CodeGasMeasure(
        code=second,
        overhead_cost=opcode_overhead(second, second_bare, fork),
        extra_stack_items=0,
        sstore_key=1,
    )

    contract = pre.deploy_contract(code=code, storage={data_slot: 1})

    tx = Transaction(
        to=contract,
        sender=pre.fund_eoa(),
        gas_limit=1_000_000,
    )

    # Slots 0/1 hold the two measured writes; the data slot ends at its
    # final written value.
    post = {
        contract: Account(
            storage={0: expected_first, 1: expected_second, data_slot: 3}
        )
    }
    state_test(pre=pre, post=post, tx=tx)
