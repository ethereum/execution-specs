"""Tests ecadd/ecmul precompiled contracts gas pricing."""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    CodeGasMeasure,
    Fork,
    StateTestFiller,
    Storage,
    Transaction,
)
from execution_testing import (
    Macros as Om,
)
from execution_testing.forks.forks.forks import Berlin
from execution_testing.vm import Opcodes as Op

from .spec import PointG1, Scalar, Spec, ref_spec_196

REFERENCE_SPEC_GIT_PATH = ref_spec_196.git_path
REFERENCE_SPEC_VERSION = ref_spec_196.version


@pytest.mark.valid_from("Byzantium")
@pytest.mark.parametrize(
    "precompile_address",
    [
        pytest.param(Spec.ECADD, id="ecadd"),
        pytest.param(Spec.ECMUL, id="ecmul"),
    ],
)
@pytest.mark.parametrize("enough_gas", [True, False])
def test_gas_costs(
    state_test: StateTestFiller,
    pre: Alloc,
    precompile_address: Address,
    precompile_gas: int,
    enough_gas: bool,
) -> None:
    """
    Tests the constant gas behavior of `ecadd/ecmul` precompiled contracts.
    """
    gas = precompile_gas if enough_gas else precompile_gas - 1
    storage = Storage()

    account = pre.deploy_contract(
        code=Op.SSTORE(
            storage.store_next(1 if enough_gas else 0),
            Op.STATICCALL(gas=gas, address=precompile_address),
        ),
        storage=storage.canary(),
    )

    tx = Transaction(
        to=account,
        sender=pre.fund_eoa(),
        gas_limit=1_000_000,
        protected=True,
    )

    post = {account: Account(storage=storage)}

    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Byzantium")
@pytest.mark.parametrize(
    "precompile_address, invalid_input",
    [
        pytest.param(
            Spec.ECADD,
            PointG1(1, 3) + Spec.INF_G1,
            id="ecadd",
        ),
        pytest.param(
            Spec.ECMUL,
            PointG1(1, 3) + Scalar(1),
            id="ecmul",
        ),
    ],
)
@pytest.mark.parametrize(
    "extra_gas",
    [
        pytest.param(0, id="exact"),
        pytest.param(100_000, id="extra_100k"),
    ],
)
def test_invalid_gas_consumption(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    precompile_address: Address,
    precompile_gas: int,
    invalid_input: bytes,
    extra_gas: int,
) -> None:
    """
    Test that invalid inputs to ecadd/ecmul consume all forwarded gas.

    Use CodeGasMeasure to verify the STATICCALL with invalid input
    consumes exactly the warm call cost plus all forwarded gas.
    """
    gas_forward = precompile_gas + extra_gas
    input_size = len(invalid_input)
    storage = Storage()

    staticcall_code = Op.STATICCALL(
        gas=gas_forward,
        address=precompile_address,
        args_size=input_size,
    )
    push_cost = staticcall_code.gas_cost(fork) - Op.STATICCALL(
        address_warm=False
    ).gas_cost(fork)

    # Pre-EIP-2929: fixed G_call = 700; Berlin+: warm access cost.
    gas_costs = fork.gas_costs()
    if fork >= Berlin:
        staticcall_base = gas_costs.GAS_WARM_ACCOUNT_ACCESS
    else:
        staticcall_base = 700

    account = pre.deploy_contract(
        code=(
            Om.MSTORE(invalid_input)
            # Warm the precompile address
            + Op.POP(Op.STATICCALL(gas=0, address=precompile_address))
            + CodeGasMeasure(
                code=staticcall_code,
                overhead_cost=push_cost,
                extra_stack_items=1,
                sstore_key=storage.store_next(staticcall_base + gas_forward),
            )
        ),
        storage=storage.canary(),
    )

    tx = Transaction(
        to=account,
        sender=pre.fund_eoa(),
        gas_limit=1_000_000,
        protected=True,
    )

    post = {account: Account(storage=storage)}

    state_test(pre=pre, post=post, tx=tx)
