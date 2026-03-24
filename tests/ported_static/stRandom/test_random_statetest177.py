"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stRandom/randomStatetest177Filler.json
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
    ["tests/static/state_tests/stRandom/randomStatetest177Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest177(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x4f3f701464972e74606d6ea82d4d3080599a0e79")
    sender = EOA(
        key=0xB1F4CBC3A50042184425A6F9E996D0910F7BA879457CE5DAC5C71E498AD3C005
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre[sender] = Account(balance=0xDE0B6B3A7640000)
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.JUMPI(
                pc=0x9,
                condition=Op.ISZERO(Op.SLOAD(key=Op.CALLDATALOAD(offset=0x0))),
            )
            + Op.STOP
            + Op.JUMPDEST
            + Op.SSTORE(
                key=Op.CALLDATALOAD(offset=0x0),
                value=Op.CALLDATALOAD(offset=0x20),
            )
        ),
        balance=46,
        nonce=0,
        address=coinbase,  # noqa: E501
    )
    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=(
            Op.PUSH31[
                0x24654D920BEE1C2AF8B3225F6035EA04B87E1D3F2486057268ED05D8D6E5A6  # noqa: E501
            ]
            + Op.PUSH32[
                0x3DA4409848B450C9AB9713BF10EC5124E50FDA175ACCC13D0DB75BBC03A25A06  # noqa: E501
            ]
            + Op.PUSH14[0x85332A97EAE6E7219BC62CE53F23]
            + Op.PUSH10[0xF1DF7F7B11C1659165B]
            + Op.PUSH29[
                0x438533BC1F73A59AE2C28E633D8C971763576DD25386518678A15C64A2
            ]
            + Op.PUSH9[0x2C68BF3C1A7433AF2E]
            + Op.PUSH14[0xD0276F494254235FE7B28B1F9976]
            + Op.PUSH2[0xEBA4]
            + Op.PUSH23[0x7C05F37A8B9B7980106E2BBE8744BED6D0F782AC6A99E0]
            + Op.PUSH30[
                0x9486451AB20E48C9E99F083973D5A10A57F4C3E7E3FA3BFD63A39006F35F
            ]
            + Op.PUSH20[0x25AE8B67348D74C87E78D6DC699541FDF8D08569]
            + Op.PUSH31[
                0x58B02F9FEF3F78554901CC888449B92FE07E74FB3069F7BE725F408005886E  # noqa: E501
            ]
            + Op.PUSH20[0xE720275F04F63284F6F10B6DF25694B3A55936D0]
            + Op.PUSH15[0xD8C18D03D868D30B7766BD0D6A111F]
            + Op.PUSH20[0x4650113A9F6B31EF3BE38904CCD66A304BBF877E]
            + Op.SWAP14
            + Op.PUSH13[0xCC3E98FA65A685B0BF181C6DD6]
            + Op.PUSH29[
                0x9DB728914FF2977B8C19193F67B9053F72C819B5BC5542945BD6A90799
            ]
            + Op.PUSH6[0xD91F47A11F38]
            + Op.PUSH3[0xD346CB]
            + Op.PUSH12[0x70D29ECA71B0D12D01996B89]
            + Op.PUSH23[0x3F13059617D671DDC626D93A3E3FDA99999484470E3427]
            + Op.PUSH32[
                0x9AC904A6BE6B8B9F0A91E98E2759A946222E419D34089491DB069BBEEEA7D198  # noqa: E501
            ]
            + Op.PUSH9[0xE6FEF55CD7440FBBDD]
            + Op.PUSH28[
                0xF7CAB153DE2F407FC2C1F51952D5D5388159F73C98DEB0A3F75D04EB
            ]
            + Op.PUSH17[0xCEE4F3DD886B6BA2AB3D1E110DB841C507]
            + Op.PUSH8[0xA4E0ED4ABCA1BD1D]
            + Op.PUSH7[0x88861C4BB169FA]
            + Op.DUP12
            + Op.PUSH4[0xD253F1A4]
            + Op.PUSH4[0x6A397939]
            + Op.PUSH10[0x65AE9C16C2197C57851D]
            + Op.PUSH9[0xF1EE6FFF3C92E794D0]
            + Op.PUSH29[
                0xC6D2F5B964448FEE1C3F52921CD138BFE26F57A3CE26AE8E622C80FCFB
            ]
            + Op.PUSH32[
                0x414B5750048E67DD2C715BDF907A881EF7A77DC8B166B413EBB4261BDA628C26  # noqa: E501
            ]
            + Op.PUSH7[0x6D7EC3D2D20BDC]
            + Op.PUSH31[
                0x117960DA38D995574327FC1B63764875B839F395793A937B5F2793DB93B23B  # noqa: E501
            ]
            + Op.PUSH18[0x60BB44CF7BF515A85769D5F51851260F0739]
            + Op.PUSH10[0xB185817C3E5B65875394]
            + Op.PUSH32[
                0x6AE534B0E68AFA57A476FF52028737E7D342C1DDC7C5DC786FE6216838882C6F  # noqa: E501
            ]
            + Op.PUSH15[0x8519B16B2D9451EA2F048765576AF4]
            + Op.PUSH2[0xAAB4]
            + Op.PUSH3[0x31F6A]
            + Op.PUSH5[0xF0AE07FA9A]
            + Op.PUSH5[0xD4772252EB]
            + Op.SWAP15
            + Op.PUSH11[0xA14429A7E2A1D434826990]
            + Op.PUSH6[0xE44695FBEA17]
            + Op.PUSH14[0x63D01D22231D221B6F8DFDA47F51]
            + Op.PUSH5[0xA47454AB39]
            + Op.PUSH16[0x17257DDEC269F67ED7C6D17FFAC1C613]
            + Op.PUSH19[0xAAF587427EEE43772C5F28FDE9D395B65BF2D7]
            + Op.PUSH31[
                0x4EAA635BEA61396414A53508797E2506ED2F921F29BF2FDA1796F4396C4EDB  # noqa: E501
            ]
            + Op.PUSH16[0x6ECC6D79FD82D9838A512DF1454CE722]
            + Op.PUSH9[0xD8A32E0971C718B683]
            + Op.PUSH15[0x4BCB788766F266A3EDFDD24686274F]
            + Op.PUSH9[0x4C4B0A7FD708215976]
            + Op.PUSH16[0x4670A09A9E231BF61FE5F955A75B8870]
            + Op.PUSH21[0x4EC89C81940D46BE921C40917862E1C186679F354A]
            + Op.PUSH17[0x4FD5537CEB310616ACF9779C43C8F585C0]
            + Op.PUSH5[0xFAFA775D27]
            + Op.SWAP14
            + Op.CREATE(value=0x1E, offset=0x5FC16D, size=0xAEC380)
            + Op.PUSH8[0xEDDFFDF0F1359F38]
            + Op.PUSH10[0x70FE2EB95C063421601A]
            + Op.PUSH27[
                0x5F9256A6398651BE88998DEB83D16EDD603992A27F758BDA8C1BF9
            ]
            + Op.PUSH21[0xE49A52CF19C9BC32A79DB4778535677E3CAEAE7F2F]
            + Op.PUSH11[0xC54F147D2729C30D694BCB]
            + Op.PUSH3[0x2C1310]
            + Op.PUSH13[0x3382D4C27BC4EE55EADB4921D9]
            + Op.PUSH26[0x65E605BD3DAA1C233230119DCE876049813474DC4B3EC1D0EA8D]
            + Op.PUSH20[0xD182BEB19CD3C8F198578D863907A60FD633A658]
            + Op.PUSH19[0xD93E47DC134FC815D9800BAD3F2D58BB97B577]
            + Op.PUSH16[0x42800F1F182951BA5ACED03A7C3ABD85]
            + Op.SWAP10
            + Op.CODECOPY(
                dest_offset=0x2867293DBFE29B7346020EF70D18CACD7508CCB3731B,
                offset=0x10D13F07077,
                size=0x483189606297788FBF55,
            )
        ),
        nonce=0,
        address=Address("0xd18174aba5b877bd17dc67a4272d8a567cfa8925"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex(
            "387814bf0652a6f3aefce6ef7be00599328bbf7e802e1ea22644a96fbf319d273c0e7150"  # noqa: E501
            "67e4e5e74ecfc3ae60fd917b9224a4bbaa6db919506fc9e3cd4792dbecb1427e907653a3"  # noqa: E501
            "e359acf57c1e4afae77816fdc406706133e14efc6fe3ed1dc01f663f8e79c5fb6a32685e"  # noqa: E501
            "c748da76ab766d20766430b1775afa280f1c02e5617230d3b68fa16d4d73a1b27ae07b10"  # noqa: E501
            "96d44b02414374765d0907504a2f25e45aee4fdbb17b244e93714f36d9c035346d67ce3c"  # noqa: E501
            "18bf3d3af42f3b5f807689e8f429c0070a5812d602d25c4664cccfa7ddff8188f174c046"  # noqa: E501
            "eef00dcd5355c37d900a2ce940246fcaada0526acdd4eaf98a420bae34e22b37"
        ),
        gas_limit=100000,
        value=1928806571,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
