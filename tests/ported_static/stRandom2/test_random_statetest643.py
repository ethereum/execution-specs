"""
Return ~1 MB out of bounds of the init code. should throw codesize error after EIP158 and create empty account before EIP158

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
        key=0x2c6bec15d915620a88056cc6bfb70707afa902abd52c7dfeab0864be472cb8af
    )

    env = Environment(
        fee_recipient=sender,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=35761922600709271,
    )

    # Source: raw
    # 0x79ecfecf2ab84463f738fc85b069590fcff0334fb1a7108861a44465a26237bc83297ff893a1a95c84afbecc79e1ee4acc8fca826df1ab268bdfd9e712ad0d261f5ede0b6545e6a7d462826d39eb0ac5b4c3ef35f0b4e6d9e05f0773fc63be0c082847f6f9f7728764e142fcd95702c36d65c1e55ec0e2128768030e4eb0de74b57969caa2f2493998537ad0ecba9400ebae911dad6f98bd15da63a8614aa455dc593fa70386a260c66270f1d7527b75f1bf8a683b5d1721f7dd57755bd6a9bed9f874e3876cfcac6762ea51
    addr_0x1000000000000000000000000000000000000000 = pre.deploy_contract(
        code=Op.PUSH26[0xecfecf2ab84463f738fc85b069590fcff0334fb1a7108861a444]
        + Op.SIGNEXTEND(0xf893a1a95c84afbecc79e1ee4acc8fca826df1ab268bdfd9e712ad0d261f5ede, 0xa26237bc8329)
        + Op.SMOD(0x39eb0ac5b4c3ef35f0b4e6d9e05f, 0x45e6a7d46282)
        + Op.LOG2(offset=0x98bd15da63a8614aa455dc593fa70386, size=0xb57969caa2f2493998537ad0ecba9400ebae911dad, topic_1=0x65c1e55ec0e2128768030e4eb0de, topic_2=0xfc63be0c082847f6f9f7728764e142fcd95702c3)
        + Op.MSTORE(offset=0x70f1d7, value=0xc6)
        + Op.MLOAD(offset=0x75f1bf8a683b5d1721f7dd57755bd6a9bed9f874e3876cfcac6762ea),
        balance=0x3f91b25c1601534b,
        nonce=210,
        address=Address("0x6e40c70f8be9a7633e8a31580c85f275b86362ef"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xa015cddab7107b04)
    # Source: raw
    # 0x436debc3912504eded08f73b9ff9490d73fc4f820a0890b7e8417fa97940713aeb870e59a790607f6b3d5649e57458ea8692da323253735967657e3fc6e02f6de1c0ff6cc18e051bdd52ad7b1eb441440620426b3485ab683d44ff8d5544eb7f7fb3e1f4c30063640b5a626f341b6271dd59621208476208431973<contract:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b>6338f86b9af4
    addr_0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b = pre.deploy_contract(
        code=Op.NUMBER + Op.PUSH14[0xebc3912504eded08f73b9ff9490d]
        + Op.PUSH20[0xfc4f820a0890b7e8417fa97940713aeb870e59a7] + Op.SWAP1
        + Op.MSTORE8(offset=0x3d5649e57458ea8692da3232, value=0x7f)
        + Op.SIGNEXTEND(0x1eb441440620426b3485ab683d44ff8d5544eb7f7fb3e1f4c3006364, 0x5967657e3fc6e02f6de1c0ff6cc18e051bdd52ad)
        + Op.GAS
        + Op.DELEGATECALL(gas=0x38f86b9a, address=0x971ab94b9c20484b37b157476a9f106f639779ed, args_offset=0x84319, args_size=0x120847, ret_offset=0x71dd59, ret_size=0x6f341b),
        balance=0x262e8de142312a2d,
        nonce=243,
        address=Address("0x971ab94b9c20484b37b157476a9f106f639779ed"),  # noqa: E501
    )


    tx = Transaction(
        sender=sender,
        to=None,
        data=bytes.fromhex("620d15bc62074ac2f3789b4ff89d27fb5018b60a3730731819c16c8a1e6513c3c2703e63f82ce3617b9c5bdd435cc4e8eaffa5d05d45aef99b6726757bbe89b4ae0e5b9b6062855c2d525b6ca347c35412d0ab99dbc839a14f619a34621beef752635999fd987437da3edb75b58f986d9b62ffc1e6dae25c7e0c019f73922a0ab96d77aef70627e71d0a63d38d2d09afec6a9f6dd36fff38e99a634e506f29060c4e3c3371d213d31078939857877d1780bc984b1ae1225b8dc7cc534cd080ba4b324f436d2c211b3c30889cf66d57b8f669c1be7711d78254d859636790551a4a0f6e0c06664680c8fadd1d7e7b3e887ea3cff5077d014551ed36a72977742f6dcee4113c33297428527783529e675399ca43d5df7d9a4151fcac7093585bb8c6df7d6563faafe035226b81786f72b243bfdbc99e8fd67571df50e0ed7a8e1aaca76fcc65151e7730dee525a07c75d1b3855ae0bfbe0d79ff4905974c837e30a06fb163d89d"),  # noqa: E501
        gas_limit=9840869,
        value=0xf0ec2ce5,
        nonce=0,
        gas_price=10,
    )

    post = {
        addr_0x1000000000000000000000000000000000000000: Account(storage={}, nonce=210),
        sender: Account(storage={}, code=b"", nonce=1),
        addr_0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b: Account(storage={}, nonce=243),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
