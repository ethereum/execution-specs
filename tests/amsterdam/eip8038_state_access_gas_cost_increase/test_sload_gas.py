"""
Tests for [EIP-8038: State Access Gas Cost Increase](https://eips.ethereum.org/EIPS/eip-8038).

Covers the EIP-8038 ``SLOAD`` repricing: a cold storage slot read costs
``COLD_STORAGE_ACCESS`` and a warm read costs ``WARM_SLOAD``.
A slot is warmed either by listing it in the transaction access list or by
a prior in-frame access; warmth acquired inside a sub-call that REVERTs is
discarded, so a subsequent read in the outer frame is cold again.
"""

import pytest
from execution_testing import (
    AccessList,
    Account,
    Alloc,
    Bytecode,
    CodeGasMeasure,
    Environment,
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


def _measure_sload(slot: int, fork: Fork) -> CodeGasMeasure:
    """
    Build a ``CodeGasMeasure`` around a single ``SLOAD`` whose stored
    result is the bare opcode cost (the PUSH wrapper is subtracted out).

    The runtime warmth of ``slot`` determines whether the measured value
    lands at ``COLD_STORAGE_ACCESS`` or ``WARM_SLOAD``.
    """
    measured_code = Op.SLOAD(slot)
    # Subtract the SLOAD opcode's own cold cost so only the PUSH wrapper
    # remains as overhead; the runtime access cost is what gets stored.
    overhead_cost = measured_code.gas_cost(fork) - Op.SLOAD(
        key_warm=False
    ).gas_cost(fork)
    return CodeGasMeasure(
        code=measured_code,
        overhead_cost=overhead_cost,
        extra_stack_items=1,
    )


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.parametrize("warm", [False, True], ids=["cold", "warm"])
def test_sload_gas(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    fork: Fork,
    warm: bool,
) -> None:
    """
    Measure the gas of a ``SLOAD`` on a slot that is either cold or
    pre-warmed via the transaction access list.

    A cold read must cost ``COLD_STORAGE_ACCESS``; a warm read must
    cost ``WARM_SLOAD``.
    """
    slot = 0x42
    expected_gas = Op.SLOAD(key_warm=warm).gas_cost(fork)

    measure_address = pre.deploy_contract(
        code=_measure_sload(slot, fork),
        storage={slot: 1},
    )

    # Warm the slot via the access list when required; the cold case
    # leaves it unlisted so its first runtime read is cold.
    access_list = (
        [AccessList(address=measure_address, storage_keys=[slot])]
        if warm
        else None
    )
    tx = Transaction(
        to=measure_address,
        sender=pre.fund_eoa(),
        access_list=access_list,
    )

    # Slot 0 holds the measured gas; the read slot keeps its value.
    post = {measure_address: Account(storage={0: expected_gas, slot: 1})}
    state_test(env=env, pre=pre, post=post, tx=tx)


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
def test_sload_warm_after_prior_touch(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    A first ``SLOAD`` on a cold slot warms it; the second in-frame
    ``SLOAD`` of the same slot is charged ``WARM_SLOAD``.

    Slot 0 records the cold first read and slot 1 the warm second read.
    """
    slot = 0x42
    cold_gas = Op.SLOAD(key_warm=False).gas_cost(fork)
    warm_gas = Op.SLOAD(key_warm=True).gas_cost(fork)

    measured_code = Op.SLOAD(slot)
    overhead_cost = measured_code.gas_cost(fork) - Op.SLOAD(
        key_warm=False
    ).gas_cost(fork)

    # First measure (slot 0): cold read. Second measure (slot 1): the
    # same slot is now warm.
    code = CodeGasMeasure(
        code=measured_code,
        overhead_cost=overhead_cost,
        extra_stack_items=1,
        sstore_key=0,
    ) + CodeGasMeasure(
        code=measured_code,
        overhead_cost=overhead_cost,
        extra_stack_items=1,
        sstore_key=1,
    )
    measure_address = pre.deploy_contract(code=code, storage={slot: 1})

    tx = Transaction(to=measure_address, sender=pre.fund_eoa())

    # Slots 0/1 hold the two measured reads; the read slot keeps its
    # value.
    post = {
        measure_address: Account(storage={0: cold_gas, 1: warm_gas, slot: 1})
    }
    state_test(env=env, pre=pre, post=post, tx=tx)


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
def test_sload_warmth_reverts_on_subcall_revert(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Warmth acquired inside a reverted sub-call does not persist.

    An inner contract ``SLOAD``s the slot via ``DELEGATECALL`` (so the
    warmed ``(address, slot)`` pair belongs to the outer account) then
    ``REVERT``s. Back in the outer frame, that same slot's first
    ``SLOAD`` is cold again and is charged ``COLD_STORAGE_ACCESS``,
    proving the warm-slot set is rolled back on revert.
    """
    slot = 0x42
    cold_gas = Op.SLOAD(key_warm=False).gas_cost(fork)

    # Inner: read the slot (warming it in the delegating account's
    # context) then revert.
    inner = pre.deploy_contract(
        code=Op.SLOAD(slot) + Op.REVERT(0, 0),
    )

    # Outer: DELEGATECALL inner (which reverts), then measure its own
    # first SLOAD of the slot. DELEGATECALL keeps the outer account's
    # storage context, so inner's read warms (outer, slot); the revert
    # discards that warmth, making the measured read cold.
    measured_code = Op.SLOAD(slot)
    overhead_cost = measured_code.gas_cost(fork) - Op.SLOAD(
        key_warm=False
    ).gas_cost(fork)

    outer_code: Bytecode = Op.POP(
        Op.DELEGATECALL(gas=100_000, address=inner)
    ) + CodeGasMeasure(
        code=measured_code,
        overhead_cost=overhead_cost,
        extra_stack_items=1,
    )
    outer = pre.deploy_contract(code=outer_code, storage={slot: 1})

    tx = Transaction(to=outer, sender=pre.fund_eoa())

    # Slot 0 holds the measured (cold) read; the read slot keeps its
    # value.
    post = {outer: Account(storage={0: cold_gas, slot: 1})}
    state_test(env=env, pre=pre, post=post, tx=tx)
