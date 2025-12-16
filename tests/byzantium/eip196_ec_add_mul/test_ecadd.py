"""Tests the ecadd precompiled contract."""

import pytest
from execution_testing import (
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)

from .spec import PointG1, Spec, ref_spec_196

REFERENCE_SPEC_GIT_PATH = ref_spec_196.git_path
REFERENCE_SPEC_VERSION = ref_spec_196.version

pytestmark = [
    pytest.mark.valid_from("Byzantium"),
    pytest.mark.parametrize("precompile_address", [Spec.ECADD], ids=["ecadd"]),
]


@pytest.mark.parametrize(
    "input_data, expected_output",
    [
        pytest.param(
            Spec.G1 + Spec.INF_G1,
            Spec.G1,
            id="generator_plus_inf",
        ),
    ],
)
def test_valid(
    state_test: StateTestFiller,
    pre: Alloc,
    post: dict,
    tx: Transaction,
) -> None:
    """Test the valid inputs to the ECADD precompile."""
    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post=post,
    )


@pytest.mark.parametrize(
    "input_data, expected_output",
    [
        pytest.param(
            PointG1(1, 1) + Spec.INF_G1,
            b"",
            id="pt_1_1_plus_inf",
        ),
    ],
)
def test_invalid(
    state_test: StateTestFiller,
    pre: Alloc,
    post: dict,
    tx: Transaction,
) -> None:
    """Test the invalid inputs to the ECADD precompile."""
    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post=post,
    )
