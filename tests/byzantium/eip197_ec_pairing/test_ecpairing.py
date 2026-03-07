"""Test the ecpairing precompiled contract."""

import pytest
from execution_testing import (
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)

from .spec import PointG1, PointG2, Spec, ref_spec_197

REFERENCE_SPEC_GIT_PATH = ref_spec_197.git_path
REFERENCE_SPEC_VERSION = ref_spec_197.version

pytestmark = [
    pytest.mark.valid_from("Byzantium"),
    pytest.mark.parametrize(
        "precompile_address", [Spec.ECPAIRING], ids=["ecpairing"]
    ),
]


@pytest.mark.parametrize(
    "input_data, expected_output",
    [
        pytest.param(
            b"",
            Spec.PAIRING_TRUE,
            id="empty",
        ),
        pytest.param(
            Spec.INF_G1 + Spec.G2,
            Spec.PAIRING_TRUE,
            id="one_pair_g1_zero",
        ),
        pytest.param(
            Spec.G1 + Spec.INF_G2,
            Spec.PAIRING_TRUE,
            id="one_pair_g2_zero",
        ),
        pytest.param(
            Spec.G1 + Spec.G2 + Spec.NEG_G1 + Spec.G2,
            Spec.PAIRING_TRUE,
            id="two_pairs_negated_g1",
        ),
    ],
)
@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecpairing_empty_dataFiller.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecpairing_one_point_with_g1_zeroFiller.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecpairing_one_point_with_g2_zeroFiller.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecpairing_two_point_match_1Filler.json",
    ],
    pr=["https://github.com/ethereum/execution-specs/pull/2422"],
)
def test_valid(
    state_test: StateTestFiller,
    pre: Alloc,
    post: dict,
    tx: Transaction,
) -> None:
    """Test valid inputs where the pairing check succeeds."""
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
            Spec.G1 + Spec.G2,
            Spec.PAIRING_FALSE,
            id="one_pair",
        ),
    ],
)
@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecpairing_one_point_failFiller.json",
    ],
    pr=["https://github.com/ethereum/execution-specs/pull/2422"],
)
def test_fail(
    state_test: StateTestFiller,
    pre: Alloc,
    post: dict,
    tx: Transaction,
) -> None:
    """Test valid inputs where the pairing check fails."""
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
            (Spec.G1 + Spec.G2)[:191],
            Spec.INVALID,
            id="bad_length_191",
        ),
        pytest.param(
            Spec.G1 + Spec.G2 + b"\x00",
            Spec.INVALID,
            id="bad_length_193",
        ),
        pytest.param(
            PointG1(1, 3) + Spec.G2,
            Spec.INVALID,
            id="g1_not_on_curve",
        ),
        # G1 coordinates >= P
        pytest.param(
            PointG1(Spec.P, 0) + Spec.INF_G2,
            Spec.INVALID,
            id="g1_x_eq_P",
        ),
        pytest.param(
            PointG1(0, Spec.P) + Spec.INF_G2,
            Spec.INVALID,
            id="g1_y_eq_P",
        ),
        pytest.param(
            PointG1(Spec.G1.x + Spec.P, Spec.G1.y) + Spec.INF_G2,
            Spec.INVALID,
            id="g1_x_plus_P",
        ),
        pytest.param(
            PointG1(Spec.G1.x, Spec.G1.y + Spec.P) + Spec.INF_G2,
            Spec.INVALID,
            id="g1_y_plus_P",
        ),
        # G2 coordinates >= P
        pytest.param(
            Spec.INF_G1 + PointG2((Spec.P, 0), (0, 0)),
            Spec.INVALID,
            id="g2_x0_eq_P",
        ),
        pytest.param(
            Spec.INF_G1 + PointG2((0, Spec.P), (0, 0)),
            Spec.INVALID,
            id="g2_x1_eq_P",
        ),
        pytest.param(
            Spec.INF_G1 + PointG2((0, 0), (Spec.P, 0)),
            Spec.INVALID,
            id="g2_y0_eq_P",
        ),
        pytest.param(
            Spec.INF_G1 + PointG2((0, 0), (0, Spec.P)),
            Spec.INVALID,
            id="g2_y1_eq_P",
        ),
        pytest.param(
            Spec.INF_G1
            + PointG2((Spec.G2.x[0] + Spec.P, Spec.G2.x[1]), Spec.G2.y),
            Spec.INVALID,
            id="g2_x0_plus_P",
        ),
        pytest.param(
            Spec.INF_G1
            + PointG2((Spec.G2.x[0], Spec.G2.x[1] + Spec.P), Spec.G2.y),
            Spec.INVALID,
            id="g2_x1_plus_P",
        ),
        pytest.param(
            Spec.INF_G1
            + PointG2(Spec.G2.x, (Spec.G2.y[0] + Spec.P, Spec.G2.y[1])),
            Spec.INVALID,
            id="g2_y0_plus_P",
        ),
        pytest.param(
            Spec.INF_G1
            + PointG2(Spec.G2.x, (Spec.G2.y[0], Spec.G2.y[1] + Spec.P)),
            Spec.INVALID,
            id="g2_y1_plus_P",
        ),
        pytest.param(
            Spec.INF_G1
            + PointG2((Spec.G2.x[0] + Spec.N, Spec.G2.x[1]), Spec.G2.y),
            Spec.INVALID,
            id="g2_x0_plus_N",
        ),
        pytest.param(
            Spec.INF_G1
            + PointG2((Spec.G2.x[0], Spec.G2.x[1] + Spec.N), Spec.G2.y),
            Spec.INVALID,
            id="g2_x1_plus_N",
        ),
        pytest.param(
            Spec.INF_G1
            + PointG2(Spec.G2.x, (Spec.G2.y[0] + Spec.N, Spec.G2.y[1])),
            Spec.INVALID,
            id="g2_y0_plus_N",
        ),
        pytest.param(
            Spec.INF_G1
            + PointG2(Spec.G2.x, (Spec.G2.y[0], Spec.G2.y[1] + Spec.N)),
            Spec.INVALID,
            id="g2_y1_plus_N",
        ),
        pytest.param(
            Spec.INF_G1 + PointG2((Spec.G2.x[0] + 1, Spec.G2.x[1]), Spec.G2.y),
            Spec.INVALID,
            id="g2_x0_plus_one",
        ),
        pytest.param(
            Spec.INF_G1 + PointG2((Spec.G2.x[0], Spec.G2.x[1] + 1), Spec.G2.y),
            Spec.INVALID,
            id="g2_x1_plus_one",
        ),
        pytest.param(
            Spec.INF_G1 + PointG2(Spec.G2.x, (Spec.G2.y[0] + 1, Spec.G2.y[1])),
            Spec.INVALID,
            id="g2_y0_plus_one",
        ),
        pytest.param(
            Spec.INF_G1 + PointG2(Spec.G2.x, (Spec.G2.y[0], Spec.G2.y[1] + 1)),
            Spec.INVALID,
            id="g2_y1_plus_one",
        ),
        pytest.param(
            Spec.INF_G1
            + PointG2(
                (0x0, 0x8),
                (
                    0x00D3270B7DA683F988D3889ABCDAD9776ECD45ABACA689F1118C3FD33404B439,
                    0x2588360D269AF2CD3E0803839EA274C2B8F062A6308E8DA85FD774C26F1BCB87,
                ),
            ),
            Spec.INVALID,
            id="one_point_not_in_subgroup",
        ),
        pytest.param(
            PointG1(0x11, 0x2) + Spec.INF_G2,
            Spec.INVALID,
            id="one_point_with_g2_zero_and_g1_invalid",
        ),
        pytest.param(
            PointG1(Spec.N, 0x0) + Spec.G2,
            Spec.INVALID,
            id="perturb_x0_by_curve_order",
        ),
        pytest.param(
            PointG1(0x0, Spec.N) + Spec.G2,
            Spec.INVALID,
            id="perturb_x1_by_curve_order",
        ),
    ],
)
@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecpairing_bad_length_191Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecpairing_bad_length_193Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecpairing_perturb_g2_by_field_modulusFiller.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecpairing_perturb_g2_by_field_modulus_againFiller.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecpairing_one_point_not_in_subgroupFiller.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecpairing_one_point_with_g2_zero_and_g1_invalidFiller.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecpairing_perturb_g2_by_curve_orderFiller.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecpairing_perturb_g2_by_oneFiller.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecpairing_perturb_zeropoint_by_curve_orderFiller.json",
    ],
    pr=["https://github.com/ethereum/execution-specs/pull/2422"],
)
def test_invalid(
    state_test: StateTestFiller,
    pre: Alloc,
    post: dict,
    tx: Transaction,
) -> None:
    """Test invalid inputs to the ecpairing precompile."""
    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post=post,
    )


@pytest.mark.parametrize(
    "input_data, expected_output, precompile_gas_modifier",
    [
        pytest.param(
            b"",
            Spec.INVALID,
            -1,
            id="empty_data_insufficient_gas",
        ),
        pytest.param(
            Spec.G1 + Spec.G2,
            Spec.INVALID,
            -1,
            id="one_pair_insufficient_gas",
        ),
    ],
)
@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecpairing_empty_data_insufficient_gasFiller.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecpairing_one_point_insufficient_gasFiller.json",
    ],
    pr=["https://github.com/ethereum/execution-specs/pull/2422"],
)
def test_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    post: dict,
    tx: Transaction,
) -> None:
    """Test gas combinations to the ecpairing precompile."""
    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post=post,
    )
