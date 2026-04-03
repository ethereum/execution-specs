"""
Tests BLS12 precompiles before fork activation.

Tests the BLS12 precompiles behavior before fork activation from
[EIP-2537: Precompile for BLS12-381 curve operations]
(https://eips.ethereum.org/EIPS/eip-2537).
"""

import pytest
from execution_testing import (
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
    TransitionFork,
)

from .spec import (
    FP,
    FP2,
    Scalar,
    Spec,
    build_gas_calculation_function_map,
    ref_spec_2537,
)

REFERENCE_SPEC_GIT_PATH = ref_spec_2537.git_path
REFERENCE_SPEC_VERSION = ref_spec_2537.version

pytestmark = pytest.mark.valid_at_transition_to("Prague")


@pytest.fixture
def precompile_gas(
    precompile_address: int,
    input_data: bytes,
    vector_gas_value: int | None,
    fork: TransitionFork,
) -> int:
    """Gas cost for the precompile."""
    gas_map = build_gas_calculation_function_map(
        fork.transitions_to().gas_costs()
    )
    calculated_gas = gas_map[precompile_address](len(input_data))
    if vector_gas_value is not None:
        assert calculated_gas == vector_gas_value, (
            f"Calculated gas {calculated_gas} != Vector gas {vector_gas_value}"
        )
    return calculated_gas


@pytest.fixture
def tx_gas_limit(
    fork: TransitionFork, input_data: bytes, precompile_gas: int
) -> int:
    """
    Transaction gas limit used for the test (Can be overridden in the test).
    """
    intrinsic_gas_cost_calculator = (
        fork.transitions_from().transaction_intrinsic_cost_calculator()
    )
    memory_expansion_gas_calculator = (
        fork.transitions_from().memory_expansion_gas_calculator()
    )
    extra_gas = 100_000
    return (
        extra_gas
        + intrinsic_gas_cost_calculator(calldata=input_data)
        + memory_expansion_gas_calculator(new_bytes=len(input_data))
        + precompile_gas
    )


@pytest.mark.parametrize(
    "precompile_address,input_data",
    [
        pytest.param(
            Spec.G1ADD,
            Spec.INF_G1 + Spec.INF_G1,
            id="G1ADD",
        ),
        pytest.param(
            Spec.G1MSM,
            Spec.INF_G1 + Scalar(0),
            id="G1MSM",
        ),
        pytest.param(
            Spec.G2ADD,
            Spec.INF_G2 + Spec.INF_G2,
            id="G2ADD",
        ),
        pytest.param(
            Spec.G2MSM,
            Spec.INF_G2 + Scalar(0),
            id="G2MSM",
        ),
        pytest.param(
            Spec.PAIRING,
            Spec.INF_G1 + Spec.INF_G2,
            id="PAIRING",
        ),
        pytest.param(
            Spec.MAP_FP_TO_G1,
            FP(0),
            id="MAP_FP_TO_G1",
        ),
        pytest.param(
            Spec.MAP_FP2_TO_G2,
            FP2((0, 0)),
            id="MAP_FP2_TO_G2",
        ),
    ],
)
@pytest.mark.parametrize(
    "expected_output,call_succeeds", [pytest.param(b"", True, id="")]
)
def test_precompile_before_fork(
    state_test: StateTestFiller,
    pre: Alloc,
    post: dict,
    tx: Transaction,
) -> None:
    """
    Test all BLS12 precompiles before the Prague hard fork is active.

    The call must succeed but the output must be empty.
    """
    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post=post,
    )
