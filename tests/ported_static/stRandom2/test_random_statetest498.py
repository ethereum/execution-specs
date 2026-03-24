"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stRandom2/randomStatetest498Filler.json
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
    ["tests/static/state_tests/stRandom2/randomStatetest498Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.pre_alloc_mutable
def test_random_statetest498(
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

    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=(
            Op.ISZERO(0xD243DBCFDC6982733E4CD626)
            + Op.PUSH21[0xFC6CDEC93282FF50EF24D8BE05D58BE29301DDB00D]
            + Op.PUSH22[0x47F6B65997E73D232B76D6484C11EB15C87B01F89E27]
            + Op.PUSH26[0xC427711BA193E4E163967EFD1B9315187C3227F67B9282FC7524]
            + Op.PUSH10[0x2FBF851CB370D396D53F]
            + Op.PUSH27[
                0x86353AACECC5C1EADEDDBB3925522F935FC5ED03568FBF40261C05
            ]
            + Op.PUSH11[0x124F1334CC9FA8EEA2BDBF]
            + Op.PUSH9[0xF04C10CC08B6BABCBB]
            + Op.PUSH15[0xE8D3FB88DD42D06D445B5EAB34CB5D]
            + Op.PUSH5[0x408CF652FD]
            + Op.PUSH22[0x68ACAA81B573F66FA8781E83185438E42796631AE9A9]
            + Op.SWAP9
            + Op.LOG4(
                offset=0xB52EFE,
                size=0xF1,
                topic_1=0x85A2C56B21A53C0E612AE0A8D78D,
                topic_2=0x9A5213C33778AF679417D77733645F87B6042BE92C553DBB,
                topic_3=0x6F9F495B0AC9E37FBE5F23014C68D8D032BFAE,
                topic_4=0x714D986F94FC6354921A9367BB6B9E555F24107CB814557F8BD87547AD612C3E,  # noqa: E501
            )
            + Op.SSTORE(
                key=0x94198CDB286CD2F21F06659320130750E7AA2C83CEB28015,
                value=0xEBB0472B3E,
            )
            + Op.PUSH25[0x5C9F02455252560846587006E90CBFFC955445D9EF1F55EEB0]
            + Op.PUSH17[0x11C02CEE02DF12DC35B36702539873E4B7]
            + Op.PUSH7[0xE4AE9E829A4424]
            + Op.PUSH1[0xDD]
            + Op.PUSH32[
                0x845CD37DC08F93BEF98A4D5B53ECD4CF4DD1A5C416F92116160F0FB673C30B78  # noqa: E501
            ]
            + Op.PUSH20[0xB85A2FF6331A5D371F3D109F5794D712E03493B1]
            + Op.PUSH32[
                0xC562AC7589411127E654CE32D273F8300CC8544E7BD782AA7828B543958DADF8  # noqa: E501
            ]
            + Op.PUSH19[0xD7F13401A51B13835CC8A36BE87CC7347CDF0F]
            + Op.PUSH27[
                0xA2DF420BB03E925C117D4BEFBC7E69472FD75F01F3F6C966DE8181
            ]
            + Op.PUSH21[0xABA3B7A43014C3DD39414FB3D239D72E06852AE48E]
            + Op.PUSH3[0x3C60A]
            + Op.PUSH31[
                0x844D6FD61C5B519D43780D383D103989F9BFCE5ED122804CBA183C188F5CE4  # noqa: E501
            ]
            + Op.PUSH29[
                0x348A96973ECA904F096AED4FB77D40CA9139447527F267A028EAE5E370
            ]
            + Op.PUSH15[0x1975FC3E38327505E81D0E8C9FAB1F]
            + Op.PUSH1[0xEC]
            + Op.PUSH31[
                0xCE71CC87510F308984EBDCB8AB84E1905DFDC0A19EE3C5F37E88DC3A9F2649  # noqa: E501
            ]
            + Op.PUSH29[
                0x51427DA28F6D777D9585B4EC790722BACAA179B1DC5B086D945623F9D2
            ]
            + Op.SWAP16
            + Op.CALL(
                gas=0x1AC754FA,
                address=0x1A819DD2E8CEC87D7E886DF4843E21775F6672A4,
                value=0x4F4421EB,
                args_offset=0x19,
                args_size=0x9,
                ret_offset=0xC,
                ret_size=0x13,
            )
            + Op.PUSH22[0x6F9CC63229E7FE309B7A2F1ACF074A43AA4DD2B75BF]
            + Op.PUSH14[0xADF21AADB9A3E239A9592F576C92]
            + Op.PUSH6[0xEEBD2420E262]
            + Op.PUSH14[0x2B2F1F7EE7A56725D7D4FE23DA45]
            + Op.PUSH19[0x5E8B709D2976703147EF66A8FC9A6C1225DF7B]
            + Op.PUSH26[0xEEC95DDDA5E91C6E19BBC55BAF9D6C440CC805F0D229738D17A7]
            + Op.PUSH16[0x95E329F94D5BC48CC5964933F9597FB5]
            + Op.PUSH27[
                0x6F7290649722D68A72FA2D081C4547943B3BBCA2EDC5F4032C5C91
            ]
            + Op.PUSH15[0x585FA6ABD1B209E2B6FB64498A37B9]
            + Op.PUSH26[0x6C95DA3FDB8013C13EF99ED49B29282AE55458C651FDB8598B52]
            + Op.PUSH17[0x24D2DA1E8A7015F65EE4AB0178B68AB8C8]
            + Op.PUSH24[0xD55F3C89A7F1F7BC6C0D86BC69688CBCC252972693993BF7]
            + Op.PUSH7[0xAAC4EFB2B65B21]
            + Op.PUSH13[0xCA2E721DEA3F3B3DF3ABBBFB7B]
            + Op.DUP14
        ),
        nonce=0,
        address=Address("0x1a819dd2e8cec87d7e886df4843e21775f6672a4"),  # noqa: E501
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

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex(
            "7349d4fb4fa5c26263087f9f9885a7033ed1f85282806175626c7aff6e85d032f987501c"  # noqa: E501
            "7f07e672602eea9a752c14f2fea044cbadb4acbbbece186bfae0ddfa5c3a4f602e867451"  # noqa: E501
            "6e7ead3a1b9f0c321f53474588f38a996f7512fbdf364372a2f5b5329a5866cb8867c095"  # noqa: E501
            "26eabd04524486650cba94b9d20e8079263be537932206f67f64915b81ac1ea4b1f3723b"  # noqa: E501
            "aa86b2d9ad667f11ff36b05f0ec27d14051ce250c5c524eaa31472f153582c9aafa7a0b3"  # noqa: E501
            "17230863944f1b5e7444ad06685190a6f9ff72b7af0f52a4619591d022037c3bd19aa01d"  # noqa: E501
            "358a540c4ec6e43870dc653bab5c707f953b919477ed89448472e11b10e241ad82a32be0"  # noqa: E501
            "2adf21cd183ae47f2776bce3701b75afea9a175cd04e616f3a1913f3be49294c5e633b4d"  # noqa: E501
            "01cf719e06325d1f498e74d5a153c41ba83f49339f6d7f4711edfa5370e2ee9c7986401c"  # noqa: E501
            "6b27b5cb4f46435c84c8f0239876415740df4646423c790ce1917c3e178e3f0117f07b8a"  # noqa: E501
            "e37a6353868f7ca9313379cd727ae9732fb0a56da2b8a4cb682eb38ca47df0353f6b9322"  # noqa: E501
            "ac474740ac5b14488677765f48677e720ed20e2c76b94ca77acdd3e9e54f2230a0c2d120"  # noqa: E501
            "3130ebbf95aeb6212d52393d33efa63f79c2feba7168b770a3cd3fa97b8b515fd38a1995"  # noqa: E501
            "8fccde6ec198be7d2f780422a69c9047ab7474d8f1c3272b9836bca4050a856a916e9bb3"  # noqa: E501
            "0724727d1ba26058199098d65ad54d5580e51dcb2bd077db415b0ff41457c68f61d0f86d"  # noqa: E501
            "8c4c549388abf78a75cc9163016c7e988e60e97b95f1d253b52168cbb01407c8ebca87f9"  # noqa: E501
            "50ca4049e12ac76cbe3e374065a3c7703bcd5f7af279a1c12425c93ef8e74a12b699f4a9"  # noqa: E501
            "c651db15561be1d91ca95575636dad39636bea70b5309b3354a73bb1b83ba72ff63f6918"  # noqa: E501
            "2888e8f17d3e1ec0367173eb3831614e653fc63989af65bc9b676645638915ede2603666"  # noqa: E501
            "ccff0c03af0fda7ad7b7e846076158daad3df7ad07e1cfe8ce41757c4d77f02d65bee264"  # noqa: E501
            "fe0a98374a61532e797167af5719a427a267234fa27697f1a3f47a1453ea150821da1c66"  # noqa: E501
            "5de7878ac0e5e26fc78911427cc1d8d0b029ee09bf9322446635d50de718ecb79f"  # noqa: E501
        ),
        gas_limit=824267821,
        value=1958828689,
    )

    post = {
        contract: Account(
            storage={
                0x94198CDB286CD2F21F06659320130750E7AA2C83CEB28015: 0xEBB0472B3E,  # noqa: E501
            },
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
