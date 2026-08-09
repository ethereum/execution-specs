"""Tests the ecadd precompiled contract."""

import pytest
from execution_testing import Alloc, StateTestFiller, Transaction

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
        pytest.param(
            Spec.INF_G1 + Spec.G1,
            Spec.G1,
            id="inf_plus_generator",
        ),
        pytest.param(
            Spec.G1 + Spec.INF_G1 + Spec.INF_G1,
            Spec.G1,
            id="generator_plus_inf_extra_inf",
        ),
        pytest.param(
            Spec.INF_G1 + Spec.G1 + Spec.INF_G1,
            Spec.G1,
            id="inf_plus_generator_extra_inf",
        ),
        pytest.param(
            b"",
            Spec.INF_G1,
            id="empty",
        ),
        pytest.param(
            Spec.INF_G1,
            Spec.INF_G1,
            id="single_inf",
        ),
        pytest.param(
            Spec.INF_G1 + Spec.INF_G1,
            Spec.INF_G1,
            id="double_inf",
        ),
        pytest.param(
            Spec.INF_G1 + Spec.INF_G1 + Spec.INF_G1,
            Spec.INF_G1,
            id="triple_inf",
        ),
        pytest.param(
            bytes(Spec.INF_G1)[:-1],
            Spec.INF_G1,
            id="inf_minus_1_byte",
        ),
        pytest.param(
            Spec.INF_G1 + b"\0" * 1,
            Spec.INF_G1,
            id="inf_plus_1_zero_byte",
        ),
        pytest.param(
            Spec.INF_G1 + Spec.INF_G1 + b"\0" * 1,
            Spec.INF_G1,
            id="double_inf_plus_1_zero_byte",
        ),
        pytest.param(
            b"\0" * 80,
            Spec.INF_G1,
            id="80_zero_bytes",
        ),
        pytest.param(
            Spec.G1,
            Spec.G1,
            id="single_generator",
        ),
        pytest.param(
            Spec.G1 + Spec.G1,
            Spec.G1x2,
            id="double_generator",
        ),
        pytest.param(
            Spec.G1 + Spec.G1 + Spec.G1,
            Spec.G1x2,  # Last generator is ignored data
            id="triple_generator",
        ),
        pytest.param(
            Spec.G1 + Spec.G1 + Spec.INF_G1,
            Spec.G1x2,
            id="double_generator_extra_inf",
        ),
        pytest.param(
            Spec.G1 + Spec.G1 + PointG1(1, 3),
            Spec.G1x2,  # Extra invalid point is ignored
            id="double_generator_extra_pt_1_3",
        ),
        pytest.param(
            Spec.P1 + Spec.Q1,
            Spec.R1,
            id="p1_plus_q1",
        ),
        pytest.param(
            Spec.P1 + PointG1(Spec.P1.x, Spec.P - Spec.P1.y),
            Spec.INF_G1,
            id="p1_plus_neg_p1",
        ),
        pytest.param(
            Spec.S1 + Spec.S1,
            Spec.S1x2,
            id="s1_doubled",
        ),
        pytest.param(
            Spec.S1 + Spec.S1x2,
            Spec.S1x3,
            id="s1_plus_s1x2",
        ),
        pytest.param(
            Spec.S1 + Spec.G1,
            Spec.S1_PLUS_G1,
            id="s1_plus_generator",
        ),
        pytest.param(
            Spec.S1,
            Spec.S1,
            id="single_s1",
        ),
        # Ported from pointMulAdd / pointMulAdd2 (ECADD vs ECMUL)
        pytest.param(
            Spec.S1x2 + Spec.S1,
            Spec.S1x3,
            id="s1x2_plus_s1",
        ),
        pytest.param(
            PointG1(Spec.S1x3.x, Spec.P - Spec.S1x3.y) + Spec.S1x3,
            Spec.INF_G1,
            id="neg_s1x3_plus_s1x3",
        ),
        pytest.param(
            PointG1(Spec.S1x3.x, Spec.P - Spec.S1x3.y)
            + PointG1(Spec.S1x3.x, Spec.P - Spec.S1x3.y),
            PointG1(
                0x255E468453D7636CC1563E43F7521755F95E6C56043C7321B4AE04E772945FB0,
                0x225C5F1623620FD84BFBAB2D861A9D1E570F7727C540F403085998EBAF407C4,
            ),
            id="neg_s1x3_doubled",
        ),
        pytest.param(
            PointG1(Spec.S1x3.x, Spec.P - Spec.S1x3.y) + Spec.INF_G1,
            PointG1(Spec.S1x3.x, Spec.P - Spec.S1x3.y),
            id="neg_s1x3_plus_inf",
        ),
        pytest.param(
            Spec.S1x2 + Spec.INF_G1,
            Spec.S1x2,
            id="s1x2_plus_inf",
        ),
        pytest.param(
            Spec.G1 + PointG1(Spec.G1.x, Spec.P - Spec.G1.y),
            Spec.INF_G1,
            id="generator_plus_neg_generator",
        ),
        pytest.param(
            PointG1(Spec.G1.x, Spec.P - Spec.G1.y)
            + PointG1(Spec.G1.x, Spec.P - Spec.G1.y),
            PointG1(Spec.G1x2.x, Spec.P - Spec.G1x2.y),
            id="neg_generator_doubled",
        ),
        pytest.param(
            PointG1(Spec.G1x2.x, Spec.P - Spec.G1x2.y)
            + PointG1(Spec.G1.x, Spec.P - Spec.G1.y),
            PointG1(
                0x769BF9AC56BEA3FF40232BCB1B6BD159315D84715B8E679F2D355961915ABF0,
                0x5ACB4B400E90C0063006A39F478F3E865E306DD5CD56F356E2E8CD8FE7EDAE6,
            ),
            id="neg_g1x2_plus_neg_generator",
        ),
        pytest.param(
            PointG1(Spec.G1.x, Spec.P - Spec.G1.y) + Spec.INF_G1,
            PointG1(Spec.G1.x, Spec.P - Spec.G1.y),
            id="neg_generator_plus_inf",
        ),
        pytest.param(
            Spec.SAMPLE_G1 + PointG1(Spec.G1.x, Spec.P - Spec.G1.y),
            PointG1(
                0x113AECCECDAF57CD8C0AACE591774949DCDAF892555FA86726FA7E679B89C067,
                0xBFFBA84127A19ABDE488A8251A9A3FCE33B34A76F96AAFB11AB4A6CEF3E9979,
            ),
            id="sample_plus_neg_generator",
        ),
        pytest.param(
            Spec.SAMPLE_G1 + Spec.SAMPLE_G1,
            PointG1(
                0x1FD3B816D9951DCB9AA9797D25E51A865987703AE83CD69C4658679F0350AE2B,
                0x29CE3D80A74DDC13784BEB25CA9FBFD048A3265A32C6F38B92060C5093A0E7A7,
            ),
            id="sample_doubled",
        ),
        pytest.param(
            Spec.SAMPLE_G1 + Spec.INF_G1,
            Spec.SAMPLE_G1,
            id="sample_plus_inf",
        ),
        pytest.param(
            PointG1(Spec.G1x2_256_1.x, Spec.P - Spec.G1x2_256_1.y)
            + PointG1(Spec.G1.x, Spec.P - Spec.G1.y),
            PointG1(
                0x1D78954C630B3895FBBFAFAC1294F2C0158879FDC70BFE18222890E7BFB66FBA,
                0x101C3346E98B136A7078AEBD427DCED763722D77E3D7985342E0BFFCC6EA4D56,
            ),
            id="neg_g1x2_256_1_plus_neg_generator",
        ),
        pytest.param(
            PointG1(Spec.G1x2_256_1.x, Spec.P - Spec.G1x2_256_1.y)
            + PointG1(Spec.G1x2_256_1.x, Spec.P - Spec.G1x2_256_1.y),
            PointG1(
                0x2FA739D4CDE056D8FD75427345CBB34159856E06A4FFAD64159C4773F23FBF4B,
                0x1EED5D5325C31FC89DD541A13D7F63B981FAE8D4BF78A6B08A38A601FCFEA97B,
            ),
            id="neg_g1x2_256_1_doubled",
        ),
        pytest.param(
            PointG1(Spec.G1x2_256_1.x, Spec.P - Spec.G1x2_256_1.y)
            + Spec.INF_G1,
            PointG1(Spec.G1x2_256_1.x, Spec.P - Spec.G1x2_256_1.y),
            id="neg_g1x2_256_1_plus_inf",
        ),
        pytest.param(
            Spec.G1x2 + Spec.G1,
            PointG1(
                0x769BF9AC56BEA3FF40232BCB1B6BD159315D84715B8E679F2D355961915ABF0,
                0x2AB799BEE0489429554FDB7C8D086475319E63B40B9C5B57CDF1FF3DD9FE2261,
            ),
            id="g1x2_plus_generator",
        ),
        pytest.param(
            PointG1(Spec.G1.x, Spec.P - Spec.G1.y) + Spec.G1,
            Spec.INF_G1,
            id="neg_generator_plus_generator",
        ),
        pytest.param(
            PointG1(Spec.SAMPLE_G1.x, Spec.P - Spec.SAMPLE_G1.y) + Spec.G1,
            PointG1(
                0x113AECCECDAF57CD8C0AACE591774949DCDAF892555FA86726FA7E679B89C067,
                0x246493EECEB7867DDA07BB342FD7B460B44635E9F8DB1F922A7541A9E93E63CE,
            ),
            id="neg_sample_plus_generator",
        ),
        pytest.param(
            PointG1(Spec.SAMPLE_G1.x, Spec.P - Spec.SAMPLE_G1.y)
            + PointG1(Spec.SAMPLE_G1.x, Spec.P - Spec.SAMPLE_G1.y),
            PointG1(
                0x1FD3B816D9951DCB9AA9797D25E51A865987703AE83CD69C4658679F0350AE2B,
                0x69610F239E3C41640045A90B6E1988D4EDE443735AAD701AA1A7FC644DC15A0,
            ),
            id="neg_sample_doubled",
        ),
        pytest.param(
            PointG1(Spec.SAMPLE_G1.x, Spec.P - Spec.SAMPLE_G1.y) + Spec.INF_G1,
            PointG1(Spec.SAMPLE_G1.x, Spec.P - Spec.SAMPLE_G1.y),
            id="neg_sample_plus_inf",
        ),
        pytest.param(
            Spec.G1x2_256_1 + Spec.G1,
            PointG1(
                0x1D78954C630B3895FBBFAFAC1294F2C0158879FDC70BFE18222890E7BFB66FBA,
                0x20481B2BF7A68CBF47D796F93F038986340F3D19849A3239F93FCC1A1192AFF1,
            ),
            id="g1x2_256_1_plus_generator",
        ),
        pytest.param(
            Spec.G1x2_256_1 + Spec.G1x2_256_1,
            PointG1(
                0x2FA739D4CDE056D8FD75427345CBB34159856E06A4FFAD64159C4773F23FBF4B,
                0x1176F11FBB6E80611A7B04154401F4A4158681BCA8F923DCB1E7E614DB7E53CC,
            ),
            id="g1x2_256_1_doubled",
        ),
        pytest.param(
            Spec.G1x2_256_1 + Spec.INF_G1,
            Spec.G1x2_256_1,
            id="g1x2_256_1_plus_inf",
        ),
    ],
)
@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stZeroKnowledge/pointAddFiller.json",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stZeroKnowledge/pointAddTruncFiller.json",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stZeroKnowledge2/ecadd_0-0_0-0_21000_0Filler.json",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stZeroKnowledge2/ecadd_0-0_0-0_21000_64Filler.json",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stZeroKnowledge2/ecadd_0-0_0-0_21000_80_ParisFiller.json",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stZeroKnowledge2/ecadd_0-0_0-0_21000_128Filler.json",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stZeroKnowledge2/ecadd_0-0_0-0_21000_192Filler.json",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stZeroKnowledge2/ecadd_0-0_0-0_25000_0Filler.json",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stZeroKnowledge2/ecadd_0-0_0-0_25000_64Filler.json",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stZeroKnowledge2/ecadd_0-0_0-0_25000_80Filler.json",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stZeroKnowledge2/ecadd_0-0_0-0_25000_128Filler.json",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stZeroKnowledge2/ecadd_0-0_0-0_25000_192Filler.json",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stZeroKnowledge2/ecadd_0-0_1-2_21000_128Filler.json",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stZeroKnowledge2/ecadd_0-0_1-2_21000_192Filler.json",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stZeroKnowledge2/ecadd_0-0_1-2_25000_128Filler.json",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stZeroKnowledge2/ecadd_0-0_1-2_25000_192Filler.json",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stZeroKnowledge2/ecadd_1-2_0-0_21000_64Filler.json",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stZeroKnowledge2/ecadd_1-2_0-0_21000_128Filler.json",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stZeroKnowledge2/ecadd_1-2_0-0_21000_192Filler.json",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stZeroKnowledge2/ecadd_1-2_0-0_25000_64Filler.json",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stZeroKnowledge2/ecadd_1-2_0-0_25000_128Filler.json",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stZeroKnowledge2/ecadd_1-2_0-0_25000_192Filler.json",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stZeroKnowledge2/ecadd_1-2_1-2_21000_128Filler.json",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stZeroKnowledge2/ecadd_1-2_1-2_21000_192Filler.json",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stZeroKnowledge2/ecadd_1-2_1-2_25000_128Filler.json",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stZeroKnowledge2/ecadd_1-2_1-2_25000_192Filler.json",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stZeroKnowledge2/ecadd_1145-3932_1145-4651_21000_192Filler.json",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stZeroKnowledge2/ecadd_1145-3932_1145-4651_25000_192Filler.json",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stZeroKnowledge2/ecadd_1145-3932_2969-1336_21000_128Filler.json",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stZeroKnowledge2/ecadd_1145-3932_2969-1336_25000_128Filler.json",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stZeroKnowledge/pointMulAddFiller.json",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stZeroKnowledge/pointMulAdd2Filler.json",
    ],
    pr=[
        "https://github.com/ethereum/execution-specs/pull/1935",
        "https://github.com/ethereum/execution-specs/pull/2477",
    ],
)
def test_valid(
    state_test: StateTestFiller,
    pre: Alloc,
    post: dict,
    tx: Transaction,
) -> None:
    """Test the valid inputs to the ECADD precompile."""
    state_test(pre=pre, tx=tx, post=post)


