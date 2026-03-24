"""
Test the ecpairing precompiled contract using fuzzed inputs from
ecpairing_inputsFiller.yml static test.
"""

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
    pytest.mark.ported_from(
        [
            "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stZeroKnowledge/ecpairing_inputsFiller.yml",
        ],
        pr=["https://github.com/ethereum/execution-specs/pull/2443"],
    ),
]


@pytest.mark.parametrize(
    "expected_output", [pytest.param(Spec.INVALID, id=pytest.HIDDEN_PARAM)]
)
@pytest.mark.parametrize(
    "input_data",
    [
        pytest.param(
            PointG1(
                0x0, 0xBE00BE00BEBEBEBEBEBE0000000000000000000000000000000000
            )
            + Spec.INF_G2,
        ),
        pytest.param(
            PointG1(0x0, 0xFFFFFFFF << 216) + Spec.INF_G2,
        ),
        pytest.param(
            PointG1(0x0, Spec.P - 0x1B7193500000000002) + Spec.INF_G2,
        ),
        pytest.param(
            PointG1(
                0xFFFF7D7D7D7D7D7D7D7D7D7D7D7D,
                0x30644E72E131A0297D7D7D7DFFFFFFFFFF000000000000000000000000000000,
            )
            + PointG2(
                (
                    0xFF7D7D7D7D7D817D7D7D7D7DFFFFFFFFFFA100,
                    0xFFFFFFFFFFFFFFFFFFFFFFFFFFFF7D7D7D7D7D7D7D7D7D7D7D7D,
                ),
                (
                    0x30644E72E131A0297D7D7D7DFFFFFFFFFF000000000000000000000000000000,
                    0xFF7D7D7D7D7D817D7D7D7D7D827D7D7D7D7D7D,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x2900000000000000000000000000000000000000000000000000, 0x0
            )
            + PointG2(
                (0xFFFFFFFFFFFFFFF80000000000000000000000, 0x0), (0x0, 0x0)
            ),
        ),
        pytest.param(
            PointG1(
                0xFFFFFFFFFDFFFFFE2E0000000000000000000000000000000000, 0x0
            )
            + Spec.INF_G2,
        ),
        pytest.param(
            PointG1(
                0x0A12D3FB2743836BBBB51414A351E5E70429A5DE70C0FE7CEC084E47D6027709,
                0x006A8C414196ABF21DA0B3F6944846C77A1032B519BAA1ABF125F4F84010C47A,
            )
            + PointG2(
                (
                    0x250F9CF43675BC1077753C607600F3E51B627A10F3AA68A7E462D89A6BD2A213,
                    0x12AE5D695C4F9792CF70228A1BA07E5E0C2CB47D7AECBAE923A84A3734A94FF1,
                ),
                (
                    0x0BDCD3D0B8E47A925F98BAD0184DFE81967AAFF8DB8F0DFAE31AFCCBCB8C4BD6,
                    0x148DFF646F2764243BA9100A930EB7CC8C766B58E0D9953256698DA5DBE66CC3,
                ),
            )
            + PointG1(
                0x1F372B78747DB898121455853A5672E71977957F134615FD0DD1FAB4938B65E7,
                0x201458C7D8EC49141BD3289F8CC4D19BB52041D51187432579E2E67CAB27C847,
            )
            + PointG2(
                (
                    0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
                    0x1800DEEF121F1E76426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED,
                ),
                (
                    0x090689D0585FF075EC9E99AD690C3395BC4B313370B38EF355ACDADCD122975B,
                    0x12C85EA5DB8C6DEB4AAB71808DCB408FE3D1E7690C43D37B4CE6CC0166FA7DAA,
                ),
            )
            + PointG1(
                0x2110E6D9F2378C1C1CD070A3F1507C3AA924A60F67259ABE487621B0D3C5C38F,
                0x0C26130B8AAA54109A5D82FBB2782B9ED461A4B8FAA69341CCF652D2F73E1887,
            )
            + PointG2(
                (
                    0x22F1ACBB03C4508760C2430AF35865E7CDF9F3EB1224504FDCC3708DDB954A48,
                    0x2A344FAD01C2ED0ED73142AE1752429EAEA515C6F3F6B941103CC21C2308E1CB,
                ),
                (
                    0x159F15B842BA9C8449AA3268F981010D4C7142E5193473D80B464E964845C3F8,
                    0x0EFD30AC7B6F8D0D3CCBC2207587C2ACBAD1532DC0293F0D034CF8258CD428B3,
                ),
            )
            + PointG1(
                0x00710C68E1B8B73A72A289422D2B6F841CC56FE8C51105021C56AE30C3AE1ACA,
                0x0B2FF392A2FC535427EC9B7E1AE1C35A7961986788CF648349190DD92E182F05,
            )
            + PointG2(
                (
                    0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
                    0x1800DEEF121F1E76426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED,
                ),
                (
                    0x090689D0585FF075EC9E99AD690C3395BC4B313370B38EF355ACDADCD122975B,
                    0x12C85EA5DB8C6DEB4AAB71808DCB408FE3D1E7690C43D37B4CE6CC0166FA7DAA,
                ),
            )
            + PointG1(
                0xBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBE,
                0xBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBE,
            )
            + PointG2(
                (
                    0xBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBE,
                    0xBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBE,
                ),
                (
                    0xBEFDBEBEBEBEABC689BEBEBEBE43BE92BE5FBEBEBEBEBEBEBEBEBEBEBEBEBEBE,
                    0xBEBEBEBEBEBEBEBEBE9EBEBEBE2ABEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBE,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x25A78FA05DE3E5F7C69F35AB209D6595697E8664C3572A57EA0C971FE33532ED,
                0x0BC38B0A2D9961CF8D392DE63BE18471FFAAA192111CD8ADCCC98B7D790B6114,
            )
            + Spec.INF_G2
            + PointG1(
                0x8013E823575500FFFFFFFFFFFFFFFA00000000000000000000000000, 0x0
            )
            + Spec.INF_G2,
        ),
        pytest.param(
            PointG1(
                0x2DEC711C75595613E8F7E4723C19F6E69BE2EBAFE07E965A001F4FA00A41EECC,
                0x10246180D145035DFE0E334A8E1F4274A189B8DDE0B2CC683CDDFD9CAE9B634B,
            )
            + PointG2(
                (
                    0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
                    0x1800DEEF121F1E76426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED,
                ),
                (
                    0x090689D0585FF075EC9E99AD690C3395BC4B313370B38EF355ACDADCD122975B,
                    0x12C85EA5DB8C6DEB4AAB71808DCB408FE3D1E7690C43D37B4CE6CC0166FA7DAA,
                ),
            )
            + PointG1(0x0, 0xFFFFFFFFFFFFFF0F000000000000000000)
            + Spec.INF_G2,
        ),
        pytest.param(
            PointG1(
                0x30644E72E131A029B85045AC81EC585DFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                0xFFFF7D7DFFFF7D817F827D7D7D7D7D7D7D7D7D7D7D7D7D7D7D7D7D7D7D7D7D7D,
            )
            + PointG2(
                (
                    0x7D7D767D7D7D7D7D7D797D7D7D7D7D7D7D7D7D7D7D7D7D7D7D7D7D7D7D7F7D7D,
                    0x7D7D7D7D7D7D7D7D7D7D7D7D7D7D7D8D7D7D7D7D7D7D7DFFFFFFFFFFFFFFFFFF,
                ),
                (
                    0xFFFF01FFFFFFFFFFFFFFFFFFFFFF747D7D7D7D7D7D7D7D7DFD7D7D7D7D7D7D7D,
                    0x7D7D7D7D7D7D7D7D7D7D7DFFFFFFFFFFFFFFFFFFFFFFFF29FFFFFF0AFFFFFF0A,
                ),
            ),
        ),
        pytest.param(
            PointG1(Spec.N, 0x0)
            + PointG2(
                (
                    0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
                    0x1800DEEF121F1E76426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED,
                ),
                (
                    0x090689D0585FF075EC9E99AD690C3395BC4B313370B38EF355ACDADCD122975B,
                    0x12C85EA5DB8C6DEB4AAB71808DCB408FE3D1E7690C43D37B4CE6CC0166FA7DAA,
                ),
            ),
        ),
        pytest.param(
            PointG1(Spec.P, 0x0)
            + PointG2(
                (
                    0xFFFFFF000060BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
                    0x1800DEEF121F1E76426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED,
                ),
                (
                    0x090689D0585FF075EC9E99AD0C693395BC4B313370B38EF355ACDADCD122975B,
                    0x12C85EA5DB8C6DEB4AAB71808DCB408FE3D1E7690C43D37B4CE6CC0166FA7DAA,
                ),
            ),
        ),
        pytest.param(
            PointG1(Spec.P + 0x10000000000, 0x0)
            + Spec.INF_G2
            + Spec.INF_G1
            + Spec.INF_G2,
        ),
    ],
    ids=lambda _: "invalid_g1_point_",
)
def test_invalid_g1_point(
    state_test: StateTestFiller,
    pre: Alloc,
    post: dict,
    tx: Transaction,
) -> None:
    """Test invalid g1 point inputs to the ecpairing precompile."""
    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post=post,
    )


@pytest.mark.parametrize(
    "expected_output", [pytest.param(Spec.INVALID, id=pytest.HIDDEN_PARAM)]
)
@pytest.mark.parametrize(
    "input_data",
    [
        pytest.param(
            Spec.INF_G1
            + Spec.INF_G2
            + Spec.INF_G1
            + PointG2(
                (
                    0x2D00E9FF0000000000000000FFFFFFFFFFFFFFFFBFB2FFFFFFFFFFFFFFFFA120,
                    0xFFFFFFFFFFF7FFFFFFFFFFFF0000000000000000000000000000,
                ),
                (
                    0x2D0002FF0000000000000000FFFFFFFFFFFF,
                    0xFFFFBFFFFFFFFFFFFFFFFFFFA120000000000000FF007D7D7D7D7D7D7D7D7D7D,
                ),
            ),
        ),
        pytest.param(
            Spec.INF_G1
            + PointG2(
                (0x0, 0x0),
                (0x0, 0xFFFFFFFFFFFF0000000000000000FFFFFFFFFFFFFFFFFFFF),
            ),
        ),
        pytest.param(
            Spec.INF_G1
            + PointG2((0x0, 0x0), (0x8000000, 0x0))
            + PointG1(0xF8FFFFFFFFFFFFFF0000, 0x0)
            + PointG2((0x0, 0x0), (0x8000000, 0x0)),
        ),
        pytest.param(
            Spec.INF_G1
            + PointG2(
                (0xFFFFFFFFFFFFFFFFFFA10000000000FFFFFFFFFFFFFFFFFFA100, 0x0),
                (
                    0x16C46EBE0077418D002F28E20236919AD92313729F18578BA8547626478EA52C,
                    0x2B5B688B4D8078D1E1ACD7ACC7BE7F9E0E30812CE2925B35559213646C93237F,
                ),
            )
            + Spec.INF_G1
            + Spec.INF_G2,
        ),
        pytest.param(
            Spec.INF_G1
            + PointG2(
                (0xFFFFFFFF << 184, 0xFFFFFFFF << 184),
                (
                    0x00FB55BF7DF894A746FBE20B6F8C54D0DC0D9FD4ED005174A42FC3C45E6E27F9,
                    0x12A20D63D446EB175733853B88DD36708EB7A81F5C79E7659C3A6E2B2C470077,
                ),
            )
            + PointG1(
                0x005ED60BA723A2DD3A5FC35520F982963DE61E3B563636FE6996CC2C30080357,
                0x20AD16F835A46FACA48C6D39AE00A10D3514E93AE3B946EE2F009EA2DCCFF97E,
            )
            + PointG2(
                (
                    0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
                    0x1800DEEF121F1E76426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED,
                ),
                (
                    0x09068950585FF0759E99ECAD6903000000000000000000000000000000002C00,
                    0x85B7AEF328C21800DEEF5E0000AA426A00665E0000AA,
                ),
            ),
        ),
        pytest.param(
            Spec.INF_G1
            + PointG2(
                (
                    0x1A76DAE6D3272396D0CBE61FCED2BC532EDAC647851E3AC53CE1CC9C7E645A83,
                    0x0,
                ),
                (
                    0x0,
                    0x1A76DAE6D3272396D0CBE61FCED2BC532EDAC647851E3AC53CE1CC9C7E645A83,
                ),
            )
            + PointG1(
                0x29A0D6D5E7D14A774C3ABFF1435361DA2EE5D8B4F3EE62085CE779F248B41D4A,
                0x2FD37AE5468F6A17B7F9A0BCCA02EE128BDCED61402A566E4EEE2D0FA825F03D,
            )
            + PointG2(
                (
                    0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
                    0x1800DEEF121F1E76426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED,
                ),
                (
                    0x090689D0585FF075EC9E99AD690C3395BC4B313370B38EF355ACDADCD122975B,
                    0x12C85EA5DB8C6DEB4AAB71808DCB408FE3D1E7690C43D37B4CE6CC0166FA7DAA,
                ),
            ),
        ),
        pytest.param(
            Spec.INF_G1
            + PointG2(
                (
                    0x2D00E9FF0000000000000000FFFFFFFFFFFFFFFFBFFFFFFFFFFFFFFFFFFFA120,
                    0xFFFFFFFFFFF7FFFFFFFFFFFF0000000000000000000000000000,
                ),
                (
                    0x2D0002FF0000000000000000FFFFFFFFFFFF,
                    0xFFFFBFFFFFFFFFFFFFFFFFFFA120000000000000FF007D7D7D7D7D7D7D7D7D7D,
                ),
            ),
        ),
        pytest.param(
            Spec.INF_G1
            + PointG2(
                (
                    0x30644E72E131A0294FAFBA497E1EC6D18C48814A690000000100000000300000,
                    0x00CD71EC682D26313681EA8A1A9A410C862CC44A5D0000000000000000000001,
                ),
                (
                    0x158D600A2D8411F2E9BD1A1B51EAC64E43B0C511F2E9BD1A1B51EAC64E43B0C5,
                    0x11FC9BA8B80B727A2C28EE454FC286FD659262C510A3E7F11A4B0E4B74BEBAFC,
                ),
            ),
        ),
        pytest.param(
            Spec.INF_G1
            + PointG2(
                (Spec.P, 0x45000000000000000000000000000000000000000000000001),
                (
                    0x07B55DE1642362D16B8FC4DCCFEC9E794D24968511CF8E252ED27AFC4D72CA1E,
                    0x0301CB4D7E0B7B52A6A8F78613C403EAD1543FEDB0D3F28C77685FDB9EAA2742,
                ),
            )
            + PointG1(
                0x0CDC335FA81DFF303B71CFFB0256D7097C2B4C6715CA7B1589EA9386A41C2F85,
                0x1223D6BB1F3E68DDFB08F4C95F590F99227FB681A3B0ABDF685CF12BDE37D8EE,
            )
            + PointG2(
                (0x0, 0x10000000000000000000000000000),
                (
                    0x1F1CD7F247F2AE1BA9A1AEB4B32ED4C8C13C70C8861B6AB5340E276C58E1046B,
                    0x13D7DE2B557E0AE2B53380AD596BA79F07C037C9D9AA17CF407E9ED86201436E,
                ),
            ),
        ),
        pytest.param(
            PointG1(0x1, 0x2)
            + Spec.INF_G2
            + Spec.INF_G1
            + PointG2(
                (
                    0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
                    0x1800DEEF121F1E76426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED,
                ),
                (
                    0x95BC4B313370B38EF355ACDADCD122975B4B313370B38EF355ACDADCD122975B,
                    0x120000C8DB8C6DEB4AAB71808DCB408FE3D1E7690C43D37B4CE6CC0166FA7DAA,
                ),
            ),
        ),
        pytest.param(
            PointG1(0x1, 0x2)
            + PointG2(
                (
                    0x5B0045000000000000000000000000000000000000000000000001,
                    Spec.P,
                ),
                (
                    0x218C0CEF2A606613357BFAA3C880E71FF8490195337FA26205A21CCD9A6949A3,
                    0x13FED2C79ADD9D85B9949C5852EF8CCCF02B69EA6FC4DB0D1660AC7B50DF39E1,
                ),
            )
            + PointG1(0x1, Spec.P - 2)
            + PointG2(
                (
                    0x5B0045000000000000000000000000000000000000000000000001,
                    Spec.P - 2,
                ),
                (
                    0x218C0CEF2A606613357BFAA3C880E71FF8490195337FA26205A21CCD9A6949A3,
                    0x13FED2C79ADD9D85B9949C5852EF8CCCF02B69EA6FC4DB0D1660AC7B50DF39E1,
                ),
            ),
        ),
        pytest.param(
            PointG1(0x1, 0x2)
            + PointG2(
                (
                    0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
                    0x1800DEEF121F1E76426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED,
                ),
                (
                    0x090689D0585FF075EC9E99AD690C3395BC4B313370B38EF355ACDADCD122975B,
                    0x12C85EA5DB8C6DEB4AAB71808DCB408FE3D1E7690C43D37B4CE6CC0166FA7DAA,
                ),
            )
            + PointG1(
                0x0F25929BCB43D5A57391564615C9E70A992B10EAFA4DB109709649CF48C50DD2,
                0x16DA2F5CB6BE7A0AA72C440C53C9BBDFEC6C36C7D515536431B3A865468ACBBA,
            )
            + PointG2(
                (
                    0x2E89718AD33C8BED92E210E81D1853435399A271913A6520736A4729CF0D51EB,
                    0x01A9E2FFA2E92599B68E44DE5BCF354FA2642BD4F26B259DAA6F7CE3ED57AEB3,
                ),
                (
                    0x14A9A87B789A58AF499B314E13C3D65BEDE56C07EA2D418D6874857B70763713,
                    0x178FB49A2D6CD347DC58973FF49613A20757D0FCC22079F9ABD10C3BAEE24590,
                ),
            )
            + PointG1(0x1, 0x2)
            + PointG2(
                (
                    0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
                    0x1800DEEF121F1E76426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED,
                ),
                (
                    0x090689D0585FF075EC9E99AD690C3395BC4B313370B38EF355ACDADCD122975B,
                    0x12C85EA5DB8C6DEB4AAB71808DCB408FE3D1E7690C43D37B4CE6CC0166FA7DAA,
                ),
            )
            + Spec.INF_G1
            + PointG2((0x200000000000000000000000000000B4, 0x0), (0x0, 0x0)),
        ),
        pytest.param(
            PointG1(
                0x2A4F1DBC9FE6D2882462FB11AFEAE7B7F2A0CF213B1F19C45CB222336283F380,
                0x1141763C897C9A90E387EA80F68EB88C2D79AAB680196D9538CD2CA632A5E81B,
            )
            + PointG2(
                (
                    0x0E540F5B5BE91F82ED05349750761224F543068CE30D2D5E838BF66866F34520,
                    0x0FA5AC8C46F725E54505019BDA3356EF6E35B0A89B9B4F79BB0C62211235C931,
                ),
                (
                    0x2E6D97A1F7E0428FC0BE6BE02C811095F5166710DCBE869C36A8EF89CAC63E01,
                    0x2657BBAF3BCFD106DD677EEF03172F693A6C919776F441DC0FD47A4BD91D0487,
                ),
            )
            + PointG1(
                0x225FDAB8FE6CD876363D27075CDF0D01C209DA61B1634B574A5D811CFAE40700,
                0x1216B7C3E2ADC07C3BEF31771C7BB9E1D02F07FF3A5B74953C4FD5BF9A7A6DFF,
            )
            + PointG2(
                (
                    0x25F63FCC543337B8F6275F97D6479633B921541A96AC1BC2AFF2E0905DB7407C,
                    0x206776F9480168741ECA625C06E5526B4664A02CE664BC656F39664D96278B6E,
                ),
                (
                    0x1E40E8084FD648BA315F691E8367BE1D4C13844421C87223D84829C31A0D7AFE,
                    0x24B8042D4CB604AE66C0DC97CA8A9C2D22C743335D92BC401700F6B00D5CDC5B,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x2ECA0C7238BF16E83E7A1E6C5D49540685FF51380F309842A98561558019FC02,
                0x03D3260361BB8451DE5FF5ECD17F010FF22F5C31CDF184E9020B06FA5997DB84,
            )
            + PointG2(
                (
                    0x1213D2149B006137FCFB23036606F848D638D576A120CA981B5B1A5F9300B3EE,
                    0x2276CF730CF493CD95D64677BBB75FC42DB72513A4C1E387B476D056F80AA75F,
                ),
                (
                    0x21EE6226D31426322AFCDA621464D0611D226783262E21BB3BC86B537E986237,
                    0x096DF1F82DFF337DD5972E32A8AD43E28A78A96A823EF1CD4DEBE12B6552EA5F,
                ),
            )
            + PointG1(
                0x06967A1237EBFECA9AAAE0D6D0BAB8E28C198C5A339EF8A2407E31CDAC516DB9,
                0x22160FA257A5FD5B280642FF47B65ECA77E626CB685C84FA6D3B6882A283DDD1,
            )
            + PointG2(
                (
                    0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
                    0xE8FF2110EDE0E189426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED,
                ),
                (
                    0x090689D0585FF075EC9E99AD690C3395BC4B313370B38EF355ACDADCD122975B,
                    0x12C85EA5DB8C6DEB4AAB71808DCB408FE3D1E7690C43D37B4CE6CC0166FA7DAA,
                ),
            ),
        ),
    ],
    ids=lambda _: "invalid_g2_point_",
)
def test_invalid_g2_point(
    state_test: StateTestFiller,
    pre: Alloc,
    post: dict,
    tx: Transaction,
) -> None:
    """Test invalid g2 point inputs to the ecpairing precompile."""
    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post=post,
    )


@pytest.mark.parametrize(
    "expected_output", [pytest.param(Spec.INVALID, id=pytest.HIDDEN_PARAM)]
)
@pytest.mark.parametrize(
    "input_data",
    [
        pytest.param(
            Spec.INF_G1
            + PointG2(
                (0x0, 0x800),
                (
                    0x104E75A20B641566A0C71C9069A5256391AA31E22021D36C037C108DFB79C662,
                    0x00BF257AE3D66A589214F980A2AE34F9544BE2FCBCC13B21F4C1642F31AA4D20,
                ),
            )
            + Spec.INF_G1
            + PointG2(
                (0x0, 0x800),
                (
                    0x104E75A20B641566A0C71C9069A5256391AA31E22021D36C037C108DFB79C662,
                    0x00BF257AE3D66A589214F980A2AE34F9544BE2FCBCC13B21F4C1642F31AA4D20,
                ),
            ),
        ),
        pytest.param(
            Spec.INF_G1
            + PointG2(
                (0x0, 0x80000000000000000000),
                (
                    0x12AB9BB0C853FB1D884197CDEFDF654C01A289B677094FE609C835D2B249DCC5,
                    0x1460243CC357281001B8B257C6396865C729761AC575A85B2F8F0E58AF439C84,
                ),
            )
            + Spec.INF_G1
            + Spec.INF_G2,
        ),
        pytest.param(
            Spec.INF_G1
            + PointG2(
                (
                    0x0,
                    0x080A77C09A07DFAF666EA36F7879462C0A78EB28F5C70B5ED35D438DC58F0D9D,
                ),
                (
                    0x058BCABF53CCB1B6F2AD14E6BC531485DBA856600B7941C8C5A4968940FBA978,
                    0x210DC371BFD9736EB879D25BE8A799EFF45BEA91130B9B2768689786235ACCD9,
                ),
            )
            + Spec.INF_G1
            + Spec.INF_G2
            + Spec.INF_G1
            + Spec.INF_G2
            + Spec.INF_G1
            + Spec.INF_G2,
        ),
        pytest.param(
            Spec.INF_G1
            + PointG2(
                (0x800104E75, 0x0),
                (
                    0x0A535BC14C0F581A039D0BFB15E730B6BBB3D6E33ECDA8C74EBD901DEEB4EF84,
                    0x23E99EADCC72CED9221DF2DB154B36F6931270C3F21F4EC8C4206B9211924BB2,
                ),
            )
            + PointG1(
                0x03A99966A8DB46602AC05B8F0D7669C3BC066FB7B9A188CC79E5239E27E35805,
                0x17E54F1FFF192038A907711C8123997F785D2C2C9A214355466B60652EE53E4D,
            )
            + PointG2(
                (
                    0x00C662006274FB346E22EEB59635C82CB4E20E34DA7230644E72E131C82CB4E2,
                    0x104E75A20B64000000000000000000150000000000000000006629C731,
                ),
                (
                    0x270EF2EA6F8C3DAD3832F95F309CB6A1591AD53AF025C6E0809992F15234E5FE,
                    0x1B37771CE3BB5A62017C56C496E57673E2617634E900C587724D21F24E603A63,
                ),
            )
            + PointG1(
                0x03A99966A8DB46602AC05B8F0D7669C3BC066FB7B9A188CC79E5239E27E35805,
                0x187EFF52E2187FF10F48D49A005DBEDE1F243E64CE508737F5B52BB1A997BEFA,
            )
            + PointG2(
                (0x0, 0xBF000000000000000000),
                (
                    0x1284BDD8E69832B232222D3493A6ABB523575BE2A5AF6E88F5501CEF408AA5BB,
                    0x0CA4D5B3C58E0BC7BE2C8885E53C673B54F3057CFF97CB1020CB2F5A9F61AFFB,
                ),
            )
            + Spec.INF_G1
            + PointG2((0x0, 0x0), (0x8000000, 0x0)),
        ),
        pytest.param(
            Spec.INF_G1
            + PointG2(
                (0x4000000000000000000, 0x0),
                (
                    0x0FB1B0E8C8B85EC99EBEDAE0880006B0809F5151890CCA524EEA2C0B3AD87F32,
                    0x29D3E6BC7F0886B75E186B10564DC990258855E0311E3E2E72F9D9C0DFAB4F0D,
                ),
            )
            + Spec.INF_G1
            + PointG2(
                (0x4000000000000000000, 0x0),
                (
                    0x0FB1B0E8C8B85EC99EBEDAE0880006B0809F5151890CCA524EEA2C0B3AD87F32,
                    0x29D3E6BC7F0886B75E186B10564DC990258855E0311E3E2E72F9D9C0DFAB4F0D,
                ),
            ),
        ),
        pytest.param(
            Spec.INF_G1
            + PointG2(
                (0x2000000000000000000000000, 0x0),
                (
                    0x114CC34C5044C87540B942287D555CE935499CE155202081CA5CE495C3568960,
                    0x09FD9490A6F214B7729F9574D53FCE82A2D46B3CCF7499AB5616B2C4F36582D7,
                ),
            )
            + Spec.INF_G1
            + PointG2((0x0, 0x0), (0x8000000, 0x0)),
        ),
        pytest.param(
            Spec.INF_G1
            + PointG2(
                (0x310000000000000000000000000CCC36905059, 0x0),
                (
                    0x034E16015E4AEADB3C1C93FD54F496A6A75271F9E514B6C51782D145A1771A98,
                    0x27910E860D8264C87A784C364D78F117CA598153FC5947C915EB6E2E7E0AD6D5,
                ),
            )
            + PointG1(0x1, 0x2)
            + Spec.INF_G2
            + PointG1(0x1, 0x2)
            + Spec.INF_G2
            + PointG1(0x1, 0x2)
            + Spec.INF_G2
            + PointG1(0x1, 0x2)
            + Spec.INF_G2
            + PointG1(0x1, 0x2)
            + Spec.INF_G2,
        ),
        pytest.param(
            Spec.INF_G1
            + PointG2(
                (
                    0x800000000000000000000000000000000000000000,
                    0x070A77C19A07DF2E666EA36F7879462C0A78EBBDF5C70B3DD35D438DC58F0D9D,
                ),
                (
                    0x0A2DD5B476A606A8243E7E879BDDAA8086BA658087AACC4D986A10C74DD9E774,
                    0x2D46618F9D516E0F07A59D3C97F5E167A1B49EBE9FB30DD05BDED8185A545420,
                ),
            ),
        ),
        pytest.param(
            Spec.INF_G1
            + PointG2(
                (
                    0x192B7E3A0CA8B63592989FE8B2589465703315272BC7,
                    0x30644E72E131A029B85045B68181585D00001B86B77538000000000100000000,
                ),
                (
                    0x128A694E7017AE1DB6A312C9EF648B1A4910A41E684CB554302044A2065F0468,
                    0x0DF2D76A91278279CF401D431C31876EE9C8AD35070694552CCBD36875541383,
                ),
            )
            + Spec.INF_G1
            + PointG2(
                (
                    0x192B7E3A0CA8B63592989FE8B2589465703315272BC7,
                    0x30644E72E131A029B85045B68181585D00001B86B77538000000000100000000,
                ),
                (
                    0x128A694E7017AE1DB6A312C9EF648B1A4910A41E684CB554302044A2065F0468,
                    0x0DF2D76A91278279CF401D431C31876EE9C8AD35070694552CCBD36875541383,
                ),
            ),
        ),
        pytest.param(
            Spec.INF_G1
            + PointG2(
                (
                    0x5B000000000045000000002A000000000080000000000000000001,
                    0x30644E72E131A029B65045B68181585D2B0D3025C6ABDBAA75EF4D163A7CFD40,
                ),
                (
                    0x17C66E1806ECE8D631D792F8CBD8BDF7514A9058C183A3B2FCDA7E86C44B7752,
                    0x301A6A722CDC812165B619F3CD2B21250D7F7083D0B984FDAF8636202E4AE047,
                ),
            )
            + PointG1(0x1, 0x2)
            + PointG2(
                (
                    0x30644E72E131A029B85045B68181585D2B0D3025C6AB2EB4FBEF4D16D87CFD40,
                    0x5B004500000000000000002A000000000000000000000000000001,
                ),
                (
                    0x109BEDDBAA84026C8F71D34A485AF27FE418028129B55B0A0DF51E3DBA231002,
                    0x1AEA54403CE01876467152AA79CA1F227B6B1E0F95B56CB0537583190252556D,
                ),
            ),
        ),
        pytest.param(
            Spec.INF_G1
            + PointG2(
                (0xFFFFFFFF << 184, 0xFFFFFFFF << 184),
                (
                    0x00FB55BF7DF894A746FBE20B6F8C54D5DC0D9FD4EDA4742FC35100C45E6E27F9,
                    0x12A20D63D446EB175733853B88DD36708EB7A81F5C79E7659C3A6E2B2C470077,
                ),
            )
            + Spec.INF_G1
            + PointG2(
                (0xFFFFFFFF << 184, 0xFFFFFFFF << 184),
                (
                    0x00FB55BF7DF894A746FBE20B6F8C549FEDDC0DD0D4005174A42FC3C45E6E27F9,
                    0x12A20D63D446EB175733853B88DD36708EB7A81F5C79E7659C3A6E2B2C470077,
                ),
            ),
        ),
        pytest.param(
            Spec.INF_G1
            + PointG2(
                (
                    0xEA1146AF1A0C4DF0000000001000000000000000000000000000000,
                    0x0,
                ),
                (
                    0x15D42E5A1C18703100BEF65A743007BEAD1FC389B7D8F0A8CCDA34B7D30620CB,
                    0x1C4156D243211B733AF4F4FFF11B9C0928308BF3C3102415E3105B986166D0CD,
                ),
            )
            + PointG1(0xF8FFFFFFFFFFFFFF0000, 0x0)
            + PointG2((0x0, 0x0), (0x8000000, 0x0)),
        ),
        pytest.param(
            Spec.INF_G1
            + PointG2(
                (
                    0x249409822E0000000000000000000000000000000000000001154BAF,
                    0x30644E72E131A029B85045B66AC4175696816A916871CA8D3C208C161A46C432,
                ),
                (
                    0x126F44FAB27034BA2832173059EBF31A96607ADA20F006B4F12D4A8BAD410D8F,
                    0x02EEE77897359CFC599B6CA4E8C2A47F641FC0CD6D4146D8ECA263A85C7AA365,
                ),
            )
            + Spec.INF_G1
            + PointG2(
                (
                    0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
                    0x1800DEEF121F1E76426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED,
                ),
                (
                    0x090689D0585FF075EC9E99AD690C3395BC4B313370B38EF355ACDADCD122975B,
                    0x12C85EA5DB8C6DEB4AAB71808DCB408FE3D1E7690C43D37B4CE6CC0166FA7DAA,
                ),
            ),
        ),
        pytest.param(
            Spec.INF_G1
            + PointG2(
                (
                    0x05908648C919B2BD65122716E5E4AA74FB342E22EEB59635C84BB4E20E34DA72,
                    0x30644E72E131A0296427B6542E3A6A00CCFA1D43577C305499096BBD8414F16C,
                ),
                (
                    0x0DF67CF39CB400A898E9AA727937CA9E07D92185F3FBA6AA42BE45DDAD4FDADB,
                    0x145DA376A6EC6D77185DF39EDDE6E9037E58065A054CDA2796F4E669BCDCBF1F,
                ),
            )
            + Spec.INF_G1
            + PointG2(
                (
                    0x05908648C919B2BD65122716E5E4AA74FB342E22EEB59635C84BB4E20E34DA72,
                    0x30644E72E131A0296427B6542E3A6A00CCFA1D43577C305499096BBD8414F16C,
                ),
                (
                    0x0DF67CF39CB400A898E9AA727937CA9E07D92185F3FBA6AA42BE45DDAD4FDADB,
                    0x145DA376A6EC6D77185DF39EDDE6E9037E58065A054CDA2796F4E669BCDCBF1F,
                ),
            )
            + Spec.INF_G1
            + PointG2(
                (
                    0x05908648C919B2BD65122716E5E4AA74FB342E22EEB59635C84BB4E20E34DA72,
                    0x30644E72E131A0296427B6542E3A6A00CCFA1D43577C305499096BBD8414F16C,
                ),
                (
                    0x0DF67CF39CB400A898E9AA727937CA9E07D92185F3FBA6AA42BE45DDAD4FDADB,
                    0x145DA376A6EC6D77185DF39EDDE6E9037E58065A054CDA2796F4E669BCDCBF1F,
                ),
            ),
        ),
        pytest.param(
            Spec.INF_G1
            + PointG2(
                (
                    0x05908648C919B2BD65122716E5E4AA74FB342E22EEB59635C84BB4E20E34DA72,
                    0x30644E72E131A0296427B6542E3A6A00CCFA1D43577C305499096BBD8414F16C,
                ),
                (
                    0x0DF67CF39CB400A898E9AA727937CA9E07D92185F3FBA6AA42BE45DDAD4FDADB,
                    0x145DA376A6EC6D77185DF39EDDE6E9037E58065A054CDA2796F4E669BCDCBF1F,
                ),
            )
            + Spec.INF_G1
            + PointG2(
                (
                    0x05908648C919B2BD65122716E5E4AA74FB342E22EEB59635C84BB4E20E34DA72,
                    0x30644E72E131A0296427B6542E3A6A00CCFA1D43577C305499096BBD8414F16C,
                ),
                (
                    0x0DF67CF39CB400A898E9AA727937CA9E07D92185F3FBA6AA42BE45DDAD4FDADB,
                    0x145DA376A6EC6D77185DF39EDDE6E9037E58065A054CDA2796F4E669BCDCBF1F,
                ),
            )
            + Spec.INF_G1
            + PointG2(
                (
                    0x05908648C919B2BD65122716E5E4AA74FB342E22EEB59635C84BB4E20E34DA72,
                    0x30644E72E131A0296427B6542E3A6A00CCFA1D43577C305499096BBD8414F16C,
                ),
                (
                    0x0DF67CF39CB400A898E9AA727937CA9E07D92185F3FBA6AA42BE45DDAD4FDADB,
                    0x145DA376A6EC6D77185DF39EDDE6E9037E58065A054CDA2796F4E669BCDCBF1F,
                ),
            )
            + Spec.INF_G1
            + PointG2(
                (
                    0x05908648C919B2BD65122716E5E4AA74FB342E22EEB59635C84BB4E20E34DA72,
                    0x30644E72E131A0296427B6542E3A6A00CCFA1D43577C305499096BBD8414F16C,
                ),
                (
                    0x0DF67CF39CB400A898E9AA727937CA9E07D92185F3FBA6AA42BE45DDAD4FDADB,
                    0x145DA376A6EC6D77185DF39EDDE6E9037E58065A054CDA2796F4E669BCDCBF1F,
                ),
            ),
        ),
        pytest.param(
            Spec.INF_G1
            + PointG2(
                (
                    0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
                    0x1A76DAE6D3272396D0CBE61FCED2BC532EDAC647851E3AC53CE1CC9C7E645A83,
                ),
                (
                    0x05B993046905746641A19B500EBBBD30CF0068A845BFBEE9DE55B8FE57D1DEE8,
                    0x243EF33537F73EF4ACE4279D86344D93A5DC8C20C69045865C0FA3B924933879,
                ),
            )
            + Spec.INF_G1
            + PointG2(
                (
                    0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
                    0x1A76DAE6D3272396D0CBE61FCED2BC532EDAC647851E3AC53CE1CC9C7E645A83,
                ),
                (
                    0x05B993046905746641A19B500EBBBD30CF0068A845BFBEE9DE55B8FE57D1DEE8,
                    0x243EF33537F73EF4ACE4279D86344D93A5DC8C20C69045865C0FA3B924933879,
                ),
            ),
        ),
        pytest.param(
            Spec.INF_G1
            + PointG2(
                (
                    0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
                    0x1A76DAE6D3272396D0CBE61FCED2BC532EDAC647851E3AC53CE1CC9C7E645A83,
                ),
                (
                    0x05B993046905746641A19B500EBBBD30CF0068A845BFBEE9DE55B8FE57D1DEE8,
                    0x243EF33537F73EF4ACE4279D86344D93A5DC8C20C69045865C0FA3B924933879,
                ),
            )
            + Spec.INF_G1
            + PointG2(
                (
                    0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
                    0x1A76DAE6D3272396D0CBE61FCED2BC532EDAC647851E3AC53CE1CC9C7E645A83,
                ),
                (
                    0x05B993046905746641A19B500EBBBD30CF0068A845BFBEE9DE55B8FE57D1DEE8,
                    0x243EF33537F73EF4ACE4279D86344D93A5DC8C20C69045865C0FA3B924933879,
                ),
            )
            + Spec.INF_G1
            + PointG2(
                (
                    0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
                    0x1A76DAE6D3272396D0CBE61FCED2BC532EDAC647851E3AC53CE1CC9C7E645A83,
                ),
                (
                    0x05B993046905746641A19B500EBBBD30CF0068A845BFBEE9DE55B8FE57D1DEE8,
                    0x243EF33537F73EF4ACE4279D86344D93A5DC8C20C69045865C0FA3B924933879,
                ),
            ),
        ),
        pytest.param(
            Spec.INF_G1
            + PointG2(
                (
                    0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
                    0x1A76DAE6D3272396D0CBE61FCED2BC532EDAC647851E3AC53CE1CC9C7E645A83,
                ),
                (
                    0x05B993046905746641A19B500EBBBD30CF0068A845BFBEE9DE55B8FE57D1DEE8,
                    0x243EF33537F73EF4ACE4279D86344D93A5DC8C20C69045865C0FA3B924933879,
                ),
            )
            + Spec.INF_G1
            + PointG2(
                (
                    0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
                    0x1A76DAE6D3272396D0CBE61FCED2BC532EDAC647851E3AC53CE1CC9C7E645A83,
                ),
                (
                    0x05B993046905746641A19B500EBBBD30CF0068A845BFBEE9DE55B8FE57D1DEE8,
                    0x243EF33537F73EF4ACE4279D86344D93A5DC8C20C69045865C0FA3B924933879,
                ),
            )
            + Spec.INF_G1
            + PointG2(
                (
                    0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
                    0x1A76DAE6D3272396D0CBE61FCED2BC532EDAC647851E3AC53CE1CC9C7E645A83,
                ),
                (
                    0x05B993046905746641A19B500EBBBD30CF0068A845BFBEE9DE55B8FE57D1DEE8,
                    0x243EF33537F73EF4ACE4279D86344D93A5DC8C20C69045865C0FA3B924933879,
                ),
            )
            + Spec.INF_G1
            + PointG2(
                (
                    0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
                    0x1A76DAE6D3272396D0CBE61FCED2BC532EDAC647851E3AC53CE1CC9C7E645A83,
                ),
                (
                    0x05B993046905746641A19B500EBBBD30CF0068A845BFBEE9DE55B8FE57D1DEE8,
                    0x243EF33537F73EF4ACE4279D86344D93A5DC8C20C69045865C0FA3B924933879,
                ),
            ),
        ),
        pytest.param(
            Spec.INF_G1
            + PointG2(
                (
                    0x1A36C98D1ECE5FD647AFBA497E7EA7A2687E956E978E3572C3DF75E9278302B9,
                    0x991B498795,
                ),
                (
                    0x099A3FAF27255B9542DAF48D9588FC4D6927C7FCD88C5784A4245345474E1E45,
                    0x09A44EA53F191DDEF8A32EC03A7E1A24E06588F8DE364BA0024B3B8A062CA91A,
                ),
            )
            + Spec.INF_G1
            + PointG2(
                (
                    0x1A36C98D1ECE5FD647AFBA497E7EA7A2687E956E978E3572C3DF75E9278302B9,
                    0x991B498795,
                ),
                (
                    0x099A3FAF27255B9542DAF48D9588FC4D6927C7FCD88C5784A4245345474E1E45,
                    0x09A44EA53F191DDEF8A32EC03A7E1A24E06588F8DE364BA0024B3B8A062CA91A,
                ),
            )
            + PointG1(0x1, Spec.P - 2)
            + PointG2(
                (
                    0x30644E72E131A029B85045B68181585D97816A68917120CA8D3C8C16D87CFD45,
                    0x5B0045000000000000000000000000000000000000000040000001,
                ),
                (
                    0x11EE2BE185FB562C979EEB452DF376F91C7852BFB8A6D5727024444A2FC58C15,
                    0x2825D78E66BE7952503E9E1BF2D8AAD4C39F4CE4095349043106508BAB20D6E5,
                ),
            )
            + PointG1(0x1, Spec.P - 2)
            + PointG2(
                (
                    0x30644E72E131A029B85045B68181585D97816A68917120CA8D3C8C16D87CFD45,
                    0x5B0045000000000000000000000000000000000000000040000001,
                ),
                (
                    0x11EE2BE185FB562C979EEB452DF376F91C7852BFB8A6D5727024444A2FC58C15,
                    0x2825D78E66BE7952503E9E1BF2D8AAD4C39F4CE4095349043106508BAB20D6E5,
                ),
            )
            + PointG1(0x1, Spec.P - 2)
            + PointG2(
                (
                    0x30644E72E131A029B85045B68181585D97816A68917120CA8D3C8C16D87CFD45,
                    0x5B0045000000000000000000000000000000000000000040000001,
                ),
                (
                    0x11EE2BE185FB562C979EEB452DF376F91C7852BFB8A6D5727024444A2FC58C15,
                    0x2825D78E66BE7952503E9E1BF2D8AAD4C39F4CE4095349043106508BAB20D6E5,
                ),
            ),
        ),
        pytest.param(
            Spec.INF_G1
            + PointG2(
                (
                    0x30644E72E131A029000000000000000000000000000000004000000000000000,
                    0x1000000000000000000000000000000000000000017F66B91112534050000,
                ),
                (
                    0x06F2A18A982E6E9436F171F8BCDB4F60B9EA1DAFAF115F9228E11DDD98CA9680,
                    0x304502B9C299712D0CF851E73ADC8CE68C549A5B2AE712A44811DB357D3BDB97,
                ),
            )
            + PointG1(
                0x17956B549321B92C524D191A62B90C81F08E694AF4DCEB00A80094E53120D39E,
                0x2FD15D78815388959CAA54AFFA2D7B2C8D52C528E6A1F6C0A50FCF0498FAC7EE,
            )
            + PointG2(
                (
                    0x30644E72E131A029000000000000000000000000000000004000000000000000,
                    0x0,
                ),
                (
                    0x016B9E28A32EE61A7AD5BD4BAD29D64FC35A8FB46B510BE2067907069497AE1F,
                    0x0C3C07C40F41A731FE27D953F1154B4E9A8ACF3EF44608817150DE0DF916503A,
                ),
            )
            + PointG1(
                0x17956B549321B92C524D191A62B90C81F08E694AF4DCEB00A80094E53120D39E,
                0x2FD15D78815388959CAA54AFFA2D7B2C8D52C528E6A1F6C0A50FCF0498FAC7EE,
            )
            + PointG2(
                (
                    0x30644E72E131A029000000000000000000000000000000004000000000000000,
                    0x0,
                ),
                (
                    0x016B9E28A32EE61A7AD5BD4BAD29D64FC35A8FB46B510BE2067907069497AE1F,
                    0x0C3C07C40F41A731FE27D953F1154B4E9A8ACF3EF44608817150DE0DF916503A,
                ),
            )
            + PointG1(
                0x17956B549321B92C524D191A62B90C81F08E694AF4DCEB00A80094E53120D39E,
                0x2FD15D78815388959CAA54AFFA2D7B2C8D52C528E6A1F6C0A50FCF0498FAC7EE,
            )
            + PointG2(
                (
                    0x30644E72E131A029000000000000000000000000000000004000000000000000,
                    0x0,
                ),
                (
                    0x016B9E28A32EE61A7AD5BD4BAD29D64FC35A8FB46B510BE2067907069497AE1F,
                    0x0C3C07C40F41A731FE27D953F1154B4E9A8ACF3EF44608817150DE0DF916503A,
                ),
            ),
        ),
        pytest.param(
            Spec.INF_G1
            + PointG2(
                (
                    0x30644E72E131A029B85045B68181585D977F9597358C206E72C88C16E622B8B2,
                    0x4500000000000000000000000107B55DE1642362D16B8FC4DC,
                ),
                (
                    0x2A314ECA6ADB97BF3A3872A406ECF97BF2BDD210B6CBA667EBA043F71C1FFC20,
                    0x0BA9CAA5888AE7C0E6D2B54181905E66769D9ED9BADC43DA3D9F3E56B46CB43B,
                ),
            )
            + PointG1(
                0x0ACFD59A153BDC736907CC4A640A2FB675CDAA8066A58616537CE4CD7145AA06,
                0x1B1D6BF901BDA3C5E3DF60E3741D6F5D6660F4034E2F99545E0DC71E9B53AF2C,
            )
            + PointG2(
                (
                    0x30644E72E131A029B85045B68181585D977F956E978C3572C8208C166622B8B2,
                    0x4500000000000000000000000107B55DE1642362D16B8FC4DC,
                ),
                (
                    0x2AD9BB009C15BDC11D5ED75A805D5F24BA0E10E5B7953E281E241F72D208CE88,
                    0x0D6F072450FD6EF76DD73FF2924238CBEE09EA4C6281B867A897D85D8D091B33,
                ),
            )
            + PointG1(
                0x0ACFD59A153BDC736907CC4A640A2FB675CDAA8066A58616537CE4CD7145AA06,
                0x1B1D6BF901BDA3C5E3DF60E3741D6F5D6660F4034E2F99545E0DC71E9B53AF2C,
            )
            + PointG2(
                (
                    0x30644E72E131A029B85045B68181585D977F956E978C3572C8208C166622B8B2,
                    0x4500000000000000000000000107B55DE1642362D16B8FC4DC,
                ),
                (
                    0x2AD9BB009C15BDC11D5ED75A805D5F24BA0E10E5B7953E281E241F72D208CE88,
                    0x0D6F072450FD6EF76DD73FF2924238CBEE09EA4C6281B867A897D85D8D091B33,
                ),
            )
            + PointG1(
                0x0ACFD59A153BDC736907CC4A640A2FB675CDAA8066A58616537CE4CD7145AA06,
                0x1546E279DF73FC63D470E4D30D63E9003120768E1A423138DE12C4F83D294E1B,
            )
            + PointG2(
                (
                    0x30644E72E131A029B85045B68181585D977F956E978C3572C8208C166622B8B2,
                    0x4500000000000000000000000107B55DE1642362D16B8FC4DC,
                ),
                (
                    0x2AD9BB009C15BDC11D5ED75A805D5F24BA0E10E5B7953E281E241F72D208CE88,
                    0x0D6F072450FD6EF76DD73FF2924238CBEE09EA4C6281B867A897D85D8D091B33,
                ),
            ),
        ),
        pytest.param(
            Spec.INF_G1
            + PointG2(
                (Spec.P - 2, 0x2),
                (
                    0x0833E47A2EAA8BBE12D33B2DA1A4FA8D763F5C567FE0DA6C5C9DA2E246F2096F,
                    0x28DC125BF7443BC1826C69FE4C7BF30C26EC60882350E784C4848C822726EB43,
                ),
            )
            + PointG1(0x1, Spec.P - 2)
            + PointG2(
                (Spec.P - 2, 0x2),
                (
                    0x0833E47A2EAA8BBE12D33B2DA1A4FA8D763F5C567FE0DA6C5C9DA2E246F2096F,
                    0x28DC125BF7443BC1826C69FE4C7BF30C26EC60882350E784C4848C822726EB43,
                ),
            ),
        ),
        pytest.param(
            Spec.INF_G1
            + PointG2(
                (Spec.P - 2, 0x2),
                (
                    0x0833E47A2EAA8BBE12D33B2DA1A4FA8D763F5C567FE0DA6C5C9DA2E246F2096F,
                    0x28DC125BF7443BC1826C69FE4C7BF30C26EC60882350E784C4848C822726EB43,
                ),
            )
            + PointG1(
                0x1A3CF0C503B2DBC6E1B0F8AEA605DE20D8612FE14627C6F4D3706F8272A1CF84,
                0x2A0BB098018CA4392A1DDC08B9605602AED954308944AC729E2F99BFDD0166DD,
            )
            + PointG2(
                (0x10000, 0x0),
                (
                    0x24B364D16400886C82900AF060FD117CB2F4E0B93590CBF6EC34ED97F4C391EC,
                    0x26A10E3233AEFF776D578DE9178A9B7BB919E6EB6CF2CF924EB16EC8DC659AF9,
                ),
            ),
        ),
        pytest.param(
            Spec.INF_G1
            + PointG2(
                (Spec.P - 2, 0x2),
                (
                    0x0833E47A2EAA8BBE12D33B2DA1A4FA8D763F5C567FE0DA6C5C9DA2E246F2096F,
                    0x28DC125BF7443BC1826C69FE4C7BF30C26EC60882350E784C4848C822726EB43,
                ),
            )
            + PointG1(
                0x1A5D389CA17607C4B12D7F1C8463B960754DBBB74EE00F645CA559F5EE759AD5,
                0x231FDB414002B25EBEED48FD799214F4DB09A7DAE25AC92C15B7E429E1800A70,
            )
            + PointG2(
                (
                    0x297861CED3673FA135F178751F203F13D8A4C9F15AD9FDBB4BB7468154AF97F7,
                    0x1698710AF2EFBDE1687BC1530E7DA2CA42C8E85BAF594682890D36C8FB8D08F9,
                ),
                (
                    0x106F1D083223BD63D1630BAF008588AC9C0392C289C68AFEE37B013030A9F7D1,
                    0x0128036F1A405F40BCE08BC346F0F83CB8CA2FE81D18FDFFFA984C97CEF37358,
                ),
            )
            + Spec.INF_G1
            + PointG2(
                (Spec.P - 2, 0x2),
                (
                    0x0833E47A2EAA8BBE12D33B2DA1A4FA8D763F5C567FE0DA6C5C9DA2E246F2096F,
                    0x28DC125BF7443BC1826C69FE4C7BF30C26EC60882350E784C4848C822726EB43,
                ),
            )
            + PointG1(
                0x1C251D57A884434484D488B3FA5BB0B0D8566A251BFA57CDCFA452EE114A1960,
                0x1BCD6DEC5E0B17FB9BB77B1145793CD6A99534DE85911F41C37934FC6F1F508E,
            )
            + PointG2(
                (
                    0x203E205DB4F19B37B60121B83A7333706DB86431C6D835849957ED8C3928AD79,
                    0x27DC7234FD11D3E8C36C59277C3E6F149D5CD3CFA9A62AEE49F8130962B4B3B9,
                ),
                (
                    0x195E8AA5B7827463722B8C15393157AD3505566B4EDF48D498E185F0509DE152,
                    0x04BB53B8977E5F92A0BC372742C4830944A59B4FE6B1C0466E2A6DAD122B5D2E,
                ),
            ),
        ),
        pytest.param(
            PointG1(0x1, 0x2)
            + PointG2(
                (
                    0x0,
                    0x30644E72E131A029B05040FF0000000000000000000000000000000000000000,
                ),
                (
                    0x2E00D573B028B22B9D347DA8044A53C94B6C3AEE7D9BFB00AB2C0A10EB4775E6,
                    0x19E1A75BE1C5D39A105504A0E5D16C949524742DDE6BBB6E831668FEF921A143,
                ),
            )
            + PointG1(0x1, 0x2)
            + PointG2(
                (
                    0x30644E72E131A029B050FFFFFFFF585D97816A86B77537DAFBEF4D16D87CFD45,
                    0x5B00450000F400000000002A00647D903B504C1A02000000000001,
                ),
                (
                    0x2DB3D49DA56012CF4F73CBF19FDB59EF41356CEBB4F4B6F692F9A38FB282A9FF,
                    0x2D96DB5D24DCEA418A44FEAE6052FBC7788E65E521B17232666818386252176A,
                ),
            ),
        ),
        pytest.param(
            PointG1(0x1, 0x2)
            + PointG2(
                (0x107B55DE1642362D16B8F25DCCF, (Spec.P >> 24) << 24),
                (
                    0x09EAE594F627B7CCF496D680F0266E7364F51D2D99CCD69801F29137D889E1E0,
                    0x06EA1409D3F9BB38BD40E8DA0701D122E059A02FC3C3C4A99A8CBF6E4290BDC0,
                ),
            )
            + PointG1(0x1, Spec.P - 2)
            + PointG2(
                (0x107B55DE1642362D16B8F25DCCF, (Spec.P >> 24) << 24),
                (
                    0x09EAE594F627B7CCF496D680F0266E7364F51D2D99CCD69801F29137D889E1E0,
                    0x06EA1409D3F9BB38BD40E8DA0701D122E059A02FC3C3C4A99A8CBF6E4290BDC0,
                ),
            ),
        ),
        pytest.param(
            PointG1(0x1, 0x2)
            + PointG2(
                (
                    0x5B0045000000000000000000000000000000000000000000000001,
                    Spec.P - 2,
                ),
                (
                    0x218C0CEF2A606613357BFAA3C880E71FF8490195337FA26205A21CCD9A6949A3,
                    0x13FED2C79ADD9D85B9949C5852EF8CCCF02B69EA6FC4DB0D1660AC7B50DF39E1,
                ),
            )
            + PointG1(0x1, Spec.P - 2)
            + PointG2(
                (
                    0x5B0045000000000000000000000000000000000000000000000001,
                    Spec.P - 2,
                ),
                (
                    0x218C0CEF2A606613357BFAA3C880E71FF8490195337FA26205A21CCD9A6949A3,
                    0x13FED2C79ADD9D85B9949C5852EF8CCCF02B69EA6FC4DB0D1660AC7B50DF39E1,
                ),
            )
            + PointG1(0x1, Spec.P - 2)
            + PointG2(
                (
                    0x5B0045000000000000000000000000000000000000000000000001,
                    Spec.P - 2,
                ),
                (
                    0x218C0CEF2A606613357BFAA3C880E71FF8490195337FA26205A21CCD9A6949A3,
                    0x13FED2C79ADD9D85B9949C5852EF8CCCF02B69EA6FC4DB0D1660AC7B50DF39E1,
                ),
            )
            + PointG1(0x1, Spec.P - 2)
            + PointG2(
                (
                    0x5B0045000000000000000000000000000000000000000000000001,
                    Spec.P - 2,
                ),
                (
                    0x218C0CEF2A606613357BFAA3C880E71FF8490195337FA26205A21CCD9A6949A3,
                    0x13FED2C79ADD9D85B9949C5852EF8CCCF02B69EA6FC4DB0D1660AC7B50DF39E1,
                ),
            ),
        ),
        pytest.param(
            PointG1(0x1, 0x2)
            + PointG2(
                (
                    0x5B0045000000000000000000000000000000000000000000000008,
                    Spec.P - 0x65FA7E,
                ),
                (
                    0x19C023CE224A0C0B121DD4F578B39E0DDF00A55580B03265CB32FCB623BBF778,
                    0x240F6BF16B9A25500A02B09FBE8ABFA933F9EE09EFFB104D712BAF573463EF8C,
                ),
            )
            + PointG1(0x1, Spec.P - 2)
            + PointG2(
                (
                    0x5B0045000000000000000000000000000000000000000000000008,
                    Spec.P - 0x65FA7E,
                ),
                (
                    0x19C023CE224A0C0B121DD4F578B39E0DDF00A55580B03265CB32FCB623BBF778,
                    0x240F6BF16B9A25500A02B09FBE8ABFA933F9EE09EFFB104D712BAF573463EF8C,
                ),
            )
            + PointG1(0x1, Spec.P - 2)
            + PointG2(
                (
                    0x5B0045000000000000000000000000000000000000000000000001,
                    Spec.P - 2,
                ),
                (
                    0x218C0CEF2A606613357BFAA3C880E71FF8490195337FA26205A21CCD9A6949A3,
                    0x13FED2C79ADD9D85B9949C5852EF8CCCF02B69EA6FC4DB0D1660AC7B50DF39E1,
                ),
            ),
        ),
        pytest.param(
            PointG1(0x1, 0x2)
            + PointG2(
                (
                    0x5B00450000000000DA76B36B83C728300000000000000000000008,
                    0x30644E72E131A029B85045B68181585D97816A916871CA8D104D5B2BAF573463,
                ),
                (
                    0x1B8765E7F5163862FCD3BC29F751AF42D869A0C8A329F5A53472D3C977038BB7,
                    0x068CD6BC298BD1EC695A49E1DB0620332F26E03A4A0ED9076973C1FEA43099F2,
                ),
            )
            + PointG1(0x1, Spec.P - 2)
            + PointG2(
                (
                    0x5B0045000000000000000000000000000000000000000000000001,
                    Spec.P - 2,
                ),
                (
                    0x218C0CEF2A606613357BFAA3C880E71FF8490195337FA26205A21CCD9A6949A3,
                    0x13FED2C79ADD9D85B9949C5852EF8CCCF02B69EA6FC4DB0D1660AC7B50DF39E1,
                ),
            ),
        ),
        pytest.param(
            PointG1(0x1, 0x2)
            + PointG2(
                (
                    0x5B00450000FC00000000002A00647D903B504C1A02000000000001,
                    0x30644E72E131A029B85045B68181585D97816A86B77537DAFBEF4D16D87CFD45,
                ),
                (
                    0x0125B8EDEDE9E4F320E4DBFD7EE46D23A82508C3B44DBB99CB29724DAAA5C560,
                    0x2D663CC48C6D7469CC9DF0E861F3A9B93239AF8001F8ECF28B4572F201EF1369,
                ),
            )
            + PointG1(0x1, Spec.P - 2)
            + PointG2(
                (
                    0x30644E72E131A029B85045B68181585D97816A86B77538DAFBEF4D16D87CFD45,
                    0x5B004500000000000000002A00647D903B504C1A02000000000001,
                ),
                (
                    0x247F1F6FBF2FE1FFF7E28D816724080774979F57692C2FA8569EA1A3CE52DFC5,
                    0x1F5C96F77D84AE24B701A32FF1B8D95B982C76BF5AB02E605C9BA4FA9F45B958,
                ),
            ),
        ),
        pytest.param(
            PointG1(0x1, 0x2)
            + PointG2(
                (
                    0x012CD187FAAE3648A35E12CC197DDB26D9D3A44A625D97816A86B77537DAFBEF,
                    0x30644E72E131A029B050FFFFFFFF5802086325C1129AD4A34EBB48EE96340160,
                ),
                (
                    0x08AEF33D9388C8F993F0AF340E047C1C9519D222062186F7B025291B6F6F4EF2,
                    0x293F1064B0E3345895DC4968BC8BB52FCBE960621C1F15CD7C693C7347078E32,
                ),
            )
            + PointG1(0x1, Spec.P - 2)
            + PointG2(
                (
                    0x012CD187FAAE3648A35E12CC197DDB26D9D3A44A625D97816A86B77537DAFBEF,
                    0x30644E72E131A029B050FFFFFFFF5802086325C1129AD4A34EBB48EE96340160,
                ),
                (
                    0x08AEF33D9388C8F993F0AF340E047C1C9519D222062186F7B025291B6F6F4EF2,
                    0x293F1064B0E3345895DC4968BC8BB52FCBE960621C1F15CD7C693C7347078E32,
                ),
            ),
        ),
        pytest.param(
            PointG1(0x1, 0x2)
            + PointG2(
                (
                    0x0D7D3BE95C6B1FC7D70F2EDC7B7BF6E7397BC04BC6AAA0584B9E5BBC064DE4FA,
                    Spec.P - 0x1D8A9F8B4C998A61149D6C,
                ),
                (
                    0x10FB4E584F10053CBA1117D920DB188F54D1AB64E66E10B6177401A44C71E250,
                    0x20F50C6423205B18D96CDF7A832041D89076CF36DCDE6700E62833186ACD60B6,
                ),
            )
            + PointG1(0x1, 0x2)
            + PointG2(
                (
                    0x0D7D3BE95C6B1FC7D70F2EDC7B7BF6E7397BC04BC6AAA0584B9E5BBC064DE4FA,
                    Spec.P - 0x1D8A9F8B4C998A61149D6C,
                ),
                (
                    0x10FB4E584F10053CBA1117D920DB188F54D1AB64E66E10B6177401A44C71E250,
                    0x20F50C6423205B18D96CDF7A832041D89076CF36DCDE6700E62833186ACD60B6,
                ),
            )
            + PointG1(0x1, 0x2)
            + PointG2(
                (
                    0x0D7D3BE95C6B1FC7D70F2EDC7B7BF6E7397BC04BC6AAA0584B9E5BBC064DE4FA,
                    Spec.P - 0x1D8A9F8B4C998A61149D6C,
                ),
                (
                    0x10FB4E584F10053CBA1117D920DB188F54D1AB64E66E10B6177401A44C71E250,
                    0x20F50C6423205B18D96CDF7A832041D89076CF36DCDE6700E62833186ACD60B6,
                ),
            )
            + PointG1(0x1, 0x2)
            + PointG2(
                (
                    0x0D7D3BE95C6B1FC7D70F2EDC7B7BF6E7397BC04BC6AAA0584B9E5BBC064DE4FA,
                    Spec.P - 0x1D8A9F8B4C998A61149D6C,
                ),
                (
                    0x10FB4E584F10053CBA1117D920DB188F54D1AB64E66E10B6177401A44C71E250,
                    0x20F50C6423205B18D96CDF7A832041D89076CF36DCDE6700E62833186ACD60B6,
                ),
            ),
        ),
        pytest.param(
            PointG1(0x1, 0x2)
            + PointG2(
                (
                    0x0D7D3BE95C6B1FC7D70F2EDC7B7BF6E7397BC04BC6AAA0584B9E5BBC064DE4FA,
                    Spec.P - 0x1D8A9F8B4C998A61149D6C,
                ),
                (
                    0x10FB4E584F10053CBA1117D920DB188F54D1AB64E66E10B6177401A44C71E250,
                    0x20F50C6423205B18D96CDF7A832041D89076CF36DCDE6700E62833186ACD60B6,
                ),
            )
            + PointG1(0x1, Spec.P - 2)
            + PointG2(
                (
                    0x0D7D3BE95C6B1FC7D70F2EDC7B7BF6E7397BC04BC6AAA0584B9E5BBC064DE4FA,
                    Spec.P - 0x1D8A9F8B4C998A61149D6C,
                ),
                (
                    0x10FB4E584F10053CBA1117D920DB188F54D1AB64E66E10B6177401A44C71E250,
                    0x20F50C6423205B18D96CDF7A832041D89076CF36DCDE6700E62833186ACD60B6,
                ),
            )
            + PointG1(0x1, 0x2)
            + PointG2(
                (
                    0x0D7D3BE95C6B1FC7D70F2EDC7B7BF6E7397BC04BC6AAA0584B9E5BBC064DE4FA,
                    Spec.P - 0x1D8A9F8B4C998A61149D6C,
                ),
                (
                    0x10FB4E584F10053CBA1117D920DB188F54D1AB64E66E10B6177401A44C71E250,
                    0x20F50C6423205B18D96CDF7A832041D89076CF36DCDE6700E62833186ACD60B6,
                ),
            ),
        ),
        pytest.param(
            PointG1(0x1, 0x2)
            + PointG2(
                (
                    0x30644E72E131A029B05045B68181585D97816A86B77537DAFBEF4D16D87CFD45,
                    0x5B00450000FC00000000002A00647D903B504C1A02000000000001,
                ),
                (
                    0x2C32D7465B0607CFAEBE0B13577B25E42FE6D9E49EEB9D5C0CA78CC17E114CBC,
                    0x2CD71C8288EBBD272A784C5B4921128CB68E9E2DDAAEC0595B266126C4E526BD,
                ),
            )
            + PointG1(0x1, Spec.P - 2)
            + PointG2(
                (
                    0x30644E72E131A029B05045B68181585D97816A86B77537DAFBEF4D16D87CFD45,
                    0x5B00450000FC00000000002A00647D903B504C1A02000000000001,
                ),
                (
                    0x2C32D7465B0607CFAEBE0B13577B25E42FE6D9E49EEB9D5C0CA78CC17E114CBC,
                    0x2CD71C8288EBBD272A784C5B4921128CB68E9E2DDAAEC0595B266126C4E526BD,
                ),
            ),
        ),
        pytest.param(
            PointG1(0x1, 0x2)
            + PointG2(
                (
                    0x30644E72E131A029B85045B68181585D97816A68917120CA8D3C8C16D87CFD45,
                    0x5B0045000000000000000000000000000000000000000040000001,
                ),
                (
                    0x11EE2BE185FB562C979EEB452DF376F91C7852BFB8A6D5727024444A2FC58C15,
                    0x2825D78E66BE7952503E9E1BF2D8AAD4C39F4CE4095349043106508BAB20D6E5,
                ),
            )
            + PointG1(0x1, Spec.P - 2)
            + PointG2(
                (
                    0x30644E72E131A029B85045B68181585D97816A68917120CA8D3C8C16D87CFD45,
                    0x5B0045000000000000000000000000000000000000000040000001,
                ),
                (
                    0x11EE2BE185FB562C979EEB452DF376F91C7852BFB8A6D5727024444A2FC58C15,
                    0x2825D78E66BE7952503E9E1BF2D8AAD4C39F4CE4095349043106508BAB20D6E5,
                ),
            ),
        ),
        pytest.param(
            PointG1(0x1, 0x2)
            + PointG2(
                (
                    0x30644E72E131A029B85045B68181585D97816A68917120CA8D3C8C16D87CFD45,
                    0x5B0045000000000000000000000000000000000000000040000001,
                ),
                (
                    0x11EE2BE185FB562C979EEB452DF376F91C7852BFB8A6D5727024444A2FC58C15,
                    0x2825D78E66BE7952503E9E1BF2D8AAD4C39F4CE4095349043106508BAB20D6E5,
                ),
            )
            + PointG1(0x1, Spec.P - 2)
            + PointG2(
                (
                    0x30644E72E131A029B85045B68181585D97816A68917120CA8D3C8C16D87CFD45,
                    0x5B0045000000000000000000000000000000000000000040000001,
                ),
                (
                    0x11EE2BE185FB562C979EEB452DF376F91C7852BFB8A6D5727024444A2FC58C15,
                    0x2825D78E66BE7952503E9E1BF2D8AAD4C39F4CE4095349043106508BAB20D6E5,
                ),
            )
            + PointG1(0x1, Spec.P - 2)
            + PointG2(
                (
                    0x30644E72E131A029B85045B68181585D97816A68917120CA8D3C8C16D87CFD45,
                    0x5B0045000000000000000000000000000000000000000040000001,
                ),
                (
                    0x11EE2BE185FB562C979EEB452DF376F91C7852BFB8A6D5727024444A2FC58C15,
                    0x2825D78E66BE7952503E9E1BF2D8AAD4C39F4CE4095349043106508BAB20D6E5,
                ),
            ),
        ),
        pytest.param(
            PointG1(0x1, 0x2)
            + PointG2(
                (
                    0x30644E72E131A029B85045B68181585D97816A86B77538DAFBEF4D16D87CFD45,
                    0x5B004500000000000000002A000000000000000000000000000001,
                ),
                (
                    0x124CA5DC43ED1E22D1C616B50A7D4249A012C1D65330AE8E4CAD70567C8231BB,
                    0x23F9415FA570E58E0AC61E4E6E7A6BD02A564F6B206A9D4645401B1D677BF3AB,
                ),
            )
            + PointG1(0x1, Spec.P - 2)
            + PointG2(
                (
                    0x30644E72E131A029B85045B68181585D97816A86B77538DAFBEF4D16D87CFD45,
                    0x5B004500000000000000002A000000000000000000000000000001,
                ),
                (
                    0x124CA5DC43ED1E22D1C616B50A7D4249A012C1D65330AE8E4CAD70567C8231BB,
                    0x23F9415FA570E58E0AC61E4E6E7A6BD02A564F6B206A9D4645401B1D677BF3AB,
                ),
            ),
        ),
        pytest.param(
            PointG1(0x1, 0x2)
            + PointG2(
                (
                    0x30644E72E131A029B85045B68181585D97816A86B77538DAFBEF4D16D87CFD45,
                    0x5B004500000000000000002A00647D903B504C1A02000000000001,
                ),
                (
                    0x247F1F6FBF2FE1FFF7E28D816724080774979F57692C2FA8569EA1A3CE52DFC5,
                    0x1F5C96F77D84AE24B701A32FF1B8D95B982C76BF5AB02E605C9BA4FA9F45B958,
                ),
            )
            + PointG1(0x1, Spec.P - 2)
            + PointG2(
                (
                    0x30644E72E131A029B85045B68181585D97816A86B77538DAFBEF4D16D87CFD45,
                    0x5B004500000000000000002A00647D903B504C1A02000000000001,
                ),
                (
                    0x247F1F6FBF2FE1FFF7E28D816724080774979F57692C2FA8569EA1A3CE52DFC5,
                    0x1F5C96F77D84AE24B701A32FF1B8D95B982C76BF5AB02E605C9BA4FA9F45B958,
                ),
            ),
        ),
        pytest.param(
            PointG1(0x1, 0x2)
            + PointG2(
                (
                    Spec.P - 0xC0C80FD98EAC3DB,
                    0x5B0045000000000000000000000000000000080000000000000001,
                ),
                (
                    0x301A8B8043356B83C4341D5E9CFC67071C61C0B053EC979B59AD8C0455B71C98,
                    0x15F88E8C709168C1AB898CA5288423B585331497F16B2C074DCBF76C2480E8C9,
                ),
            )
            + PointG1(0x1, Spec.P - 2)
            + PointG2(
                (
                    Spec.P - 0xC0C80FD98EAC3DB,
                    0x5B0045000000000000000000000000000000080000000000000001,
                ),
                (
                    0x301A8B8043356B83C4341D5E9CFC67071C61C0B053EC979B59AD8C0455B71C98,
                    0x15F88E8C709168C1AB898CA5288423B585331497F16B2C074DCBF76C2480E8C9,
                ),
            ),
        ),
        pytest.param(
            PointG1(0x1, Spec.P - 2)
            + PointG2(
                (
                    0x1800DEEF121F1E76426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED,
                    0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
                ),
                (
                    0x1CC9A9EB823F8D97ADEE0206828C9F19EAF8F536C23207D68AE3D056A1480BB2,
                    0x1990DDB90388B94F31089D3B4FF594D5449C04FCDF2A3681017B5D7749367BA1,
                ),
            )
            + PointG1(0x1, Spec.P - 2)
            + PointG2(
                (
                    0x1800DEEF121F1E76426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED,
                    0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
                ),
                (
                    0x1CC9A9EB823F8D97ADEE0206828C9F19EAF8F536C23207D68AE3D056A1480BB2,
                    0x1990DDB90388B94F31089D3B4FF594D5449C04FCDF2A3681017B5D7749367BA1,
                ),
            )
            + PointG1(0x1, Spec.P - 2)
            + PointG2(
                (
                    0x1800DEEF121F1E76426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED,
                    0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
                ),
                (
                    0x1CC9A9EB823F8D97ADEE0206828C9F19EAF8F536C23207D68AE3D056A1480BB2,
                    0x1990DDB90388B94F31089D3B4FF594D5449C04FCDF2A3681017B5D7749367BA1,
                ),
            )
            + PointG1(0x1, Spec.P - 2)
            + PointG2(
                (
                    0x1800DEEF121F1E76426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED,
                    0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
                ),
                (
                    0x1CC9A9EB823F8D97ADEE0206828C9F19EAF8F536C23207D68AE3D056A1480BB2,
                    0x1990DDB90388B94F31089D3B4FF594D5449C04FCDF2A3681017B5D7749367BA1,
                ),
            ),
        ),
        pytest.param(
            PointG1(0x1, Spec.P - 2)
            + PointG2(
                (
                    0x2B0D3F819FD0046AEE4D0E54CC759AD714C473BD5F86A0D68DF977F7450390F7,
                    0x30644E72E131A029B85045AE0000000000000107B55DE1642362D16B8FC4DCCF,
                ),
                (
                    0x2A5C3A27C4A417EA34F627B9481B9004E3B0EF59619DAA16E846D8A152D6BF77,
                    0x1301A8BB9C71966A4B557A21EEA89447294E8A9CC1308F0C8EECB16DFBF5D53B,
                ),
            )
            + PointG1(0x1, Spec.P - 2)
            + PointG2(
                (
                    Spec.P - 2,
                    0x45000000000000000000000000000000000000000000000001,
                ),
                (
                    0x07B55DE1642362D16B8FC4DCCFEC9E794D24968511CF8E252ED27AFC4D72CA1E,
                    0x0301CB4D7E0B7B52A6A8F78613C403EAD1543FEDB0D3F28C77685FDB9EAA2742,
                ),
            ),
        ),
        pytest.param(
            PointG1(0x1, Spec.P - 2)
            + PointG2(
                (
                    (Spec.P >> 8) << 8,
                    0x5B0045000000000000000000000000000000000000000000000001,
                ),
                (
                    0x112006831F3F0E121585C21CDF0AAF63F09728BCFEE141BB4CD407CAAE7715E3,
                    0x19DF1E217AD7B1F874726C6683AB87B423C1737F46A54DC5356A9B617C6B9E28,
                ),
            )
            + PointG1(0x1, Spec.P - 2)
            + PointG2(
                (
                    0x5B0045000000000000000000000000000000000000000000000001,
                    Spec.P - 2,
                ),
                (
                    0x218C0CEF2A606613357BFAA3C880E71FF8490195337FA26205A21CCD9A6949A3,
                    0x13FED2C79ADD9D85B9949C5852EF8CCCF02B69EA6FC4DB0D1660AC7B50DF39E1,
                ),
            ),
        ),
        pytest.param(
            PointG1(0x1, Spec.P - 2)
            + PointG2(
                (Spec.P - 2, 0x2),
                (
                    0x0833E47A2EAA8BBE12D33B2DA1A4FA8D763F5C567FE0DA6C5C9DA2E246F2096F,
                    0x28DC125BF7443BC1826C69FE4C7BF30C26EC60882350E784C4848C822726EB43,
                ),
            ),
        ),
        pytest.param(
            PointG1(0x1, Spec.P - 2)
            + PointG2(
                (Spec.P - 2, 0x2),
                (
                    0x0833E47A2EAA8BBE12D33B2DA1A4FA8D763F5C567FE0DA6C5C9DA2E246F2096F,
                    0x28DC125BF7443BC1826C69FE4C7BF30C26EC60882350E784C4848C822726EB43,
                ),
            )
            + Spec.INF_G1
            + PointG2(
                (Spec.P - 2, 0x2),
                (
                    0x0833E47A2EAA8BBE12D33B2DA1A4FA8D763F5C567FE0DA6C5C9DA2E246F2096F,
                    0x28DC125BF7443BC1826C69FE4C7BF30C26EC60882350E784C4848C822726EB43,
                ),
            )
            + PointG1(0x1, Spec.P - 2)
            + PointG2(
                (Spec.P - 2, 0x2),
                (
                    0x0833E47A2EAA8BBE12D33B2DA1A4FA8D763F5C567FE0DA6C5C9DA2E246F2096F,
                    0x28DC125BF7443BC1826C69FE4C7BF30C26EC60882350E784C4848C822726EB43,
                ),
            )
            + Spec.INF_G1
            + PointG2(
                (Spec.P - 2, 0x2),
                (
                    0x0833E47A2EAA8BBE12D33B2DA1A4FA8D763F5C567FE0DA6C5C9DA2E246F2096F,
                    0x28DC125BF7443BC1826C69FE4C7BF30C26EC60882350E784C4848C822726EB43,
                ),
            ),
        ),
        pytest.param(
            PointG1(0x1, Spec.P - 2)
            + PointG2(
                (
                    Spec.P - 2,
                    0x45000000000000000000000000000000000000000000000001,
                ),
                (
                    0x07B55DE1642362D16B8FC4DCCFEC9E794D24968511CF8E252ED27AFC4D72CA1E,
                    0x0301CB4D7E0B7B52A6A8F78613C403EAD1543FEDB0D3F28C77685FDB9EAA2742,
                ),
            )
            + PointG1(0x1, Spec.P - 2)
            + PointG2(
                (
                    Spec.P - 2,
                    0x45000000000000000000000000000000000000000000000001,
                ),
                (
                    0x07B55DE1642362D16B8FC4DCCFEC9E794D24968511CF8E252ED27AFC4D72CA1E,
                    0x0301CB4D7E0B7B52A6A8F78613C403EAD1543FEDB0D3F28C77685FDB9EAA2742,
                ),
            )
            + PointG1(0x1, Spec.P - 2)
            + PointG2(
                (
                    Spec.P - 2,
                    0x45000000000000000000000000000000000000000000000001,
                ),
                (
                    0x07B55DE1642362D16B8FC4DCCFEC9E794D24968511CF8E252ED27AFC4D72CA1E,
                    0x0301CB4D7E0B7B52A6A8F78613C403EAD1543FEDB0D3F28C77685FDB9EAA2742,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x003DB26A0B244FB3FD47F7F5F0F8A289E088FD932D340F0592696503FC621248,
                0x24C9B9423EF04336563ADC35604BA729A4C9E6104BFCB55517E3198B8EDBDF98,
            )
            + PointG2(
                (
                    0x1800DEEF121F1E76426A00665E5C4479674322D4F75EDADDDE46BD5CD992F6ED,
                    0x198E9393920D483A7260BFB731DD5D25F1AA493335A9E71297E485B7AEF312C2,
                ),
                (
                    0x0B9F1099ECEFA8B45575D349B0A6F04C16D0D58AF9007F2C6D8BD7AA763A3B0E,
                    0x0B7C77862FE8D10D489A493A1A5C5D0F282C7D4E8148F340653C4B6297A1088F,
                ),
            )
            + PointG1(
                0x003DB26A0B244FB3FD47F7F5F0F8A289E088FD932D340F0592696503FC621248,
                0x24C9B9423EF04336563ADC35604BA729A4C9E6104BFCB55517E3198B8EDBDF98,
            )
            + PointG2(
                (
                    0x198E9393920D483A7260BFB731DD5D25F1AA493335A9E71297E485B7AEF312C2,
                    0x1800DEEF121F1E76426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED,
                ),
                (
                    0x2BA3E0CAB22EFBFEF96E027F1A29BA7EC11A0F824024A3787D3CB8370B9EED71,
                    0x103CE48DAC2E3FF691B61C7E4466ADF35AA183AADE7F15386BF7C789628B1B0E,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x01EA6E2EAE2A2501D6830A3F5EA1353A5F920719AAEEEA537DDE0DF31BEC7A80,
                0x2B40433B22AAAEC8F6D6D21DC04994AB99BA4A4B16545F63430A6ECF01881E09,
            )
            + PointG2(
                (
                    0x4000000000000000000000000000000000000000000000000000000,
                    0x196EC634C6397F591EBEE925F9FA9E89A1FA55BA5E38D5CB0F7DCFA49E0C0AE4,
                ),
                (
                    0x260377B5B8FED1C2F2A2F848038464FFC8C3BD1D71844FCC85F64B478248B21D,
                    0x0990A17D0F06D3BB026B17967CC55B2160D7570FDE6A448502BD28E8192DB67E,
                ),
            )
            + PointG1(
                0x01EA6E2EAE2A2501D6830A3F5EA1353A5F920719AAEEEA537DDE0DF31BEC7A80,
                0x05240B37BE86F160C1797398C137C3B1FDC72046521D6B29F9161D47D6F4DF3E,
            )
            + PointG2(
                (
                    0x4000000000000000000000000000000000000000000000000000000,
                    0x196EC634C6397F591EBEE925F9FA9E89A1FA55BA5E38D5CB0F7DCFA49E0C0AE4,
                ),
                (
                    0x260377B5B8FED1C2F2A2F848038464FFC8C3BD1D71844FCC85F64B478248B21D,
                    0x0990A17D0F06D3BB026B17967CC55B2160D7570FDE6A448502BD28E8192DB67E,
                ),
            )
            + PointG1(0x1, 0x2)
            + PointG2(
                (
                    0x0D7D3BE95C6B1FC7D70F2EDC7B7BF6E7397BC04BC6AAA0584B9E5BBC064DE4FA,
                    Spec.P - 0x1D8A9F8B4C998A61149D6C,
                ),
                (
                    0x10FB4E584F10053CBA1117D920DB188F54D1AB64E66E10B6177401A44C71E250,
                    0x20F50C6423205B18D96CDF7A832041D89076CF36DCDE6700E62833186ACD60B6,
                ),
            )
            + PointG1(0x1, 0x2)
            + PointG2(
                (
                    0x0D7D3BE95C6B1FC7D70F2EDC7B7BF6E7397BC04BC6AAA0584B9E5BBC064DE4FA,
                    Spec.P - 0x1D8A9F8B4C998A61149D6C,
                ),
                (
                    0x10FB4E584F10053CBA1117D920DB188F54D1AB64E66E10B6177401A44C71E250,
                    0x20F50C6423205B18D96CDF7A832041D89076CF36DCDE6700E62833186ACD60B6,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x0272AF94B7AEB772C1666DB65FF3987FD8EC43B8454AAD395232B5EEF18CA2C5,
                0x1D5FC6B50EF577096EC2489356E8ECCCD5ED5A144928C5338AF5549701DBB40D,
            )
            + PointG2(
                (
                    0x255495FFBA02A0ED6877A0A6ED658C93A1487A3319AAA05934E35BBB953673AF,
                    0x279573FBFE8E6C2300000000000030640472E131A029B85045,
                ),
                (
                    0x090D17C2EAEDA0D61DD0442997D161E176FB98A27091FE8B6B5746FE2F344A0F,
                    0x26F1F16556D24506AF1FD1C8CB4B3B6DFA73E2CE958C50E3B937FD59A1DF623F,
                ),
            )
            + PointG1(
                0x0272AF94B7AEB772C1666DB65FF3987FD8EC43B8454AAD395232B5EEF18CA2C5,
                0x130487BDD23C2920498DFD232A986B90C194107D1F490559B12B377FD6A1493A,
            )
            + PointG2(
                (
                    0x255495FFBA02A0ED6877A0A6ED658C93A1487A3319AAA05934E35BBB953673AF,
                    0x279573FBFE8E6C2300000000000030640472E131A029B85045,
                ),
                (
                    0x090D17C2EAEDA0D61DD0442997D161E176FB98A27091FE8B6B5746FE2F344A0F,
                    0x26F1F16556D24506AF1FD1C8CB4B3B6DFA73E2CE958C50E3B937FD59A1DF623F,
                ),
            )
            + PointG1(0x0, Spec.P)
            + PointG2(
                (0xFCFF0000000000000000000000, 0x0),
                (
                    0x212A3B4059E59D125DD17F662945170E1E13024FAE97A401895690ACAC63CF68,
                    0x1AECB67409D1D9C142FFD13375BD79FD0457DEB278DFA91B5756378FB837FD60,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x03A99966A8DB46602AC05B8F0D7669C3BC066FB7B9A188CC79E5239E27E35805,
                0x187EFF52E2187FF10F48D49A005DBEDE1F243E64CE508737F5B52BB1A997BEFA,
            )
            + PointG2(
                (0x0, 0xBF000000000000000000),
                (
                    0x1284BDD8E69832B232222D3493A6ABB523575BE2A5AF6E88F5501CEF408AA5BB,
                    0x0CA4D5B3C58E0BC7BE2C8885E53C673B54F3057CFF97CB1020CB2F5A9F61AFFB,
                ),
            )
            + PointG1(
                0x03A99966A8DB46602AC05B8F0D7669C3BC066FB7B9A188CC79E5239E27E35805,
                0x17E54F1FFF192038A907711C8123997F785D2C2C9A214355466B60652EE53E4D,
            )
            + PointG2(
                (
                    0x00C662006274FB346E22EEB59635C82CB4E20E34DA7230644E72E131C82CB4E2,
                    0x104E75A20B64000000000000000000150000000000000000006629C731,
                ),
                (
                    0x270EF2EA6F8C3DAD3832F95F309CB6A1591AD53AF025C6E0809992F15234E5FE,
                    0x1B37771CE3BB5A62017C56C496E57673E2617634E900C587724D21F24E603A63,
                ),
            )
            + Spec.INF_G1
            + PointG2(
                (0x0, 0x800),
                (
                    0x104E75A20B641566A0C71C9069A5256391AA31E22021D36C037C108DFB79C662,
                    0x00BF257AE3D66A589214F980A2AE34F9544BE2FCBCC13B21F4C1642F31AA4D20,
                ),
            )
            + Spec.INF_G1
            + PointG2((0x0, 0x0), (0x8000000, 0x0)),
        ),
        pytest.param(
            PointG1(
                0x06E42BC7EB32A979B39A77435202C2A062C8BEF977F46500B040FA35B8A45B23,
                0x15CA114B0522BDD5E928F9629ED2A283D36141F3307071CAD74FB768721CBB0E,
            )
            + Spec.INF_G2
            + PointG1(
                0x06E42BC7EB32A979B39A77435202C2A062C8BEF977F46500B040FA35B8A45B23,
                0x1A9A3D27DC0EE253CF274C53E2AEB5D9C420289E380158C264D0D4AE66604239,
            )
            + PointG2(
                (
                    0x1000000000000000000,
                    0x1611179006BEFD3749602129813BD7247045AC58EA0000000100000000000000,
                ),
                (
                    0x202A170A4A4385BDCEFBE36ADE6CC7C0E9834B78FC6CA233E8DE345A2D5782DC,
                    0x1699F57DEAACB74E8B98BD8532C3F152570DB884FC1755FBC0C8CB3EF54A537F,
                ),
            )
            + PointG1(
                0x26C6E104E6C30ED077379B1762D05AC66A6D8E1BB0699FF4F8E3FA52568F0F77,
                0x09179C965E45C4F28E2EE2AFFB9B86744B8F29DF08357DC80776ECEDE39ADC7F,
            )
            + PointG2(
                (
                    0x221276DFFF5B3A2B6A46EC6C0E0891AEFD121170D8361187B73B46E1C6B1218F,
                    0x29255D7955576BBA25241EC1EDFDFC08C9B8D29379D4213025FA95B0DBDD1646,
                ),
                (
                    0x0FF9FDFCCCDA82FB0DD8F17931E05823321073A1A4E484699ACDC9D0F14EA6F6,
                    0x0C25B531FED0C7E8899296888CC0B27FBB6DBFC2041D482E21D908E240772A23,
                ),
            )
            + PointG1(
                0x26C6E104E6C30ED077379B1762D05AC66A6D8E1BB0699FF4F8E3FA52568F0F77,
                0x09179C965E45C4F28E2EE2AFFB9B86744B8F29DF08357DC80776ECEDE39ADC7F,
            )
            + PointG2(
                (
                    0x221276DFFF5B3A2B6A46EC6C0E0891AEFD121170D8361187B73B46E1C6B1218F,
                    0x29255D7955576BBA25241EC1EDFDFC08C9B8D29379D4213025FA95B0DBDD1646,
                ),
                (
                    0x0FF9FDFCCCDA82FB0DD8F17931E05823321073A1A4E484699ACDC9D0F14EA6F6,
                    0x0C25B531FED0C7E8899296888CC0B27FBB6DBFC2041D482E21D908E240772A23,
                ),
            )
            + PointG1(
                0x26C6E104E6C30ED077379B1762D05AC66A6D8E1BB0699FF4F8E3FA52568F0F77,
                0x09179C965E45C4F28E2EE2AFFB9B86744B8F29DF08357DC80776ECEDE39ADC7F,
            )
            + PointG2(
                (
                    0x221276DFFF5B3A2B6A46EC6C0E0891AEFD121170D8361187B73B46E1C6B1218F,
                    0x29255D7955576BBA25241EC1EDFDFC08C9B8D29379D4213025FA95B0DBDD1646,
                ),
                (
                    0x0FF9FDFCCCDA82FB0DD8F17931E05823321073A1A4E484699ACDC9D0F14EA6F6,
                    0x0C25B531FED0C7E8899296888CC0B27FBB6DBFC2041D482E21D908E240772A23,
                ),
            )
            + PointG1(
                0x26C6E104E6C30ED077379B1762D05AC66A6D8E1BB0699FF4F8E3FA52568F0F77,
                0x09179C965E45C4F28E2EE2AFFB9B86744B8F29DF08357DC80776ECEDE39ADC7F,
            )
            + PointG2(
                (
                    0x221276DFFF5B3A2B6A46EC6C0E0891AEFD121170D8361187B73B46E1C6B1218F,
                    0x29255D7955576BBA25241EC1EDFDFC08C9B8D29379D4213025FA95B0DBDD1646,
                ),
                (
                    0x0FF9FDFCCCDA82FB0DD8F17931E05823321073A1A4E484699ACDC9D0F14EA6F6,
                    0x0C25B531FED0C7E8899296888CC0B27FBB6DBFC2041D482E21D908E240772A23,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x0A96696A78E6818DA746C504A8B83F7A3FAEA0DFEE0A2C52751F3CFAE5FE979B,
                0x017A319DCE2D1976671EDDD5B909781C102E5EED5C40DB00BDBD19A14397B889,
            )
            + PointG2(
                (
                    0x198E9393920DAEF312C20B9F1099ECEFA8B45575D349B0A6F04C16D0D58AF900,
                    0x1800DEEF121F1E76426A00665E5C4479674322D4F75EDADDDE46BD5CD992F6ED,
                ),
                (
                    0x05A7A5759338C23CA603C1C4ADF979E004C2F3E3C5BAD6F07693C59A85D600A9,
                    0x22376289C558493C1D6CC413A5F07DCB54526A964E4E687B65A881AA9752FAA2,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x0CDC335FA81DFF303B71CFFB0256D7097C2B4C6715CA7B1589EA9386A41C2F85,
                0x1E4077B7C1F3374BBD4750ED222848C47501B40FC4C11EADD3C39AEAFA452459,
            )
            + PointG2(
                (0x0, 0x10000000000000000000000000000),
                (
                    0x1F1CD7F247F2AE1BA9A1AEB4B32ED4C8C13C70C8861B6AB5340E276C58E1046B,
                    0x13D7DE2B557E0AE2B53380AD596BA79F07C037C9D9AA17CF407E9ED86201436E,
                ),
            )
            + PointG1(
                0x0CDC335FA81DFF303B71CFFB0256D7097C2B4C6715CA7B1589EA9386A41C2F85,
                0x1223D6BB1F3E68DDFB08F4C95F590F99227FB681A3B0ABDF685CF12BDE37D8EE,
            )
            + PointG2(
                (0x0, 0x10000000000000000000000000000),
                (
                    0x1F1CD7F247F2AE1BA9A1AEB4B32ED4C8C13C70C8861B6AB5340E276C58E1046B,
                    0x13D7DE2B557E0AE2B53380AD596BA79F07C037C9D9AA17CF407E9ED86201436E,
                ),
            )
            + PointG1(0x1, Spec.P - 2)
            + PointG2(
                (
                    Spec.P - 2,
                    0x45000000000000000000000000000000000000000000000001,
                ),
                (
                    0x07B55DE1642362D16B8FC4DCCFEC9E794D24968511CF8E252ED27AFC4D72CA1E,
                    0x0301CB4D7E0B7B52A6A8F78613C403EAD1543FEDB0D3F28C77685FDB9EAA2742,
                ),
            )
            + PointG1(
                0x12EE4836F908E5E39090A4124B75F3EC5B665A729997F55CDEA80F76AB940C59,
                0x02A12BA6400116479DCF5179E4D06471A65E72229FB444B34D8F07458A4A8157,
            )
            + PointG2(
                (0xFFFFFFFF << 184, 0xFFFFFFFF << 184),
                (
                    0x00FB55BF7DF894A746FBE20B6F8C54D5DC0D9FD4EDA4742FC35100C45E6E27F9,
                    0x12A20D63D446EB175733853B88DD36708EB7A81F5C79E7659C3A6E2B2C470077,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x0D1E4322F03FA0515F8ED6CB02B15E5A024B5092003DD7792D2AC055F14AC67D,
                0x155C53A1DAA56E3A5E9BD097CEBFCD44038F2C606C8951310AAE0EA01A447253,
            )
            + PointG2(
                (
                    0x279573FBFE8E6C2300000000000030640472E131A029B85045,
                    0x255495FFBA02A0ED6877A0A6ED4684235053C04CC3AAA05934E35BBB953673AF,
                ),
                (
                    0x0E1CEC4C9D6D3921992E4C5C71523F5D097CDE90F25B3E6C52C9C63E764A6787,
                    0x0FE0CFE24E0B2F78D4F909C9131E3794FA911B1109DF4A567B1423475CF409C1,
                ),
            )
            + PointG1(0x0, Spec.P)
            + PointG2(
                (0xFCFF0000000000000000000000, 0x0),
                (
                    0x212A3B4059E59D125DD17F662945170E1E13024FAE97A401895690ACAC63CF68,
                    0x1AECB67409D1D9C142FFD13375BD79FD0457DEB278DFA91B5756378FB837FD60,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x0E474956B0FBC11BA65F3C7632AFB3C66A98340871CEE7C974DB4461D8791B8D,
                0x25410E545457AF7BB0E9D2F1F8126180F11DEC9BFCF69CD2934E6814741C9AA2,
            )
            + PointG2(
                (
                    0x231E75FDDF7E2FA8B38B7DD6FD13EB4B70460000000000000000000002006500,
                    0x2546AC8393E836A297,
                ),
                (
                    0x0D312FC0AC642C207B5B36E17990B4F7D0EF39CFE6F0D46B9C556A0B7935714B,
                    0x1E4CD9FD726048138DCDEA456203D4B7414F3BA5EF7B37817AA98874D71C191F,
                ),
            )
            + PointG1(
                0x2E5EFCB149C6A4914B8D85BE71E79254F9FDF19F62DE2B2F6CC0822E578A420F,
                0x07FD874051CB395CA999E596047A25FC6BC12CBA97DAB578F9F903612C1C757F,
            )
            + PointG2(
                (
                    0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
                    0x1800DEEF121F1E76426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED,
                ),
                (
                    0x090689D0585FF075EC9E99AD690C3395BC4B313370B38EF355ACDADCD122975B,
                    0x12C85EA5DB8C6DEB4AAB71808DCB408FE3D1E7690C43D37B4CE6CC0166FA7DAA,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x102C9AFAA6AC9D2553D0F47E2A945816F56B10014DDCC00EF63F5CDA3D143102,
                0x0DB583622C614B32310911623E2F71F7871413D13DC372ACE97F1813D2622D59,
            )
            + PointG2(
                (
                    0x0A0E124CD6005B33C8A16492B1B451897B1679F44F3D288585EC8F82B49F6F50,
                    0x1579CD1AA3FB1BF108C6B7B5D1F4AE1FAE44099A8BF5FDDC74D87665E29812BA,
                ),
                (
                    0x0D5DB514CA1C318CC409BCBF9A75055B1A8E7B783127734D902B6118B518EE96,
                    0x2F24A2ABDA945E843C6952A5F0632365146CFD4E2034B70E41A78772FC404BEA,
                ),
            )
            + PointG1(
                0x102C9AFAA6AC9D2553D0F47E2A945816F56B10014DDCC00EF63F5CDA3D143102,
                0x22AECB10B4D054F7874734544351E666106D56C02AAE57E052A17403061ACFEE,
            )
            + PointG2(
                (
                    0x0A0E124CD6005B33C8A16492B1B451897B1679F44F3D288585EC8F82B49F6F50,
                    0x1579CD1AA3FB1BF108C6B7B5D1F4AE1FAE44099A8BF5FDDC74D87665E29812BA,
                ),
                (
                    0x0D5DB514CA1C318CC409BCBF9A75055B1A8E7B783127734D902B6118B518EE96,
                    0x2F24A2ABDA945E843C6952A5F0632365146CFD4E2034B70E41A78772FC404BEA,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x111F95E1632A3624DD29BBC012E6462B7836EB9C80E281B9381E103AEBE63237,
                0x2B38B76D492B3AF692EB99D03CD8DCFD8A8C3A6E4A161037C42F542AF5564C41,
            )
            + PointG2(
                (
                    0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
                    0x1A76DAE6D3272396D0CBE61FCED2BC532EDAC647851E3AC53CE1CC9C7E645A83,
                ),
                (
                    0x05B993046905746641A19B500EBBBD30CF0068A845BFBEE9DE55B8FE57D1DEE8,
                    0x243EF33537F73EF4ACE4279D86344D93A5DC8C20C69045865C0FA3B924933879,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x11C8F0EA735E099781F852FB93256540C7C7611BA324F67680F3DBFC00BBDDA1,
                0x2D7FB8D83E13AFA4EA8A9D8817CD5B7C5B1804AA1006AF2A8AB7E9C7757B300C,
            )
            + PointG2(
                (
                    0x040000002DB3759AAFF5357156BC2E8D52EACD11EFB7D108D3B4034162839A93,
                    0x300000000000000000000000000000000000000000003100000000,
                ),
                (
                    0x0649EBC27A3909E089C6023C7ED952098A3E5547CE56E79953929BA4D718F131,
                    0x1C2C7E752E7947B506C14A8300A0D15D9022BD6FBA67461CC8A0783DFEBA77FB,
                ),
            )
            + PointG1(
                0x11C8F0EA735E099781F852FB93256540C7C7611BA324F67680F3DBFC00BBDDA1,
                0x02E4959AA31DF084CDC5A82E69B3FCE13C6965E7586B1B62B168A24F6301CD3B,
            )
            + PointG2(
                (
                    0x040000002DB3759AAFF5357156BC2E8D52EACD11EFB7D108D3B4034162839A93,
                    0x300000000000000000000000000000000000000000003100000000,
                ),
                (
                    0x0649EBC27A3909E089C6023C7ED952098A3E5547CE56E79953929BA4D718F131,
                    0x1C2C7E752E7947B506C14A8300A0D15D9022BD6FBA67461CC8A0783DFEBA77FB,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x12CA97E893996E5BB392C57ABBA4578276654D2856B336B640EAFD84DE31140E,
                0x055370544625EA3C3E85A42831DCAF47353695B158149BC2D5BF4061326F089E,
            )
            + PointG2(
                (
                    0x0E80426227CE5FD647AFBA497E7EA7A2687E956E978E3572C3DF73E9278302B9,
                    0xC451F8749A,
                ),
                (
                    0x05602FDE384569BE9950C3466D0FB40A66A63F202C3A685856CD21C76CEA2BE7,
                    0x0ED4F367E657BC59C785BF6BF6AC33FB4B653E8BD68D1D838E0416E8C47B5F53,
                ),
            )
            + PointG1(
                0x12CA97E893996E5BB392C57ABBA4578276654D2856B336B640EAFD84DE31140E,
                0x2B10DE1E9B0BB5ED79CAA18E4FA4A916624AD4E0105D2ECA66614BB5A60DF4A9,
            )
            + PointG2(
                (
                    0x0E80426227CE5FD647AFBA497E7EA7A2687E956E978E3572C3DF73E9278302B9,
                    0xC451F8749A,
                ),
                (
                    0x05602FDE384569BE9950C3466D0FB40A66A63F202C3A685856CD21C76CEA2BE7,
                    0x0ED4F367E657BC59C785BF6BF6AC33FB4B653E8BD68D1D838E0416E8C47B5F53,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x1425B11B4FE47A394DBFC0AD3E99DC93C3E1C0980B9BCB68529BA9DE33DBF585,
                0x168B8CDFF7AE7D084FD111608FA03E018B415FD4F0755F7E8F039A2D852BDA0E,
            )
            + PointG2(
                (
                    0x5B00,
                    0x149BB18D1ECE5FD647AFBA497E7EA7A2687E956E978E3072C4FC9EC579B80946,
                ),
                (
                    0x2061EBAFFAEDC532D8BB542F9D93CAE5DC6C4B431833EE0A7BE4D053E2E0D60D,
                    0x03C12E282E4442C88F5235D004E8EDBA3080754CA41C976D03CD332A9B6FA42D,
                ),
            )
            + PointG1(
                0x1425B11B4FE47A394DBFC0AD3E99DC93C3E1C0980B9BCB68529BA9DE33DBF585,
                0x19D8C192E9832321687F3455F1E11A5C0C400ABC77FC6B0EAD1CF1E953512339,
            )
            + PointG2(
                (
                    0x149BB18D1ECE5FD647AFBA497E7EA7A2687E956E978E3572C4FC9EC579B80946,
                    0x5B00,
                ),
                (
                    0x29E864B516B661105D0A2708F21BEAAE1BF1636608AC53864C4D8F0EA2E7DC38,
                    0x05C3B957CAA8F4C5F248E3E6E754304E9BA7E5B6DD3A4ECE125F47811A525E65,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x1565586940BBB0E082639A1E2C9ECFE96BFF6CBDA25A93C4D462B83602300672,
                0x19767D96DD90432F459BF8F6181C9FEA507BF7BCD4063FD070FE8E72093E8BF9,
            )
            + PointG2(
                (0xE8, 0x0),
                (
                    0x23812D70E97CFD777C5CF0B64B18400F3EA88AFB56146BFC1F34071EEBB05998,
                    0x27352C710F0E1711B5D18E672B5CAB3C369CD8D84B70ED159BB712C7D929C8E5,
                ),
            )
            + PointG1(
                0x1565586940BBB0E082639A1E2C9ECFE96BFF6CBDA25A93C4D462B83602300672,
                0x16EDD0DC03A15CFA72B44CC06964B873470572D4946B8ABCCB21FDA4CF3E714E,
            )
            + PointG2(
                (
                    0x252B5EC0E7DF7DF26D0CC46DD811ACE847A4174AA634C8D9269CCEBB52845D78,
                    0x29A0FE67466554BC0A6C97089DEC1EBAC672344BC3A69B8FC6904F9B83438CBB,
                ),
                (
                    0x24C159CDA85A7F7E04F7E128101E8FBE502FEE784946FFCE0A9174424F0254B2,
                    0x2B0C8AC28082E97EAE5EE175AE2C1A6E466C7DD693238A386EC80F7743FFC517,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x17956B549321B92C524D191A62B90C81F08E694AF4DCEB00A80094E53120D39E,
                0x2FD15D78815388959CAA54AFFA2D7B2C8D52C528E6A1F6C0A50FCF0498FAC7EE,
            )
            + PointG2(
                (
                    0x30644E72E131A029000000000000000000000000000000004000000000000000,
                    0x0,
                ),
                (
                    0x016B9E28A32EE61A7AD5BD4BAD29D64FC35A8FB46B510BE2067907069497AE1F,
                    0x0C3C07C40F41A731FE27D953F1154B4E9A8ACF3EF44608817150DE0DF916503A,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x17956B549321B92C524D191A62B90C81F08E694AF4DCEB00A80094E53120D39E,
                0x2FD15D78815388959CAA54AFFA2D7B2C8D52C528E6A1F6C0A50FCF0498FAC7EE,
            )
            + PointG2(
                (
                    0x30644E72E131A029000000000000000000000000000000004000000000000000,
                    0x0,
                ),
                (
                    0x016B9E28A32EE61A7AD5BD4BAD29D64FC35A8FB46B510BE2067907069497AE1F,
                    0x0C3C07C40F41A731FE27D953F1154B4E9A8ACF3EF44608817150DE0DF916503A,
                ),
            )
            + PointG1(
                0x17956B549321B92C524D191A62B90C81F08E694AF4DCEB00A80094E53120D39E,
                0x2FD15D78815388959CAA54AFFA2D7B2C8D52C528E6A1F6C0A50FCF0498FAC7EE,
            )
            + PointG2(
                (
                    0x30644E72E131A029000000000000000000000000000000004000000000000000,
                    0x0,
                ),
                (
                    0x016B9E28A32EE61A7AD5BD4BAD29D64FC35A8FB46B510BE2067907069497AE1F,
                    0x0C3C07C40F41A731FE27D953F1154B4E9A8ACF3EF44608817150DE0DF916503A,
                ),
            )
            + PointG1(
                0x17956B549321B92C524D191A62B90C81F08E694AF4DCEB00A80094E53120D39E,
                0x2FD15D78815388959CAA54AFFA2D7B2C8D52C528E6A1F6C0A50FCF0498FAC7EE,
            )
            + PointG2(
                (
                    0x30644E72E131A029000000000000000000000000000000004000000000000000,
                    0x0,
                ),
                (
                    0x016B9E28A32EE61A7AD5BD4BAD29D64FC35A8FB46B510BE2067907069497AE1F,
                    0x0C3C07C40F41A731FE27D953F1154B4E9A8ACF3EF44608817150DE0DF916503A,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x17AC723D48C98FCE706845B61C254630ACB6DA96A9620FC6CD07276A4EF8936D,
                0x1A515B7E403D2A46BB5387138F17D33C2B12E3D5051F9D22042921F35031035E,
            )
            + PointG2(
                (0x10000000000000000000000000000000000000000000000000000, 0x0),
                (
                    0x2D8AD25DC006EEA79B9C052A6A367B209D5C9215C8A4C325555A7E1E608ABED0,
                    0x22DD54ED23382326A8DF674C7BE35D7AC181C9625A10F508DD7FBD109760D762,
                ),
            )
            + PointG1(
                0x17AC723D48C98FCE706845B61C254630ACB6DA96A9620FC6CD07276A4EF8936D,
                0x1612F2F4A0F475E2FCFCBEA2F26985216C6E86BC63522D6B37F76A23884BF9E9,
            )
            + PointG2(
                (
                    0x062CA96B10A86BE7BC151A74E01170193F2AD046C2F5EB3A25A95592CC3A1775,
                    0x2043C18FE0A47868239575B1C3700BE7308890370EB6982F4E3E36916EBC28F5,
                ),
                (
                    0x2B7D22180BE2BDCA69028C5BF32181D203B2350781D675098B320766F5DCD9B0,
                    0x2A21AA3010F604FEA531E9264671D546CC94D8A0DDAB42B7146573F5C1ED26FB,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x1838CCF8D820349A8C38A57DC0A5495577898E422509E4C9636E9737FE0DCD91,
                0x16F566A30B7D2579FD6109EB09D66C005FDCCDC0D91B28F43BE34C5668F34F81,
            )
            + PointG2(
                (
                    0x2A9A64F273FA329BC9C98FF2083C627609E2219177B9C5DF7286AF31A3B27E81,
                    0x20D85101E1E6AF0126C00A95C645B192B3EA69ED72297DEAC1FBB0E6BD1440C6,
                ),
                (
                    0x00EC155AB3CD58005B488308578AAEEAEAE9C65939F785BF693FA5763C174DD6,
                    0x24D3B2ADB35AD17933D0317A00436D10F2D6908FAF109E7FE3DB77A39D5C1711,
                ),
            )
            + PointG1(
                0x175BCEC7C4C77C612DF588174DD44362722F7B8E588A0EF599129CF123F63B8D,
                0x2E1FF6C569E5CB0D20FB28504057D4F7ED248900AC99BD0F31A853AF5C10A806,
            )
            + PointG2(
                (
                    0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
                    0x1800DEEF121F1E76426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED,
                ),
                (
                    0x090689D0585FF075EC9E99AD690C3395BC4B313370B38EF355ACDADCD122975B,
                    0x12C85EA5DB8C6DEB4AAB71808DCB408FE3D1E7690C43D37B4CE6CC0166FA7DAA,
                ),
            )
            + PointG1(0x1, Spec.P - 2)
            + PointG2(
                (
                    0x1800DEEF121F1E76426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED,
                    0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
                ),
                (
                    0x1CC9A9EB823F8D97ADEE0206828C9F19EAF8F536C23207D68AE3D056A1480BB2,
                    0x1990DDB90388B94F31089D3B4FF594D5449C04FCDF2A3681017B5D7749367BA1,
                ),
            )
            + PointG1(0x1, Spec.P - 2)
            + PointG2(
                (
                    0x1800DEEF121F1E76426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED,
                    0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
                ),
                (
                    0x1CC9A9EB823F8D97ADEE0206828C9F19EAF8F536C23207D68AE3D056A1480BB2,
                    0x1990DDB90388B94F31089D3B4FF594D5449C04FCDF2A3681017B5D7749367BA1,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x1BBEFDB0536C0996D663A908ADC2CAE17180C53D971E73FE234A6927CD10DA33,
                0x2481152785517C274B2DC4AB7B6CACBBDC7D7B8E4DD396FAA05A119761130E5C,
            )
            + PointG2(
                (
                    0x039A49879C785FD647AFBA497E7EA7A2687E956E978E3572C3DF73E9278302B9,
                    0x194B9757129492217D64C4B267E5E935137AE3859EC8B99CF6E6DC61CA90BDFD,
                ),
                (
                    0x1C67B6B637C528053A25079E25734A67FFC5388209D11839B3FF1F92591C81EE,
                    0x09750D9BC6FDB71F16E6A69EEA50E7288AAC1C25A5CD674CA9C57D8AC06FAC69,
                ),
            )
            + PointG1(
                0x1BBEFDB0536C0996D663A908ADC2CAE17180C53D971E73FE234A6927CD10DA33,
                0x0BE3394B5BE024026D22810B0614ABA1BB03EF031A9E33929BC67A7F7769EEEB,
            )
            + PointG2(
                (
                    0x039A49879C785FD647AFBA497E7EA7A2687E956E978E3572C3DF73E9278302B9,
                    0x194B9757129492217D64C4B267E5E935137AE3859EC8B99CF6E6DC61CA90BDFD,
                ),
                (
                    0x1C67B6B637C528053A25079E25734A67FFC5388209D11839B3FF1F92591C81EE,
                    0x09750D9BC6FDB71F16E6A69EEA50E7288AAC1C25A5CD674CA9C57D8AC06FAC69,
                ),
            )
            + PointG1(
                0x29A0D6D5E7D14A774C3ABFF1435361DA2EE5D8B4F3EE62085CE779F248B41D4A,
                0x2FD37AE5468F6A17B7F9A0BCCA02EE128BDCED61402A566E4EEE2D0FA825F03D,
            )
            + PointG2(
                (
                    0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
                    0x1800DEEF121F1E76426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED,
                ),
                (
                    0x090689D0585FF075EC9E99AD690C3395BC4B313370B38EF355ACDADCD122975B,
                    0x12C85EA5DB8C6DEB4AAB71808DCB408FE3D1E7690C43D37B4CE6CC0166FA7DAA,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x1BBF3321BFDF76E22CA0E95089338A772A4A2982DBEDE2571C14A258BD9874FF,
                0x2B5AA74EFA3429CD77ACC68BD2E487960F34074D3A725444B06A552C1BE0CA44,
            )
            + PointG2(
                (
                    0x2471FA6C0785556DACBE4D9570FA9E89A2FA55BA5E38D5CB0F7DCFA49E0C0AE4,
                    0x181B42BBB36F2BB465708C62B0BD12AE5D6922CF5C4F928A7097F8DB8F0DFAE3,
                ),
                (
                    0x103E85DDEFBE5900DED1384BADBC32C907C50BAA4282172D02562116005AECDF,
                    0x2CCE8D04251B64CED66CC7B66A1C54000E17872B10B4793F5BD81052E5EF3E5C,
                ),
            )
            + PointG1(
                0x1BBF3321BFDF76E22CA0E95089338A772A4A2982DBEDE2571C14A258BD9874FF,
                0x0509A723E6FD765C40A37F2AAE9CD0C7884D63442DFF76488BB636EABC9C3303,
            )
            + PointG2(
                (
                    0x2471FA6C0785556DACBE4D9570FA9E89A2FA55BA5E38D5CB0F7DCFA49E0C0AE4,
                    0x181B42BBB36F2BB465708C62B0BD12AE5D6922CF5C4F928A7097F8DB8F0DFAE3,
                ),
                (
                    0x103E85DDEFBE5900DED1384BADBC32C907C50BAA4282172D02562116005AECDF,
                    0x2CCE8D04251B64CED66CC7B66A1C54000E17872B10B4793F5BD81052E5EF3E5C,
                ),
            )
            + PointG1(
                0x00710C68E1B8B73A72A289422D2B6F841CC56FE8C51105021C56AE30C3AE1ACA,
                0x0B2FF392A2FC535427EC9B7E1AE1C35A7961986788CF648349190DD92E182F05,
            )
            + PointG2(
                (
                    0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
                    0x1800DEEF121F1E76426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED,
                ),
                (
                    0x090689D0585FF075EC9E99AD690C3395BC4B313370B38EF355ACDADCD122975B,
                    0x12C85EA5DB8C6DEB4AAB71808DCB408FE3D1E7690C43D37B4CE6CC0166FA7DAA,
                ),
            )
            + PointG1(
                0xBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBE,
                0xBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBE,
            )
            + PointG2(
                (
                    0xBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBE,
                    0xBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBE,
                ),
                (
                    0xBEFDBEBEBEBEABC689BEBEBEBE43BE92BE5FBEBEBEBEBEBEBEBEBEBEBEBEBEBE,
                    0xBEBEBEBEBEBEBEBEBE9EBEBEBE2ABEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBEBE,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x1C4189BBFE590521DA71E6834B73A622528FD923E9421F18DF9A48E9123B16AA,
                0x15C8E4948927F2E089ACCB33C8D51B4C83CA69505F4A7801399573273D743991,
            )
            + PointG2(
                (0x8000, 0x8000),
                (
                    0x23AD956E40F22F18BF59310F6D23055F2A3FDC2713F05CF1B099A18041CD4982,
                    0x20B15BB64C3C6223098439E4FC7E9B2BD956ED94B2BF1F066C281D41C8560EE5,
                ),
            )
            + PointG1(
                0x1C4189BBFE590521DA71E6834B73A622528FD923E9421F18DF9A48E9123B16AA,
                0x1A9B69DE5809AD492EA37A82B8AC3D1113B701410927528C028B18EF9B08C3B6,
            )
            + PointG2(
                (0x8000, 0x8000),
                (
                    0x23AD956E40F22F18BF59310F6D23055F2A3FDC2713F05CF1B099A18041CD4982,
                    0x20B15BB64C3C6223098439E4FC7E9B2BD956ED94B2BF1F066C281D41C8560EE5,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x1C934D642C245E76EB0C016B17E8ECED3A1CF56EF6D787EACE40BC0CB933DEA9,
                0x02567D6E1141F67673E6F17A705F3D9764C6D5673F1F93E2ED5A21FD38E9A572,
            )
            + PointG2(
                (0x0, 0x770000000000000000000000),
                (
                    0x1F3953D0D836A44E15AEBEF16DD187CCF9493693379FE7D1C5A2CF2DEB87F89C,
                    0x0DD737C063475FC587C1574A8FF4E9E4F933118D67BB7BA4A70C79C1CCB0D344,
                ),
            )
            + PointG1(
                0x1C934D642C245E76EB0C016B17E8ECED3A1CF56EF6D787EACE40BC0CB933DEA9,
                0x2E0DD104CFEFA9B34469543C11221AC632BA952A295236AA4EC66A199F9357D5,
            )
            + PointG2(
                (0x0, 0x770000000000000000000000),
                (
                    0x1F3953D0D836A44E15AEBEF16DD187CCF9493693379FE7D1C5A2CF2DEB87F89C,
                    0x0DD737C063475FC587C1574A8FF4E9E4F933118D67BB7BA4A70C79C1CCB0D344,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x1CED814234531C29AA14F95E3A3F59657AACEA69FA4C35DFA5B8E03C87E80757,
                0x25C3327A2C4F61437D53ABBB2BB75DC1DC4F2427C3E9D7714D5D83DAE8069769,
            )
            + PointG2(
                (
                    0x0EC85B4F8A9224B27145B3757B7BF6E7397BC04C8634404D924689E27BB8A261,
                    0xBF89,
                ),
                (
                    0x0E717255B589C7286F7BDE23FE6AC9D838262D9E7BA5BC603E410ABF27AADA5B,
                    0x1760BBDB5183AE4E28F049CFE75FB9600B8FD03E63D9AA1A9BD709D23AFBC12F,
                ),
            )
            + PointG1(
                0x1CED814234531C29AA14F95E3A3F59657AACEA69FA4C35DFA5B8E03C87E80757,
                0x0AA11BF8B4E23EE63AFC99FB55C9FA9BBB324669A487F31BEEC3083BF07665DE,
            )
            + PointG2(
                (
                    0x0EC85B4F8A9224B27145B3757B7BF6E7397BC04C8634404D924689E27BB8A261,
                    0xBF89,
                ),
                (
                    0x0E717255B589C7286F7BDE23FE6AC9D838262D9E7BA5BC603E410ABF27AADA5B,
                    0x1760BBDB5183AE4E28F049CFE75FB9600B8FD03E63D9AA1A9BD709D23AFBC12F,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x1F9D02FA71D0AE244EDC79709AF68216D99A978A5E8FD92EBE793FFF8317AAD4,
                0x2CD6A493D88A0A87A6F6818C23FA87FF12FD84E5641E1081E849F6E88A488A43,
            )
            + PointG2(
                (
                    0x04BB53B8977E5F92A0BC372742C48309445CD3CFA9A62AEE49F8130962B4B3B9,
                    0x203E205DB4F19B37B60121B83A7333706DB86431C6D835849957EDF0509DE152,
                ),
                (
                    0x1F544B5E4AB6D13DCB7E89582AAEE12A8410A7C6B2D8A5DE7BD83E8CDB1FB1A8,
                    0x2BAEF43E095CAAF7C2ACA272AEE277D1DA98D74656F2CA01B833C67DCC08CA5D,
                ),
            )
            + PointG1(0x1, Spec.P - 2)
            + PointG2(
                (
                    0x5B0045000000000000000000000000000000000000000000000001,
                    Spec.P - 2,
                ),
                (
                    0x218C0CEF2A606613357BFAA3C880E71FF8490195337FA26205A21CCD9A6949A3,
                    0x13FED2C79ADD9D85B9949C5852EF8CCCF02B69EA6FC4DB0D1660AC7B50DF39E1,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x225FDAB8FE6CD876363D27075CDF0D01C209DA61B1634B574A5D811CFAE40700,
                0x1216B7C3E2ADC07C3BEF31771C7BB9E1D02F07FF3A5B74953C4FD5BF9A7A6DFF,
            )
            + PointG2(
                (
                    0x25F63FCC543337B8F6275F97D6479633B921541A96E0F2ACAF901BC25DB7407C,
                    0x206776F9480168741ECA625C06E5526B4664A02CE664BC656F39664D96278B6E,
                ),
                (
                    0x1E40E8084FD648BA315F691E8367BE1D4C13844421C87223D84829C31A0D7AFE,
                    0x24B8042D4CB604AE66C0DC97CA8A9C2D22C743335D92BC401700F6B00D5CDC5B,
                ),
            )
            + PointG1(
                0x2A4F1DBC9FE6D2882462FB11AFEAE7B7F2A0CF213B1F19C45CB222336283F380,
                0x1141763C897C9A90E387EA80F68EB88C2D79AAB680196D9538CD2CA632A5E81B,
            )
            + PointG2(
                (
                    0x0E540F5B5BE91F82ED05349750761224F543068CE30D2D5E838BF66866F34520,
                    0x0FA5AC8C46F725E54505019BDA3356EF6E35B0A89B9B4F79BB0C62211235C931,
                ),
                (
                    0x2E6D97A1F7E0428FC0BE6BE02C811095F5166710DCBE869C36A8EF89CAC63E01,
                    0x2657BBAF3BCFD106DD677EEF03172F693A6C919776F441DC0FD47A4BD91D0487,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x22847A3CD1CB28B60A51B54991D6DD86D206AA12B3873942C45A120B2E63A492,
                0x26C3889C7B08D9288F13F64E6E3F166C59F57B5C014CBECF815A4ABA4EBABBFB,
            )
            + PointG2(
                (
                    0x2E91F2B0F4F7A42C870FE8F6236EC1042BDEB2586A641808A5E09019514E83A0,
                    0x2B078A1F12CB5426B6BCFEB9548566AFB4BDF7454190EAF97F63E210F3A94CE1,
                ),
                (
                    0x008A9EDE8DDE2C849793027433D90C626BC326BDC248DC223F537F7152955DAC,
                    0x00B319B7060AD49091D9B52015B4AE8085BF6739B7F5A2C098C2F113FF33806A,
                ),
            )
            + PointG1(
                0x22847A3CD1CB28B60A51B54991D6DD86D206AA12B3873942C45A120B2E63A492,
                0x26C3889C7B08D9288F13F64E6E3F166C59F57B5C014CBECF815A4ABA4EBABBFB,
            )
            + PointG2(
                (
                    0x2E91F2B0F4F7A42C870FE8F6236EC1042BDEB2586A641808A5E09019514E83A0,
                    0x2B078A1F12CB5426B6BCFEB9548566AFB4BDF7454190EAF97F63E210F3A94CE1,
                ),
                (
                    0x008A9EDE8DDE2C849793027433D90C626BC326BDC248DC223F537F7152955DAC,
                    0x00B319B7060AD49091D9B52015B4AE8085BF6739B7F5A2C098C2F113FF33806A,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x26581613E6C802822867D2B3A0867FD7FD8CEA503764AE1A9D01EC0D5364D1BE,
                0x0530AE3D4FE87AC76DA4382835135AC0AEC9B1ECD0705CF84C21B48327EADE54,
            )
            + PointG2(
                (
                    0x07A13E1BE6F9072893C0E5BB528C5CC22DD6370308DDA1613068E064C6E5D15A,
                    0x067239C795D2EA27B85D93E54FC221D81E9DE3EBC8E43C20D63608E7078FAB68,
                ),
                (
                    0x22FA7EA234E21AEC74F4DB0B365AE1E7CC6E7F4AAC89BC460D0308B83399BE86,
                    0x27705B19388EBEDDBD35A5CE72830EC07E3F1BCA3F4E9FDC0AEBAAB5A1FE91B1,
                ),
            )
            + PointG1(
                0x26581613E6C802822867D2B3A0867FD7FD8CEA503764AE1A9D01EC0D5364D1BE,
                0x2B33A035914925624AAC0D8E4C6DFD9CE8B7B8A498016D94EFFED793B0921EF3,
            )
            + PointG2(
                (
                    0x07A13E1BE6F9072893C0E5BB528C5CC22DD6370308DDA1613068E064C6E5D15A,
                    0x067239C795D2EA27B85D93E54FC221D81E9DE3EBC8E43C20D63608E7078FAB68,
                ),
                (
                    0x22FA7EA234E21AEC74F4DB0B365AE1E7CC6E7F4AAC89BC460D0308B83399BE86,
                    0x27705B19388EBEDDBD35A5CE72830EC07E3F1BCA3F4E9FDC0AEBAAB5A1FE91B1,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x28100E22DF4DC1C6BF8801F63FFDEF2AF6BFB80147994395BE6DC792479CA4F5,
                0x17414E05AC69D56DEC03E0AF314645B463414A7D831AFF54459B6D409351A5A4,
            )
            + PointG2(
                (
                    0x2851FD14FBAA7FD586E3039A2D9FA136C42685CB2B5904BF0591B95B52FC,
                    0x0,
                ),
                (
                    0x24D852A54E2D52FFC43B2E4F1993FD159AE7EC19AF2F3AD548F6DAA33BD0DE31,
                    0x0B0FABBC2F33EA444E5F3C92269F11FC30C048463973A914A6787DBD616E703E,
                ),
            )
            + Spec.INF_G1
            + PointG2(
                (
                    0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
                    0x1800DEEF121F1E76426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED,
                ),
                (
                    0x090689D0585FF075EC9E99AD690C3395BC4B313370B38EF355ACDADCD122975B,
                    0x12C85EA5DB8C6DEB4AAB71808DCB408FE3D1E7690C43D37B4CE6CC0166FA7DAA,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x299A5917ADB7B45C30CEA045EDAA623F5036280DF176F4A2C751CA728C2C9E3A,
                0x2BEDF30BA7D8BD0814E9D091913EA5BC6A4B60EE993E949507832DF601906519,
            )
            + PointG2(
                (0x10000000, 0x0),
                (
                    0x213D689AF09B7F52AC4A04C34BCDB2F90521B1CD213EDCFE48FA3063520B6BE2,
                    0x2EF0F3110EA3051248E907221493E6C2943EBE8D70794188A515EC23DF5D9B2B,
                ),
            )
            + PointG1(
                0x299A5917ADB7B45C30CEA045EDAA623F5036280DF176F4A2C751CA728C2C9E3A,
                0x04765B673958E321A3667524F042B2A12D3609A2CF3335F8349D5E20D6EC982E,
            )
            + PointG2(
                (0x10000000, 0x0),
                (
                    0x213D689AF09B7F52AC4A04C34BCDB2F90521B1CD213EDCFE48FA3063520B6BE2,
                    0x2EF0F3110EA3051248E907221493E6C2943EBE8D70794188A515EC23DF5D9B2B,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x299A5917ADB7B45C30CEA045EDAA623F5036280DF176F4A2C751CA728C2C9E3A,
                0x2BEDF30BA7D8BD0814E9D091913EA5BC6A4B60EE993E949507832DF601906519,
            )
            + PointG2(
                (0x10000000, 0x0),
                (
                    0x213D689AF09B7F52AC4A04C34BCDB2F90521B1CD213EDCFE48FA3063520B6BE2,
                    0x2EF0F3110EA3051248E907221493E6C2943EBE8D70794188A515EC23DF5D9B2B,
                ),
            )
            + PointG1(
                0x299A5917ADB7B45C30CEA045EDAA623F5036280DF176F4A2C751CA728C2C9E3A,
                0x04765B673958E321A3667524F042B2A12D3609A2CF3335F8349D5E20D6EC982E,
            )
            + PointG2(
                (0x10000000, 0x0),
                (
                    0x213D689AF09B7F52AC4A04C34BCDB2F90521B1CD213EDCFE48FA3063520B6BE2,
                    0x2EF0F3110EA3051248E907221493E6C2943EBE8D70794188A515EC23DF5D9B2B,
                ),
            )
            + PointG1(
                0x299A5917ADB7B45C30CEA045EDAA623F5036280DF176F4A2C751CA728C2C9E3A,
                0x2BEDF30BA7D8BD0814E9D091913EA5BC6A4B60EE993E949507832DF601906519,
            )
            + PointG2(
                (0x10000000, 0x0),
                (
                    0x213D689AF09B7F52AC4A04C34BCDB2F90521B1CD213EDCFE48FA3063520B6BE2,
                    0x2EF0F3110EA3051248E907221493E6C2943EBE8D70794188A515EC23DF5D9B2B,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x29C19B11665CBEB0FD496542E6115CEEF9B628AB4BC7419802E7016CF1B2C931,
                0x057CDBEC3F7C2AD0F4DA33B3CFD3234EA29F71C6C46B8B90EB2D4A5851ADF74B,
            )
            + PointG2(
                (
                    0x00BB00B95E1B59FCA2159A5F33F27F36B15FE6BCDA0B1EE0381B0EF7DD804BD6,
                    0x25ED3C1A0120B6531E39CCA6F67F35F9A849CFBFE958CC1840D1C20CC6B3E1AD,
                ),
                (
                    0x08CBBA5815581DCEA62FA0426DBFF39C8F0E9FDC451B1FB127A4E7A4C0587996,
                    0x19068E06466A9DD7543AC89D53A17A8BEB6C11C59C3AF32EA0C1BBC55E0FAE7B,
                ),
            )
            + PointG1(
                0x2C52AB9E7E9296183B9695387E3AE3D06C9D11A98676E4E046914B36B636DDC4,
                0x050ABC3606826F8AEAAC5AA7BE9F44D15A55805037EB2B260C32D43BD32ADEF1,
            )
            + PointG2(
                (
                    0x0763B017BC2777AC81FF30FFF09F65381C24912BFC9D1490A23765B4830F0AAE,
                    0x2B71C998ABC367AD761DA7E9900EB7E579989F82EEE3338C17B8DC17E53E052B,
                ),
                (
                    0x21E242369877673070A6B8B0307DA6E84E32BDFB3EB09D514B25E8704BD55D43,
                    0x1782C07D2D471AF10469A13476A49EC51D1BC538D49BBAF85A63FDB6B412FB4A,
                ),
            )
            + PointG1(
                0x1BC85B155EEE2E33BF5322810C7C0150158F373E998316EDF821AE9804A2AC19,
                0x1899A5E18C57F4E6B5F736C2F21E95F4147A4235ED2C1F6E6615EB0E00979F09,
            )
            + PointG2(
                (
                    0x20568D8F3B2F2D0A6A596EA20B3E62191BAF420DE10125557F9A665900A82A59,
                    0x25A43A697CEAA9DEBA01A97D8722815E8185973A402E11FDCA62FA908DA409C4,
                ),
                (
                    0x054081D5B9D0E3AA18A31CC5F9D0FA925205FD50A71EDF4CA157A607587E2457,
                    0x1C9CACF3B3D821146083F9E5FE6BE23546643E3AD4540A1F02C02728010A4B9F,
                ),
            )
            + Spec.INF_G1
            + PointG2(
                (
                    Spec.P - 0x725A44E7,
                    0x4500000000000000000000000107B55DE1642362D16B8FC4DC,
                ),
                (
                    0x2215436159D2BDB4E084A6C63BD04F6B84D69BFAD793DA72C21B421F3F89B22F,
                    0x22B811A1A4FA51DF281657F0B0A1ADD382FAB768AC1ED8886BF979E2BF11402D,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x2DEB529E45720F20BE41088DFD7489C315E9E18FE23DD1C8A8183295DC770DEE,
                0x1090B3FCD1898780C332B7D73A602CADD1B26029124DB9DA19941250EDA890B5,
            )
            + PointG2(
                (0xFF0A69A42C284614E3D7DE26B3F9B2F3C71FF6, 0x0),
                (
                    0x1E2C7F9D6A525B6AF5DAD683C5E6408661DA29780860C3209B2DDDCAD5A88795,
                    0x033123665850406FC2428227BBB3509FC71C911CF41623DE1605CD3E0A281B90,
                ),
            )
            + PointG1(
                0x2DEB529E45720F20BE41088DFD7489C315E9E18FE23DD1C8A8183295DC770DEE,
                0x1090B3FCD1898780C332B7D73A602CADD1B26029124DB9DA19941250EDA890B5,
            )
            + PointG2(
                (0x275680008DED35BA000000, 0x0),
                (
                    0x19367FE97B92D85D7C29090C2313DE1A85F030239CFA71F939A197249CB17B89,
                    0x0465A8498153883ACA20E4DE66AC02B1B6957FAB9B4BCE71DF334CD6BEE5FF95,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x2DEB529E45720F20BE41088DFD7489C315E9E18FE23DD1C8A8183295DC770DEE,
                0x1090B3FCD1898780C332B7D73A602CADD1B26029124DB9DA19941250EDA890B5,
            )
            + PointG2(
                (0xFF0A69A42C284614E3D7DE26B3F9B2F3C71FF6, 0x0),
                (
                    0x1E2C7F9D6A525B6AF5DAD683C5E6408661DA29780860C3209B2DDDCAD5A88795,
                    0x033123665850406FC2428227BBB3509FC71C911CF41623DE1605CD3E0A281B90,
                ),
            )
            + PointG1(
                0x2DEB529E45720F20BE41088DFD7489C315E9E18FE23DD1C8A8183295DC770DEE,
                0x1090B3FCD1898780C332B7D73A602CADD1B26029124DB9DA19941250EDA890B5,
            )
            + PointG2(
                (0x275680008DED35BA000000, 0x0),
                (
                    0x19367FE97B92D85D7C29090C2313DE1A85F030239CFA71F939A197249CB17B89,
                    0x0465A8498153883ACA20E4DE66AC02B1B6957FAB9B4BCE71DF334CD6BEE5FF95,
                ),
            )
            + PointG1(
                0x2DEB529E45720F20BE41088DFD7489C315E9E18FE23DD1C8A8183295DC770DEE,
                0x1090B3FCD1898780C332B7D73A602CADD1B26029124DB9DA19941250EDA890B5,
            )
            + PointG2(
                (0x275680008DED35BA000000, 0x0),
                (
                    0x19367FE97B92D85D7C29090C2313DE1A85F030239CFA71F939A197249CB17B89,
                    0x0465A8498153883ACA20E4DE66AC02B1B6957FAB9B4BCE71DF334CD6BEE5FF95,
                ),
            )
            + PointG1(
                0x2DEB529E45720F20BE41088DFD7489C315E9E18FE23DD1C8A8183295DC770DEE,
                0x1090B3FCD1898780C332B7D73A602CADD1B26029124DB9DA19941250EDA890B5,
            )
            + PointG2(
                (0x275680008DED35BA000000, 0x0),
                (
                    0x19367FE97B92D85D7C29090C2313DE1A85F030239CFA71F939A197249CB17B89,
                    0x0465A8498153883ACA20E4DE66AC02B1B6957FAB9B4BCE71DF334CD6BEE5FF95,
                ),
            ),
        ),
    ],
    ids=lambda _: "invalid_g2_subgroup_",
)
def test_invalid_g2_subgroup(
    state_test: StateTestFiller,
    pre: Alloc,
    post: dict,
    tx: Transaction,
) -> None:
    """Test invalid g2 subgroup inputs to the ecpairing precompile."""
    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post=post,
    )


@pytest.mark.parametrize(
    "expected_output",
    [pytest.param(Spec.PAIRING_FALSE, id=pytest.HIDDEN_PARAM)],
)
@pytest.mark.parametrize(
    "input_data",
    [
        pytest.param(
            Spec.INF_G1
            + PointG2(
                (
                    0x092A62B029973FCD9EC18DB33EB4C7B6B649A2E6196561761789E39BC84F11AC,
                    0x0A59F2672462BE814A277F495D53244691C40DA85D39B210ED3E099B397A4CF9,
                ),
                (
                    0x2AD603022931E8C20C927FA114866CA26B305156336511A9224D6BD88E5BA7FB,
                    0x2B44DD02DF7F7A846F546C77F3330CC171ABEEA7747EC03607C4B754A0710142,
                ),
            )
            + PointG1(
                0x1F4B96B82BD3631447045F1BB66198FA6A904E48092750762EFD419FB5FF52B5,
                0x1FAC61C1A7265D0E1A6433E9767CB51C71E9AC5A119BE9894F509BF92B0FB1B4,
            )
            + PointG2(
                (
                    0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
                    0x1800DEEF121F1E76426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED,
                ),
                (
                    0x090689D0585FF075EC9E99AD690C3395BC4B313370B38EF355ACDADCD122975B,
                    0x12C85EA5DB8C6DEB4AAB71808DCB408FE3D1E7690C43D37B4CE6CC0166FA7DAA,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x0624D2C76767981FADC8F74F29C034F7AE0522585E1E0201308109C40D1D5420,
                0x251BA3C545339BBE22DA0FE90692A099384C435EC0902C99BE7E7A84D62BB49C,
            )
            + PointG2(
                (
                    0x0C0B524584214B17414A25236E4E2B6F4BF398EC62E9ABEB7EA1F158D89DF05B,
                    0x0E05F600BF1408AB25C0F3DBB98FF26C4D85A6CE6A63BEBC3B2E360DE77CF606,
                ),
                (
                    0x2488EB90497D64621124420825ABD353268FE00BD90726991D0CE623E59DA9C6,
                    0x2340B1FB006017382CB76606A873F48DE8F31434CC243C8F465CB908D8CC7346,
                ),
            )
            + PointG1(
                0x18CDE0D7BDE7E1DA88FB8192CE94BEA754F24A53F1F000F15B4C5C151C12DF4F,
                0x0066B16BF4229EDF5375B78A5C7469DDF68F7D5C7577642ED2C90D5D42C231ED,
            )
            + PointG2(
                (
                    0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
                    0x1800DEEF121F1E76426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED,
                ),
                (
                    0x090689D0585FF075EC9E99AD690C3395BC4B313370B38EF355ACDADCD122975B,
                    0x12C85EA5DB8C6DEB4AAB71808DCB408FE3D1E7690C43D37B4CE6CC0166FA7DAA,
                ),
            )
            + PointG1(
                0x2948734DB775BB41A29257214B19A6356E6640894C2A48F201ADDCE62DE7B41E,
                0x1BB87BDDBE46D75809751232405928C3314934082052131A64574FF5A59C7DB7,
            )
            + PointG2(
                (
                    0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
                    0x1800DEEF121F1E76426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED,
                ),
                (
                    0x090689D0585FF075EC9E99AD690C3395BC4B313370B38EF355ACDADCD122975B,
                    0x12C85EA5DB8C6DEB4AAB71808DCB408FE3D1E7690C43D37B4CE6CC0166FA7DAA,
                ),
            )
            + PointG1(
                0x09C91A687E6C44F2917682DC5D0A34BE7C77FFF361AA36610EFFAB6F6D2D87AC,
                0x13849277ED76B58020AB993F1847EBCC0F1BCF711FBA15F4A7A80AB72B4FE964,
            )
            + PointG2(
                (
                    0x2F0C63D0C53B3DFBCA27B6B43AE7FBF55A38D78A21470996485B03128ACCC208,
                    0x00556502356E37ED150DB2E36531B0F275FD6835C0FC1945922E270B48C48A86,
                ),
                (
                    0x02644C27B5DBD793592A70B735E22C798A5E309FA17A992A7DC2A050E01B298F,
                    0x194776B6A53439D7336F389D2A8F6651E40885F5CA2538B0DC9CB534FB23F7FA,
                ),
            )
            + PointG1(
                0x1E379E19DBFFBA1EDF0A04505F67229E707A4B82F19285D3C186964E83E15536,
                0x08EE58BAA16641B1513F007DA7D3CF58B503B80F73C7D8E792DB63DEF167E0D8,
            )
            + PointG2(
                (
                    0x2B1F95D6AA6FD6F5E6978D0135C206079770D5C3BA001967C5D94C5902F95FE9,
                    0x264AD64952CB1D30A7230BCA35B3907B2457ABDCD6052E14E2A132D768222225,
                ),
                (
                    0x14F79CE35164ACFDB802551E02A9AEBDB20BF4248C0CCF5C6CF5E57690877841,
                    0x0F8DFB99AAA272BBAA49012DA81DFAFA1A3C07EBA89355602143C58F63DF2939,
                ),
            )
            + PointG1(
                0x117A8203A67AB052AF18032434B61FE6B33E0A6AD5AB70D57AEF4444478B42BA,
                0x123A80E91F77C135F657E2DBF5AF0D07E9A4FB63585B88E5439DDAB7741C0961,
            )
            + PointG2(
                (
                    0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
                    0x1800DEEF121F1E76426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED,
                ),
                (
                    0x090689D0585FF075EC9E99AD690C3395BC4B313370B38EF355ACDADCD122975B,
                    0x12C85EA5DB8C6DEB4AAB71808DCB408FE3D1E7690C43D37B4CE6CC0166FA7DAA,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x104F6D8507D6A112E8FD516D70BFE3D2474539948276D36EEE987BE127A9E3AB,
                0x199EEF24146007E80386F391EDC886F5DDBA22B5CF131EFA3B6AE71A673FC88E,
            )
            + PointG2(
                (
                    0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
                    0x1800DEEF121F1E76426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED,
                ),
                (
                    0x090689D0585FF075EC9E99AD690C3395BC4B313370B38EF355ACDADCD122975B,
                    0x12C85EA5DB8C6DEB4AAB71808DCB408FE3D1E7690C43D37B4CE6CC0166FA7DAA,
                ),
            )
            + PointG1(
                0x2642F046AD222F094C9282816131317B8D52FC0FEE64F26898232432D34FDAE6,
                0x05A5F2A2E8F15BA27E90F54FAFF78391B307B402A0AE995D1C12F92C0B574593,
            )
            + PointG2(
                (
                    0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
                    0x1800DEEF121F1E76426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED,
                ),
                (
                    0x090689D0585FF075EC9E99AD690C3395BC4B313370B38EF355ACDADCD122975B,
                    0x12C85EA5DB8C6DEB4AAB71808DCB408FE3D1E7690C43D37B4CE6CC0166FA7DAA,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x142C9123C08A0D7F66D95F3AD637A06B95700BC525073B75610884EF45416E16,
                0x10104C796F40BFEEF3588E996C040D2A88C0B4B85AFD2578327B99413C6FE820,
            )
            + PointG2(
                (
                    0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
                    0x1800DEEF121F1E76426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED,
                ),
                (
                    0x275DC4A288D1AFB3CBB1AC09187524C7DB36395DF7BE3B99E673B13A075A65EC,
                    0x1D9BEFCD05A5323E6DA4D435F3B617CDB3AF83285C2DF711EF39C01571827F9D,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x1F0AB114F50077D71A195869DD8C07E2A031A55A8DAC07C522EE7AC74136C50C,
                0x229C9D498F5CA70A27612A244743773FE22668370A91410B645FE22F2E6EB78C,
            )
            + Spec.INF_G2
            + PointG1(
                0x284869D750E478E4B09637F7AE55BCCE23BD622F04E986E1CBA0F64B59B02320,
                0x0A88BC2898A2930AEE2B92055CA2F97360A79C598F5E8998FED7ADD43A692D10,
            )
            + PointG2(
                (
                    0x21F4F3DDD5250962BAAEFC6EF587F464C8FDAD1BB7812B292DCE48D5462039DF,
                    0x14044CA96015F3C6666F98D756FBF7BD0E12C3E884DB4100391DA8A47DEFF16E,
                ),
                (
                    0x00B30C250F71DB58EB20E14D67CD98EBB47790A7E7D45D30A90CE707175F295B,
                    0x1E45ECA08667A7CFE06158FAE4A38CAC01A37853E730EAA28B2F7167FD74C22D,
                ),
            ),
        ),
    ],
    ids=lambda _: "negative_",
)
def test_negative(
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
    "expected_output",
    [pytest.param(Spec.PAIRING_TRUE, id=pytest.HIDDEN_PARAM)],
)
@pytest.mark.parametrize(
    "input_data",
    [
        pytest.param(
            Spec.INF_G1
            + Spec.INF_G2
            + Spec.INF_G1
            + Spec.INF_G2
            + Spec.INF_G1
            + Spec.INF_G2,
        ),
        pytest.param(
            Spec.INF_G1
            + Spec.INF_G2
            + Spec.INF_G1
            + Spec.INF_G2
            + Spec.INF_G1
            + Spec.INF_G2
            + Spec.INF_G1
            + Spec.INF_G2
            + Spec.INF_G1
            + Spec.INF_G2
            + Spec.INF_G1
            + Spec.INF_G2,
        ),
        pytest.param(
            Spec.INF_G1
            + Spec.INF_G2
            + PointG1(
                0x103AA4B2AEFF1BC7AFC5CD39952C872C8F29D64188E8D18C1B65E526D6277A33,
                0x209854E0AC153A98EFF0FD08A0C73D46DBBE4209F8A6A4F2AAD914E40686F472,
            )
            + Spec.INF_G2
            + PointG1(0x1, 0x2)
            + Spec.INF_G2,
        ),
        pytest.param(
            Spec.INF_G1
            + PointG2(
                (
                    0x0EF4AAC9B7954D5FC6EAFAE7F4F4C2A732AB05B45F8D50D102CEE4973F36EB2C,
                    0x23DB7D30C99E0A2A7F3BB5CD1F04635AAEA58732B58887DF93D9239C28230D28,
                ),
                (
                    0x2BD99D31A5054F2556D226F2E5EF0E075423D8604178B2E2C08006311CAEE54F,
                    0x0F11AFB0C6073D12D21B13F4F78210E8CA9A66729206D3FCC2C1B04824C425F2,
                ),
            )
            + Spec.INF_G1
            + PointG2(
                (
                    0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
                    0x1800DEEF121F1E76426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED,
                ),
                (
                    0x090689D0585FF075EC9E99AD690C3395BC4B313370B38EF355ACDADCD122975B,
                    0x12C85EA5DB8C6DEB4AAB71808DCB408FE3D1E7690C43D37B4CE6CC0166FA7DAA,
                ),
            )
            + Spec.INF_G1
            + PointG2(
                (
                    0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
                    0x1800DEEF121F1E76426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED,
                ),
                (
                    0x090689D0585FF075EC9E99AD690C3395BC4B313370B38EF355ACDADCD122975B,
                    0x12C85EA5DB8C6DEB4AAB71808DCB408FE3D1E7690C43D37B4CE6CC0166FA7DAA,
                ),
            ),
        ),
        pytest.param(
            PointG1(0x1, 0x2)
            + Spec.INF_G2
            + PointG1(0x1, 0x2)
            + Spec.INF_G2
            + PointG1(0x1, 0x2)
            + Spec.INF_G2
            + PointG1(0x1, 0x2)
            + Spec.INF_G2,
        ),
        pytest.param(
            PointG1(0x1, 0x2)
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
                0x104316C97997C17267A1BB67365523B4388E1306D66EA6E4D8F4A4A4B65F5C7D,
                0x06E286B49C56F6293B2CEA30764F0D5EABE5817905468A41F09B77588F692E8B,
            )
            + PointG2(
                (
                    0x081070EFE3D4913DDE35BBA2513C426D065DEE815C478700CEF07180FB614618,
                    0x2432428B1490A4F25053D4C20C8723A73DE6F0681BD3A8FCA41008A6C3C28825,
                ),
                (
                    0x2D50F18403272E96C10135F96DB0F8D0AEC25033EBDFFB88D2E7956C9BB198EC,
                    0x072462211EBC0A2F042F993D5BD76CAF4ADB5E99610DCF7C1D992595E6976AA3,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x0084C3136563609CE6D7218719AF3024E2163EA8124130CFB61C2521379B0067,
                0x2E775227CCD46BB5BD8B9F9714ECAE9E037F8E91246B2A7E171337CF1332E341,
            )
            + PointG2(
                (
                    0x1FEE9EEA81AF0F92485CB60CEC6FDD90385B3F390C67D0885520BEA38A07BB08,
                    0x1242A8A318BA046CD7F4B87B4EDE31C0C19F823CE0AB3192F36ACC7683A91704,
                ),
                (
                    0x11D50FA9A8A15815BAF103030117065601AFF6B54F4242D2A5A14E3147E89E25,
                    0x133CA084BE363F41CB3886EED01FA8D896A609C22E099C4C9F5BB5A4363A57AD,
                ),
            )
            + PointG1(
                0x2F9B2CAF0345E3EC3ECCBC16AF5713BBF15EAF2A17CD9F7A02966BD5E7CCD6FE,
                0x185A77DFE45C4C1C9042C67FDB65D25BBD8B6F79DFDDE27458A35792653443F3,
            )
            + PointG2(
                (
                    0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
                    0x1800DEEF121F1E76426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED,
                ),
                (
                    0x090689D0585FF075EC9E99AD690C3395BC4B313370B38EF355ACDADCD122975B,
                    0x12C85EA5DB8C6DEB4AAB71808DCB408FE3D1E7690C43D37B4CE6CC0166FA7DAA,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x00898CC97B5A1F95221E7272C6EA8CEB56E702D678AC6C24275A4F6147D2B279,
                0x16F336255E3F8970FD79A12281E6A6BEE510E7D2CE5117214F4DD8C764E00EF3,
            )
            + PointG2(
                (
                    0x12580B380DDF94A3370E6842E68B260A12012AB02C883678ABF3F0F37606F55C,
                    0x268F02E60DFC36A40BB1FA3DBA22BBA44953358031876C21748D5D57DFB39EF4,
                ),
                (
                    0x07C890D2B747CB1E0456C9C1B30C03BADFFB8CDE540704104B016976D0A37447,
                    0x2A3E2918076D66622D7D6014299B77850A74B2691DDA1DADCD0232FBBFE2A9E0,
                ),
            )
            + PointG1(
                0x2781B3ACE921B11D98193720D1493609C4D47F607A2266D608185C6382B5D235,
                0x19797C215563C8B73CC7F0041D1F5FE1CE017B36AFBEFFE56683E3FFCCB9380B,
            )
            + PointG2(
                (
                    0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
                    0x1800DEEF121F1E76426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED,
                ),
                (
                    0x090689D0585FF075EC9E99AD690C3395BC4B313370B38EF355ACDADCD122975B,
                    0x12C85EA5DB8C6DEB4AAB71808DCB408FE3D1E7690C43D37B4CE6CC0166FA7DAA,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x06236320CF783A01E2B8BE7816A84671DE9E8BEBDA0E8F957809EE1253565BAE,
                0x0A4CE1AC405B9974E4EAF9342C2A43BD1FDC4EDC2BD18235249BF51EC4328744,
            )
            + Spec.INF_G2
            + PointG1(0x1, 0x2)
            + Spec.INF_G2
            + PointG1(0x1, 0x2)
            + Spec.INF_G2,
        ),
        pytest.param(
            PointG1(
                0x082A5B0EB620C491DC7CFBF269EA3E9DB35FDAF6C7C4BAA25A829127A56F63C4,
                0x1C49E6C57C3C0DDCA035138E5AADB79AC638F67A918E6A4377200EBFA80ED188,
            )
            + PointG2(
                (
                    0x0BF4734681E3030E126C2A595DE85F80B46BD327BAE8A860A3ED5F5BE7318037,
                    0x116C5E07DE19E858EB720604F6E2935BF0F5E40D9194CFBA05BFEA0AB69F1D82,
                ),
                (
                    0x263EE7293C68743B04034A5B63E1D2B65261F7C6758D8084A50419CC65D02AD2,
                    0x14189E61084D61CF2AD9B6140B951CA35AE18A008CB3C1C4904E59F462E66B04,
                ),
            )
            + PointG1(
                0x28EC2C3D544A901AD85AF62E1EC02AAC643E707A3A45983EF168877B6901A19D,
                0x108E7A47061FD472BD715C35B71B842FC1914A8972E472A2A4FAA4880E0D2787,
            )
            + PointG2(
                (
                    0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
                    0x1800DEEF121F1E76426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED,
                ),
                (
                    0x090689D0585FF075EC9E99AD690C3395BC4B313370B38EF355ACDADCD122975B,
                    0x12C85EA5DB8C6DEB4AAB71808DCB408FE3D1E7690C43D37B4CE6CC0166FA7DAA,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x09148BA3625B1D4862ECFED71970E395D22BC4DAFAA4A662546E4FB39141D8BA,
                0x0A8F563782B2B31347C9E7CED5A21D959A38F4AE4BBC7CD37B1180A0D491CAD6,
            )
            + PointG2(
                (
                    0x17F32B902D2096A48B25F94AD6C692A99C68E937A4BAE3C820F25093CF2786AB,
                    0x155C57D2B7F4AEFC0E1A44A78C7D59D2CAC917546717C665DC001FA43CF57753,
                ),
                (
                    0x17B81FE685DD2E24A14899EF74821D1D147B88FE0C63D0921EB45C191146E7E4,
                    0x1C9AE775EBA85EA225258C9BAFDF5CBAD6106CD79194F4B0F8E7814068370DAF,
                ),
            )
            + PointG1(
                0x302AC8191CD6D55B858891D05B919AD95F5E2F16B78C5B0AD2ECC72C3FE23842,
                0x1A924FA7E779AD503830C25838C2489D9BBC21FD519CEB3F4A10F4DC3E3B72BE,
            )
            + PointG2(
                (
                    0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
                    0x1800DEEF121F1E76426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED,
                ),
                (
                    0x090689D0585FF075EC9E99AD690C3395BC4B313370B38EF355ACDADCD122975B,
                    0x12C85EA5DB8C6DEB4AAB71808DCB408FE3D1E7690C43D37B4CE6CC0166FA7DAA,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x0EE7F0252E8210EAA3EE452C8731AD6864D8506BA61836F48C99A16A03D59B0D,
                0x2BA1DDC868F452EF0CFDCAC410E9D38D726557B05EDC84F8D4F62203ACC1F9F0,
            )
            + PointG2(
                (
                    0x29AA08ECADE2C1D537C14BAF6CF62758C02E6F3C4EEB0B621AD3AB941B1559DE,
                    0x11EAC12AAF058F799EE8146F36A0BBBF8E67A0AA0F9E2C192BAFD05FF8DA45D3,
                ),
                (
                    0x03B7BD661BECFA6FF5092B36F1768C815434F3B7F4254FB4B8ABF68E36086CD3,
                    0x196CAA297895D4A1D58A5FE388416FBAC2A74FB9BEB835DBBBAA8F6B63BF9CAB,
                ),
            )
            + PointG1(
                0x29A00816ED140FC36E515F43FB054C891B4B07F013C9E6D5C3F284C8528C71AE,
                0x2F060699E8F54B1028B78E5F016D8142563947ADCAC5A5857137B6958DDC995E,
            )
            + PointG2(
                (
                    0x141DD828AF529924148912360FD71EF6A365A707173AA2C06C8290D54FAE458E,
                    0x1CF61D5E9CECED0C662C6E2DF96D63ADC7D84E182FA0F62E08B9AFDD5C90545E,
                ),
                (
                    0x01F3E8049B7934995DEE28FAA0E401289B92CCD1A2F408C85383F5312F528C9E,
                    0x2C6AAA06B56E9D6C98A701B4A9CF2F8CFDDBFA93D7104D5EAFBAD9A84B5174E5,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x0F740D88DE760DF099674C96DD2D476B42673D0F2972E6D5D1F9DBA95A29D26A,
                0x04A44D72C2A82088DA663FF162FE2D3DDD4A139E1EF6C0BBB1124D8DE75F7C68,
            )
            + PointG2(
                (
                    0x196346D9774F017C351DBBDD99960E834B188B3347B92FAC7F83CC6453617FE1,
                    0x1E3BA24A0848096A0D6484133AF97B7487CA9A4309CB5574D8BB96CFD7F22678,
                ),
                (
                    0x235603772D0E9CF9503D05742962B07CD0AF71A7C7B757960CED6FCFA74D3DED,
                    0x1CEED193F30FBBE5E9A9438E82BAC927A0977B49F6E476AEE20923E1A230F2C4,
                ),
            )
            + PointG1(
                0x201AF9371C7CEA66800F961D6A7219DA9C27FBE61B5DF43FCCB275D8C034BF8E,
                0x1F0E7C5A1143B0F8E850D9516EA2C836B0331521829DC2B71DBF775078C770F4,
            )
            + PointG2(
                (
                    0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
                    0x1800DEEF121F1E76426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED,
                ),
                (
                    0x090689D0585FF075EC9E99AD690C3395BC4B313370B38EF355ACDADCD122975B,
                    0x12C85EA5DB8C6DEB4AAB71808DCB408FE3D1E7690C43D37B4CE6CC0166FA7DAA,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x107B8A2CB6318AABD95763C0CAFC3B24D8A9ACDF8DD967176F05C400951B3E06,
                0x13A1C9847BF87C8CC79EF1120ED6E3E98412F0DD4E9C8C8C421057A2353279E6,
            )
            + PointG2(
                (
                    0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
                    0x1800DEEF121F1E76426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED,
                ),
                (
                    0x090689D0585FF075EC9E99AD690C3395BC4B313370B38EF355ACDADCD122975B,
                    0x12C85EA5DB8C6DEB4AAB71808DCB408FE3D1E7690C43D37B4CE6CC0166FA7DAA,
                ),
            )
            + PointG1(
                0x2FB5B7E464A0A76D9ACA8698E73802782DA01FCE50384F459BE1427855C0EB50,
                0x2E6C7AF07418CD0203FAD6A1ABDE95E745C41A78C6AD1AE7B1B2ADA2E643FD37,
            )
            + PointG2(
                (
                    0x260E01B251F6F1C7E7FF4E580791DEE8EA51D87A358E038B4EFE30FAC09383C1,
                    0x0118C4D5B837BCC2BC89B5B398B5974E9F5944073B32078B7E231FEC938883B0,
                ),
                (
                    0x04FC6369F7110FE3D25156C1BB9A72859CF2A04641F99BA4EE413C80DA6A5FE4,
                    0x22FEBDA3C0C0632A56475B4214E5615E11E6DD3F96E6CEA2854A87D4DACC5E55,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x1147057B17237DF94A3186435ACF66924E1D382B8C935FDD493CEB38C38DEF73,
                0x03CD046286139915160357CE5B29B9EA28BFB781B71734455D20EF1A64BE76CA,
            )
            + PointG2(
                (
                    0x0DAA7CC4983CF74C94607519DF747F61E317307C449BAFB6923F6D6A65299A7E,
                    0x1D48DB8F275830859FD61370ADDBC5D5EF3F0CE7491D16918E065F7E3727439D,
                ),
                (
                    0x1CA8AC2F4A0F540E5505EDBE1D15D13899A2A0DFCCB012D068134AC66EDEC625,
                    0x2162C315417D1D12C9D7028C5619015391003A9006D4D8979784C7AF2C4537A3,
                ),
            )
            + PointG1(
                0x0D221A19CA86DAFA8CB804DAFF78FD3D1BED30AA32E7D4029B1AA69AFDA2D750,
                0x018628C766A98DE1D0CCA887A6D90303E68A7729490F25F937B76B57624BA0BE,
            )
            + PointG2(
                (
                    0x14550CCF7139312DA6FA9EB1259C6365B0BD688A27473CCB42BC5CD6F14C8ABD,
                    0x165F8721EE9F614382C8C7EDB103C941D3A55C1849C9787F34317777D5D9365B,
                ),
                (
                    0x0D19DA7439EDB573A1B3E357FAADE63D5D68B6031771FD911459B7AB0BDA9D3F,
                    0x25A50A44D10C99C5F107E3B3874F717873CB2D4674699A468204DF27C0C50A9A,
                ),
            )
            + PointG1(
                0x0D7136C59B907615E1B45CF730FBFD6CF38B7E126E85E52BE804620A23ACE4FB,
                0x03E80C29D24ED5CC407329AE093BB1BE00F9E3C9332F532BC3658937110D7607,
            )
            + PointG2(
                (
                    0x2129813BD7247065AC58EAC42C81E874044E199F48C12AA749A9FE6BB6E4BDDC,
                    0x1B72B9AB4579283E62445555D5B2921424213D09A776152361C46988B82BE8A7,
                ),
                (
                    0x111BC8198F932E379B8F9825F01AF0F5E5CACBF8BFE274BF674F6EAA6E338E04,
                    0x259F58D438FD6391E158C991E155966218E6A432703A84068A32543965749857,
                ),
            )
            + PointG1(
                0x1BA47A91D487CCE77AA78390A295DF54D9351637D67810C400415FB374278E3F,
                0x24318BBC05A4E4D779B9498075841C360C6973C1C51DEA254281829BBC9AEF33,
            )
            + PointG2(
                (
                    0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
                    0x1800DEEF121F1E76426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED,
                ),
                (
                    0x090689D0585FF075EC9E99AD690C3395BC4B313370B38EF355ACDADCD122975B,
                    0x12C85EA5DB8C6DEB4AAB71808DCB408FE3D1E7690C43D37B4CE6CC0166FA7DAA,
                ),
            )
            + PointG1(
                0x1E219772C16EEE72450BBF43E9CADAE7BF6B2E6AE6637CFEB1D1E8965287ACFB,
                0x0347E7BF4245DEBD3D00B6F51D2D50FD718E6769352F4FE1DB0EFE492FED2FC3,
            )
            + PointG2(
                (
                    0x24FDCC7D4ED0953E3DAD500C7EF9836FC61DED44BA454EC76F0A6D0687F4C1B4,
                    0x282B18F7E59C1DB4852E622919B2CE9AA5980CA883EAC312049C19A3DEB79F6D,
                ),
                (
                    0x0C9D6CE303B7811DD7EA506C8FA124837405BD209B8731BDA79A66EB7206277B,
                    0x1AC5DAC62D2332FAA8069FACA3B0D27FCDF95D8C8BAFC9074EE72B5C1F33AA70,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x117196C7EA11E6362BCA58533A55DE3DEADC441B18B0A7CA68557F374DFED6A6,
                0x29B1B63F1D649480AA9655406C454B55CBBF8D29F3AEDC30DE3B0745BED3BE52,
            )
            + PointG2(
                (
                    0x226AD93C0A164E73D8D9161F9D0206AB232FA5A08CB349F7DF3633096CD04E92,
                    0x0DE4A56223EE43AA3C4A18BF4C84BE1879DD9182FD4A03318A4BEBD642627D1E,
                ),
                (
                    0x142A0ED74BA11936E27101A43DB8E16F6A603953C3EA4B14EAEBBE117970268A,
                    0x2ABCED69FFBCE2E34440530111050A4D72282DD5F4FAA7703D5762D043271756,
                ),
            )
            + PointG1(
                0x19EEDB06C5D1F53510F7F7464B39730659ECCF0E9DFEEC2CC131FD0D27C4F8E3,
                0x043AAEA131D0E69B79A816B675AC0DD21B4796046C149CA16DF5884D615025C5,
            )
            + PointG2(
                (
                    0x238F967690E26443E6F5207B5C2AF7FEDB837D534282C7DB1CA926A9BC06A739,
                    0x0EC4C043A606711A021205EF7D97785D9AE246BA06B2912E24FF9E669FB700B4,
                ),
                (
                    0x2714A2E42C4BD73A79CD7B2243D1B784CADB22A58E6360BE1AF873424EFD420C,
                    0x12F54BDCF07FF30854629A0531065973197E685193051F2FA11A7761B0CC39F6,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x13B076F9E2DDF66BD1E9EC7509945EC37289D9AD65F210ED35E78BA2B02E7E3D,
                0x2C6D9689097E79C4227B7B8519E4850BE2D795F9496A70AE8607A3172208371A,
            )
            + PointG2(
                (
                    0x0774089B1BE2375B269AC0CD913803AF1E8E967C7A12DED9E38BBFE816CB6B2B,
                    0x25E481BF589A76E531E3CBAEE9B47A07FB832B052A71029665A5CA89F1EB6D6B,
                ),
                (
                    0x0F10223646F0D0F8F79189C456F40295FA02708A2629B8A88D7AE36CAAB47055,
                    0x2B4BF562F83ED28EDF524EDC1646B4C4CD538BEC5D544D8071F0C73406339B2E,
                ),
            )
            + PointG1(
                0x2043A8194E50B9FF3B93D13873035FEE0CCC3B4A0FDA33D34AC7A4771C9B884D,
                0x291B24054553ECAB7EB9A6807281A895BDCF29E95D8D3A2552749B7FC0932637,
            )
            + PointG2(
                (
                    0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
                    0x1800DEEF121F1E76426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED,
                ),
                (
                    0x090689D0585FF075EC9E99AD690C3395BC4B313370B38EF355ACDADCD122975B,
                    0x12C85EA5DB8C6DEB4AAB71808DCB408FE3D1E7690C43D37B4CE6CC0166FA7DAA,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x15D6EAAA18C5737E7BD229C2900F8DEDDF6DA9C0E20E7E905E7B7491D041EABA,
                0x2AB7D1B2A259B85054253DA8947C2FD38B04A4EDE3BFA6E258E22F668DCB5A63,
            )
            + PointG2(
                (
                    0x092A62B029973FCD9EC18DB33EB4C7B6B649A2E6196561761789E39BC84F11AC,
                    0x0A59F2672462BE814A277F495D53244691C40DA85D39B210ED3E099B397A4CF9,
                ),
                (
                    0x2AD603022931E8C20C927FA114866CA26B305156336511A9224D6BD88E5BA7FB,
                    0x2B44DD02DF7F7A846F546C77F3330CC171ABEEA7747EC03607C4B754A0710142,
                ),
            )
            + PointG1(
                0x1F4B96B82BD3631447045F1BB66198FA6A904E48092750762EFD419FB5FF52B5,
                0x1FAC61C1A7265D0E1A6433E9767CB51C71E9AC5A119BE9894F509BF92B0FB1B4,
            )
            + PointG2(
                (
                    0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
                    0x1800DEEF121F1E76426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED,
                ),
                (
                    0x090689D0585FF075EC9E99AD690C3395BC4B313370B38EF355ACDADCD122975B,
                    0x12C85EA5DB8C6DEB4AAB71808DCB408FE3D1E7690C43D37B4CE6CC0166FA7DAA,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x16F5D1473D8A9012DF4EFC624AE3B5FC3B1C1742BB73B9B62AA50C0DEC9848AD,
                0x1B2381A593F0A661DB10B659329907FB62B4F5FD196092EF235F0775463B11F3,
            )
            + PointG2(
                (
                    0x054F9C54B1560A307E173C70FCE534A2E4C7B248EC342F968A9DB905FB31BA36,
                    0x2513859B9C3A196E357D5D4F34E17F5CB2D78F4160103ECAE86CB57A3E48EF77,
                ),
                (
                    0x15E96B3AD7BFBCCC491029F30BE0CED0654C6C2600B49BFAFC70AF802B305A09,
                    0x154BB828C71576E1809723E3BBB5D459ECE5BDCCB9BCDFF733761FE908E1E1D5,
                ),
            )
            + PointG1(
                0x2F91CEC7B5D03D4C5930875239F825C55849B352FA27B4E20581FC4A68950C75,
                0x2EE478820A0DC3F22866E7C5111D6FD1F057C18B7C9C1568173916CE67555C47,
            )
            + PointG2(
                (
                    0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
                    0x1800DEEF121F1E76426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED,
                ),
                (
                    0x090689D0585FF075EC9E99AD690C3395BC4B313370B38EF355ACDADCD122975B,
                    0x12C85EA5DB8C6DEB4AAB71808DCB408FE3D1E7690C43D37B4CE6CC0166FA7DAA,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x18DD52DAAA11FF5DBB97C8776924D95B1BB86BF16481BA52519674873E0279EA,
                0x0B32F4758CC18142794358E62B9C29951D3CB7E705D97E4CEFD8422FA340ED58,
            )
            + PointG2(
                (
                    0x04CBAC0707B92F59B87024017AAE6941A3D8F42C6B93C619FA85CD54A3F05963,
                    0x25EF128BD051C44F95F7AA6122A390666691C2EC8A328F5302605F0AAAE670DB,
                ),
                (
                    0x14A3194DB0C978125B0212D2DBCF3639650E40F8ACAEFF5A5C20BA700DE3966F,
                    0x004D3F0A629EB1456685DB5A1B94D4B2F8DC0A9CDC5D29CCCC5B596D88BA29FE,
                ),
            )
            + PointG1(
                0x0BCF53D38A1B0732FD90B73149559E0EE767F525875EBDB26F7F123136282AFA,
                0x28E440620EA4064D1F0190C75E2A36003F18643507A927926130EB54ECC1004D,
            )
            + PointG2(
                (
                    0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
                    0x1800DEEF121F1E76426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED,
                ),
                (
                    0x090689D0585FF075EC9E99AD690C3395BC4B313370B38EF355ACDADCD122975B,
                    0x12C85EA5DB8C6DEB4AAB71808DCB408FE3D1E7690C43D37B4CE6CC0166FA7DAA,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x1B6E4577CC71DF5E856ED88D2D14A464343F140B07693E3B08308570B28FD55B,
                0x24198AA6EE0F5BFEC020AD2FF15729434439E4AF7554FA0F7395EE20CB926346,
            )
            + PointG2(
                (
                    0x246B8E8C771C3DB7226A8066537632923D7D5A542F8E0D600E7F0195240F1EC5,
                    0x13CBE706F9BA436DD4A781FAB85FA2E9D82854446CF91182DCFA66EB68C4B7E7,
                ),
                (
                    0x2533A60B837F9CF4838C4C38F4F9C8988FEE10C9895753E7925A86330E925DB7,
                    0x02F47F10F7DA957CFCC613361AB6AAEB67F14D22C06EEC14E47E36988C4EE067,
                ),
            )
            + PointG1(
                0x05A596BD22BBB13DC898ACFDD420C88893DD09F7FD4875E8B3FB65B54AD9643F,
                0x2847AB3C7D853E89CFDF520DE28E1092C1955B7E17D9CBA5808F047A3D6898FD,
            )
            + PointG2(
                (
                    0x2F64F057DEDA8BBB646D5B9864D9789A696ABF2A42218F7AF28BAAE517F5E457,
                    0x23BD3952D332068086B2079260B285896CB84C73ECE3647094FAC90D8B1374C2,
                ),
                (
                    0x1EEBB3F8EA3C3D9147FA09E4506BCFF1C222A02EA8B4904FC6DF3BCA1CC0505E,
                    0x133D9A4794EB099E9BDF82A6FECDB2E2E29B0867BF0FE557475DC758D796714E,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x1EE2AF29808BC7BAAD8EB3E87BF55588EF59763AE59585453AA57222A6040914,
                0x1756D11B0679F2E3C44A95592D270F55F76670C2D248FE2C0B391A11AA90D0EC,
            )
            + PointG2(
                (
                    0x0EA16E33157B6D0F197ED197CE3AD5B93AC91458632464DD5E4AA23EC628E6CB,
                    0x03C160EB0D2AB47566D495F1A53B7B1CDB659CB64E26C848C74267BC74FFEEC8,
                ),
                (
                    0x1D5EE181514337F685E60BA02DACCDED24EA3122FB04D9DA37790F3DCE545878,
                    0x03087C55D223005FF8AD78F6F417B19CAFF564E8B8CB820D0EADB6BEC43F0CF9,
                ),
            )
            + PointG1(
                0x02B88F6E24920BD60DBBF082DF1CD200ABF141B6C01E7FCB262525364C14C205,
                0x02958D26F4E6AD2D9B1DB8A6B23E7FA5DC4D0E4C6673B0F840C000EEAC001988,
            )
            + PointG2(
                (
                    0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
                    0x1800DEEF121F1E76426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED,
                ),
                (
                    0x090689D0585FF075EC9E99AD690C3395BC4B313370B38EF355ACDADCD122975B,
                    0x12C85EA5DB8C6DEB4AAB71808DCB408FE3D1E7690C43D37B4CE6CC0166FA7DAA,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x1F357DB2CD961C374F81A4AE374F5306787361C3AEA270815962003C0915B5D2,
                0x044C12E4C6321F0A73B09480C1D7A84CE30EE9219B3B649FF36EC7553150428F,
            )
            + PointG2(
                (
                    0x1B789C458E1E033DB933F65230C01F173DC581494D23407494818CBC70C5E4EB,
                    0x05685001B0F48E5191BC50797F1330BEB69D7DABE58B9B7D0C9C86C61C8D2A33,
                ),
                (
                    0x01C8DC500074BC4207038E94F028D954405D8B6FF8B3F1B52A7CE67C97382C0B,
                    0x0A9C7D7844CA3F0A571B04211C021DC96A29628119B067364A06FEA760698A06,
                ),
            )
            + PointG1(
                0x0452283EEFD9B336E591F37119AA473F03932C9C6D7CB0256C93E2BB7EBC2140,
                0x24A87B7AFBB4143434A5AECBEC2C38E02C7E01E8B056B812C80DEAB761BD9429,
            )
            + PointG2(
                (
                    0x06B4A2CADF0C0D14E9015F1DD1833E1A71BDECFCC8D400F0C96C309DD8F3F30E,
                    0x243FDDB630078AF3593C50273C6FBC2C33F2FC6E208AD1E6DD537079F569CD5F,
                ),
                (
                    0x25E6C61EB8D52BFE15205FB66A6E90DA703A7CB8B441023F90AE987E35C72F80,
                    0x0E8E708E896B7BA90163F4DD87BB6660359CA5558473831DEA4AAC4D222FE443,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x21B1479BE2A88D421D6AA893A59FE4966322436BCD047E610F90929A5823188A,
                0x2FEB0BAED066808BE65012E37E364243877A4D47B75CD9FFE4A5DF3011A68F90,
            )
            + PointG2(
                (
                    0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
                    0x1800DEEF121F1E76426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED,
                ),
                (
                    0x090689D0585FF075EC9E99AD690C3395BC4B313370B38EF355ACDADCD122975B,
                    0x12C85EA5DB8C6DEB4AAB71808DCB408FE3D1E7690C43D37B4CE6CC0166FA7DAA,
                ),
            )
            + PointG1(
                0x1AA2BA0E64E80047D931DF5931420DE2D4DC0B7B6FC83121A9F155DDF9D65775,
                0x20108E265338E3F2BDCC276BF69D955D60C73419D7BA24C25A40E9EFD4CB24B8,
            )
            + PointG2(
                (
                    0x0DBBD035AB913DC40917C815E66941EEF6529D94ECBAAEE8F77EFE9AAC45AAB2,
                    0x2FF4691BD3AA5F5BBB6067C1A4392DC87BB7A9997F7A660DD960DF462203C18F,
                ),
                (
                    0x2D4E9EE9F56967D24826884A2473B374D24B5AFEF1CB8D11555A2A62249B44A9,
                    0x07A93F02C17DA88BBEF2E8B41A34EE1137AA7EDB0459E06BE0BD88EF68A876B0,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x2371E7D92E9FC444D0E11526F0752B520318C80BE68BF0131704B36B7976572E,
                0x2DCA8F05ED5D58E0F2E13C49AE40480C0F99DFCD9268521EEA6C81C6387B66C4,
            )
            + PointG2(
                (
                    0x051A93D697DB02AFD3DCF8414ECB906A114A2BFDB6B06C95D41798D1801B3CBD,
                    0x2E275FEF7A0BDB0A2AEA77D8EC5817E66E199B3D55BC0FA308DCDDA74E85060B,
                ),
                (
                    0x1C7E33C2A72D6E12A31EABABAD3DBC388525135628102BB64742D9E325F43410,
                    0x115DC41FA10B2DBF99036F252AD6F00E8876B22F02CB4738DC4413B22EA9B2DF,
                ),
            )
            + PointG1(
                0x09A760EA8F9BD87DC258A949395A03F7D2500C6E72C61F570986328A096B610A,
                0x148027063C072345298117EB2CB980AD79601DB31CC69BBA6BCBE4937ADA6720,
            )
            + PointG2(
                (
                    0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,
                    0x1800DEEF121F1E76426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED,
                ),
                (
                    0x090689D0585FF075EC9E99AD690C3395BC4B313370B38EF355ACDADCD122975B,
                    0x12C85EA5DB8C6DEB4AAB71808DCB408FE3D1E7690C43D37B4CE6CC0166FA7DAA,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x23E6648726D779A5E9943A9CB2C3D89CC966F0CA965BBE7BBDC1BD93DF642930,
                0x2A1E299A0D2C7FB74AF9E086C19B07B357C55E76D2C65FBA3B122C8158EE2B76,
            )
            + PointG2(
                (
                    0x071A0694C6A785AE2FF2553F4C06E2D24D031B86A4023A0D41A095B9D35EC8D3,
                    0x0C1AB42B9A9D852E0901C708A5A0DFA9920E0BA08828620A5EBBDF1FFB8F9D85,
                ),
                (
                    0x1741332DCD8798B695EDF6BE41E0E58803AB926516D0D600514C4572575B2924,
                    0x1A64993DDD9BE2BAB46A7190024DE9E051862F46AC3130DB54EDE8C322E604A2,
                ),
            )
            + PointG1(
                0x2E198A9651F4D48DC87F0EBC9FBA1061D49962668790EDC37948681DA728A79F,
                0x1649DC12A9101AD7E6C1631C1290BEC29720BF5617EE6B5AFA720733748BC3FE,
            )
            + PointG2(
                (
                    0x2AE647DA926E44CC8E5476A15FFC62F11EAFC89CB7D1D9EA1107403E1773C49A,
                    0x2408EAAABD36AA0A8DC6DB3FB091F3C8B4DF202714F74AE8D8CCA11A216A3017,
                ),
                (
                    0x25EF6BF83C607781E9C1696E31CB5BAA60B9E2DEB0856479B342737592C09612,
                    0x11D363F2F2FC286D903A1E94C6673714464530BDB734DED5608B4654466D3F35,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x24AB69F46F3E3333027D67D51AF71571141BD5652B9829157A3C5D1268461984,
                0x0F0E1495665BCCF97D627B714E8A49E9C77C21E8D5B383AD7DDE7E50040D0F62,
            )
            + PointG2(
                (
                    0x2CAB595B9D579F8B82E433249B83AE1D7B62D7073A4F67CB3AEB9B316988907F,
                    0x1326D1905FFDE0C77E8EBD98257AA239B05AE76C8EC7723EC19BBC8282B0DEBE,
                ),
                (
                    0x130502106676B537E01CC356765E91C005D6C4BD1A75F5F6D41D2556C73E56AC,
                    0x2DC4CB08068B4AA5F14B7F1096AB35D5C13D78319EC7E66E9F67A1FF20CBBF03,
                ),
            )
            + PointG1(
                0x1459F4140B271CBC8746DE9DFCB477D5B72D50EF95BEC5FEF4A68DD69DDFDB2E,
                0x2C589584551D16A9723B5D356D1EE2066D10381555CDC739E39EFCA2612FC544,
            )
            + PointG2(
                (
                    0x229AB0ABDB0A7D1A5F0D93FB36CE41E12A31BA52FD9E3C27BEBCE524AB6C4E9B,
                    0x00F8756832B244377D06E2D00EEB95EC8096DCFD81F4E4931B50FEA23C04A2FE,
                ),
                (
                    0x29605352CE973EC48D1AB2C8355643C999B70FF771946078B519C556058C3D56,
                    0x059A65AE6E0189D4E04A966140AA40F781A1345824A90A91BB035E12AD29AF1D,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x24AB69F46F3E3333027D67D51AF71571141BD5652B9829157A3C5D1268461984,
                0x0F0E1495665BCCF97D627B714E8A49E9C77C21E8D5B383AD7DDE7E50040D0F62,
            )
            + PointG2(
                (
                    0x2CAB595B9D579F8B82E433249B83AE1D7B62D7073A4F67CB3AEB9B316988907F,
                    0x1326D1905FFDE0C77E8EBD98257AA239B05AE76C8EC7723EC19BBC8282B0DEBE,
                ),
                (
                    0x130502106676B537E01CC356765E91C005D6C4BD1A75F5F6D41D2556C73E56AC,
                    0x2DC4CB08068B4AA5F14B7F1096AB35D5C13D78319EC7E66E9F67A1FF20CBBF03,
                ),
            )
            + PointG1(
                0x1459F4140B271CBC8746DE9DFCB477D5B72D50EF95BEC5FEF4A68DD69DDFDB2E,
                0x2C589584551D16A9723B5D356D1EE2066D10381555CDC739E39EFCA2612FC544,
            )
            + PointG2(
                (
                    0x229AB0ABDB0A7D1A5F0D93FB36CE41E12A31BA52FD9E3C27BEBCE524AB6C4E9B,
                    0x00F8756832B244377D06E2D00EEB95EC8096DCFD81F4E4931B50FEA23C04A2FE,
                ),
                (
                    0x29605352CE973EC48D1AB2C8355643C999B70FF771946078B519C556058C3D56,
                    0x059A65AE6E0189D4E04A966140AA40F781A1345824A90A91BB035E12AD29AF1D,
                ),
            )
            + PointG1(
                0x1459F4140B271CBC8746DE9DFCB477D5B72D50EF95BEC5FEF4A68DD69DDFDB2E,
                0x2C589584551D16A9723B5D356D1EE2066D10381555CDC739E39EFCA2612FC544,
            )
            + PointG2(
                (
                    0x229AB0ABDB0A7D1A5F0D93FB36CE41E12A31BA52FD9E3C27BEBCE524AB6C4E9B,
                    0x00F8756832B244377D06E2D00EEB95EC8096DCFD81F4E4931B50FEA23C04A2FE,
                ),
                (
                    0x29605352CE973EC48D1AB2C8355643C999B70FF771946078B519C556058C3D56,
                    0x059A65AE6E0189D4E04A966140AA40F781A1345824A90A91BB035E12AD29AF1D,
                ),
            )
            + PointG1(
                0x24AB69F46F3E3333027D67D51AF71571141BD5652B9829157A3C5D1268461984,
                0x0F0E1495665BCCF97D627B714E8A49E9C77C21E8D5B383AD7DDE7E50040D0F62,
            )
            + PointG2(
                (
                    0x2CAB595B9D579F8B82E433249B83AE1D7B62D7073A4F67CB3AEB9B316988907F,
                    0x1326D1905FFDE0C77E8EBD98257AA239B05AE76C8EC7723EC19BBC8282B0DEBE,
                ),
                (
                    0x130502106676B537E01CC356765E91C005D6C4BD1A75F5F6D41D2556C73E56AC,
                    0x2DC4CB08068B4AA5F14B7F1096AB35D5C13D78319EC7E66E9F67A1FF20CBBF03,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x2B5154892605B4B57C6F309A1F39D91A89D985264F9DC47342470B5605532939,
                0x153954F4AC012E3D5860731081C59B0B5D9DF76EEECA47C1EDE99D0A73A8D135,
            )
            + PointG2(
                (
                    0x1B7962C4F91943B75BFA71D26698F33807C0A82C4AFF43116E6B0E97E087D64E,
                    0x0337B7F3F182A6241093041180E874062C10467E0147E1ABD93857DDA7E6AA34,
                ),
                (
                    0x153CAC48663D8DE0C9F23D1A2CECF0BD14F6D7CF877EF833751F8A524D0F4C1C,
                    0x1FF902721CD414E4C564C569143A0356D3B6CB7B1970067365C0A0F8ECB4976B,
                ),
            )
            + PointG1(
                0x0DA26CA39BACCC3B276B50CBD06DB50B1C544055C0C636256FA35AFDAFEE49BF,
                0x2238E1B69BC5E674C9351B702C26021F8EB254E0F890595F5F22CA04B2057480,
            )
            + PointG2(
                (
                    0x03D0A15AC5814B86F5463C48D5F7D398DA010569D67F979B2AF9381802B485FD,
                    0x2D3DE1B5338AC2222D3D1BFCA2E20F7C1A280780BA9ABD54B46D42380FDA599C,
                ),
                (
                    0x243C33DBB5C54E9566FDDA8567E059B596FBA1E9AFEF57DEB1703F27CD93CE74,
                    0x19779141BB51EAA0EA4F1FD39EFC61AEE4E6B40316248277599C599EC30C8DD4,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x2CC6C9ACABC199E21BE075D6D7885ACFA1F38FEC18999D78105C87E55A5D8EB7,
                0x238E3F5EDEA71116B4905645DF360589EED6E69FF4145A28C6AE29599CCB590E,
            )
            + PointG2(
                (
                    0x0E8248A6CCD8770C3CDBBD6D7F247C76F189978508B6F3514877833B00A7C593,
                    0x261D44028C3119AD2707A456739918AD10B51E7257B539A34E7F479F2E76707A,
                ),
                (
                    0x2B359C070959C19EB7BB2BF1DBBB2CC060558F6DD682965535CBA0F2392D13B8,
                    0x18A023E2B4D60C38C7C0AB6AF9FF0887DD192AC88B5070851F4D0E7495A1144D,
                ),
            )
            + PointG1(
                0x0ED1531303F89B56EBE6E9A39E7B7C4B5F2385D774AB00AB0B3C32C9B110552A,
                0x0794C8D242F2AA6F638A597E53D8F236C780FCAC4A7E2CABCB688896A84046C7,
            )
            + PointG2(
                (
                    0x13532C71AEAC024EEA1BBCCB01B45CEB4AD91E106200B7E25B0E30BC588D7835,
                    0x20692D41373A18914E163949FA765D49DBAA5999B1D606300A469555DA182B59,
                ),
                (
                    0x1FE664FC1DC73F67D3261D81477FD5B43E9B7D9A376A09E4A2B82F935CE0EF73,
                    0x0ABD60B3B4CA1E15EAE3DD484E5E22F0F8F50DFBC756B40CB2406E6A1D86C07C,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x2E565CD418929C3795ADF3EA378F2616AF24A1D7A93962C5BE375E7FBDFE3D73,
                0x1197465669E70FD0793C00FB922D25DD53C8C35D4D686985E4E04741569497D1,
            )
            + Spec.INF_G2
            + PointG1(
                0x03A781E0964591A816D07C8D6AA23D23B2AD50AE3ACC529F877ABF4D13E3F35E,
                0x0FC25D443BA88FF661C914498D09F6C47BD3DB7F8768C13AC2602E02250C34D1,
            )
            + Spec.INF_G2,
        ),
        pytest.param(
            PointG1(
                0x2E5E8D67B60E1D06ACD7A490F8394BE4AAB0ECA89EAC6738FFF6664263500F2B,
                0x23A1B85312F58351B078BFABD3AB8517E383900CC23A4D9A8FDB0A5AE691BD00,
            )
            + PointG2(
                (
                    0x23751D707CD5ABABE78100ADE4BCC1691182EF8A6086BE7AF4A0A62B52D7A594,
                    0x0DEA3332F3C63C37814CBA5AFB4380C5C3EE3920EF5DE5484C1961A98430C282,
                ),
                (
                    0x0C10E66F5BD143C35562D6B5F1BD6D0A256F4AFB69641A3D8C871F5CAA98FA6A,
                    0x1C8F31E252726F5FB9F5F444F60B32FCF94BA5E077C9724D36246EC666D767CC,
                ),
            )
            + PointG1(
                0x1F0BEFE534AA028FAF6181644D6774E4E14F600A5657B3E2F6287115317F678C,
                0x13357844009932B0B873101C362A9EE9FEA643412DA278256377C345E3F409DC,
            )
            + PointG2(
                (
                    0x1DB60E215FC52C5AF9D1B5045473F2F06BB20399DE3CDE3CE877BA545B994F33,
                    0x27C359CD987E9F2D05F015974E1B18B98B8F9684A24B0A50441244333BF5A35A,
                ),
                (
                    0x023036AEB27F556CA1E93DD351651594C723239A7C0CB15B8AB7A0446BA789FF,
                    0x17E4FCBE1D017009100203F39E446D7B686E30FCE3323EF61D46BC956143947C,
                ),
            ),
        ),
        pytest.param(
            PointG1(
                0x30618669FA4F387A7E9FCBF763BC0DC9908CF927D1F92B585CA17D46B7E97FD9,
                0x02ACC05526844E174394B69B1E0B78D24F7B5BD0CFADCB6A33AA6DC090D9028F,
            )
            + PointG2(
                (
                    0x160C5AF4494850EE7590972D0EFDA781E2879E76C807A16DD60EDE657E0BE6A8,
                    0x230F495774D31E8B73BF7CE73E6F87826D7A59E1C47B508D5F953A61C2B4939F,
                ),
                (
                    0x0492560C98F9FEAB356C744C09F1EC80F5FC9CC579F9929A3C7D9046585431B7,
                    0x273A1175635E2AB1F1B63838C13BD9D1DAF4DAD2620A0E72BEAE5F66AB88ACAB,
                ),
            )
            + PointG1(
                0x0F0887388FBCFEED9D128B7324B47676549D378C55D6D28B80CC179258A28017,
                0x11423DE6D1555ACFFE946EEBAEE182F8D007D5BAFEA10C7E00236552DE1C68B3,
            )
            + PointG2(
                (
                    0x2B74C50FE814021736DF034CFE502673B483BAA8F12825B9C7F74C59943CA535,
                    0x16196E1E69CEE3DC1A0CEEBCD6163C57F0155AFB41D78AAC57966A2681FCCD02,
                ),
                (
                    0x29B85E084727DB2843D66CC73E163875AE0CDF5CE9386BD6B2BE7018476D4606,
                    0x25BB91869E1C2453109BA45CDA0FA3F4BA9B8186DF72098E81CA6F131140D8B0,
                ),
            ),
        ),
    ],
    ids=lambda _: "positive_",
)
def test_positive(
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
