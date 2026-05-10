"""Tests for EIP-7843 (SLOTNUM)."""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Environment,
    Fork,
    Header,
    Op,
    StateTestFiller,
    Transaction,
)

from .spec import ref_spec_7843

REFERENCE_SPEC_GIT_PATH = ref_spec_7843.git_path
REFERENCE_SPEC_VERSION = ref_spec_7843.version

pytestmark = pytest.mark.valid_from("EIP7843")


@pytest.mark.parametrize(
    "slot_number",
    [
        pytest.param(0, id="slot_zero"),
        pytest.param(1, id="slot_one"),
        pytest.param(0x1000, id="slot_4096"),
        pytest.param(2**32, id="slot_large"),
        pytest.param(2**64 - 1, id="slot_max_u64"),
    ],
)
def test_slotnum_value(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    slot_number: int,
) -> None:
    """
    Test that SLOTNUM opcode returns the correct slot number.

    The slot number is provided by the consensus layer and should be
    accessible via the SLOTNUM opcode (0x4B).
    """
    # Store SLOTNUM result at storage key 0. Metadata pins the
    # storage transition (0->slot_number) so `code.gas_cost(fork)`
    # picks the right SSTORE branch under EIP-8037's 2D gas model.
    code = Op.SSTORE(
        key=0,
        value=Op.SLOTNUM,
        key_warm=False,
        original_value=0,
        new_value=slot_number,
    )
    code_address = pre.deploy_contract(code)

    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()()
    code_state = code.state_cost(fork)
    code_regular = code.gas_cost(fork) - code_state

    tx = Transaction(
        sender=pre.fund_eoa(),
        gas_limit=intrinsic_cost + code_regular + code_state,
        to=code_address,
    )

    # block.gas_used = max(regular_dimension, state_dimension).
    expected_gas_used = max(intrinsic_cost + code_regular, code_state)

    state_test(
        env=Environment(slot_number=slot_number),
        pre=pre,
        tx=tx,
        post={code_address: Account(storage={0: slot_number})},
        blockchain_test_header_verify=Header(gas_used=expected_gas_used),
    )


@pytest.mark.parametrize(
    "gas_delta,call_succeeds",
    [
        pytest.param(0, True, id="enough_gas"),
        pytest.param(-1, False, id="out_of_gas"),
    ],
)
def test_slotnum_gas_cost(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_delta: int,
    call_succeeds: bool,
) -> None:
    """
    Test that SLOTNUM opcode costs exactly 2 gas (G_BASE).
    """
    slotnum_gas = Op.SLOTNUM.gas_cost(fork)
    call_gas = slotnum_gas + gas_delta

    # Callee just executes SLOTNUM
    callee_code = Op.SLOTNUM + Op.STOP
    callee_address = pre.deterministic_deploy_contract(deploy_code=callee_code)

    # Caller calls the callee with `call_gas`; SSTOREs the call's
    # success bit (1 if SLOTNUM had enough gas, 0 if it OOG'd).
    sstore_value = 1 if call_succeeds else 0
    caller_code = Op.SSTORE(
        key=0,
        value=Op.CALL(
            gas=call_gas,
            address=callee_address,
            address_warm=False,
        ),
        key_warm=False,
        original_value=0,
        new_value=sstore_value,
    )
    caller_address = pre.deploy_contract(caller_code)

    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()()
    code_state = caller_code.state_cost(fork)
    # Static opcode-metadata calc misses the gas burned in the inner
    # CALL frame; add it back. `call_gas` is the full forwarded amount
    # — for `enough_gas` SLOTNUM consumes it all; for `out_of_gas`
    # the OOG burns the entire forwarded budget.
    code_regular = caller_code.gas_cost(fork) - code_state + call_gas

    tx = Transaction(
        sender=pre.fund_eoa(),
        gas_limit=intrinsic_cost + code_regular + code_state,
        to=caller_address,
    )

    expected_gas_used = max(intrinsic_cost + code_regular, code_state)

    state_test(
        env=Environment(slot_number=12345),
        pre=pre,
        tx=tx,
        post={caller_address: Account(storage={0: sstore_value})},
        blockchain_test_header_verify=Header(gas_used=expected_gas_used),
    )
