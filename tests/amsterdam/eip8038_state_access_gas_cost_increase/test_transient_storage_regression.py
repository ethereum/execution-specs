"""
Tests for [EIP-8038: State Access Gas Cost Increase](https://eips.ethereum.org/EIPS/eip-8038).

Regression guard: EIP-8038 reprices persistent storage and account
access but must NOT touch transient storage. ``TLOAD`` and ``TSTORE``
remain at their EIP-1153 cost of ``OPCODE_TLOAD`` / ``OPCODE_TSTORE``
(100 each), unchanged by the persistent-storage repricing and distinct
from the (repriced) persistent ``COLD_STORAGE_WRITE``.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
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


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
def test_transient_storage_gas_unchanged(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Measure ``TLOAD`` and ``TSTORE`` gas and confirm EIP-8038 left them
    at the transient-storage price of 100 each.

    The bare-opcode costs (excluding their PUSH wrappers) must equal
    ``OPCODE_TLOAD`` / ``OPCODE_TSTORE``. The guard
    ``OPCODE_TSTORE != COLD_STORAGE_WRITE`` ensures the persistent
    write repricing did not bleed into transient storage.
    """
    gas_costs = fork.gas_costs()
    # Guard against over-eager repricing: the transient write must not
    # have been folded into the (repriced) persistent cold write cost.
    assert gas_costs.OPCODE_TSTORE != gas_costs.COLD_STORAGE_WRITE

    # Measure TSTORE then TLOAD of the same transient slot in one frame,
    # subtracting the PUSH wrapper so the stored value is the bare opcode
    # cost.
    push_cost = Op.PUSH1(0).execution_cost(fork)
    tstore_code = CodeGasMeasure(
        code=Op.TSTORE(0, 1),
        overhead_cost=2 * push_cost,
        extra_stack_items=0,
        sstore_key=0,
    )
    tload_code = CodeGasMeasure(
        code=Op.TLOAD(0),
        overhead_cost=1 * push_cost,
        extra_stack_items=1,
        sstore_key=1,
    )
    contract = pre.deploy_contract(code=tstore_code + tload_code)

    tx = Transaction(to=contract, sender=pre.fund_eoa())

    # Slot 0: measured TSTORE cost. Slot 1: measured TLOAD cost. Both must
    # equal the fork's declared transient-storage opcode costs, which
    # EIP-8038 leaves unchanged.
    post = {
        contract: Account(
            storage={
                0: gas_costs.OPCODE_TSTORE,
                1: gas_costs.OPCODE_TLOAD,
            }
        )
    }
    state_test(env=env, pre=pre, post=post, tx=tx)
