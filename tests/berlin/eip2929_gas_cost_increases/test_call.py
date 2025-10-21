"""Test the CALL opcode after EIP-2929."""

import pytest
from ethereum_test_forks import Fork
from ethereum_test_tools import (
    Account,
    Alloc,
    CodeGasMeasure,
    Environment,
    StateTestFiller,
    Transaction,
)
from ethereum_test_vm import Opcodes as Op

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
    gas_costs = fork.gas_costs()
    destination = pre.fund_eoa(1)
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
            code=Op.BALANCE(destination),
            overhead_cost=gas_costs.G_VERY_LOW,  # PUSH20 costs 3 gas
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
                1: gas_costs.G_WARM_ACCOUNT_ACCESS,  # Warm access cost
            },
        ),
    }
    state_test(env=env, pre=pre, post=post, tx=tx)
