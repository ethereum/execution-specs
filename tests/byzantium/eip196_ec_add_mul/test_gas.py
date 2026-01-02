"""Tests ecadd/ecmul precompiled contracts gas pricing."""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Byzantium
from execution_testing.forks.helpers import Fork
from execution_testing.vm import Opcodes as Op

from .spec import Spec, ref_spec_196

REFERENCE_SPEC_GIT_PATH = ref_spec_196.git_path
REFERENCE_SPEC_VERSION = ref_spec_196.version


@pytest.mark.valid_from("Byzantium")
@pytest.mark.parametrize(
    "address",
    [
        pytest.param(Spec.ECADD, id="ecadd"),
        pytest.param(Spec.ECMUL, id="ecmul"),
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
    Tests the constant gas behavior of `ecadd/ecmul` precompiled contracts.
    """
    gas_costs = fork.gas_costs()
    gas = (
        gas_costs.G_PRECOMPILE_ECADD
        if address == Spec.ECADD
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
