"""
Test_pairing_test.

Ported from:
state_tests/stZeroKnowledge/pairingTestFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stZeroKnowledge/pairingTestFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="d0-g0",
        ),
        pytest.param(
            0,
            1,
            0,
            id="d0-g1",
        ),
        pytest.param(
            0,
            2,
            0,
            id="d0-g2",
        ),
        pytest.param(
            0,
            3,
            0,
            id="d0-g3",
        ),
        pytest.param(
            1,
            0,
            0,
            id="d1-g0",
        ),
        pytest.param(
            1,
            1,
            0,
            id="d1-g1",
        ),
        pytest.param(
            1,
            2,
            0,
            id="d1-g2",
        ),
        pytest.param(
            1,
            3,
            0,
            id="d1-g3",
        ),
        pytest.param(
            2,
            0,
            0,
            id="d2-g0",
        ),
        pytest.param(
            2,
            1,
            0,
            id="d2-g1",
        ),
        pytest.param(
            2,
            2,
            0,
            id="d2-g2",
        ),
        pytest.param(
            2,
            3,
            0,
            id="d2-g3",
        ),
        pytest.param(
            3,
            0,
            0,
            id="d3-g0",
        ),
        pytest.param(
            3,
            1,
            0,
            id="d3-g1",
        ),
        pytest.param(
            3,
            2,
            0,
            id="d3-g2",
        ),
        pytest.param(
            3,
            3,
            0,
            id="d3-g3",
        ),
        pytest.param(
            4,
            0,
            0,
            id="d4-g0",
        ),
        pytest.param(
            4,
            1,
            0,
            id="d4-g1",
        ),
        pytest.param(
            4,
            2,
            0,
            id="d4-g2",
        ),
        pytest.param(
            4,
            3,
            0,
            id="d4-g3",
        ),
        pytest.param(
            5,
            0,
            0,
            id="d5-g0",
        ),
        pytest.param(
            5,
            1,
            0,
            id="d5-g1",
        ),
        pytest.param(
            5,
            2,
            0,
            id="d5-g2",
        ),
        pytest.param(
            5,
            3,
            0,
            id="d5-g3",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_pairing_test(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_pairing_test."""
    coinbase = Address(0x68795C4AA09D6F4ED3E5DEDDF8C2AD3049A601DA)
    contract_0 = Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    contract_1 = Address(0xC94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    contract_2 = Address(0xD94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000, nonce=1)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=14012015,
    )

    # Source: lll
    # {(MSTORE 32 (CALLDATALOAD 32)) (MSTORE 64 (CALLDATALOAD 64)) (MSTORE 96 (CALLDATALOAD 96)) (MSTORE 128 (CALLDATALOAD 128)) (MSTORE 160 (CALLDATALOAD 160)) (MSTORE 192 (CALLDATALOAD 192)) (MSTORE 224 (CALLDATALOAD 224)) (MSTORE 256 (CALLDATALOAD 256)) (MSTORE 288 (CALLDATALOAD 288)) (MSTORE 320 (CALLDATALOAD 320)) (MSTORE 352 (CALLDATALOAD 352)) (MSTORE 384 (CALLDATALOAD 384)) (MSTORE 416 (CALLDATALOAD 416)) (MSTORE 448 (CALLDATALOAD 448)) (MSTORE 480 (CALLDATALOAD 480)) (MSTORE 512 (CALLDATALOAD 512)) (MSTORE 544 (CALLDATALOAD 544)) (MSTORE 576 (CALLDATALOAD 576)) (MSTORE 608 (CALLDATALOAD 608)) (MSTORE 640 (CALLDATALOAD 640)) (MSTORE 672 (CALLDATALOAD 672)) (MSTORE 704 (CALLDATALOAD 704)) (MSTORE 736 (CALLDATALOAD 736)) [[0]](CALLCODE 500000 8 0 32 (CALLDATALOAD 0) 1000 32)  [[1]] (MLOAD 1000) }  # noqa: E501
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x20, value=Op.CALLDATALOAD(offset=0x20))
        + Op.MSTORE(offset=0x40, value=Op.CALLDATALOAD(offset=0x40))
        + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x60))
        + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x80))
        + Op.MSTORE(offset=0xA0, value=Op.CALLDATALOAD(offset=0xA0))
        + Op.MSTORE(offset=0xC0, value=Op.CALLDATALOAD(offset=0xC0))
        + Op.MSTORE(offset=0xE0, value=Op.CALLDATALOAD(offset=0xE0))
        + Op.MSTORE(offset=0x100, value=Op.CALLDATALOAD(offset=0x100))
        + Op.MSTORE(offset=0x120, value=Op.CALLDATALOAD(offset=0x120))
        + Op.MSTORE(offset=0x140, value=Op.CALLDATALOAD(offset=0x140))
        + Op.MSTORE(offset=0x160, value=Op.CALLDATALOAD(offset=0x160))
        + Op.MSTORE(offset=0x180, value=Op.CALLDATALOAD(offset=0x180))
        + Op.MSTORE(offset=0x1A0, value=Op.CALLDATALOAD(offset=0x1A0))
        + Op.MSTORE(offset=0x1C0, value=Op.CALLDATALOAD(offset=0x1C0))
        + Op.MSTORE(offset=0x1E0, value=Op.CALLDATALOAD(offset=0x1E0))
        + Op.MSTORE(offset=0x200, value=Op.CALLDATALOAD(offset=0x200))
        + Op.MSTORE(offset=0x220, value=Op.CALLDATALOAD(offset=0x220))
        + Op.MSTORE(offset=0x240, value=Op.CALLDATALOAD(offset=0x240))
        + Op.MSTORE(offset=0x260, value=Op.CALLDATALOAD(offset=0x260))
        + Op.MSTORE(offset=0x280, value=Op.CALLDATALOAD(offset=0x280))
        + Op.MSTORE(offset=0x2A0, value=Op.CALLDATALOAD(offset=0x2A0))
        + Op.MSTORE(offset=0x2C0, value=Op.CALLDATALOAD(offset=0x2C0))
        + Op.MSTORE(offset=0x2E0, value=Op.CALLDATALOAD(offset=0x2E0))
        + Op.SSTORE(
            key=0x0,
            value=Op.CALLCODE(
                gas=0x7A120,
                address=0x8,
                value=0x0,
                args_offset=0x20,
                args_size=Op.CALLDATALOAD(offset=0x0),
                ret_offset=0x3E8,
                ret_size=0x20,
            ),
        )
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x3E8))
        + Op.STOP,
        nonce=0,
    )
    # Source: lll
    # { (MSTORE 0 (CALLDATALOAD 0)) (MSTORE 32 (CALLDATALOAD 32)) (MSTORE 64 0x30644e72e131a029b85045b68181585d2833e84879b9709143e1f593f0000000)  [[0]](CALLCODE 5000000 7 0 0 96 1000 64)  [[1]](MLOAD 1000) [[2]](MLOAD 1032) }  # noqa: E501
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.CALLDATALOAD(offset=0x0))
        + Op.MSTORE(offset=0x20, value=Op.CALLDATALOAD(offset=0x20))
        + Op.MSTORE(
            offset=0x40,
            value=0x30644E72E131A029B85045B68181585D2833E84879B9709143E1F593F0000000,  # noqa: E501
        )
        + Op.SSTORE(
            key=0x0,
            value=Op.CALLCODE(
                gas=0x4C4B40,
                address=0x7,
                value=0x0,
                args_offset=0x0,
                args_size=0x60,
                ret_offset=0x3E8,
                ret_size=0x40,
            ),
        )
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x3E8))
        + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0x408))
        + Op.STOP,
        nonce=0,
    )
    # Source: lll
    # { (MSTORE 0 (CALLDATALOAD 0)) (MSTORE 32 (CALLDATALOAD 32)) (MSTORE 64 (CALLDATALOAD 64)) (MSTORE 96 (CALLDATALOAD 96)) [[0]](CALLCODE 5000000 6 0 0 128 1000 64)  [[1]](MLOAD 1000) [[2]](MLOAD 1032) }  # noqa: E501
    contract_2 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.CALLDATALOAD(offset=0x0))
        + Op.MSTORE(offset=0x20, value=Op.CALLDATALOAD(offset=0x20))
        + Op.MSTORE(offset=0x40, value=Op.CALLDATALOAD(offset=0x40))
        + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x60))
        + Op.SSTORE(
            key=0x0,
            value=Op.CALLCODE(
                gas=0x4C4B40,
                address=0x6,
                value=0x0,
                args_offset=0x0,
                args_size=0x80,
                ret_offset=0x3E8,
                ret_size=0x40,
            ),
        )
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x3E8))
        + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0x408))
        + Op.STOP,
        nonce=0,
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [0, 1, 2, 3, 4], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_0: Account(storage={0: 1, 1: 1})},
        },
        {
            "indexes": {"data": -1, "gas": [1, 2, 3], "value": -1},
            "network": [">=Cancun"],
            "result": {contract_0: Account(storage={})},
        },
        {
            "indexes": {"data": [5], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_0: Account(storage={0: 1, 1: 0})},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Hash(0x180)
        + Hash(
            0x1C76476F4DEF4BB94541D57EBBA1193381FFA7AA76ADA664DD31C16024C43F59
        )
        + Hash(
            0x3034DD2920F673E204FEE2811C678745FC819B55D3E9D294E45C9B03A76AEF41
        )
        + Hash(
            0x209DD15EBFF5D46C4BD888E51A93CF99A7329636C63514396B4A452003A35BF7
        )
        + Hash(
            0x4BF11CA01483BFA8B34B43561848D28905960114C8AC04049AF4B6315A41678
        )
        + Hash(
            0x2BB8324AF6CFC93537A2AD1A445CFD0CA2A71ACD7AC41FADBF933C2A51BE344D
        )
        + Hash(
            0x120A2A4CF30C1BF9845F20C6FE39E07EA2CCE61F0C9BB048165FE5E4DE877550
        )
        + Hash(
            0x111E129F1CF1097710D41C4AC70FCDFA5BA2023C6FF1CBEAC322DE49D1B6DF7C
        )
        + Hash(
            0x2032C61A830E3C17286DE9462BF242FCA2883585B93870A73853FACE6A6BF411
        )
        + Hash(
            0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2
        )
        + Hash(
            0x1800DEEF121F1E76426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED
        )
        + Hash(
            0x90689D0585FF075EC9E99AD690C3395BC4B313370B38EF355ACDADCD122975B
        )
        + Hash(
            0x12C85EA5DB8C6DEB4AAB71808DCB408FE3D1E7690C43D37B4CE6CC0166FA7DAA
        ),
        Hash(0x180)
        + Hash(
            0x2ECA0C7238BF16E83E7A1E6C5D49540685FF51380F309842A98561558019FC02
        )
        + Hash(
            0x3D3260361BB8451DE5FF5ECD17F010FF22F5C31CDF184E9020B06FA5997DB84
        )
        + Hash(
            0x1213D2149B006137FCFB23036606F848D638D576A120CA981B5B1A5F9300B3EE
        )
        + Hash(
            0x2276CF730CF493CD95D64677BBB75FC42DB72513A4C1E387B476D056F80AA75F
        )
        + Hash(
            0x21EE6226D31426322AFCDA621464D0611D226783262E21BB3BC86B537E986237
        )
        + Hash(
            0x96DF1F82DFF337DD5972E32A8AD43E28A78A96A823EF1CD4DEBE12B6552EA5F
        )
        + Hash(
            0x6967A1237EBFECA9AAAE0D6D0BAB8E28C198C5A339EF8A2407E31CDAC516DB9
        )
        + Hash(
            0x22160FA257A5FD5B280642FF47B65ECA77E626CB685C84FA6D3B6882A283DDD1
        )
        + Hash(
            0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2
        )
        + Hash(
            0x1800DEEF121F1E76426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED
        )
        + Hash(
            0x90689D0585FF075EC9E99AD690C3395BC4B313370B38EF355ACDADCD122975B
        )
        + Hash(
            0x12C85EA5DB8C6DEB4AAB71808DCB408FE3D1E7690C43D37B4CE6CC0166FA7DAA
        ),
        Hash(0x180)
        + Hash(
            0xF25929BCB43D5A57391564615C9E70A992B10EAFA4DB109709649CF48C50DD2
        )
        + Hash(
            0x16DA2F5CB6BE7A0AA72C440C53C9BBDFEC6C36C7D515536431B3A865468ACBBA
        )
        + Hash(
            0x2E89718AD33C8BED92E210E81D1853435399A271913A6520736A4729CF0D51EB
        )
        + Hash(
            0x1A9E2FFA2E92599B68E44DE5BCF354FA2642BD4F26B259DAA6F7CE3ED57AEB3
        )
        + Hash(
            0x14A9A87B789A58AF499B314E13C3D65BEDE56C07EA2D418D6874857B70763713
        )
        + Hash(
            0x178FB49A2D6CD347DC58973FF49613A20757D0FCC22079F9ABD10C3BAEE24590
        )
        + Hash(
            0x1B9E027BD5CFC2CB5DB82D4DC9677AC795EC500ECD47DEEE3B5DA006D6D049B8
        )
        + Hash(
            0x11D7511C78158DE484232FC68DAF8A45CF217D1C2FAE693FF5871E8752D73B21
        )
        + Hash(
            0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2
        )
        + Hash(
            0x1800DEEF121F1E76426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED
        )
        + Hash(
            0x90689D0585FF075EC9E99AD690C3395BC4B313370B38EF355ACDADCD122975B
        )
        + Hash(
            0x12C85EA5DB8C6DEB4AAB71808DCB408FE3D1E7690C43D37B4CE6CC0166FA7DAA
        ),
        Hash(0x240)
        + Hash(
            0x2F2EA0B3DA1E8EF11914ACF8B2E1B32D99DF51F5F4F206FC6B947EAE860EDDB6
        )
        + Hash(
            0x68134DDB33DC888EF446B648D72338684D678D2EB2371C61A50734D78DA4B72
        )
        + Hash(
            0x25F83C8B6AB9DE74E7DA488EF02645C5A16A6652C3C71A15DC37FE3A5DCB7CB1
        )
        + Hash(
            0x22ACDEDD6308E3BB230D226D16A105295F523A8A02BFC5E8BD2DA135AC4C245D
        )
        + Hash(
            0x65BBAD92E7C4E31BF3757F1FE7362A63FBFEE50E7DC68DA116E67D600D9BF68
        )
        + Hash(
            0x6D302580DC0661002994E7CD3A7F224E7DDC27802777486BF80F40E4CA3CFDB
        )
        + Hash(
            0x186BAC5188A98C45E6016873D107F5CD131F3A3E339D0375E58BD6219347B008
        )
        + Hash(
            0x122AE2B09E539E152EC5364E7E2204B03D11D3CAA038BFC7CD499F8176AACBEE
        )
        + Hash(
            0x1F39E4E4AFC4BC74790A4A028AFF2C3D2538731FB755EDEFD8CB48D6EA589B5E
        )
        + Hash(
            0x283F150794B6736F670D6A1033F9B46C6F5204F50813EB85C8DC4B59DB1C5D39
        )
        + Hash(
            0x140D97EE4D2B36D99BC49974D18ECCA3E7AD51011956051B464D9E27D46CC25E
        )
        + Hash(
            0x764BB98575BD466D32DB7B15F582B2D5C452B36AA394B789366E5E3CA5AABD4
        )
        + Hash(
            0x15794AB061441E51D01E94640B7E3084A07E02C78CF3103C542BC5B298669F21
        )
        + Hash(
            0x1B88DA1679B0B64A63B7E0E7BFE52AAE524F73A55BE7FE70C7E9BFC94B4CF0DA
        )
        + Hash(
            0x1213D2149B006137FCFB23036606F848D638D576A120CA981B5B1A5F9300B3EE
        )
        + Hash(
            0x2276CF730CF493CD95D64677BBB75FC42DB72513A4C1E387B476D056F80AA75F
        )
        + Hash(
            0x21EE6226D31426322AFCDA621464D0611D226783262E21BB3BC86B537E986237
        )
        + Hash(
            0x96DF1F82DFF337DD5972E32A8AD43E28A78A96A823EF1CD4DEBE12B6552EA5F
        ),
        Hash(0x240)
        + Hash(
            0x20A754D2071D4D53903E3B31A7E98AD6882D58AEC240EF981FDF0A9D22C5926A
        )
        + Hash(
            0x29C853FCEA789887315916BBEB89CA37EDB355B4F980C9A12A94F30DEEED3021
        )
        + Hash(
            0x1213D2149B006137FCFB23036606F848D638D576A120CA981B5B1A5F9300B3EE
        )
        + Hash(
            0x2276CF730CF493CD95D64677BBB75FC42DB72513A4C1E387B476D056F80AA75F
        )
        + Hash(
            0x21EE6226D31426322AFCDA621464D0611D226783262E21BB3BC86B537E986237
        )
        + Hash(
            0x96DF1F82DFF337DD5972E32A8AD43E28A78A96A823EF1CD4DEBE12B6552EA5F
        )
        + Hash(
            0x1ABB4A25EB9379AE96C84FFF9F0540ABCFC0A0D11AEDA02D4F37E4BAF74CB0C1
        )
        + Hash(
            0x1073B3FF2CDBB38755F8691EA59E9606696B3FF278ACFC098FA8226470D03869
        )
        + Hash(
            0x217CEE0A9AD79A4493B5253E2E4E3A39FC2DF38419F230D341F60CB064A0AC29
        )
        + Hash(
            0xA3D76F140DB8418BA512272381446EB73958670F00CF46F1D9E64CBA057B53C
        )
        + Hash(
            0x26F64A8EC70387A13E41430ED3EE4A7DB2059CC5FC13C067194BCC0CB49A9855
        )
        + Hash(
            0x2FD72BD9EDB657346127DA132E5B82AB908F5816C826ACB499E22F2412D1A2D7
        )
        + Hash(
            0xF25929BCB43D5A57391564615C9E70A992B10EAFA4DB109709649CF48C50DD2
        )
        + Hash(
            0x198A1F162A73261F112401AA2DB79C7DAB1533C9935C77290A6CE3B191F2318D
        )
        + Hash(
            0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2
        )
        + Hash(
            0x1800DEEF121F1E76426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED
        )
        + Hash(
            0x90689D0585FF075EC9E99AD690C3395BC4B313370B38EF355ACDADCD122975B
        )
        + Hash(
            0x12C85EA5DB8C6DEB4AAB71808DCB408FE3D1E7690C43D37B4CE6CC0166FA7DAA
        ),
        Hash(0x180)
        + Hash(
            0x1C76476F4DEF4BB94541D57EBBA1193381FFA7AA76ADA664DD31C16024C43F59
        )
        + Hash(
            0x3034DD2920F673E204FEE2811C678745FC819B55D3E9D294E45C9B03A76AEF41
        )
        + Hash(
            0x209DD15EBFF5D46C4BD888E51A93CF99A7329636C63514396B4A452003A35BF7
        )
        + Hash(
            0x4BF11CA01483BFA8B34B43561848D28905960114C8AC04049AF4B6315A41678
        )
        + Hash(
            0x2BB8324AF6CFC93537A2AD1A445CFD0CA2A71ACD7AC41FADBF933C2A51BE344D
        )
        + Hash(
            0x120A2A4CF30C1BF9845F20C6FE39E07EA2CCE61F0C9BB048165FE5E4DE877550
        )
        + Hash(
            0x111E129F1CF1097710D41C4AC70FCDFA5BA2023C6FF1CBEAC322DE49D1B6DF7C
        )
        + Hash(
            0x103188585E2364128FE25C70558F1560F4F9350BAF3959E603CC91486E110936
        )
        + Hash(
            0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2
        )
        + Hash(
            0x1800DEEF121F1E76426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED
        )
        + Hash(
            0x90689D0585FF075EC9E99AD690C3395BC4B313370B38EF355ACDADCD122975B
        )
        + Hash(
            0x12C85EA5DB8C6DEB4AAB71808DCB408FE3D1E7690C43D37B4CE6CC0166FA7DAA
        ),
    ]
    tx_gas = [10000000, 90000, 110000, 150000]

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        nonce=1,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
