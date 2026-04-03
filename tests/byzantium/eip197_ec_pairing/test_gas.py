"""Tests ecpairing precompiled contract gas pricing."""

import pytest
from execution_testing import (
    Account,
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

from .spec import PointG1, Spec, ref_spec_197

REFERENCE_SPEC_GIT_PATH = ref_spec_197.git_path
REFERENCE_SPEC_VERSION = ref_spec_197.version


@pytest.fixture
def input_data() -> bytes:
    """Default empty input data (0 pairs)."""
    return b""


@pytest.mark.valid_from("Byzantium")
@pytest.mark.parametrize("enough_gas", [True, False])
def test_gas_costs(
    state_test: StateTestFiller,
    pre: Alloc,
    precompile_gas: int,
    enough_gas: bool,
) -> None:
    """
    Test the base gas cost of the ecpairing precompile with zero pairs.
    """
    gas = precompile_gas if enough_gas else precompile_gas - 1
    storage = Storage()

    account = pre.deploy_contract(
        code=Op.SSTORE(
            storage.store_next(1 if enough_gas else 0),
            Op.STATICCALL(gas=gas, address=Spec.ECPAIRING),
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
    "input_data",
    [
        pytest.param(
            PointG1(1, 3) + Spec.G2,
            id="invalid_g1_point",
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
    precompile_gas: int,
    input_data: bytes,
    extra_gas: int,
) -> None:
    """
    Test that invalid input to ecpairing consumes all forwarded gas.

    Use CodeGasMeasure to verify the STATICCALL with invalid input
    consumes exactly the warm call cost plus all forwarded gas.
    """
    gas_forward = precompile_gas + extra_gas
    input_size = len(input_data)
    storage = Storage()

    staticcall_code = Op.STATICCALL(
        gas=gas_forward,
        address=Spec.ECPAIRING,
        args_size=input_size,
    )
    push_cost = staticcall_code.gas_cost(fork) - Op.STATICCALL(
        address_warm=False
    ).gas_cost(fork)

    # Pre-EIP-2929: fixed G_call = 700; Berlin+: warm access cost.
    gas_costs = fork.gas_costs()
    if fork >= Berlin:
        staticcall_base = gas_costs.GAS_WARM_ACCESS
    else:
        staticcall_base = 700

    account = pre.deploy_contract(
        code=(
            Om.MSTORE(input_data)
            # Warm the precompile address
            + Op.POP(Op.STATICCALL(gas=0, address=Spec.ECPAIRING))
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
