"""
Tests P256VERIFY precompiles of [EIP-7951: Precompile for secp256r1
Curve Support](https://eips.ethereum.org/EIPS/eip-7951).

Tests P256VERIFY
precompiles of [EIP-7951: Precompile for secp256r1 Curve
Support](https://eips.ethereum.org/EIPS/eip-7951) before the Osaka hard fork is
active.
"""

import pytest
from execution_testing import (
    Alloc,
    Block,
    BlockchainTestFiller,
    EIPChecklist,
    Transaction,
    TransitionFork,
)

from .spec import Spec, ref_spec_7951

REFERENCE_SPEC_GIT_PATH = ref_spec_7951.git_path
REFERENCE_SPEC_VERSION = ref_spec_7951.version

pytestmark = pytest.mark.valid_at_transition_to("Osaka")


@pytest.fixture
def precompile_gas(vector_gas_value: int | None, fork: TransitionFork) -> int:
    """Gas cost for the precompile."""
    gas = fork.transitions_to().gas_costs().PRECOMPILE_P256VERIFY
    if vector_gas_value is not None:
        assert vector_gas_value == gas, (
            f"Calculated gas {vector_gas_value} != Vector gas {gas}"
        )
    return gas


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
    "precompile_address,input_data,precompile_gas_modifier",
    [
        pytest.param(
            Spec.P256VERIFY,
            Spec.H0 + Spec.R0 + Spec.S0 + Spec.X0 + Spec.Y0,
            0,
            id="P256VERIFY_valid_input_6900_gas",
        ),
        pytest.param(
            Spec.P256VERIFY,
            Spec.H0 + Spec.R0 + Spec.S0 + Spec.X0 + Spec.X0,
            0,
            id="P256VERIFY_invalid_input",
        ),
        pytest.param(
            Spec.P256VERIFY,
            Spec.H0 + Spec.R0 + Spec.S0 + Spec.X0 + Spec.Y0,
            -6900,
            id="P256VERIFY_valid_input_zero_gas",
        ),
    ],
)
@pytest.mark.parametrize(
    "expected_output,call_succeeds",
    [pytest.param(Spec.INVALID_RETURN_VALUE, True, id=pytest.HIDDEN_PARAM)],
)
@EIPChecklist.Precompile.Test.ForkTransition.Before.InvalidInput()
@EIPChecklist.Precompile.Test.ForkTransition.Before.ZeroGas()
def test_precompile_before_fork(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    post: dict,
    tx: Transaction,
) -> None:
    """
    Test P256VERIFY precompiles before the Osaka hard fork is active.

    The call must succeed but the output must be empty.
    """
    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx])],
        post=post,
    )
