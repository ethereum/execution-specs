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
        pytest.param(
            Spec.G1
            + Spec.G2
            + Spec.G1
            + PointG2(
                Spec.G2.x,
                (
                    0x275DC4A288D1AFB3CBB1AC09187524C7DB36395DF7BE3B99E673B13A075A65EC,
                    0x1D9BEFCD05A5323E6DA4D435F3B617CDB3AF83285C2DF711EF39C01571827F9D,
                ),
            ),
            Spec.PAIRING_TRUE,
            id="two_point_match_2",
        ),
        pytest.param(
            Spec.G1
            + PointG2(
                (
                    0x203E205DB4F19B37B60121B83A7333706DB86431C6D835849957ED8C3928AD79,
                    0x27DC7234FD11D3E8C36C59277C3E6F149D5CD3CFA9A62AEE49F8130962B4B3B9,
                ),
                (
                    0x195E8AA5B7827463722B8C153931579D3505566B4EDF48D498E185F0509DE152,
                    0x04BB53B8977E5F92A0BC372742C4830944A59B4FE6B1C0466E2A6DAD122B5D2E,
                ),
            )
            + PointG1(
                0x030644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD3,
                0x1A76DAE6D3272396D0CBE61FCED2BC532EDAC647851E3AC53CE1CC9C7E645A83,
            )
            + Spec.G2,
            Spec.PAIRING_TRUE,
            id="two_point_match_3",
        ),
        pytest.param(
            PointG1(
                0x105456A333E6D636854F987EA7BB713DFD0AE8371A72AEA313AE0C32C0BF1016,
                0x0CF031D41B41557F3E7E3BA0C51BEBE5DA8E6ECD855EC50FC87EFCDEAC168BCC,
            )
            + PointG2(
                (
                    0x0476BE093A6D2B4BBF907172049874AF11E1B6267606E00804D3FF0037EC57FD,
                    0x3010C68CB50161B7D1D96BB71EDFEC9880171954E56871ABF3D93CC94D745FA1,
                ),
                (
                    0x14C059D74E5B6C4EC14AE5864EBE23A71781D86C29FB8FB6CCE94F70D3DE7A21,
                    0x01B33461F39D9E887DBB100F170A2345DDE3C07E256D1DFA2B657BA5CD030427,
                ),
            )
            + Spec.G1
            + PointG2(
                (
                    0x1A2C3013D2EA92E13C800CDE68EF56A294B883F6AC35D25F587C09B1B3C635F7,
                    0x290158A80CD3D66530F74DC94C94ADB88F5CDB481ACCA997B6E60071F08A115F,
                ),
                (
                    0x2F997F3DBD66A7AFE07FE7862CE239EDBA9E05C5AFFF7F8A1259C9733B2DFBB9,
                    0x29D1691530CA701B4A106054688728C9972C8512E9789E9567AAE23E302CCD75,
                ),
            ),
            Spec.PAIRING_TRUE,
            id="two_point_match_4",
        ),
        pytest.param(
            Spec.G1 + Spec.INF_G2 + Spec.INF_G1 + Spec.G2,
            Spec.PAIRING_TRUE,
            id="two_point_match_5",
        ),
        pytest.param(
            PointG1(
                0x105456A333E6D636854F987EA7BB713DFD0AE8371A72AEA313AE0C32C0BF1016,
                0x0CF031D41B41557F3E7E3BA0C51BEBE5DA8E6ECD855EC50FC87EFCDEAC168BCC,
            )
            + PointG2(
                (
                    0x0476BE093A6D2B4BBF907172049874AF11E1B6267606E00804D3FF0037EC57FD,
                    0x3010C68CB50161B7D1D96BB71EDFEC9880171954E56871ABF3D93CC94D745FA1,
                ),
                (
                    0x14C059D74E5B6C4EC14AE5864EBE23A71781D86C29FB8FB6CCE94F70D3DE7A21,
                    0x01B33461F39D9E887DBB100F170A2345DDE3C07E256D1DFA2B657BA5CD030427,
                ),
            )
            + Spec.G1
            + PointG2(
                (
                    0x1A2C3013D2EA92E13C800CDE68EF56A294B883F6AC35D25F587C09B1B3C635F7,
                    0x290158A80CD3D66530F74DC94C94ADB88F5CDB481ACCA997B6E60071F08A115F,
                ),
                (
                    0x2F997F3DBD66A7AFE07FE7862CE239EDBA9E05C5AFFF7F8A1259C9733B2DFBB9,
                    0x29D1691530CA701B4A106054688728C9972C8512E9789E9567AAE23E302CCD75,
                ),
            )
            + Spec.G1
            + Spec.INF_G2,
            Spec.PAIRING_TRUE,
            id="three_point_match_1",
        ),
        pytest.param(
            # e(16*G1, G2) * e(G1, -16*G2) == 1
            # Exercises the FQ2 multiplicative inverse for scalar 16,
            # which previously triggered a bug in the specification.
            PointG1(
                0x17F485337F6E10FCA0E385F7A93D1AC0A977E43995C3E4D9B8F89DAA6A183F44,
                0x05CCDC1561DB963516DA62C66EDD39D1BB9C6C4674990C4440403C88025C95AD,
            )
            + Spec.G2
            + Spec.G1
            + PointG2(
                (
                    0x27A819BCF5C2C30229550CC0D34EE9C923EE6C3033A89F0BE27204893B112207,
                    0x29E39258393EE0C24EB66B69973E9FEB8B02E9D94A9897492C98EFE5B0EB459A,
                ),
                (
                    0x12C79F74D498D73F3F1C4F2489FF4C5EF88C6A2C932560FEC4B5D2A1AE20D274,
                    0x1FBD1A0CA265F11112AF813152C1AD30B95AA1CBF94F7571552CA27658A6940C,
                ),
            ),
            Spec.PAIRING_TRUE,
            id="fq2_inverse_scalar_16",
        ),
    ],
)
@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecpairing_empty_dataFiller.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecpairing_one_point_with_g1_zeroFiller.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecpairing_one_point_with_g2_zeroFiller.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecpairing_two_point_match_1Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecpairing_two_point_match_2Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecpairing_two_point_match_3Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecpairing_two_point_match_4Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecpairing_two_point_match_5Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecpairing_three_point_match_1Filler.json",
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
        pytest.param(
            Spec.G1 + Spec.G2 + Spec.G1 + Spec.G2,
            Spec.PAIRING_FALSE,
            id="two_point_fail_1",
        ),
        pytest.param(
            PointG1(
                0x105456A333E6D636854F987EA7BB713DFD0AE8371A72AEA313AE0C32C0BF1016,
                0x0CF031D41B41557F3E7E3BA0C51BEBE5DA8E6ECD855EC50FC87EFCDEAC168BCC,
            )
            + PointG2(
                (
                    0x0476BE093A6D2B4BBF907172049874AF11E1B6267606E00804D3FF0037EC57FD,
                    0x3010C68CB50161B7D1D96BB71EDFEC9880171954E56871ABF3D93CC94D745FA1,
                ),
                (
                    0x14C059D74E5B6C4EC14AE5864EBE23A71781D86C29FB8FB6CCE94F70D3DE7A21,
                    0x01B33461F39D9E887DBB100F170A2345DDE3C07E256D1DFA2B657BA5CD030427,
                ),
            )
            + Spec.G1
            + PointG2(
                (
                    0x105384B6DD6C48634B9FE89CB3E19667C1FE6736C69DF070D674C95A42B3B824,
                    0x2C0D8E67F0F2C14C43734B430D8BE4265AF8C4F7A67DEB0B029FD2DFF99CC6B9,
                ),
                (
                    0x015EAEC465D922580C7DE5D4A5C26DE75EAF2AF6841B7412EF2EEBD1E051076F,
                    0x1B4C21849E48DE12D1BAE2BAD3299717AA8664ADE430E19DEC72A6E10A39B0AB,
                ),
            ),
            Spec.PAIRING_FALSE,
            id="two_point_fail_2",
        ),
        pytest.param(
            Spec.G1 + Spec.INF_G2 + Spec.G1 + Spec.G2,
            Spec.PAIRING_FALSE,
            id="two_points_with_one_g2_zero",
        ),
        pytest.param(
            PointG1(
                0x105456A333E6D636854F987EA7BB713DFD0AE8371A72AEA313AE0C32C0BF1016,
                0x0CF031D41B41557F3E7E3BA0C51BEBE5DA8E6ECD855EC50FC87EFCDEAC168BCC,
            )
            + PointG2(
                (
                    0x0476BE093A6D2B4BBF907172049874AF11E1B6267606E00804D3FF0037EC57FD,
                    0x3010C68CB50161B7D1D96BB71EDFEC9880171954E56871ABF3D93CC94D745FA1,
                ),
                (
                    0x14C059D74E5B6C4EC14AE5864EBE23A71781D86C29FB8FB6CCE94F70D3DE7A21,
                    0x01B33461F39D9E887DBB100F170A2345DDE3C07E256D1DFA2B657BA5CD030427,
                ),
            )
            + Spec.G1
            + PointG2(
                (
                    0x1A2C3013D2EA92E13C800CDE68EF56A294B883F6AC35D25F587C09B1B3C635F7,
                    0x290158A80CD3D66530F74DC94C94ADB88F5CDB481ACCA997B6E60071F08A115F,
                ),
                (
                    0x00CACF3523CAF879D7D05E30549F1E6FDCE364CBB8724B0329C6C2A39D4F018E,
                    0x0692E55DB067300E6E3FE56218FA2F940054E57E7EF92BF7D475A9D8A8502FD2,
                ),
            )
            + Spec.G1
            + Spec.G2,
            Spec.PAIRING_FALSE,
            id="three_point_fail_1",
        ),
    ],
)
@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecpairing_one_point_failFiller.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecpairing_two_point_fail_1Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecpairing_two_point_fail_2Filler.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecpairing_two_points_with_one_g2_zeroFiller.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecpairing_three_point_fail_1Filler.json",
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
        pytest.param(
            PointG1(Spec.P, 0) + Spec.G2,
            Spec.INVALID,
            id="perturb_zeropoint_by_field_modulus",
        ),
        pytest.param(
            PointG1(1, 0) + Spec.G2,
            Spec.INVALID,
            id="perturb_zeropoint_by_one",
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
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecpairing_perturb_zeropoint_by_field_modulusFiller.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecpairing_perturb_zeropoint_by_oneFiller.json",
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
        pytest.param(
            Spec.G1 + Spec.G2 + PointG1(0x1, Spec.P - 2) + Spec.G2,
            Spec.INVALID,
            -1,
            id="two_point_oog",
        ),
    ],
)
@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecpairing_empty_data_insufficient_gasFiller.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecpairing_one_point_insufficient_gasFiller.json",
        "https://github.com/ethereum/legacytests/tree/master/Cancun/GeneralStateTests/stZeroKnowledge/ecpairing_two_point_oogFiller.json",
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
