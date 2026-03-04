"""Tests the ecmul precompiled contract."""

import pytest
from execution_testing import (
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)

from .spec import FP, PointG1, Spec, ref_spec_196

REFERENCE_SPEC_GIT_PATH = ref_spec_196.git_path
REFERENCE_SPEC_VERSION = ref_spec_196.version

pytestmark = [
    pytest.mark.valid_from("Byzantium"),
    pytest.mark.parametrize("precompile_address", [Spec.ECMUL], ids=["ecmul"]),
]


@pytest.mark.parametrize(
    "input_data, expected_output",
    [
        pytest.param(
            Spec.G1 + FP(0),
            Spec.INF_G1,
            id="generator_times_zero",
        ),
        pytest.param(
            Spec.G1 + FP(1),
            Spec.G1,
            id="generator_times_one",
        ),
        pytest.param(
            Spec.G1 + FP(2),
            Spec.G1x2,
            id="generator_times_two",
        ),
        pytest.param(
            Spec.P1 + FP(0),
            Spec.INF_G1,
            id="p1_times_zero",
        ),
        pytest.param(
            Spec.P1 + FP(1),
            Spec.P1,
            id="p1_times_one",
        ),
        pytest.param(
            Spec.INF_G1 + FP(0),
            Spec.INF_G1,
            id="inf_times_zero",
        ),
        pytest.param(
            Spec.INF_G1 + FP(1),
            Spec.INF_G1,
            id="inf_times_one",
        ),
        pytest.param(
            Spec.INF_G1 + FP(2),
            Spec.INF_G1,
            id="inf_times_two",
        ),
        pytest.param(
            b"",
            Spec.INF_G1,
            id="empty",
        ),
        pytest.param(
            Spec.G1,
            Spec.INF_G1,
            id="no_scalar",
        ),
        pytest.param(
            Spec.G1 + FP(1) + b"\0" * 32,
            Spec.G1,
            id="generator_times_one_extra_data",
        ),
    ],
)
@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecmul_1-2_2_28000_128Filler.json",
    ],
    pr=["https://github.com/ethereum/execution-specs/pull/2403"],
)
def test_valid(
    state_test: StateTestFiller,
    pre: Alloc,
    post: dict,
    tx: Transaction,
) -> None:
    """Test the valid inputs to the ECMUL precompile."""
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
            PointG1(1, 3) + FP(0),
            b"",
            id="not_on_curve_1_3_times_zero",
        ),
        pytest.param(
            PointG1(1, 3) + FP(1),
            b"",
            id="not_on_curve_1_3_times_one",
        ),
        pytest.param(
            PointG1(1, 3) + FP(2),
            b"",
            id="not_on_curve_1_3_times_two",
        ),
        pytest.param(
            PointG1(7827, 6598) + FP(0),
            b"",
            id="not_on_curve_7827_6598_times_zero",
        ),
        pytest.param(
            PointG1(7827, 6598) + FP(1),
            b"",
            id="not_on_curve_7827_6598_times_one",
        ),
        pytest.param(
            PointG1(0, 3) + FP(1),
            b"",
            id="not_on_curve_0_3",
        ),
        pytest.param(
            PointG1(Spec.P, 0) + FP(1),
            b"",
            id="x_eq_P",
        ),
        pytest.param(
            PointG1(0, Spec.P) + FP(1),
            b"",
            id="y_eq_P",
        ),
        pytest.param(
            PointG1(Spec.G1.x + Spec.P, Spec.G1.y) + FP(1),
            b"",
            id="x_plus_P",
        ),
        pytest.param(
            PointG1(Spec.G1.x, Spec.G1.y + Spec.P) + FP(1),
            b"",
            id="y_plus_P",
        ),
    ],
)
@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecmul_1-3_0_21000_128Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecmul_1-3_1_28000_128Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecmul_1-3_2_28000_128Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecmul_7827-6598_0_21000_128Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecmul_7827-6598_1_21000_128Filler.json",
    ],
    pr=["https://github.com/ethereum/execution-specs/pull/2403"],
)
def test_invalid(
    state_test: StateTestFiller,
    pre: Alloc,
    post: dict,
    tx: Transaction,
) -> None:
    """Test the invalid inputs to the ECMUL precompile."""
    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post=post,
    )
