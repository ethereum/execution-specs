"""Tests ecpairing precompiled contract gas pricing."""

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

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-197.md"
REFERENCE_SPEC_VERSION = "9f9b3d33440e7c122b6c9192facfc380bc009422"

EC_PAIRING_ADDRESS = Address(0x08)


@pytest.mark.valid_from("Byzantium")
@pytest.mark.parametrize(
    "address",
    [
        pytest.param(EC_PAIRING_ADDRESS, id="ecpairing"),
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
    gas = fork.gas_costs().G_PRECOMPILE_ECPAIRING_BASE
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
