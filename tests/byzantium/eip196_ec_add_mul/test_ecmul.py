"""Tests the ecmul precompiled contract."""

import pytest
from execution_testing import (
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)

from .spec import PointG1, Scalar, Spec, ref_spec_196

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
            Spec.G1 + Scalar(0),
            Spec.INF_G1,
            id="generator_times_zero",
        ),
        pytest.param(
            Spec.G1 + Scalar(1),
            Spec.G1,
            id="generator_times_one",
        ),
        pytest.param(
            Spec.G1 + Scalar(2),
            Spec.G1x2,
            id="generator_times_two",
        ),
        pytest.param(
            Spec.G1 + Scalar(9),
            Spec.G1x9,
            id="generator_times_nine",
        ),
        pytest.param(
            Spec.G1 + Scalar(2**128),
            Spec.G1x2_128,
            id="generator_times_2_pow_128",
        ),
        pytest.param(
            Spec.G1 + Scalar(2**256 - 1),
            Spec.G1x2_256_1,
            id="generator_times_2_pow_256_minus_1",
        ),
        pytest.param(
            Spec.G1 + Scalar(Spec.N - 1),
            PointG1(1, Spec.P - 2),
            id="generator_times_group_order_minus_one",
        ),
        pytest.param(
            Spec.G1 + Scalar(Spec.N),
            Spec.INF_G1,
            id="generator_times_group_order",
        ),
        pytest.param(
            Spec.G1 + Scalar(Spec.N + 1),
            Spec.G1,
            id="generator_times_group_order_plus_one",
        ),
        pytest.param(
            Spec.G1 + Scalar(2 * Spec.N - 1),
            PointG1(1, Spec.P - 2),
            id="generator_times_double_group_order_minus_one",
        ),
        pytest.param(
            Spec.G1 + Scalar(2 * Spec.N),
            Spec.INF_G1,
            id="generator_times_double_group_order",
        ),
        pytest.param(
            Spec.G1 + Scalar(2 * Spec.N + 1),
            Spec.G1,
            id="generator_times_double_group_order_plus_one",
        ),
        pytest.param(
            Spec.T1 + Scalar(0),
            Spec.INF_G1,
            id="t1_point_times_zero",
        ),
        pytest.param(
            Spec.T1 + Scalar(1),
            Spec.T1,
            id="t1_point_times_one",
        ),
        pytest.param(
            Spec.T1 + Scalar(2),
            Spec.T1x2,
            id="t1_point_times_two",
        ),
        pytest.param(
            Spec.T1 + Scalar(9),
            Spec.T1x9,
            id="t1_point_times_nine",
        ),
        pytest.param(
            Spec.T1 + Scalar(2**128),
            Spec.T1x2_128,
            id="t1_point_times_2_pow_128",
        ),
        pytest.param(
            Spec.T1 + Scalar(2**256 - 1),
            Spec.T1x2_256_1,
            id="t1_point_times_2_pow_256_minus_1",
        ),
        pytest.param(
            Spec.T1 + Scalar(Spec.N - 1),
            PointG1(Spec.T1.x, Spec.P - Spec.T1.y),
            id="t1_point_times_group_order_minus_one",
        ),
        pytest.param(
            Spec.T1 + Scalar(Spec.N),
            Spec.INF_G1,
            id="t1_point_times_group_order",
        ),
        pytest.param(
            Spec.P1 + Scalar(0),
            Spec.INF_G1,
            id="p1_times_zero",
        ),
        pytest.param(
            Spec.P1 + Scalar(1),
            Spec.P1,
            id="p1_times_one",
        ),
        pytest.param(
            Spec.INF_G1 + Scalar(0),
            Spec.INF_G1,
            id="inf_times_zero",
        ),
        pytest.param(
            Spec.INF_G1 + Scalar(1),
            Spec.INF_G1,
            id="inf_times_one",
        ),
        pytest.param(
            Spec.INF_G1 + Scalar(2),
            Spec.INF_G1,
            id="inf_times_two",
        ),
        pytest.param(
            Spec.INF_G1 + Scalar(9),
            Spec.INF_G1,
            id="inf_times_nine",
        ),
        pytest.param(
            Spec.INF_G1 + Scalar(2**128),
            Spec.INF_G1,
            id="inf_times_2_pow_128",
        ),
        pytest.param(
            Spec.INF_G1 + Scalar(2**256 - 1),
            Spec.INF_G1,
            id="inf_times_2_pow_256_minus_1",
        ),
        pytest.param(
            Spec.INF_G1 + Scalar(Spec.N - 1),
            Spec.INF_G1,
            id="inf_times_group_order_minus_one",
        ),
        pytest.param(
            Spec.INF_G1 + Scalar(Spec.N),
            Spec.INF_G1,
            id="inf_times_group_order",
        ),
        # Extra data (>96 bytes)
        pytest.param(
            Spec.G1 + Scalar(1) + b"\0",
            Spec.G1,
            id="generator_times_one-single_extra_byte_0x00",
        ),
        pytest.param(
            Spec.G1 + Scalar(1) + b"\xff",
            Spec.G1,
            id="generator_times_one-single_extra_byte_0xff",
        ),
        pytest.param(
            Spec.G1 + Scalar(1) + b"\0" * 32,
            Spec.G1,
            id="generator_times_one-32_extra_byte_0x00",
        ),
        pytest.param(
            Spec.G1 + Scalar(1) + b"\xff" * 32,
            Spec.G1,
            id="generator_times_one-32_extra_byte_0xff",
        ),
        pytest.param(
            Spec.INF_G1 + Scalar(0) + b"\0" * 32,
            Spec.INF_G1,
            id="generator_times_zero-32_extra_byte_0x00",
        ),
        # Shorter data (<96 bytes)
        pytest.param(
            (Spec.G1 + Scalar(0))[:80],
            Spec.INF_G1,
            id="generator_times_zero-length_80",
        ),
        pytest.param(
            (Spec.G1 + Scalar(2**128))[:80],
            Spec.G1x2_128,
            id="generator_times_2_pow_128-length_80",
        ),
        pytest.param(
            (Spec.G1 + Scalar(2**128))[:95],
            Spec.G1x2_128,
            id="generator_times_2_pow_128-length_95",
        ),
        pytest.param(
            b"",
            Spec.INF_G1,
            id="empty",
        ),
        pytest.param(
            Spec.INF_G1,
            Spec.INF_G1,
            id="inf_no_scalar",
        ),
        pytest.param(
            bytes(Spec.INF_G1)[:40],
            Spec.INF_G1,
            id="inf-length_40",
        ),
        pytest.param(
            bytes(Spec.INF_G1)[:80],
            Spec.INF_G1,
            id="inf-length_80",
        ),
        pytest.param(
            Spec.G1,
            Spec.INF_G1,
            id="generator_no_scalar",
        ),
        # Ported from pointMulAdd / pointMulAdd2 (ECADD vs ECMUL)
        pytest.param(
            Spec.S1 + Scalar(2),
            Spec.S1x2,
            id="s1_times_two",
        ),
        pytest.param(
            Spec.S1 + Scalar(3),
            Spec.S1x3,
            id="s1_times_three",
        ),
        pytest.param(
            Spec.S1x3 + Scalar(0),
            Spec.INF_G1,
            id="s1x3_times_zero",
        ),
        pytest.param(
            PointG1(Spec.S1x3.x, Spec.P - Spec.S1x3.y) + Scalar(2),
            PointG1(
                0x255E468453D7636CC1563E43F7521755F95E6C56043C7321B4AE04E772945FB0,
                0x225C5F1623620FD84BFBAB2D861A9D1E570F7727C540F403085998EBAF407C4,
            ),
            id="neg_s1x3_times_two",
        ),
        pytest.param(
            Spec.S1x3 + Scalar(Spec.N - 1),
            PointG1(Spec.S1x3.x, Spec.P - Spec.S1x3.y),
            id="s1x3_times_group_order_minus_one",
        ),
        pytest.param(
            Spec.S1x3 + Scalar(Spec.N - 2),
            PointG1(
                0x255E468453D7636CC1563E43F7521755F95E6C56043C7321B4AE04E772945FB0,
                0x225C5F1623620FD84BFBAB2D861A9D1E570F7727C540F403085998EBAF407C4,
            ),
            id="s1x3_times_group_order_minus_two",
        ),
        pytest.param(
            Spec.S1x2 + Scalar(1),
            Spec.S1x2,
            id="s1x2_times_one",
        ),
        pytest.param(
            Spec.INF_G1 + Scalar(3),
            Spec.INF_G1,
            id="inf_times_three",
        ),
        pytest.param(
            Spec.INF_G1 + Scalar(Spec.N - 2),
            Spec.INF_G1,
            id="inf_times_group_order_minus_two",
        ),
        pytest.param(
            Spec.INF_G1 + Scalar(Spec.P - 1),
            Spec.INF_G1,
            id="inf_times_field_modulus_minus_one",
        ),
        pytest.param(
            Spec.INF_G1 + Scalar(Spec.P - 2),
            Spec.INF_G1,
            id="inf_times_field_modulus_minus_two",
        ),
        pytest.param(
            Spec.INF_G1 + Scalar(2**256 - 2),
            Spec.INF_G1,
            id="inf_times_2_pow_256_minus_2",
        ),
        pytest.param(
            PointG1(Spec.G1.x, Spec.P - Spec.G1.y) + Scalar(2),
            PointG1(Spec.G1x2.x, Spec.P - Spec.G1x2.y),
            id="neg_generator_times_two",
        ),
        pytest.param(
            PointG1(Spec.G1.x, Spec.P - Spec.G1.y) + Scalar(3),
            PointG1(
                0x769BF9AC56BEA3FF40232BCB1B6BD159315D84715B8E679F2D355961915ABF0,
                0x5ACB4B400E90C0063006A39F478F3E865E306DD5CD56F356E2E8CD8FE7EDAE6,
            ),
            id="neg_generator_times_three",
        ),
        pytest.param(
            PointG1(Spec.G1.x, Spec.P - Spec.G1.y) + Scalar(0),
            Spec.INF_G1,
            id="neg_generator_times_zero",
        ),
        pytest.param(
            PointG1(Spec.G1.x, Spec.P - Spec.G1.y) + Scalar(Spec.N - 1),
            Spec.G1,
            id="neg_generator_times_group_order_minus_one",
        ),
        pytest.param(
            PointG1(Spec.G1.x, Spec.P - Spec.G1.y) + Scalar(Spec.N - 2),
            Spec.G1x2,
            id="neg_generator_times_group_order_minus_two",
        ),
        pytest.param(
            PointG1(Spec.G1.x, Spec.P - Spec.G1.y) + Scalar(1),
            PointG1(Spec.G1.x, Spec.P - Spec.G1.y),
            id="neg_generator_times_one",
        ),
        pytest.param(
            Spec.SAMPLE_G1 + Scalar(2),
            PointG1(
                0x1FD3B816D9951DCB9AA9797D25E51A865987703AE83CD69C4658679F0350AE2B,
                0x29CE3D80A74DDC13784BEB25CA9FBFD048A3265A32C6F38B92060C5093A0E7A7,
            ),
            id="sample_times_two",
        ),
        pytest.param(
            PointG1(Spec.G1.x, Spec.P - Spec.G1.y) + Scalar(Spec.P - 1),
            Spec.SAMPLE_G1,
            id="neg_generator_times_field_modulus_minus_one",
        ),
        pytest.param(
            PointG1(Spec.G1.x, Spec.P - Spec.G1.y) + Scalar(Spec.P - 2),
            PointG1(
                0x2C15ED1902E189486AB6B625AA982510AEF6246B21A1E1BCEA382DA4D735E8BA,
                0x2103E58CBD2FA8081763442AB46C26A9B8051E9B049C3948C8D7D0E139C5E3F,
            ),
            id="neg_generator_times_field_modulus_minus_two",
        ),
        pytest.param(
            PointG1(Spec.G1x2_256_1.x, Spec.P - Spec.G1x2_256_1.y) + Scalar(2),
            PointG1(
                0x2FA739D4CDE056D8FD75427345CBB34159856E06A4FFAD64159C4773F23FBF4B,
                0x1EED5D5325C31FC89DD541A13D7F63B981FAE8D4BF78A6B08A38A601FCFEA97B,
            ),
            id="neg_g1x2_256_1_times_two",
        ),
        pytest.param(
            PointG1(Spec.G1.x, Spec.P - Spec.G1.y) + Scalar(2**256 - 1),
            PointG1(Spec.G1x2_256_1.x, Spec.P - Spec.G1x2_256_1.y),
            id="neg_generator_times_2_pow_256_minus_1",
        ),
        pytest.param(
            PointG1(Spec.G1.x, Spec.P - Spec.G1.y) + Scalar(2**256 - 2),
            PointG1(
                0x8E2142845DB159BD105879A109FE7A6F254ED3DDAE0E9CD8A2AEAE05E5F647B,
                0x221108EE615499D2E0A1113CA1A858A34E055F9DA2D30E6E6AB392B049944A92,
            ),
            id="neg_generator_times_2_pow_256_minus_2",
        ),
        pytest.param(
            Spec.G1 + Scalar(3),
            PointG1(
                0x769BF9AC56BEA3FF40232BCB1B6BD159315D84715B8E679F2D355961915ABF0,
                0x2AB799BEE0489429554FDB7C8D086475319E63B40B9C5B57CDF1FF3DD9FE2261,
            ),
            id="generator_times_three",
        ),
        pytest.param(
            Spec.G1 + Scalar(Spec.N - 2),
            PointG1(Spec.G1x2.x, Spec.P - Spec.G1x2.y),
            id="generator_times_group_order_minus_two",
        ),
        pytest.param(
            PointG1(Spec.SAMPLE_G1.x, Spec.P - Spec.SAMPLE_G1.y) + Scalar(2),
            PointG1(
                0x1FD3B816D9951DCB9AA9797D25E51A865987703AE83CD69C4658679F0350AE2B,
                0x69610F239E3C41640045A90B6E1988D4EDE443735AAD701AA1A7FC644DC15A0,
            ),
            id="neg_sample_times_two",
        ),
        pytest.param(
            Spec.G1 + Scalar(Spec.P - 1),
            PointG1(Spec.SAMPLE_G1.x, Spec.P - Spec.SAMPLE_G1.y),
            id="generator_times_field_modulus_minus_one",
        ),
        pytest.param(
            Spec.G1 + Scalar(Spec.P - 2),
            PointG1(
                0x2C15ED1902E189486AB6B625AA982510AEF6246B21A1E1BCEA382DA4D735E8BA,
                0x2E54101A155EA5A936DA1173D63A95F2FC0118A7B82806F8AF930F08C4E09F08,
            ),
            id="generator_times_field_modulus_minus_two",
        ),
        pytest.param(
            Spec.G1x2_256_1 + Scalar(2),
            PointG1(
                0x2FA739D4CDE056D8FD75427345CBB34159856E06A4FFAD64159C4773F23FBF4B,
                0x1176F11FBB6E80611A7B04154401F4A4158681BCA8F923DCB1E7E614DB7E53CC,
            ),
            id="g1x2_256_1_times_two",
        ),
        pytest.param(
            Spec.G1 + Scalar(2**256 - 2),
            PointG1(
                0x8E2142845DB159BD105879A109FE7A6F254ED3DDAE0E9CD8A2AEAE05E5F647B,
                0xE5345847FDD0656D7AF3479DFD8FFBA497C0AF3C59EBC1ED16CF9668EE8B2B5,
            ),
            id="generator_times_2_pow_256_minus_2",
        ),
    ],
)
@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecmul_1-2_2_21000_96Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecmul_1-2_340282366920938463463374607431768211456_21000_96Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecmul_1-2_2_21000_128Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecmul_1-2_5616_21000_128Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecmul_1-2_5616_21000_96Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecmul_1-2_616_21000_96Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecmul_1-2_5617_21000_128Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecmul_1-2_5617_21000_96Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecmul_1-2_9935_21000_128Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecmul_1-2_9935_21000_96Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecmul_1-2_9_21000_128Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecmul_1-2_9_21000_96Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecmul_1-2_340282366920938463463374607431768211456_21000_80Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecmul_7827-6598_0_21000_96Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecmul_7827-6598_1456_21000_96Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecmul_7827-6598_1_21000_96Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecmul_7827-6598_2_21000_96Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecmul_7827-6598_5616_21000_96Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecmul_7827-6598_5617_21000_96Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecmul_7827-6598_9935_21000_96Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecmul_0-0_0_21000_96Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecmul_0-0_0_21000_0Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecmul_0-0_0_21000_128Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecmul_0-0_1_21000_96Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecmul_0-0_2_21000_96Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecmul_0-0_9_21000_96Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecmul_0-0_340282366920938463463374607431768211456_21000_96Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecmul_0-0_5616_21000_96Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecmul_0-0_5617_21000_96Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecmul_0-0_9935_21000_96Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecmul_0-0_0_21000_40Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecmul_0-0_0_21000_80Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge2/ecmul_1-2_0_21000_64Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge2/ecmul_1-2_0_21000_80Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge2/ecmul_1-2_0_21000_96Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge2/ecmul_1-2_1_21000_128Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge2/ecmul_1-2_1_21000_96Filler.json",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stZeroKnowledge/pointMulAddFiller.json",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stZeroKnowledge/pointMulAdd2Filler.json",
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
    "input_data",
    [
        pytest.param(
            PointG1(1, 3) + Scalar(0),
            id="not_on_curve_1_3_times_zero",
        ),
        pytest.param(
            PointG1(1, 3),
            id="not_on_curve_1_3_no_scalar",
        ),
        pytest.param(
            bytes(PointG1(1, 3))[:80],
            id="not_on_curve_1_3-length_80",
        ),
        pytest.param(
            PointG1(1, 3) + Scalar(0) + b"\0" * 32,
            id="not_on_curve_1_3-32_extra_byte_0x00",
        ),
        pytest.param(
            PointG1(1, 3) + Scalar(1),
            id="not_on_curve_1_3_times_one",
        ),
        pytest.param(
            PointG1(1, 3) + Scalar(2),
            id="not_on_curve_1_3_times_two",
        ),
        pytest.param(
            PointG1(1, 3) + Scalar(9),
            id="not_on_curve_1_3_times_nine",
        ),
        pytest.param(
            PointG1(1, 3) + Scalar(2**128),
            id="not_on_curve_1_3_times_2_pow_128",
        ),
        pytest.param(
            bytes(PointG1(1, 3) + Scalar(2**128))[:80],
            id="not_on_curve_1_3_times_2_pow_128-length_80",
        ),
        pytest.param(
            PointG1(1, 3) + Scalar(2**256 - 1),
            id="not_on_curve_1_3_times_2_pow_256_minus_1",
        ),
        pytest.param(
            PointG1(1, 3) + Scalar(Spec.N - 1),
            id="not_on_curve_1_3_times_group_order_minus_one",
        ),
        pytest.param(
            PointG1(1, 3) + Scalar(Spec.N),
            id="not_on_curve_1_3_times_group_order",
        ),
        pytest.param(
            PointG1(0, 3) + Scalar(0),
            id="not_on_curve_0_3_times_zero",
        ),
        pytest.param(
            PointG1(0, 3),
            id="not_on_curve_0_3_no_scalar",
        ),
        pytest.param(
            bytes(PointG1(0, 3))[:80],
            id="not_on_curve_0_3-length_80",
        ),
        pytest.param(
            PointG1(0, 3) + Scalar(0) + b"\0" * 32,
            id="not_on_curve_0_3-32_extra_byte_0x00",
        ),
        pytest.param(
            PointG1(0, 3) + Scalar(1),
            id="not_on_curve_0_3_times_one",
        ),
        pytest.param(
            PointG1(0, 3) + Scalar(2),
            id="not_on_curve_0_3_times_two",
        ),
        pytest.param(
            PointG1(0, 3) + Scalar(9),
            id="not_on_curve_0_3_times_nine",
        ),
        pytest.param(
            PointG1(0, 3) + Scalar(2**128),
            id="not_on_curve_0_3_times_2_pow_128",
        ),
        pytest.param(
            bytes(PointG1(0, 3) + Scalar(2**128))[:80],
            id="not_on_curve_0_3_times_2_pow_128-length_80",
        ),
        pytest.param(
            PointG1(0, 3) + Scalar(2**256 - 1),
            id="not_on_curve_0_3_times_2_pow_256_minus_1",
        ),
        pytest.param(
            PointG1(0, 3) + Scalar(Spec.N - 1),
            id="not_on_curve_0_3_times_group_order_minus_one",
        ),
        pytest.param(
            PointG1(0, 3) + Scalar(Spec.N),
            id="not_on_curve_0_3_times_group_order",
        ),
        pytest.param(
            PointG1(7827, 6598) + Scalar(0),
            id="not_on_curve_7827_6598_times_zero",
        ),
        pytest.param(
            PointG1(7827, 6598) + Scalar(1),
            id="not_on_curve_7827_6598_times_one",
        ),
        pytest.param(
            PointG1(Spec.P, 0) + Scalar(1),
            id="x_eq_P",
        ),
        pytest.param(
            PointG1(0, Spec.P) + Scalar(1),
            id="y_eq_P",
        ),
        pytest.param(
            PointG1(Spec.G1.x + Spec.P, Spec.G1.y) + Scalar(1),
            id="x_plus_P",
        ),
        pytest.param(
            PointG1(Spec.G1.x, Spec.G1.y + Spec.P) + Scalar(1),
            id="y_plus_P",
        ),
    ],
)
@pytest.mark.parametrize(
    "expected_output", [pytest.param(b"", id=pytest.HIDDEN_PARAM)]
)
@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecmul_1-3_0_21000_128Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecmul_1-3_0_21000_64Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecmul_1-3_0_21000_80Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecmul_1-3_0_21000_96Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecmul_1-3_1_21000_96Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecmul_1-3_2_21000_96Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecmul_1-3_9_21000_96Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecmul_1-3_340282366920938463463374607431768211456_21000_96Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecmul_1-3_5616_21000_96Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecmul_1-3_5617_21000_96Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecmul_1-3_9935_21000_96Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecmul_7827-6598_0_21000_128Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecmul_7827-6598_1_21000_128Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge2/ecmul_0-3_0_21000_128Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge2/ecmul_0-3_0_21000_64Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge2/ecmul_0-3_0_21000_80Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge2/ecmul_0-3_0_21000_96Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge2/ecmul_0-3_1_21000_96Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge2/ecmul_0-3_2_21000_96Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge2/ecmul_0-3_340282366920938463463374607431768211456_21000_80Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge2/ecmul_0-3_340282366920938463463374607431768211456_21000_96Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge2/ecmul_0-3_5616_21000_96Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge2/ecmul_0-3_5617_21000_96Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge2/ecmul_0-3_9935_21000_96Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge2/ecmul_0-3_9_21000_96Filler.json",
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
