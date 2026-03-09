"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stRandom2/randomStatetest458Filler.json
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
    ["tests/static/state_tests/stRandom2/randomStatetest458Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.pre_alloc_mutable
def test_random_statetest458(
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
    contract = pre.deploy_contract(
        code=(
            Op.PUSH23[0x89747FB3520231748BBE5EB9617666E630019E3E84CE71]
            + Op.PUSH26[0xC5D83B7E36050E5C05623956E599F54EB56213E4F96F69F402CD]
            + Op.PUSH20[0xE13C366095A3FE56BDD6A815D9BA23F3A9729BC4]
            + Op.PUSH3[0x385C69]
            + Op.PUSH31[
                0xD9F24192C949E33FF7ED256C84979D70148B8FD8A62438CA053DE264227145  # noqa: E501
            ]
            + Op.PUSH14[0xDE46CE78CF7C6D1D2CC48EEE658A]
            + Op.PUSH20[0xAD9F9CA1E550720490E2D0769E0A429773E42FC9]
            + Op.PUSH6[0xEA1030F6C078]
            + Op.PUSH28[
                0x4E7BC4915150A99FC758D3373561D8917C4C7D605F0CD8D2203F4D69
            ]
            + Op.PUSH1[0x61]
            + Op.SWAP9
            + Op.NUMBER
            + Op.PUSH21[0x29E2F2D2BF742B28760A9C0AB51203D0C5D5B9E16D]
            + Op.PUSH21[0xCE0428945AAFF2D0F99240A901D3233BD04E366C36]
            + Op.PUSH27[
                0xB93ECEA0C206FBF01084254636DF9C1F308C7D6875D5D5D37F3CE2
            ]
            + Op.PUSH26[0x89E39048F175F0D2DC49EAA86530DEF7AB70553F5D3904C843B5]
            + Op.PUSH20[0x6025E321E7E2AB92AF570E5B3BEF4014C54E6531]
            + Op.PUSH12[0xB546EB8906F155F7B9405326]
            + Op.PUSH21[0x104D8F5D98DC97AC374AD0C58F4385E086891B9B2]
            + Op.PUSH6[0x7E982EB15A36]
            + Op.PUSH31[
                0xAB6683B51EA9F219ABAE5CA39F669A1A88A82E14EFD4192A3EDBE04A12D356  # noqa: E501
            ]
            + Op.PUSH26[0xCF6338130D67F37C324464D16CC866BE846B0304EF9FD3C6611E]
            + Op.PUSH13[0xDF1277D65F6B2A58FFB61BA979]
            + Op.PUSH21[0xB8DF72816602071E979E6029C9307D718FFDC70F3]
            + Op.PUSH31[
                0xA0019353C06B0FB56D8E3738DFDB18418E952092E8625B51749F276CC6AE41  # noqa: E501
            ]
            + Op.PUSH11[0x85BD070C61E65240D8C271]
            + Op.SWAP13
            + Op.PUSH23[0xB0420F84ECE41C9BE0F93D4F30581C28F6976839516393]
            + Op.PUSH32[
                0x95B86DA30FA76B6937870245D9250E06B6E07DFFEA8F849A37647378DD59AC83  # noqa: E501
            ]
            + Op.PUSH6[0xA37DD908EEA2]
            + Op.PUSH12[0xE2F53375E1DBEE32ECAA7E95]
            + Op.PUSH31[
                0xACE8C6F0883E4EF830485BD43B2B7851A0B11497F752D3EE4560E312A7A91B  # noqa: E501
            ]
            + Op.PUSH28[
                0x2A88C109737C92FEB7807D481AC3FD823F038C4BA82DF40A60982A7C
            ]
            + Op.PUSH27[
                0x6F6BA2CB95233C257B30E1C9D3C84AA37B6F4268FEC34FB9EEF1F8
            ]
            + Op.PUSH1[0x2E]
            + Op.PUSH11[0x7BF1EBFA162680B57AF09F]
            + Op.PUSH27[
                0x7FC584055FF32D68A92E59DDAF20BCAAAA70D5970FD71C04CDBAB4
            ]
            + Op.PUSH13[0xF86E566E870664B6DF2C686134]
            + Op.PUSH28[
                0x2A3886788BBEBBD03CBB51ED29357F699C8B974C61528A0423F67A83
            ]
            + Op.PUSH28[
                0xFAB83AFA78A0BFF70A653EA0F398F73632D5E3BEA0A31115D65486FB
            ]
            + Op.PUSH14[0x667110448E0208264A3F76F35972]
            + Op.PUSH7[0x6E7AA7339F23B0]
            + Op.DUP15
            + Op.LOG0(offset=0x6337, size=0x28)
            + Op.CALLDATASIZE
            + Op.CALL(
                gas=0x5706352B,
                address=0x4F391713BDCA6E610DEA121DF82FF743D96D33B6,
                value=0xE6DB38E,
                args_offset=0xB,
                args_size=0x14,
                ret_offset=0x1D,
                ret_size=0x16,
            )
            + Op.PUSH10[0x5BB9E53D5AD3BA1191EA]
            + Op.PUSH6[0xAE1880D46C68]
            + Op.PUSH23[0x5148E427A09D40172DBDD5FC72FFFB1443080A39A0EE7]
            + Op.PUSH32[
                0xEED9DDC9050AFFCE41D68C34AD97C484F204A987BCFAF46B9FA4A9ED2DAD3738  # noqa: E501
            ]
            + Op.PUSH24[0x1A3CF86B43F303A8DB8CDE3ED8A40AE35574B9084F4CAB88]
            + Op.PUSH17[0x1D150E628D9B2A33E71C8F9FB0CE9E7286]
            + Op.PUSH3[0x576917]
            + Op.PUSH23[0xF999B7DDF64F22532351BD34743E08FACD1ACC94B0D6B5]
            + Op.PUSH12[0xF97491D5ED9D726AF684D1A4]
            + Op.PUSH27[
                0xBCB243B7C29D12A315E939F70AF8D2617DF63567C3BC56C16609A2
            ]
            + Op.PUSH25[0x71AF77631FE1CCAA0D15F8DA9BD9A712A544ABB92B925B1D75]
            + Op.PUSH2[0xFCED]
            + Op.PUSH1[0xB0]
            + Op.SWAP12
            + Op.PUSH12[0x22F2121B105A65A209E151B7]
            + Op.PUSH12[0x31BE481D57353D10A1D968CA]
            + Op.PUSH27[
                0x185495A8A2935571A0D17443A327BF11CB421BACA9064BC4E4497C
            ]
            + Op.PUSH30[
                0x4C486C40082CC2D01B3F6023B726DE95AC2AD53AE0B731D741676338181E
            ]
            + Op.PUSH7[0xC8AC8DAF0D5477]
            + Op.PUSH9[0x27987E79D9F617C51F]
            + Op.PUSH16[0x4B87CF8FEE734C99E5E3FC2E37F17E62]
            + Op.PUSH13[0xBFD1195157215D10FA39B4B094]
            + Op.PUSH29[
                0x3339139B280C0B042DA7EC93A24416D5C52E0BA21EC9D39D6FBCD3D742
            ]
            + Op.PUSH7[0x580EEF6CA9BB9D]
            + Op.PUSH23[0xBB4DC441F3D6D0CF38307B505251DEEA82AB39F9CCD17A]
            + Op.PUSH6[0x7BF16B38640]
            + Op.PUSH8[0x9C22F2134E8258F7]
            + Op.SWAP12
        ),
        nonce=0,
        address=Address("0x4f391713bdca6e610dea121df82ff743d96d33b6"),  # noqa: E501
    )
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

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex(
            "6cff89fd2305930f9a427748410969e86bfeabd7748df8c60e9075e32f95abb7b73e260f"  # noqa: E501
            "c345efb09ac919b22eb90402ff6b737a79722d83372adc70ef947e3a28e6dda50601f52f"  # noqa: E501
            "ea5b45a7294d90ea73bb64de313534dce604ebc4a22c7519bd1a15bc91aca303759ffdfc"  # noqa: E501
            "849b53ca82e03b1df66d1ede5b09b519084802396f8849817328c82f591c11d4b40c0653"  # noqa: E501
            "e1ec91398ca9a1a6b872165aac3c0567020253bc3f5221edb93cbbd87c7486136d4f5649"  # noqa: E501
            "a5f1ad8808013f373cbffc6c40c8707f2e0449a9ce33beba84b4974ed62803f8dd900ba3"  # noqa: E501
            "b47d3cc55ba503f903701f1188"
        ),
        gas_limit=1630523086,
        value=2131886598,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