@pytest.mark.parametrize(
    "input_data, expected_output",
    [
        pytest.param(
            PointG1(1, 1) + Spec.INF_G1,
            b"",
            id="pt_1_1_plus_inf",
        ),
        pytest.param(
            Spec.INF_G1 + PointG1(1, 3),
            b"",
            id="inf_plus_pt_1_3",
        ),
        pytest.param(
            PointG1(0, 3) + Spec.INF_G1,
            b"",
            id="pt_0_3_plus_inf",
        ),
        pytest.param(
            PointG1(1, 3) + b"\0" * 1,
            b"",
            id="pt_1_3_plus_1_zero_byte",
        ),
        pytest.param(
            PointG1(1, 3) + b"\0" * 16,
            b"",
            id="pt_1_3_plus_16_zero_bytes",
        ),
        pytest.param(
            PointG1(1, 3) + b"\0" * 32,
            b"",
            id="pt_1_3_plus_32_zero_bytes",
        ),
        pytest.param(
            PointG1(6, 9) + PointG1(0x126198C, 0x1E4DC),
            b"",
            id="pt_6_9_plus_pt_0x126198c_0x1e4dc",
        ),
        pytest.param(
            PointG1(Spec.G1.x + Spec.P, Spec.G1.y) + Spec.INF_G1,
            b"",
            id="Pplus1_2_plus_inf",
        ),
        pytest.param(
            PointG1(Spec.G1.x, Spec.G1.y + Spec.P) + Spec.INF_G1,
            b"",
            id="1_Pplus2_plus_inf",
        ),
        pytest.param(
            Spec.INF_G1 + PointG1(Spec.G1.x + Spec.P, Spec.G1.y),
            b"",
            id="inf_plus_Pplus1_2",
        ),
        pytest.param(
            Spec.INF_G1 + PointG1(Spec.G1.x, Spec.G1.y + Spec.P),
            b"",
            id="inf_plus_1_Pplus2",
        ),
        pytest.param(
            PointG1(Spec.P, 0) + Spec.INF_G1,
            b"",
            id="P_0_plus_inf",
        ),
        pytest.param(
            PointG1(0, Spec.P) + Spec.INF_G1,
            b"",
            id="0_P_plus_inf",
        ),
        pytest.param(
            Spec.INF_G1 + PointG1(Spec.P, 0),
            b"",
            id="inf_plus_P_0",
        ),
        pytest.param(
            Spec.INF_G1 + PointG1(0, Spec.P),
            b"",
            id="inf_plus_0_P",
        ),
        pytest.param(
            Spec.S1 + Spec.S1_INVALID,
            b"",
            id="valid_plus_not_on_curve",
        ),
        pytest.param(
            Spec.S1_INVALID + Spec.S1,
            b"",
            id="not_on_curve_plus_valid",
        ),
        pytest.param(
            Spec.S1_INVALID + Spec.S1_INVALID,
            b"",
            id="not_on_curve_plus_not_on_curve",
        ),
    ],
)
@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stZeroKnowledge/pointAddFiller.json",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stZeroKnowledge/pointAddTruncFiller.json",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stZeroKnowledge2/ecadd_0-0_1-3_21000_128Filler.json",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stZeroKnowledge2/ecadd_0-0_1-3_25000_128Filler.json",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stZeroKnowledge2/ecadd_0-3_1-2_21000_128Filler.json",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stZeroKnowledge2/ecadd_0-3_1-2_25000_128Filler.json",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stZeroKnowledge2/ecadd_1-3_0-0_21000_80Filler.json",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stZeroKnowledge2/ecadd_1-3_0-0_25000_80_ParisFiller.json",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stZeroKnowledge2/ecadd_6-9_19274124-124124_21000_128Filler.json",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stZeroKnowledge2/ecadd_6-9_19274124-124124_25000_128Filler.json",
    ],
    pr=[
        "https://github.com/ethereum/execution-specs/pull/1935",
        "https://github.com/ethereum/execution-specs/pull/2477",
    ],
)
@pytest.mark.eels_base_coverage
def test_invalid(
    state_test: StateTestFiller,
    pre: Alloc,
    post: dict,
    tx: Transaction,
) -> None:
    """Test the invalid inputs to the ECADD precompile."""
    state_test(pre=pre, tx=tx, post=post)
