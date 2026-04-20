"""
Return ~1 MB out of bounds of the init code. should throw codesize...

Ported from:
state_tests/stRandom2/randomStatetest643Filler.json
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
    ["state_tests/stRandom2/randomStatetest643Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest643(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Return ~1 MB out of bounds of the init code."""
    sender = EOA(
        key=0x2C6BEC15D915620A88056CC6BFB70707AFA902ABD52C7DFEAB0864BE472CB8AF
    )

    env = Environment(
        fee_recipient=sender,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
    )

    # Source: raw
    # 0x79ecfecf2ab84463f738fc85b069590fcff0334fb1a7108861a44465a26237bc83297ff893a1a95c84afbecc79e1ee4acc8fca826df1ab268bdfd9e712ad0d261f5ede0b6545e6a7d462826d39eb0ac5b4c3ef35f0b4e6d9e05f0773fc63be0c082847f6f9f7728764e142fcd95702c36d65c1e55ec0e2128768030e4eb0de74b57969caa2f2493998537ad0ecba9400ebae911dad6f98bd15da63a8614aa455dc593fa70386a260c66270f1d7527b75f1bf8a683b5d1721f7dd57755bd6a9bed9f874e3876cfcac6762ea51  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH26[0xECFECF2AB84463F738FC85B069590FCFF0334FB1A7108861A444]
        + Op.SIGNEXTEND(
            0xF893A1A95C84AFBECC79E1EE4ACC8FCA826DF1AB268BDFD9E712AD0D261F5EDE,
            0xA26237BC8329,
        )
        + Op.SMOD(0x39EB0AC5B4C3EF35F0B4E6D9E05F, 0x45E6A7D46282)
        + Op.LOG2(
            offset=0x98BD15DA63A8614AA455DC593FA70386,
            size=0xB57969CAA2F2493998537AD0ECBA9400EBAE911DAD,
            topic_1=0x65C1E55EC0E2128768030E4EB0DE,
            topic_2=0xFC63BE0C082847F6F9F7728764E142FCD95702C3,
        )
        + Op.MSTORE(offset=0x70F1D7, value=0xC6)
        + Op.MLOAD(
            offset=0x75F1BF8A683B5D1721F7DD57755BD6A9BED9F874E3876CFCAC6762EA
        ),
        balance=0x3F91B25C1601534B,
        nonce=210,
        address=Address(0x6E40C70F8BE9A7633E8A31580C85F275B86362EF),  # noqa: E501
    )
    pre[sender] = Account(balance=0xA015CDDAB7107B04)
    # Source: raw
    # 0x436debc3912504eded08f73b9ff9490d73fc4f820a0890b7e8417fa97940713aeb870e59a790607f6b3d5649e57458ea8692da323253735967657e3fc6e02f6de1c0ff6cc18e051bdd52ad7b1eb441440620426b3485ab683d44ff8d5544eb7f7fb3e1f4c30063640b5a626f341b6271dd59621208476208431973<contract:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b>6338f86b9af4  # noqa: E501
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.NUMBER
        + Op.PUSH14[0xEBC3912504EDED08F73B9FF9490D]
        + Op.PUSH20[0xFC4F820A0890B7E8417FA97940713AEB870E59A7]
        + Op.SWAP1
        + Op.MSTORE8(offset=0x3D5649E57458EA8692DA3232, value=0x7F)
        + Op.SIGNEXTEND(
            0x1EB441440620426B3485AB683D44FF8D5544EB7F7FB3E1F4C3006364,
            0x5967657E3FC6E02F6DE1C0FF6CC18E051BDD52AD,
        )
        + Op.GAS
        + Op.DELEGATECALL(
            gas=0x38F86B9A,
            address=0x971AB94B9C20484B37B157476A9F106F639779ED,
            args_offset=0x84319,
            args_size=0x120847,
            ret_offset=0x71DD59,
            ret_size=0x6F341B,
        ),
        balance=0x262E8DE142312A2D,
        nonce=243,
        address=Address(0x971AB94B9C20484B37B157476A9F106F639779ED),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=None,
        data=Op.RETURN(offset=0x74AC2, size=0xD15BC)
        + Op.PUSH25[0x9B4FF89D27FB5018B60A3730731819C16C8A1E6513C3C2703E]
        + Op.PUSH4[0xF82CE361]
        + Op.MSTORE(
            offset=0x855C2D,
            value=0x9C5BDD435CC4E8EAFFA5D05D45AEF99B6726757BBE89B4AE0E5B9B60,
        )
        + Op.JUMPDEST
        + Op.PUSH13[0xA347C35412D0AB99DBC839A14F]
        + Op.MSTORE(offset=0x1BEEF7, value=0x9A34)
        + Op.PUSH4[0x5999FD98]
        + Op.PUSH21[0x37DA3EDB75B58F986D9B62FFC1E6DAE25C7E0C019F]
        + Op.PUSH20[0x922A0AB96D77AEF70627E71D0A63D38D2D09AFEC]
        + Op.PUSH11[0x9F6DD36FFF38E99A634E50]
        + Op.PUSH16[0x29060C4E3C3371D213D3107893985787]
        + Op.PUSH30[
            0x1780BC984B1AE1225B8DC7CC534CD080BA4B324F436D2C211B3C30889CF6
        ]
        + Op.PUSH14[0x57B8F669C1BE7711D78254D85963]
        + Op.PUSH8[0x90551A4A0F6E0C06]
        + Op.PUSH7[0x4680C8FADD1D7E]
        + Op.PUSH28[0x3E887EA3CFF5077D014551ED36A72977742F6DCEE4113C3329742852]
        + Op.PUSH24[0x83529E675399CA43D5DF7D9A4151FCAC7093585BB8C6DF7D]
        + Op.PUSH6[0x63FAAFE03522]
        + Op.PUSH12[0x81786F72B243BFDBC99E8FD6]
        + Op.PUSH22[0x71DF50E0ED7A8E1AACA76FCC65151E7730DEE525A07C]
        + Op.PUSH22[0xD1B3855AE0BFBE0D79FF4905974C837E30A06FB163D8]
        + Op.SWAP14,
        gas_limit=9840869,
        value=0xF0EC2CE5,
    )

    post = {
        addr: Account(storage={}, nonce=210),
        sender: Account(storage={}, code=b"", nonce=1),
        addr_2: Account(storage={}, nonce=243),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
