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
    ],
)
@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge2/ecadd_0-0_0-0_21000_0Filler.json"
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge2/ecadd_0-0_0-0_21000_64Filler.json"
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge2/ecadd_0-0_0-0_21000_80_ParisFiller.json"
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge2/ecadd_0-0_0-0_21000_128Filler.json"
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge2/ecadd_0-0_0-0_21000_192Filler.json"
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge2/ecadd_0-0_0-0_25000_0Filler.json"
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge2/ecadd_0-0_0-0_25000_64Filler.json"
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge2/ecadd_0-0_0-0_25000_80Filler.json"
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge2/ecadd_0-0_0-0_25000_128Filler.json"
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge2/ecadd_0-0_0-0_25000_192Filler.json"
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge2/ecadd_0-0_1-2_21000_128Filler.json"
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge2/ecadd_0-0_1-2_21000_192Filler.json"
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge2/ecadd_0-0_1-2_25000_128Filler.json"
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge2/ecadd_0-0_1-2_25000_192Filler.json"
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge2/ecadd_1-2_0-0_21000_64Filler.json"
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge2/ecadd_1-2_0-0_21000_128Filler.json"
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge2/ecadd_1-2_0-0_21000_192Filler.json"
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge2/ecadd_1-2_0-0_25000_64Filler.json"
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge2/ecadd_1-2_0-0_25000_128Filler.json"
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge2/ecadd_1-2_0-0_25000_192Filler.json"
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge2/ecadd_1-2_1-2_21000_128Filler.json"
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge2/ecadd_1-2_1-2_21000_192Filler.json"
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge2/ecadd_1-2_1-2_25000_128Filler.json"
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge2/ecadd_1-2_1-2_25000_192Filler.json"
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge2/ecadd_1145-3932_1145-4651_21000_192Filler.json"
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge2/ecadd_1145-3932_1145-4651_25000_192Filler.json"
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge2/ecadd_1145-3932_2969-1336_21000_128Filler.json"
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge2/ecadd_1145-3932_2969-1336_25000_128Filler.json"
    ],
    pr=["https://github.com/ethereum/execution-specs/pull/1935"],
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
            id="Pplus1_2_plus_inf",
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
    ],
)
@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge2/ecadd_0-0_1-3_21000_128Filler.json"
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge2/ecadd_0-0_1-3_25000_128Filler.json"
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge2/ecadd_0-3_1-2_21000_128Filler.json"
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge2/ecadd_0-3_1-2_25000_128Filler.json"
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge2/ecadd_1-3_0-0_21000_80Filler.json"
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge2/ecadd_1-3_0-0_25000_80_ParisFiller.json"
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge2/ecadd_6-9_19274124-124124_21000_128Filler.json"
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge2/ecadd_6-9_19274124-124124_25000_128Filler.json"
    ],
    pr=["https://github.com/ethereum/execution-specs/pull/1935"],
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
