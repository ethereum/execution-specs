"""
Test_random_statetest178.

Ported from:
state_tests/stRandom/randomStatetest178Filler.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stRandom/randomStatetest178Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_random_statetest178(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest178."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    coinbase = pre.deploy_contract(
        code=Op.JUMPI(
            pc=0x9,
            condition=Op.ISZERO(Op.SLOAD(key=Op.CALLDATALOAD(offset=0x0))),
        )
        + Op.STOP
        + Op.JUMPDEST
        + Op.SSTORE(
            key=Op.CALLDATALOAD(offset=0x0), value=Op.CALLDATALOAD(offset=0x20)
        ),
        balance=46,
    )
    target = pre.deploy_contract(
        code=Op.CALLDATALOAD(
            offset=0x342BEABE599E4BC177FD97D36DF48D50650BA6129A9A83D4CF809EC21452  # noqa: E501
        )
        + Op.PUSH29[
            0x620167F530C3265BE9887F6E5B8186DECDC00A6A801E5F56DD8D9D36A4
        ]
        + Op.DUP1
        + Op.PUSH14[0xBCCC299E4BBF46AD577E25B5B1FC]
        + Op.PUSH23[0xB6999CB23A6A03C4035E36B8494135EE170647395DA00B]
        + Op.PUSH15[0xA64C43F3358B8BDCF593C89FB70B8]
        + Op.PUSH6[0xEF153B5195C7]
        + Op.PUSH26[0x59256BEB4F932095EB8AC80BC2C050F6F550A362AAC77F5C4B19]
        + Op.PUSH18[0x51DF039D64B77DCA22EB8FD4B8CF50FB85A3]
        + Op.PUSH16[0x1D909D1919A47FE97DE5526726B4A47B]
        + Op.DUP7
        + Op.LOG3(
            offset=0x6291,
            size=0x3E,
            topic_1=0x56FF5DD24A1F49E50B9F5924F473B2DC5306D67054CA575D0,
            topic_2=0xD9,
            topic_3=0x7B13471056439457CD7CBC50,
        )
        + Op.CALL(
            gas=0xE3319C8,
            address=Op.ADDRESS,
            value=0x38A57DDC,
            args_offset=0x1F,
            args_size=0x9,
            ret_offset=0x10,
            ret_size=0x14,
        )
        + Op.CALLER,
    )

    env = Environment(fee_recipient=coinbase, prev_randao=0x20000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(
            "66fd78520a4acd897a6e29cf1b15f576b05a2bc0c18bb93a759d3f5e1ac5d34ba1e261c70b7afd59945da98cc373eac6aa543bae2e6726e3ff03ad2e788dc33f3b736ef736637d8ac680281bb29884e641473063e58e7318f5f4cbade311c02eed1c323c19bba7df4729406464b42ed0cb6d0189be83857fb09713ae69e7d2d472e6d85d23920625c84c39489fc80d272868f40c64cc6cb93ea5741d1918dfc8f61086b1b0637390a1934b637c37ec94877d3ea763b20b9e04fa589f30da18f1565bcf15ad38bc735b9d45b5d963cadd77e9e3db27853e7462a6417a4ac9af38f967a198c6f50deb53634bcbbe9c6a83a7357847acc4f6360fa46e43595a8936969798890170a6874b4e67391c228e9d0a754f68635d505c3f9a8c2555728626e286db52177c2228fb04d4b702bea78df3747d6fa1079394222b8d2a0dfc34ce6d9e5664062fa8977526ced3516147e12a7b9e36f6628dd9efe320bef809146e8fad97d5aedf559bcc15442b1fd347758332cb1d4bb96471a01de009dc175e3eae40d189755a7c1f46c55d3353af6fd0ee638735594b4bb2e6aa99fdbc96508431f421dd770b6379f9b5cbee55423a23c5538390612dc07c752c39f1c87a02777b0fa261dd883d49b2ae5c02c6e81bd0a53ba5d53e12530485664f77811ffaca4c688d18d6122f3a564151676f40f70e45da4fe562355ba17d36458de5f760c8148a11b1fece135e184d2dbf9ecf019d634d8498ae6c6862431f356e1940bc7bb1a252ece1b1605e467f328c79bb45440e29a9444f1948f3737dc02ec2c10862323af3bae0db487768f3aa49fb0967d7eb138302bcb9cedb6b327f4d35a39cf561f1ee73c294825a5de76bd6bf707c5a660e3a417b6ac0586e80ecb6300ea61a618b628d8fcc6c80a37fbfda4e162006259f39441a81fd310c9a323be96b826199149ebdb88ea3e87df96d06c71959b65c4a3e73b50da0a67590625ad154729d9a0a585ba3fc028fc342115f2308566e69cd557f7a7a73474bae3846016f5281b41609a85ee1b4244652d5c1360c9d30fe27dd2d62b415d06a278aafd0816e734b76a3500869747b893809a7c2a185836da26ef253e0a0de429e617a82f8f17f055b1b67fe7366d9a5a491fb47f997937d38e7e8d4cbe8fa227c8b70f8a70e7b667883e393d677c86a9c8ec7144c61cf62e2403893"  # noqa: E501
        ),
        value=0x6F33BB2D,
    )

    post = {
        target: Account(storage={}, nonce=1),
        coinbase: Account(storage={}, nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
