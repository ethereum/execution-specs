"""Tests ecadd/ecmul/ecpairing precompiled contracts."""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.base_types.base_types import Address
from execution_testing.forks import Byzantium, Istanbul
from execution_testing.forks.helpers import Fork
from execution_testing.vm import Opcodes as Op


@pytest.mark.valid_from("Byzantium")
@pytest.mark.parametrize(
    "address,gas_pre_istanbul,gas_post_istanbul",
    [
        pytest.param(0x06, 500, 150, id="ecadd"),
        pytest.param(0x07, 40_000, 6000, id="ecmul"),
        pytest.param(0x08, 100_000, 45_000, id="ecpairing"),
    ],
)
@pytest.mark.parametrize("enough_gas", [True, False])
def test_bn254_precompiles_gascosts(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    address: Address,
    gas_pre_istanbul: int,
    gas_post_istanbul: int,
    enough_gas: bool,
) -> None:
    """
    Tests the constant gas behavior of `ecadd/ecmul/ecpairing` precompiled
    contract.
    """
    env = Environment()
    if fork < Istanbul:
        gas = gas_pre_istanbul
    else:
        gas = gas_post_istanbul
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

    state_test(env=env, pre=pre, post=post, tx=tx)
