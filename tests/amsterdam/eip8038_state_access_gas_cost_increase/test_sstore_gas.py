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
