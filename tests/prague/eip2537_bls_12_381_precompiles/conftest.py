"""Shared pytest definitions local to EIP-2537 tests."""

import pytest

from ...common.precompile_fixtures import (
    call_contract_address,  # noqa: F401
    call_contract_code,  # noqa: F401
    call_contract_post_storage,  # noqa: F401
    call_opcode,  # noqa: F401
    call_succeeds,  # noqa: F401
    post,  # noqa: F401
    precompile_gas_modifier,  # noqa: F401
    sender,  # noqa: F401
    tx,  # noqa: F401
    tx_gas_limit,  # noqa: F401
)
from .helpers import BLSPointGenerator
from .spec import GAS_CALCULATION_FUNCTION_MAP


@pytest.fixture
def vector_gas_value() -> int | None:
    """
    Gas value from the test vector if any.

    If `None` it means that the test scenario did not come from a file, so no
    comparison is needed.

    The `vectors_from_file` function reads the gas value from the file and
    overwrites this fixture.
    """
    return None


@pytest.fixture
def precompile_gas(
    precompile_address: int, input_data: bytes, vector_gas_value: int | None
) -> int:
    """Gas cost for the precompile."""
    calculated_gas = GAS_CALCULATION_FUNCTION_MAP[precompile_address](
        len(input_data)
    )
    if vector_gas_value is not None:
        assert calculated_gas == vector_gas_value, (
            f"Calculated gas {calculated_gas} != Vector gas {vector_gas_value}"
        )
    return calculated_gas


NUM_TEST_POINTS = 5

# Random points not in the subgroup (fast to generate)
G1_POINTS_NOT_IN_SUBGROUP = [
    BLSPointGenerator.generate_random_g1_point_not_in_subgroup(seed=i)
    for i in range(NUM_TEST_POINTS)
]
G2_POINTS_NOT_IN_SUBGROUP = [
    BLSPointGenerator.generate_random_g2_point_not_in_subgroup(seed=i)
    for i in range(NUM_TEST_POINTS)
]
# Field points that maps to the identity point using `BLS12_MAP_FP_TO_G1`
G1_FIELD_POINTS_MAP_TO_IDENTITY = (
    BLSPointGenerator.generate_g1_map_isogeny_kernel_points()
)

# Random points not on the curve (fast to generate)
G1_POINTS_NOT_ON_CURVE = [
    BLSPointGenerator.generate_random_g1_point_not_on_curve(seed=i)
    for i in range(NUM_TEST_POINTS)
]
G2_POINTS_NOT_ON_CURVE = [
    BLSPointGenerator.generate_random_g2_point_not_on_curve(seed=i)
    for i in range(NUM_TEST_POINTS)
]

# Field points that maps to the identity point using `BLS12_MAP_FP_TO_G2`
G2_FIELD_POINTS_MAP_TO_IDENTITY = (
    BLSPointGenerator.generate_g2_map_isogeny_kernel_points()
)
