"""Test the CALL opcode after EIP-2929."""

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

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-2929.md"
REFERENCE_SPEC_VERSION = "0e11417265a623adb680c527b15d0cb6701b870b"


@pytest.mark.valid_from("Berlin")
def test_call_insufficient_balance(
    state_test: StateTestFiller, pre: Alloc, env: Environment, fork: Fork
) -> None:
    """
    Test a regular CALL to see if it warms the destination with insufficient
    balance.
    """
    destination = pre.fund_eoa(1)
    warm_code = Op.BALANCE(destination, address_warm=True)
    contract_address = pre.deploy_contract(
        # Perform the aborted external calls
        Op.SSTORE(
            0,
            Op.CALL(
                gas=Op.GAS,
                address=destination,
                value=1,
                args_offset=0,
                args_size=0,
                ret_offset=0,
                ret_size=0,
            ),
        )
        # Measure the gas cost for BALANCE operation
        + CodeGasMeasure(
            code=warm_code,
            extra_stack_items=1,  # BALANCE puts balance on stack
            sstore_key=1,
        ),
        balance=0,
    )

    tx = Transaction(
        to=contract_address,
        gas_limit=100_000,
        sender=pre.fund_eoa(),
    )

    post = {
        destination: Account(
            balance=1,
        ),
        contract_address: Account(
            storage={
                0: 0,  # The CALL is aborted
                1: warm_code.gas_cost(fork),
            },
        ),
    }
    state_test(env=env, pre=pre, post=post, tx=tx)
