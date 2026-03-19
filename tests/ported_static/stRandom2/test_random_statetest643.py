"""
Return ~1 MB out of bounds of the init code. should throw codesize error...

Ported from:
tests/static/state_tests/stRandom2/randomStatetest643Filler.json
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
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stRandom2/randomStatetest643Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest643(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Return ~1 MB out of bounds of the init code. should throw..."""
    coinbase = Address("0x02a81f3b6340ef03047f2e09f2126aa8334233bd")
    sender = EOA(
        key=0x2C6BEC15D915620A88056CC6BFB70707AFA902ABD52C7DFEAB0864BE472CB8AF
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=35761922600709271,
    )

    pre[sender] = Account(balance=0xA015CDDAB7107B04)
    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=(
            Op.PUSH26[0xECFECF2AB84463F738FC85B069590FCFF0334FB1A7108861A444]
            + Op.SIGNEXTEND(
                0xF893A1A95C84AFBECC79E1EE4ACC8FCA826DF1AB268BDFD9E712AD0D261F5EDE,  # noqa: E501
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
                offset=0x75F1BF8A683B5D1721F7DD57755BD6A9BED9F874E3876CFCAC6762EA,  # noqa: E501
            )
        ),
        balance=0x3F91B25C1601534B,
        nonce=210,
        address=Address("0x6e40c70f8be9a7633e8a31580c85f275b86362ef"),  # noqa: E501
    )
    callee_1 = pre.deploy_contract(
        code=(
            Op.NUMBER
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
            )
        ),
        balance=0x262E8DE142312A2D,
        nonce=243,
        address=Address("0x971ab94b9c20484b37b157476a9f106f639779ed"),  # noqa: E501
    )

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "79ecfecf2ab84463f738fc85b069590fcff0334fb1a7108861a44465a26237bc83297ff893a1a95c84afbecc79e1ee4acc8fca826df1ab268bdfd9e712ad0d261f5ede0b6545e6a7d462826d39eb0ac5b4c3ef35f0b4e6d9e05f0773fc63be0c082847f6f9f7728764e142fcd95702c36d65c1e55ec0e2128768030e4eb0de74b57969caa2f2493998537ad0ecba9400ebae911dad6f98bd15da63a8614aa455dc593fa70386a260c66270f1d7527b75f1bf8a683b5d1721f7dd57755bd6a9bed9f874e3876cfcac6762ea51"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "436debc3912504eded08f73b9ff9490d73fc4f820a0890b7e8417fa97940713aeb870e59a790607f6b3d5649e57458ea8692da323253735967657e3fc6e02f6de1c0ff6cc18e051bdd52ad7b1eb441440620426b3485ab683d44ff8d5544eb7f7fb3e1f4c30063640b5a626f341b6271dd59621208476208431973971ab94b9c20484b37b157476a9f106f639779ed6338f86b9af4"  # noqa: E501
                    )
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(EXPECT_ENTRIES, 0, 0, 0, fork)

    tx = Transaction(
        sender=sender,
        to=None,
        data=bytes.fromhex(
            "620d15bc62074ac2f3789b4ff89d27fb5018b60a3730731819c16c8a1e6513c3c2703e63"  # noqa: E501
            "f82ce3617b9c5bdd435cc4e8eaffa5d05d45aef99b6726757bbe89b4ae0e5b9b6062855c"  # noqa: E501
            "2d525b6ca347c35412d0ab99dbc839a14f619a34621beef752635999fd987437da3edb75"  # noqa: E501
            "b58f986d9b62ffc1e6dae25c7e0c019f73922a0ab96d77aef70627e71d0a63d38d2d09af"  # noqa: E501
            "ec6a9f6dd36fff38e99a634e506f29060c4e3c3371d213d31078939857877d1780bc984b"  # noqa: E501
            "1ae1225b8dc7cc534cd080ba4b324f436d2c211b3c30889cf66d57b8f669c1be7711d782"  # noqa: E501
            "54d859636790551a4a0f6e0c06664680c8fadd1d7e7b3e887ea3cff5077d014551ed36a7"  # noqa: E501
            "2977742f6dcee4113c33297428527783529e675399ca43d5df7d9a4151fcac7093585bb8"  # noqa: E501
            "c6df7d6563faafe035226b81786f72b243bfdbc99e8fd67571df50e0ed7a8e1aaca76fcc"  # noqa: E501
            "65151e7730dee525a07c75d1b3855ae0bfbe0d79ff4905974c837e30a06fb163d89d"  # noqa: E501
        ),
        gas_limit=9840869,
        value=4042009829,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
