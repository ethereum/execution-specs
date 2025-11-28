"""Tests ecadd/ecmul precompiled contracts gas pricing."""

import pytest
from execution_testing import (
    Account,
    Alloc,
    StateTestFiller,
    Transaction,
)
from execution_testing.base_types.base_types import Address
from execution_testing.forks import Byzantium
from execution_testing.forks.helpers import Fork
from execution_testing.vm import Opcodes as Op

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-196.md"
REFERENCE_SPEC_VERSION = "6538d198b1db10784ddccd6931888d7ae718de75"

EC_ADD_ADDRESS = Address(0x06)
EC_MUL_ADDRESS = Address(0x07)


@pytest.mark.valid_from("Byzantium")
@pytest.mark.parametrize(
    "address",
    [
        pytest.param(EC_ADD_ADDRESS, id="ecadd"),
        pytest.param(EC_MUL_ADDRESS, id="ecmul"),
    ],
)
@pytest.mark.parametrize("enough_gas", [True, False])
def test_gas_costs(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    address: Address,
    enough_gas: bool,
) -> None:
    """
    Tests the constant gas behavior of `ecadd/ecmul/ecpairing` precompiled
    contract.
    """
    gas_costs = fork.gas_costs()
    gas = (
        gas_costs.G_PRECOMPILE_ECADD
        if address == EC_ADD_ADDRESS
        else gas_costs.G_PRECOMPILE_ECMUL
    )
    if not enough_gas:
        gas -= 1

    account = pre.deploy_contract(
        code=Op.SSTORE(0, Op.CALL(gas=gas, address=address)),
        storage={0: 0xDEADBEEF},
    )

    tx = Transaction(
        to=account,
        sender=pre.fund_eoa(),
        gas_limit=100_0000,
        protected=fork >= Byzantium,
    )

    post = {account: Account(storage={0: 1 if enough_gas else 0})}

    state_test(pre=pre, post=post, tx=tx)
