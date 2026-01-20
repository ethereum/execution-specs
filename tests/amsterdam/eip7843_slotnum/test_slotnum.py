"""Tests for EIP-7843 (SLOTNUM)."""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Environment,
    Fork,
    Op,
    StateTestFiller,
    Transaction,
)

from .spec import ref_spec_7843

REFERENCE_SPEC_GIT_PATH = ref_spec_7843.git_path
REFERENCE_SPEC_VERSION = ref_spec_7843.version

pytestmark = pytest.mark.valid_from("Amsterdam")


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
    slot_number: int,
) -> None:
    """
    Test that SLOTNUM opcode returns the correct slot number.

    The slot number is provided by the consensus layer and should be
    accessible via the SLOTNUM opcode (0x4B).
    """
    # Store SLOTNUM result at storage key 0
    code = Op.SSTORE(0, Op.SLOTNUM)
    code_address = pre.deploy_contract(code)

    tx = Transaction(
        sender=pre.fund_eoa(),
        gas_limit=100_000,
        to=code_address,
    )

    post = {
        code_address: Account(
            storage={0: slot_number},
        ),
    }

    state_test(
        env=Environment(slot_number=slot_number),
        pre=pre,
        tx=tx,
        post=post,
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

    # Caller calls the callee with limited gas and stores result
    caller_code = Op.SSTORE(0, Op.CALL(gas=call_gas, address=callee_address))
    caller_address = pre.deploy_contract(caller_code)

    tx = Transaction(
        sender=pre.fund_eoa(),
        gas_limit=100_000,
        to=caller_address,
    )

    post = {
        caller_address: Account(
            storage={0: 1 if call_succeeds else 0},
        ),
    }

    state_test(
        env=Environment(slot_number=12345),
        pre=pre,
        tx=tx,
        post=post,
    )
