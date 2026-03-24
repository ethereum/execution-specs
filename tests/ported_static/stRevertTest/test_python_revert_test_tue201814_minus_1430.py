"""
A random test that had failed in Python ethereum implementation.

Ported from:
tests/static/state_tests/stRevertTest/PythonRevertTestTue201814-1430Filler.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stRevertTest/PythonRevertTestTue201814-1430Filler.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Cancun")
@pytest.mark.pre_alloc_mutable
def test_python_revert_test_tue201814_minus_1430(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """A random test that had failed in Python ethereum implementation."""
    coinbase = Address("0xf7b2e80637a148b5e46945e29388928dafd5aa25")
    sender = EOA(
        key=0x3E297DF41E49C542F54718BBEE92D449778686880729C852F6D2C3C40D135341
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=5805800386153628,
    )

    pre.deploy_contract(
        code=(
            Op.MSTORE(
                offset=0x1F,
                value=0xBEE2A270429ABBD3FF3B9945F72F58DCF4F8B344417A87DFA1EBD7,
            )
            + Op.ORIGIN
            + Op.CALLCODE(
                gas=0x2C1E2816,
                address=0x69859649E8A52DE717592B881508371F8A8ED6B9,
                value=0x42A46F50,
                args_offset=0x132,
                args_size=0x27B,
                ret_offset=0x3EE,
                ret_size=0x9B,
            )
            + Op.STATICCALL(
                gas=0x2318D76F,
                address=0x843E0B83D4D70DEDE90D9A4D93FA3F10BB5011C7,
                args_offset=0x124,
                args_size=0x131,
                ret_offset=0x1EC,
                ret_size=0x172,
            )
            + Op.PUSH19[0x1A0FF381BB40BB828D7781D2EF7C0FD8695F7]
            + Op.PUSH29[
                0x5465FBADF99FDFFEF2AFD94B0E76531B6EA0D23D2332D13C20368A072
            ]
            + Op.MSTORE8(
                offset=0xA6B1EBC3464527E34C26A4379F9DFE4F8E57981A9FC08558C90D,
                value=0x4E41BC1130,
            )
            + Op.JUMPI(
                pc=0xCF72F489A4,
                condition=0x38079F1921B60FE6FA448171FEC55C4C63E811712211,
            )
            + Op.SLOAD(key=0xE83A2F5427EAB647B075A910929DE0A6554FC1426B49)
            + Op.MSTORE8(
                offset=0x3BD089A6663F6DFF488574195B848FBB357EB7BE1FFF076E997770D03B7028,  # noqa: E501
                value=0xCD8E2C770339616CE9C501FB746715DD4A20219229D0673AC05599,
            )
            + Op.DELEGATECALL(
                gas=0x47CFE65D,
                address=0x69859649E8A52DE717592B881508371F8A8ED6B9,
                args_offset=0x2DB,
                args_size=0x305,
                ret_offset=0x284,
                ret_size=0x3B3,
            )
            + Op.TIMESTAMP
            + Op.GASPRICE
            + Op.PUSH12[0x8679871DC28AA5A1399B21C8]
            + Op.STATICCALL(
                gas=0x11ECD01B,
                address=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                args_offset=0x5B,
                args_size=0x1F3,
                ret_offset=0x47,
                ret_size=0x2E4,
            )
            + Op.PUSH23[0xAFA8155ECD75DD05F9D7EB42FA3E79C6A2109DFF2A1E53]
            + Op.REVERT(offset=0x1B2, size=0x30A)
            + Op.CALLCODE(
                gas=0x42CE224D,
                address=Op.PUSH20[0x5],
                value=0x459D135B,
                args_offset=0x27F,
                args_size=0x117,
                ret_offset=0x58,
                ret_size=0x263,
            )
            + Op.MSTORE(
                offset=0xE3,
                value=0xE612FBE000BED18EEC8345F005F537C72820D8B973,
            )
            + Op.PUSH12[0x50AE523A8F7467AE14A8BD9A]
            + Op.PUSH11[0xAEE55862B685E32476CC67]
            + Op.PUSH3[0xAE2C40]
            + Op.PUSH9[0xCF55729540D111F44C]
            + Op.SWAP3
            + Op.RETURNDATACOPY(dest_offset=0x3F3, offset=0x1BC, size=0xE7)
            + Op.LT(0x9ED3BB, 0x639458DAE7AD2A9B38)
            + Op.REVERT(offset=0x36A, size=0xD8)
            + Op.CREATE(value=0x6DB4B55B, offset=0x359, size=0x123)
            + Op.MSTORE(offset=0x177, value=0x602169)
            + Op.BYTE(0x1BCF921919, 0xEA8A7B3A)
            + Op.RETURNDATACOPY(dest_offset=0x1F7, offset=0x371, size=0x3BE)
            + Op.MSTORE8(
                offset=0xA0B67479A345D1E70065,
                value=0xC0413CB5D609CA9A51645238E4F1F8268F973C3A01,
            )
            + Op.CALL(
                gas=0x35ADEABD,
                address=Op.PUSH20[0x6],
                value=0x3FF89B31,
                args_offset=0x214,
                args_size=0x2F2,
                ret_offset=0x173,
                ret_size=0x16,
            )
            + Op.RETURNDATASIZE
            + Op.SLOAD(
                key=0xE6D218AF54C3D8045447D06C726801695CFA26FDFAA6460A8685CD662855A5,  # noqa: E501
            )
            + Op.MLOAD(
                offset=0x5716140AE0B1E25AEAF04AE7CF54E8AA7A22206DA5A6E52BDD3EF82AD40A4681,  # noqa: E501
            )
            + Op.PUSH24[0xD25811167B0A3F66A727652592924DC1291A6085D537C5DA]
            + Op.RETURNDATACOPY(dest_offset=0x3A3, offset=0x1D, size=0x1B1)
            + Op.PUSH22[0x2D6272A54F882460BC76407D6361C40CC56BC88A8BC9]
            + Op.DELEGATECALL(
                gas=0x5F449586,
                address=0xE7E620C9CF6045209EDCAD4D6EF43413BEDF0949,
                args_offset=0x1F3,
                args_size=0x2C1,
                ret_offset=0x3EC,
                ret_size=0x72,
            )
        ),
        balance=0x882FD85BC18C9F00,
        nonce=29,
        address=Address("0x69859649e8a52de717592b881508371f8a8ed6b9"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xAB56295C9D120548)
    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=(
            Op.STATICCALL(
                gas=0x277795A,
                address=0xF7B2E80637A148B5E46945E29388928DAFD5AA25,
                args_offset=0x148,
                args_size=0xF5,
                ret_offset=0xFF,
                ret_size=0x2FA,
            )
            + Op.PUSH9[0x9497EDB6A665EAE52F]
            + Op.RETURNDATASIZE
            + Op.MSTORE(offset=0x3A5, value=0x524975)
            + Op.RETURNDATACOPY(dest_offset=0xCB, offset=0xFB, size=0xA8)
            + Op.REVERT(offset=0x3E0, size=0x2DD)
            + Op.PUSH16[0x568A159C0CAE9044D258C55B10F4D100]
            + Op.PUSH3[0x8D29AB]
            + Op.PUSH25[0x1DF7FCEBB789E2A8CDBAA9C67C42CD1EBE81716EAD0E94C721]
            + Op.PUSH14[0x279DD3A0B3DE311596D547292878]
            + Op.PUSH20[0x449CCCE511E6991B3DC636A178159A3D9A062274]
            + Op.PUSH3[0xCD9A67]
            + Op.PUSH9[0xCCBA17C2CB06DE468E]
            + Op.SWAP6
            + Op.PUSH20[0xBF78E55AF17E19973F2C3F5D4C21C169890B9A9]
            + Op.PUSH8[0x2491F91AA1E71426]
            + Op.PUSH8[0x60D385ED594E21B]
            + Op.PUSH14[0x2B23A6C4C50E7AB6A3EF66F83A2]
            + Op.SWAP3
            + Op.DIV(
                0x906C348472B7CB,
                0x9845B4BA85C4FDFBD0054A0123AD93EFF4B525B0F4B08D285F36F3BCAC6A985B,  # noqa: E501
            )
            + Op.LOG3(
                offset=0x61BE606EF617322E6448E3E4124DBE061257A8F486529DE397F08CE92502,  # noqa: E501
                size=0x3BFDFA7683AE0DF68BBCB534,
                topic_1=0x44C0173C10F1806BA284F9C9C7C13670005DE594DEC538CD56C274,  # noqa: E501
                topic_2=0xF536A04D436AD418A1CA,
                topic_3=0xC5A02E618666F0C50EECDC11F20FC1DC41C2FD957752E55EDE4E56F4,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x314,
                value=0x957F855818082B5B5B49E36DE5A83E8A270663088571BF2FDF8F5F29,  # noqa: E501
            )
            + Op.ORIGIN
            + Op.SSTORE(key=0x43, value=0xB9499741E3859928A237F5E5DF84C13C)
            + Op.SIGNEXTEND(
                0x74D84835800999791ABC41260472D96F604D07198E859ADC,
                0x1E82328F9093E64DEFBDD07D,
            )
            + Op.MSTORE8(
                offset=0x900E69A68B0F0E9E4F1299872881,
                value=0x806BEAE7200CF116D2B55E89DDD564ABC3,
            )
            + Op.LOG3(
                offset=0xC0F49ABE102CD44E474AB71C0237247865FA2ADD74C8B2,
                size=0x6ECF21D3A41AD554F79584DCAB761D4C8437774CAD4BB13B2BECE140358DF93E,  # noqa: E501
                topic_1=0xD270ECE7,
                topic_2=0x1C42F3B109ED2BD72A6CF13500241C2A5E5C4E17EA9ED9B05BA9B57D70D,  # noqa: E501
                topic_3=0x5D,
            )
            + Op.RETURNDATASIZE
            + Op.PUSH16[0x7041C5718A2554A72662720296DFF5B3]
            + Op.PUSH24[0xB559DF4558B8A5B2C9E7D15EB3947A70064F935C8FDF0A4E]
            + Op.PUSH19[0x6F644AA31B42C10280E50EA92A366C3D060C12]
            + Op.PUSH17[0xC6A16A75522FBEB3D7CCA702807F521781]
            + Op.PUSH15[0xAB9CCEB9E237EE8FDE4ED3A23D3EC8]
            + Op.PUSH27[
                0xDB334AC1CAA7E06523B0132DD615CF3FC16140D34C191617823C3A
            ]
            + Op.PUSH28[
                0xF47C42BC36B69CB4385463595C7F6F9EA451E05303603E0CD401E13D
            ]
            + Op.PUSH16[0xF744E2A673824D943941551704FF14DF]
            + Op.PUSH32[
                0xA8646EFBB2D8ABC4AC6E258E9924924B8001F8F0650D66B37411D484B18F41E7  # noqa: E501
            ]
            + Op.PUSH29[
                0x792BD1C169FA52BBFC8AF4A45F20ACB0EF95DB2ECBC0D4EADBBBF6732F
            ]
            + Op.PUSH5[0x8BD33B3633]
            + Op.PUSH14[0xC0FAF0CF1970BCD38093A50A44FD]
            + Op.PUSH12[0x253B0E74F2706239C499217B]
            + Op.DUP13
            + Op.ORIGIN
            + Op.SLOAD(key=0xDAE332E2)
            + Op.CALLDATALOAD(offset=0x1D5D5E7E795C998CCEED14CF46977E7D3CBB)
            + Op.CALLDATALOAD(
                offset=0x3C79EF0530C3A8AC3FD8D49F10BB0AE919FA149ADEAD67DAE0,
            )
            + Op.EXTCODECOPY(
                address=0x69859649E8A52DE717592B881508371F8A8ED6B9,
                dest_offset=0x71B518,
                offset=0x2813AC,
                size=0x7DE430,
            )
            + Op.PUSH32[
                0xB9BA628E056E0E87E029B8E5F42821D775338E6774301ECB428B3938236EE22B  # noqa: E501
            ]
            + Op.PUSH30[
                0xB5EDF2AD6997869F427BA0672A7168614233E85F61DAE5ED4283A53F605
            ]
            + Op.PUSH17[0x116DAD586DCE62833A62CA8C914C641F86]
            + Op.DELEGATECALL(
                gas=0x33D3D55F,
                address=0xF7B2E80637A148B5E46945E29388928DAFD5AA25,
                args_offset=0x31C,
                args_size=0x107,
                ret_offset=0x1D7,
                ret_size=0x52,
            )
            + Op.PUSH2[0x1A5B]
            + Op.PUSH4[0x1C4EA729]
            + Op.DUP2
            + Op.DELEGATECALL(
                gas=0x202B2EA8,
                address=Op.PUSH20[0x6],
                args_offset=0x14A,
                args_size=0x1C1,
                ret_offset=0x3CE,
                ret_size=0x256,
            )
            + Op.RETURNDATACOPY(dest_offset=0x2E, offset=0x106, size=0x221)
            + Op.PUSH5[0x8A95029ECB]
            + Op.DIV(
                0xB8F2B53E55FE01A152C8496CBCC6997447062B734CEBDE,
                0x849FE0943CB9D854C7D50AD04CFDFE648E2868,
            )
            + Op.PUSH26[0x6C6452E9EFC4ABA5BF071CBFF56208A525A8EF5F52399B4F3369]
            + Op.PUSH28[
                0xD988884F58166D734881774EFF46D77BB189C89C55B1C6591F178D2D
            ]
            + Op.PUSH29[
                0x21BF2B023ADF9BC5B8621235E3346D98D56047A3F71241FD5A24ABBB0C
            ]
            + Op.PUSH20[0xFC463FB8A5E67E32055696FE51258DD07526EBD8]
            + Op.PUSH31[
                0x439BCEBB514AE26DC12D653A5C1263705109097EC5DCDB3918AB114985F709  # noqa: E501
            ]
            + Op.PUSH32[
                0xD3003B50E58FBA91007825A6B800F644EAA306051808460FC3B2D8E276B2187C  # noqa: E501
            ]
            + Op.PUSH28[
                0x583FF29EE0B0C34F9EE57BAC9EBB996402E3300DDF06C760FC5F531F
            ]
            + Op.PUSH21[0x6B1E2BEDA7A15C07F90F92422822E8D33C5D2409EA]
            + Op.PUSH20[0x75197F7CD6D61770EDDB078206CFC7C5006CD0E9]
            + Op.PUSH30[
                0xA9EC65FA4FC683DA22CFAF6DFC995FEB5F8386A052851FC502F32E7EF934
            ]
            + Op.PUSH15[0x3D4633DEF4C0A4B9BE12F2CD7C6460]
            + Op.PUSH3[0xE14CA3]
            + Op.PUSH29[
                0xFB977524F677714C3D994EA05F1997A2462FC0AB20ED2A5958F3712602
            ]
            + Op.SWAP12
            + Op.DELEGATECALL(
                gas=0x2E83DBE,
                address=0x69859649E8A52DE717592B881508371F8A8ED6B9,
                args_offset=0x3A1,
                args_size=0x5D,
                ret_offset=0x2C9,
                ret_size=0x205,
            )
        ),
        balance=0x845252B8509DC215,
        nonce=29,
        address=Address("0x843e0b83d4d70dede90d9a4d93fa3f10bb5011c7"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.RETURNDATACOPY(dest_offset=0x101, offset=0x19F, size=0x13)
            + Op.PUSH16[0x338DB2B1165B4918F178852663192A95]
            + Op.PUSH14[0x79A68B50EEFDC639CA0B62AB4D52]
            + Op.PUSH24[0x1DB054CCC801C0666B34B3C6242BBFC5E98F20C14FB95E01]
            + Op.PUSH8[0x18BE9AD033D50E21]
            + Op.PUSH8[0x5FF59297861847EA]
            + Op.PUSH11[0x911A6A9D135E2F826DC603]
            + Op.PUSH30[
                0x850E0DB21D105B8732A34B873C7D943050B8659794F0BD3E841D35A2231E
            ]
            + Op.PUSH6[0xF697F8CDE117]
            + Op.PUSH8[0x28FA2051E87933CF]
            + Op.PUSH7[0x858E4E5E91BAA7]
            + Op.PUSH23[0x4FC1E9FFE4C7B15BA600E88F095989DC68F47ED704BE2B]
            + Op.SWAP10
            + Op.CREATE(value=0x200FBD63, offset=0x215, size=0x17)
            + Op.RETURNDATACOPY(
                dest_offset=0x99C91C,
                offset=0x93AFAA8CE1769C96CD0751AA76A98C8196FA8C92E70D7BDA17,
                size=0x41C7F86732F4D5419B41E6887CCA98E0943F141A5C66DF98BD0C6D6C4CEC65,  # noqa: E501
            )
            + Op.PUSH27[
                0x7F05DE3181109B8194387746F9EC15A6E0233F759E43360BD4E0A0
            ]
            + Op.MSTORE(offset=0x161, value=0x4E9F395117AFCD072774CE12D13DC7)
            + Op.ADDRESS
            + Op.GASPRICE
            + Op.PUSH9[0x3305858002A92140B6]
            + Op.PUSH25[0x508E3A3BE377D4825DBF618A393C7C061E75A8A496A33AFE0F]
            + Op.PUSH19[0x17F2E33549E321838B083D48893F23DCED459]
            + Op.PUSH31[
                0x2E9EA08FE3F80970D6334B6C6F1FDE8BCC81D03A7CCC244231CB6606DBA6D0  # noqa: E501
            ]
            + Op.PUSH15[0xC1C5158EF0DB6994192ACBD4CAC6AB]
            + Op.PUSH11[0xC8449D80FC2C32471946E0]
            + Op.PUSH18[0xD9606BD390266D7F712766F4765076283AD6]
            + Op.PUSH9[0x7450D7AB4DF6F3F6EE]
            + Op.SWAP7
            + Op.MSTORE8(
                offset=0xB802EC9D7ED96DC0B9CE7BD14B193DC1F0, value=0x14A
            )
            + Op.PUSH23[0xD11CE19283C7F651D4D2E7C180715FF7FCBC995EA8B276]
            + Op.PUSH3[0x13CC51]
            + Op.PUSH30[
                0x6DAD16D17F29A93220CE0DDB0A65D3D474DBC39CBA5BCB3D4FCF9FEF1910
            ]
            + Op.PUSH1[0x7D]
            + Op.PUSH5[0xC04511DF27]
            + Op.PUSH32[
                0x522AB2475FBB2BA0720711A903DBECFA0429BF11E6E90CBB0F13D4EE050C52C8  # noqa: E501
            ]
            + Op.PUSH20[0x65E0216B4096186FC604FB563FA59F1263EE91D5]
            + Op.PUSH10[0x5E407FDFFE82CA1558F7]
            + Op.DUP8
            + Op.PUSH11[0x93F3A218DD9BA6901FDEA9]
            + Op.RETURNDATASIZE
            + Op.PUSH12[0xE498F0B0E1874331115E31AA]
            + Op.PUSH16[0xAD4D87227362A9EC3E1C1BE11CDB2309]
            + Op.PUSH10[0x7BBC0C692EEADFA91616]
            + Op.PUSH10[0xB8AEC24564487DC74F8E]
            + Op.PUSH30[
                0x17E6A133B5DBE576838697DE73F856197203EF1A3A54F7EDB0DBD60F9D52
            ]
            + Op.PUSH21[0xDB6B5C1477169B77F0D817ED731A20DB4B9E5B83D2]
            + Op.PUSH25[0x6BFFEFAB084A31C4AFDA168156612F281DA0BE688E5BDB1F31]
            + Op.PUSH23[0xED78BC62343A7665ABAD6573482449E68B3ACFE820993D]
            + Op.PUSH24[0xDF5785384D51AAA0612DAB5DDBF2A9BF550736AD42293387]
            + Op.DUP9
            + Op.REVERT(offset=0x23F, size=0x119)
            + Op.CALL(
                gas=0x792C6916,
                address=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                value=0x5AF7465B,
                args_offset=0x36E,
                args_size=0x216,
                ret_offset=0x22D,
                ret_size=0x8F,
            )
            + Op.PUSH15[0xD70693587DF6CCFAE5218D01559BAC]
            + Op.PUSH1[0x15]
            + Op.REVERT(offset=0x1AD, size=0x200)
        ),
        balance=0x5B1936A53E6E440F,
        nonce=21,
        address=Address("0xe7e620c9cf6045209edcad4d6ef43413bedf0949"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=bytes.fromhex(
            "610326610100f379c940b5f2046740058558468f238b85db7f6bbe3f3d51e92a3e3268b7"  # noqa: E501
            "f7c4147541c695f376705288410b81b217e80726fb9e4c5c7b4c49eca0c1b6b97e117c16"  # noqa: E501
            "c26c9816459f38396ffc36da48d65defdc7d055cbc846c07e81cfab0fb607c6cbc968774"  # noqa: E501
            "d4de7df8e3236f581e688cc2081a96b1cad9e0609b70f4fddda49ae97714e7d325ceab23"  # noqa: E501
            "acd5f46ba15b5210474116121921a04f68f3f933b9ad91b735bf71bfe41da706499c5d47"  # noqa: E501
            "b6de1fe398cb91fdf66481cbb8661d71d457cf3cef75dabf5ea496d7012f4c56b9fe70e6"  # noqa: E501
            "c4204720e3ce66874cead08499d57a547b97d37744ce205e051f296fb116fc9e5f3c2809"  # noqa: E501
            "19aff3c93c5d5cefff9a6102d86103ca6364b68c8ef07d"
        ),
        balance=0x54C814F188394C8,
        nonce=29,
        address=coinbase,  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex(
            "66a9b45d44c78cfe774333fe0c49418dd61f183d41132f5340e48ababb825a26eb0a75c0"  # noqa: E501
            "ca693a8b465121200fd21a7b4c365a65a3255278f672705e5ca0f6146fccd36a6e5b9dec"  # noqa: E501
            "fb6e5096887651e829313a2cc9d5b518e25861c31ba04ed3f5a3310bd966993aa534b007"  # noqa: E501
            "85778d9545342410ce8c156d780a8cb4a65efed30aa9d6bd63c4778a134c9cb0c677ecda"  # noqa: E501
            "48aacef0c191de37e3cfdae69153747c2406995ea81bbae6a201663b9b37a6a9f597ae4f"  # noqa: E501
            "40e44e74ea92616bc2956328ced0d77412c265c2925470320e5f285d15a08a263b0a4445"  # noqa: E501
            "16817c266bd51fe726677144df3c080d07dd47c4eb9e44a87541ddc5a697163260a06921"  # noqa: E501
            "033eb3542b375cd0d073dfb48f6acde07152794b5539563efff1afed3b0a6b1516652617"  # noqa: E501
            "5e7184b83cc2de68df61ec5d65d1eee66ea376fcb84f2c73335db9fba49e3d40638cd7f4"  # noqa: E501
            "62f1d3b315f17b8dc1f692a68b2431b166ee71a4ba159dd322b9fa5f3237dfb85d259405"  # noqa: E501
            "6102f261025b61021d6101d3631fe4bdc373ffffffffffffffffffffffffffffffffffff"  # noqa: E501
            "ffff631ea09dc6f263edd580947c8177bd72d2244f7652371e3428d28bc6356c553b18d0"  # noqa: E501
            "0e6b3cf60206c273abbd7763059f61940b0d19fde33f7b5a96080d25791e9ae89c718dd4"  # noqa: E501
            "1c3f57b0c304fbb83978de28d23499bdd19c0472301ff527ccc9f7ed74a8dbd906b468d4"  # noqa: E501
            "48fba77f38f193e3047b02e40beb08b4f11707681ef103ec1b00585a85f27227a179f15e"  # noqa: E501
            "7e97a359268b06ff34bcee23a869974fbca6e201cb16179743ac0f8c9f8603d570e26a5a"  # noqa: E501
            "ad5217ebfff3140716923723efaa79b6cd87fbc9fd408d4ac5a048e43fb4e7a2b94053bf"  # noqa: E501
            "1fb7257562977725cde415738a99e1a7690cbe409744b737367dedc82e3063516c5bc57e"  # noqa: E501
            "35fcb2038306d9a3a6e46103515279ddcb9d30879e470f5dd81e1148184f62bd61ae9708"  # noqa: E501
            "ff61cee25c63694a73437a42be5043b1fde117ba383682ba0d91e0db8b29c882a044d0c8"  # noqa: E501
            "bb49056a25a66d8480df1b1ccc2564791df94f43d5802aa8f44bf70a6817ed784e5725bd"  # noqa: E501
            "c7718a54d6a567234286085240ba847d575dac25d7fc32c59999a9d38fee0d25e7c23986"  # noqa: E501
            "009c5bb022f7d28a2cab6e01a4bb37dd42ea42d5141d55f5730c7bd82bf08bff3928aea7"  # noqa: E501
            "7e7153bcc4a3a53996be367ec98cb6fe85797e771d020284d4d302c8b4ebe6b28a9c64a9"  # noqa: E501
            "ae2ad6894716732f6b245e7fdc5243f79a0ae9b8d874900caa1c5796a2854ceddb00a82b"  # noqa: E501
            "4ec01b513ed61c72ce89400a06fe90a109bad6d5e028143e7552937a0136347eb71a49db"  # noqa: E501
            "0072c87bd437b9cd7b2f7e6e9f3a85875c9ede6036650f9d06d4c2e8692caf2e87043c0b"  # noqa: E501
            "f5a2359c66431acbb35dcbfc6a7b86074b99c9e6f959d8417784e5e40c854c280218c0cd"  # noqa: E501
            "4e98dc3bc44f7d651d7191ead455"
        ),
        gas_limit=2643883,
        value=625999040,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stRevertTest/PythonRevertTestTue201814-1430Filler.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Prague")
@pytest.mark.pre_alloc_mutable
def test_python_revert_test_tue201814_minus_1430_from_prague(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """A random test that had failed in Python ethereum implementation."""
    coinbase = Address("0xf7b2e80637a148b5e46945e29388928dafd5aa25")
    sender = EOA(
        key=0x3E297DF41E49C542F54718BBEE92D449778686880729C852F6D2C3C40D135341
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=5805800386153628,
    )

    pre.deploy_contract(
        code=(
            Op.MSTORE(
                offset=0x1F,
                value=0xBEE2A270429ABBD3FF3B9945F72F58DCF4F8B344417A87DFA1EBD7,
            )
            + Op.ORIGIN
            + Op.CALLCODE(
                gas=0x2C1E2816,
                address=0x69859649E8A52DE717592B881508371F8A8ED6B9,
                value=0x42A46F50,
                args_offset=0x132,
                args_size=0x27B,
                ret_offset=0x3EE,
                ret_size=0x9B,
            )
            + Op.STATICCALL(
                gas=0x2318D76F,
                address=0x843E0B83D4D70DEDE90D9A4D93FA3F10BB5011C7,
                args_offset=0x124,
                args_size=0x131,
                ret_offset=0x1EC,
                ret_size=0x172,
            )
            + Op.PUSH19[0x1A0FF381BB40BB828D7781D2EF7C0FD8695F7]
            + Op.PUSH29[
                0x5465FBADF99FDFFEF2AFD94B0E76531B6EA0D23D2332D13C20368A072
            ]
            + Op.MSTORE8(
                offset=0xA6B1EBC3464527E34C26A4379F9DFE4F8E57981A9FC08558C90D,
                value=0x4E41BC1130,
            )
            + Op.JUMPI(
                pc=0xCF72F489A4,
                condition=0x38079F1921B60FE6FA448171FEC55C4C63E811712211,
            )
            + Op.SLOAD(key=0xE83A2F5427EAB647B075A910929DE0A6554FC1426B49)
            + Op.MSTORE8(
                offset=0x3BD089A6663F6DFF488574195B848FBB357EB7BE1FFF076E997770D03B7028,  # noqa: E501
                value=0xCD8E2C770339616CE9C501FB746715DD4A20219229D0673AC05599,
            )
            + Op.DELEGATECALL(
                gas=0x47CFE65D,
                address=0x69859649E8A52DE717592B881508371F8A8ED6B9,
                args_offset=0x2DB,
                args_size=0x305,
                ret_offset=0x284,
                ret_size=0x3B3,
            )
            + Op.TIMESTAMP
            + Op.GASPRICE
            + Op.PUSH12[0x8679871DC28AA5A1399B21C8]
            + Op.STATICCALL(
                gas=0x11ECD01B,
                address=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                args_offset=0x5B,
                args_size=0x1F3,
                ret_offset=0x47,
                ret_size=0x2E4,
            )
            + Op.PUSH23[0xAFA8155ECD75DD05F9D7EB42FA3E79C6A2109DFF2A1E53]
            + Op.REVERT(offset=0x1B2, size=0x30A)
            + Op.CALLCODE(
                gas=0x42CE224D,
                address=Op.PUSH20[0x5],
                value=0x459D135B,
                args_offset=0x27F,
                args_size=0x117,
                ret_offset=0x58,
                ret_size=0x263,
            )
            + Op.MSTORE(
                offset=0xE3,
                value=0xE612FBE000BED18EEC8345F005F537C72820D8B973,
            )
            + Op.PUSH12[0x50AE523A8F7467AE14A8BD9A]
            + Op.PUSH11[0xAEE55862B685E32476CC67]
            + Op.PUSH3[0xAE2C40]
            + Op.PUSH9[0xCF55729540D111F44C]
            + Op.SWAP3
            + Op.RETURNDATACOPY(dest_offset=0x3F3, offset=0x1BC, size=0xE7)
            + Op.LT(0x9ED3BB, 0x639458DAE7AD2A9B38)
            + Op.REVERT(offset=0x36A, size=0xD8)
            + Op.CREATE(value=0x6DB4B55B, offset=0x359, size=0x123)
            + Op.MSTORE(offset=0x177, value=0x602169)
            + Op.BYTE(0x1BCF921919, 0xEA8A7B3A)
            + Op.RETURNDATACOPY(dest_offset=0x1F7, offset=0x371, size=0x3BE)
            + Op.MSTORE8(
                offset=0xA0B67479A345D1E70065,
                value=0xC0413CB5D609CA9A51645238E4F1F8268F973C3A01,
            )
            + Op.CALL(
                gas=0x35ADEABD,
                address=Op.PUSH20[0x6],
                value=0x3FF89B31,
                args_offset=0x214,
                args_size=0x2F2,
                ret_offset=0x173,
                ret_size=0x16,
            )
            + Op.RETURNDATASIZE
            + Op.SLOAD(
                key=0xE6D218AF54C3D8045447D06C726801695CFA26FDFAA6460A8685CD662855A5,  # noqa: E501
            )
            + Op.MLOAD(
                offset=0x5716140AE0B1E25AEAF04AE7CF54E8AA7A22206DA5A6E52BDD3EF82AD40A4681,  # noqa: E501
            )
            + Op.PUSH24[0xD25811167B0A3F66A727652592924DC1291A6085D537C5DA]
            + Op.RETURNDATACOPY(dest_offset=0x3A3, offset=0x1D, size=0x1B1)
            + Op.PUSH22[0x2D6272A54F882460BC76407D6361C40CC56BC88A8BC9]
            + Op.DELEGATECALL(
                gas=0x5F449586,
                address=0xE7E620C9CF6045209EDCAD4D6EF43413BEDF0949,
                args_offset=0x1F3,
                args_size=0x2C1,
                ret_offset=0x3EC,
                ret_size=0x72,
            )
        ),
        balance=0x882FD85BC18C9F00,
        nonce=29,
        address=Address("0x69859649e8a52de717592b881508371f8a8ed6b9"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xAB56295C9D120548)
    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=(
            Op.STATICCALL(
                gas=0x277795A,
                address=0xF7B2E80637A148B5E46945E29388928DAFD5AA25,
                args_offset=0x148,
                args_size=0xF5,
                ret_offset=0xFF,
                ret_size=0x2FA,
            )
            + Op.PUSH9[0x9497EDB6A665EAE52F]
            + Op.RETURNDATASIZE
            + Op.MSTORE(offset=0x3A5, value=0x524975)
            + Op.RETURNDATACOPY(dest_offset=0xCB, offset=0xFB, size=0xA8)
            + Op.REVERT(offset=0x3E0, size=0x2DD)
            + Op.PUSH16[0x568A159C0CAE9044D258C55B10F4D100]
            + Op.PUSH3[0x8D29AB]
            + Op.PUSH25[0x1DF7FCEBB789E2A8CDBAA9C67C42CD1EBE81716EAD0E94C721]
            + Op.PUSH14[0x279DD3A0B3DE311596D547292878]
            + Op.PUSH20[0x449CCCE511E6991B3DC636A178159A3D9A062274]
            + Op.PUSH3[0xCD9A67]
            + Op.PUSH9[0xCCBA17C2CB06DE468E]
            + Op.SWAP6
            + Op.PUSH20[0xBF78E55AF17E19973F2C3F5D4C21C169890B9A9]
            + Op.PUSH8[0x2491F91AA1E71426]
            + Op.PUSH8[0x60D385ED594E21B]
            + Op.PUSH14[0x2B23A6C4C50E7AB6A3EF66F83A2]
            + Op.SWAP3
            + Op.DIV(
                0x906C348472B7CB,
                0x9845B4BA85C4FDFBD0054A0123AD93EFF4B525B0F4B08D285F36F3BCAC6A985B,  # noqa: E501
            )
            + Op.LOG3(
                offset=0x61BE606EF617322E6448E3E4124DBE061257A8F486529DE397F08CE92502,  # noqa: E501
                size=0x3BFDFA7683AE0DF68BBCB534,
                topic_1=0x44C0173C10F1806BA284F9C9C7C13670005DE594DEC538CD56C274,  # noqa: E501
                topic_2=0xF536A04D436AD418A1CA,
                topic_3=0xC5A02E618666F0C50EECDC11F20FC1DC41C2FD957752E55EDE4E56F4,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x314,
                value=0x957F855818082B5B5B49E36DE5A83E8A270663088571BF2FDF8F5F29,  # noqa: E501
            )
            + Op.ORIGIN
            + Op.SSTORE(key=0x43, value=0xB9499741E3859928A237F5E5DF84C13C)
            + Op.SIGNEXTEND(
                0x74D84835800999791ABC41260472D96F604D07198E859ADC,
                0x1E82328F9093E64DEFBDD07D,
            )
            + Op.MSTORE8(
                offset=0x900E69A68B0F0E9E4F1299872881,
                value=0x806BEAE7200CF116D2B55E89DDD564ABC3,
            )
            + Op.LOG3(
                offset=0xC0F49ABE102CD44E474AB71C0237247865FA2ADD74C8B2,
                size=0x6ECF21D3A41AD554F79584DCAB761D4C8437774CAD4BB13B2BECE140358DF93E,  # noqa: E501
                topic_1=0xD270ECE7,
                topic_2=0x1C42F3B109ED2BD72A6CF13500241C2A5E5C4E17EA9ED9B05BA9B57D70D,  # noqa: E501
                topic_3=0x5D,
            )
            + Op.RETURNDATASIZE
            + Op.PUSH16[0x7041C5718A2554A72662720296DFF5B3]
            + Op.PUSH24[0xB559DF4558B8A5B2C9E7D15EB3947A70064F935C8FDF0A4E]
            + Op.PUSH19[0x6F644AA31B42C10280E50EA92A366C3D060C12]
            + Op.PUSH17[0xC6A16A75522FBEB3D7CCA702807F521781]
            + Op.PUSH15[0xAB9CCEB9E237EE8FDE4ED3A23D3EC8]
            + Op.PUSH27[
                0xDB334AC1CAA7E06523B0132DD615CF3FC16140D34C191617823C3A
            ]
            + Op.PUSH28[
                0xF47C42BC36B69CB4385463595C7F6F9EA451E05303603E0CD401E13D
            ]
            + Op.PUSH16[0xF744E2A673824D943941551704FF14DF]
            + Op.PUSH32[
                0xA8646EFBB2D8ABC4AC6E258E9924924B8001F8F0650D66B37411D484B18F41E7  # noqa: E501
            ]
            + Op.PUSH29[
                0x792BD1C169FA52BBFC8AF4A45F20ACB0EF95DB2ECBC0D4EADBBBF6732F
            ]
            + Op.PUSH5[0x8BD33B3633]
            + Op.PUSH14[0xC0FAF0CF1970BCD38093A50A44FD]
            + Op.PUSH12[0x253B0E74F2706239C499217B]
            + Op.DUP13
            + Op.ORIGIN
            + Op.SLOAD(key=0xDAE332E2)
            + Op.CALLDATALOAD(offset=0x1D5D5E7E795C998CCEED14CF46977E7D3CBB)
            + Op.CALLDATALOAD(
                offset=0x3C79EF0530C3A8AC3FD8D49F10BB0AE919FA149ADEAD67DAE0,
            )
            + Op.EXTCODECOPY(
                address=0x69859649E8A52DE717592B881508371F8A8ED6B9,
                dest_offset=0x71B518,
                offset=0x2813AC,
                size=0x7DE430,
            )
            + Op.PUSH32[
                0xB9BA628E056E0E87E029B8E5F42821D775338E6774301ECB428B3938236EE22B  # noqa: E501
            ]
            + Op.PUSH30[
                0xB5EDF2AD6997869F427BA0672A7168614233E85F61DAE5ED4283A53F605
            ]
            + Op.PUSH17[0x116DAD586DCE62833A62CA8C914C641F86]
            + Op.DELEGATECALL(
                gas=0x33D3D55F,
                address=0xF7B2E80637A148B5E46945E29388928DAFD5AA25,
                args_offset=0x31C,
                args_size=0x107,
                ret_offset=0x1D7,
                ret_size=0x52,
            )
            + Op.PUSH2[0x1A5B]
            + Op.PUSH4[0x1C4EA729]
            + Op.DUP2
            + Op.DELEGATECALL(
                gas=0x202B2EA8,
                address=Op.PUSH20[0x6],
                args_offset=0x14A,
                args_size=0x1C1,
                ret_offset=0x3CE,
                ret_size=0x256,
            )
            + Op.RETURNDATACOPY(dest_offset=0x2E, offset=0x106, size=0x221)
            + Op.PUSH5[0x8A95029ECB]
            + Op.DIV(
                0xB8F2B53E55FE01A152C8496CBCC6997447062B734CEBDE,
                0x849FE0943CB9D854C7D50AD04CFDFE648E2868,
            )
            + Op.PUSH26[0x6C6452E9EFC4ABA5BF071CBFF56208A525A8EF5F52399B4F3369]
            + Op.PUSH28[
                0xD988884F58166D734881774EFF46D77BB189C89C55B1C6591F178D2D
            ]
            + Op.PUSH29[
                0x21BF2B023ADF9BC5B8621235E3346D98D56047A3F71241FD5A24ABBB0C
            ]
            + Op.PUSH20[0xFC463FB8A5E67E32055696FE51258DD07526EBD8]
            + Op.PUSH31[
                0x439BCEBB514AE26DC12D653A5C1263705109097EC5DCDB3918AB114985F709  # noqa: E501
            ]
            + Op.PUSH32[
                0xD3003B50E58FBA91007825A6B800F644EAA306051808460FC3B2D8E276B2187C  # noqa: E501
            ]
            + Op.PUSH28[
                0x583FF29EE0B0C34F9EE57BAC9EBB996402E3300DDF06C760FC5F531F
            ]
            + Op.PUSH21[0x6B1E2BEDA7A15C07F90F92422822E8D33C5D2409EA]
            + Op.PUSH20[0x75197F7CD6D61770EDDB078206CFC7C5006CD0E9]
            + Op.PUSH30[
                0xA9EC65FA4FC683DA22CFAF6DFC995FEB5F8386A052851FC502F32E7EF934
            ]
            + Op.PUSH15[0x3D4633DEF4C0A4B9BE12F2CD7C6460]
            + Op.PUSH3[0xE14CA3]
            + Op.PUSH29[
                0xFB977524F677714C3D994EA05F1997A2462FC0AB20ED2A5958F3712602
            ]
            + Op.SWAP12
            + Op.DELEGATECALL(
                gas=0x2E83DBE,
                address=0x69859649E8A52DE717592B881508371F8A8ED6B9,
                args_offset=0x3A1,
                args_size=0x5D,
                ret_offset=0x2C9,
                ret_size=0x205,
            )
        ),
        balance=0x845252B8509DC215,
        nonce=29,
        address=Address("0x843e0b83d4d70dede90d9a4d93fa3f10bb5011c7"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.RETURNDATACOPY(dest_offset=0x101, offset=0x19F, size=0x13)
            + Op.PUSH16[0x338DB2B1165B4918F178852663192A95]
            + Op.PUSH14[0x79A68B50EEFDC639CA0B62AB4D52]
            + Op.PUSH24[0x1DB054CCC801C0666B34B3C6242BBFC5E98F20C14FB95E01]
            + Op.PUSH8[0x18BE9AD033D50E21]
            + Op.PUSH8[0x5FF59297861847EA]
            + Op.PUSH11[0x911A6A9D135E2F826DC603]
            + Op.PUSH30[
                0x850E0DB21D105B8732A34B873C7D943050B8659794F0BD3E841D35A2231E
            ]
            + Op.PUSH6[0xF697F8CDE117]
            + Op.PUSH8[0x28FA2051E87933CF]
            + Op.PUSH7[0x858E4E5E91BAA7]
            + Op.PUSH23[0x4FC1E9FFE4C7B15BA600E88F095989DC68F47ED704BE2B]
            + Op.SWAP10
            + Op.CREATE(value=0x200FBD63, offset=0x215, size=0x17)
            + Op.RETURNDATACOPY(
                dest_offset=0x99C91C,
                offset=0x93AFAA8CE1769C96CD0751AA76A98C8196FA8C92E70D7BDA17,
                size=0x41C7F86732F4D5419B41E6887CCA98E0943F141A5C66DF98BD0C6D6C4CEC65,  # noqa: E501
            )
            + Op.PUSH27[
                0x7F05DE3181109B8194387746F9EC15A6E0233F759E43360BD4E0A0
            ]
            + Op.MSTORE(offset=0x161, value=0x4E9F395117AFCD072774CE12D13DC7)
            + Op.ADDRESS
            + Op.GASPRICE
            + Op.PUSH9[0x3305858002A92140B6]
            + Op.PUSH25[0x508E3A3BE377D4825DBF618A393C7C061E75A8A496A33AFE0F]
            + Op.PUSH19[0x17F2E33549E321838B083D48893F23DCED459]
            + Op.PUSH31[
                0x2E9EA08FE3F80970D6334B6C6F1FDE8BCC81D03A7CCC244231CB6606DBA6D0  # noqa: E501
            ]
            + Op.PUSH15[0xC1C5158EF0DB6994192ACBD4CAC6AB]
            + Op.PUSH11[0xC8449D80FC2C32471946E0]
            + Op.PUSH18[0xD9606BD390266D7F712766F4765076283AD6]
            + Op.PUSH9[0x7450D7AB4DF6F3F6EE]
            + Op.SWAP7
            + Op.MSTORE8(
                offset=0xB802EC9D7ED96DC0B9CE7BD14B193DC1F0, value=0x14A
            )
            + Op.PUSH23[0xD11CE19283C7F651D4D2E7C180715FF7FCBC995EA8B276]
            + Op.PUSH3[0x13CC51]
            + Op.PUSH30[
                0x6DAD16D17F29A93220CE0DDB0A65D3D474DBC39CBA5BCB3D4FCF9FEF1910
            ]
            + Op.PUSH1[0x7D]
            + Op.PUSH5[0xC04511DF27]
            + Op.PUSH32[
                0x522AB2475FBB2BA0720711A903DBECFA0429BF11E6E90CBB0F13D4EE050C52C8  # noqa: E501
            ]
            + Op.PUSH20[0x65E0216B4096186FC604FB563FA59F1263EE91D5]
            + Op.PUSH10[0x5E407FDFFE82CA1558F7]
            + Op.DUP8
            + Op.PUSH11[0x93F3A218DD9BA6901FDEA9]
            + Op.RETURNDATASIZE
            + Op.PUSH12[0xE498F0B0E1874331115E31AA]
            + Op.PUSH16[0xAD4D87227362A9EC3E1C1BE11CDB2309]
            + Op.PUSH10[0x7BBC0C692EEADFA91616]
            + Op.PUSH10[0xB8AEC24564487DC74F8E]
            + Op.PUSH30[
                0x17E6A133B5DBE576838697DE73F856197203EF1A3A54F7EDB0DBD60F9D52
            ]
            + Op.PUSH21[0xDB6B5C1477169B77F0D817ED731A20DB4B9E5B83D2]
            + Op.PUSH25[0x6BFFEFAB084A31C4AFDA168156612F281DA0BE688E5BDB1F31]
            + Op.PUSH23[0xED78BC62343A7665ABAD6573482449E68B3ACFE820993D]
            + Op.PUSH24[0xDF5785384D51AAA0612DAB5DDBF2A9BF550736AD42293387]
            + Op.DUP9
            + Op.REVERT(offset=0x23F, size=0x119)
            + Op.CALL(
                gas=0x792C6916,
                address=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                value=0x5AF7465B,
                args_offset=0x36E,
                args_size=0x216,
                ret_offset=0x22D,
                ret_size=0x8F,
            )
            + Op.PUSH15[0xD70693587DF6CCFAE5218D01559BAC]
            + Op.PUSH1[0x15]
            + Op.REVERT(offset=0x1AD, size=0x200)
        ),
        balance=0x5B1936A53E6E440F,
        nonce=21,
        address=Address("0xe7e620c9cf6045209edcad4d6ef43413bedf0949"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=bytes.fromhex(
            "610326610100f379c940b5f2046740058558468f238b85db7f6bbe3f3d51e92a3e3268b7"  # noqa: E501
            "f7c4147541c695f376705288410b81b217e80726fb9e4c5c7b4c49eca0c1b6b97e117c16"  # noqa: E501
            "c26c9816459f38396ffc36da48d65defdc7d055cbc846c07e81cfab0fb607c6cbc968774"  # noqa: E501
            "d4de7df8e3236f581e688cc2081a96b1cad9e0609b70f4fddda49ae97714e7d325ceab23"  # noqa: E501
            "acd5f46ba15b5210474116121921a04f68f3f933b9ad91b735bf71bfe41da706499c5d47"  # noqa: E501
            "b6de1fe398cb91fdf66481cbb8661d71d457cf3cef75dabf5ea496d7012f4c56b9fe70e6"  # noqa: E501
            "c4204720e3ce66874cead08499d57a547b97d37744ce205e051f296fb116fc9e5f3c2809"  # noqa: E501
            "19aff3c93c5d5cefff9a6102d86103ca6364b68c8ef07d"
        ),
        balance=0x54C814F188394C8,
        nonce=29,
        address=coinbase,  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex(
            "66a9b45d44c78cfe774333fe0c49418dd61f183d41132f5340e48ababb825a26eb0a75c0"  # noqa: E501
            "ca693a8b465121200fd21a7b4c365a65a3255278f672705e5ca0f6146fccd36a6e5b9dec"  # noqa: E501
            "fb6e5096887651e829313a2cc9d5b518e25861c31ba04ed3f5a3310bd966993aa534b007"  # noqa: E501
            "85778d9545342410ce8c156d780a8cb4a65efed30aa9d6bd63c4778a134c9cb0c677ecda"  # noqa: E501
            "48aacef0c191de37e3cfdae69153747c2406995ea81bbae6a201663b9b37a6a9f597ae4f"  # noqa: E501
            "40e44e74ea92616bc2956328ced0d77412c265c2925470320e5f285d15a08a263b0a4445"  # noqa: E501
            "16817c266bd51fe726677144df3c080d07dd47c4eb9e44a87541ddc5a697163260a06921"  # noqa: E501
            "033eb3542b375cd0d073dfb48f6acde07152794b5539563efff1afed3b0a6b1516652617"  # noqa: E501
            "5e7184b83cc2de68df61ec5d65d1eee66ea376fcb84f2c73335db9fba49e3d40638cd7f4"  # noqa: E501
            "62f1d3b315f17b8dc1f692a68b2431b166ee71a4ba159dd322b9fa5f3237dfb85d259405"  # noqa: E501
            "6102f261025b61021d6101d3631fe4bdc373ffffffffffffffffffffffffffffffffffff"  # noqa: E501
            "ffff631ea09dc6f263edd580947c8177bd72d2244f7652371e3428d28bc6356c553b18d0"  # noqa: E501
            "0e6b3cf60206c273abbd7763059f61940b0d19fde33f7b5a96080d25791e9ae89c718dd4"  # noqa: E501
            "1c3f57b0c304fbb83978de28d23499bdd19c0472301ff527ccc9f7ed74a8dbd906b468d4"  # noqa: E501
            "48fba77f38f193e3047b02e40beb08b4f11707681ef103ec1b00585a85f27227a179f15e"  # noqa: E501
            "7e97a359268b06ff34bcee23a869974fbca6e201cb16179743ac0f8c9f8603d570e26a5a"  # noqa: E501
            "ad5217ebfff3140716923723efaa79b6cd87fbc9fd408d4ac5a048e43fb4e7a2b94053bf"  # noqa: E501
            "1fb7257562977725cde415738a99e1a7690cbe409744b737367dedc82e3063516c5bc57e"  # noqa: E501
            "35fcb2038306d9a3a6e46103515279ddcb9d30879e470f5dd81e1148184f62bd61ae9708"  # noqa: E501
            "ff61cee25c63694a73437a42be5043b1fde117ba383682ba0d91e0db8b29c882a044d0c8"  # noqa: E501
            "bb49056a25a66d8480df1b1ccc2564791df94f43d5802aa8f44bf70a6817ed784e5725bd"  # noqa: E501
            "c7718a54d6a567234286085240ba847d575dac25d7fc32c59999a9d38fee0d25e7c23986"  # noqa: E501
            "009c5bb022f7d28a2cab6e01a4bb37dd42ea42d5141d55f5730c7bd82bf08bff3928aea7"  # noqa: E501
            "7e7153bcc4a3a53996be367ec98cb6fe85797e771d020284d4d302c8b4ebe6b28a9c64a9"  # noqa: E501
            "ae2ad6894716732f6b245e7fdc5243f79a0ae9b8d874900caa1c5796a2854ceddb00a82b"  # noqa: E501
            "4ec01b513ed61c72ce89400a06fe90a109bad6d5e028143e7552937a0136347eb71a49db"  # noqa: E501
            "0072c87bd437b9cd7b2f7e6e9f3a85875c9ede6036650f9d06d4c2e8692caf2e87043c0b"  # noqa: E501
            "f5a2359c66431acbb35dcbfc6a7b86074b99c9e6f959d8417784e5e40c854c280218c0cd"  # noqa: E501
            "4e98dc3bc44f7d651d7191ead455"
        ),
        gas_limit=2643883,
        value=625999040,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
