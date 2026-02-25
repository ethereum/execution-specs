"""
Return ~1 MB out of bounds of the init code. should throw codesize error after EIP158 and create empty account before EIP158

Ported from:
tests/static/state_tests/stRandom2/randomStatetest643Filler.json

contract code:
    push26 0xecfecf2ab84463f738fc85b069590fcff0334fb1a7108861a444
    push6 0xa26237bc8329
    push32 0xf893a1a95c84afbecc79e1ee4acc8fca826df1ab268bdfd9e712ad0d261f5ede
    signextend
    push6 0x45e6a7d46282
    push14 0x39eb0ac5b4c3ef35f0b4e6d9e05f
    smod
    push20 0xfc63be0c082847f6f9f7728764e142fcd95702c3
    push14 0x65c1e55ec0e2128768030e4eb0de
    push21 0xb57969caa2f2493998537ad0ecba9400ebae911dad
    push16 0x98bd15da63a8614aa455dc593fa70386
    log2
    push1 0xc6
    push3 0x70f1d7
    mstore
    push28 0x75f1bf8a683b5d1721f7dd57755bd6a9bed9f874e3876cfcac6762ea
    mload

callee_1 code:
    number
    push14 0xebc3912504eded08f73b9ff9490d
    push20 0xfc4f820a0890b7e8417fa97940713aeb870e59a7
    swap1
    push1 0x7f
    push12 0x3d5649e57458ea8692da3232
    mstore8
    push20 0x5967657e3fc6e02f6de1c0ff6cc18e051bdd52ad
    push28 0x1eb441440620426b3485ab683d44ff8d5544eb7f7fb3e1f4c3006364
    signextend
    gas
    push3 0x6f341b
    push3 0x71dd59
    push3 0x120847
    push3 0x084319
    push20 0x971ab94b9c20484b37b157476a9f106f639779ed
    push4 0x38f86b9a
    delegatecall
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
) -> None:
    """Return ~1 MB out of bounds of the init code. should throw codesize error after EIP158 and create empty account before EIP158."""
    coinbase = Address("0x02a81f3b6340ef03047f2e09f2126aa8334233bd")
    sender = Address("0x02a81f3b6340ef03047f2e09f2126aa8334233bd")
    contract = Address("0x6e40c70f8be9a7633e8a31580c85f275b86362ef")
    callee_1 = Address("0x971ab94b9c20484b37b157476a9f106f639779ed")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=35761922600709271,
    )

    pre[sender] = Account(balance=0xa015cddab7107b04, nonce=0)
    pre[contract] = Account(
        balance=0x3f91b25c1601534b,
        nonce=210,
        code=(
        Op.PUSH26[0xecfecf2ab84463f738fc85b069590fcff0334fb1a7108861a444]
        + Op.PUSH6[0xa26237bc8329]
        + Op.PUSH32[0xf893a1a95c84afbecc79e1ee4acc8fca826df1ab268bdfd9e712ad0d261f5ede]
        + Op.SIGNEXTEND + Op.PUSH6[0x45e6a7d46282]
        + Op.PUSH14[0x39eb0ac5b4c3ef35f0b4e6d9e05f] + Op.SMOD
        + Op.PUSH20[0xfc63be0c082847f6f9f7728764e142fcd95702c3]
        + Op.PUSH14[0x65c1e55ec0e2128768030e4eb0de]
        + Op.PUSH21[0xb57969caa2f2493998537ad0ecba9400ebae911dad]
        + Op.PUSH16[0x98bd15da63a8614aa455dc593fa70386] + Op.LOG2 + Op.PUSH1[0xc6]
        + Op.PUSH3[0x70f1d7] + Op.MSTORE
        + Op.PUSH28[0x75f1bf8a683b5d1721f7dd57755bd6a9bed9f874e3876cfcac6762ea]
        + Op.MLOAD
    ),
    )
    pre[callee_1] = Account(
        balance=0x262e8de142312a2d,
        nonce=243,
        code=(
        Op.NUMBER + Op.PUSH14[0xebc3912504eded08f73b9ff9490d]
        + Op.PUSH20[0xfc4f820a0890b7e8417fa97940713aeb870e59a7] + Op.SWAP1
        + Op.PUSH1[0x7f] + Op.PUSH12[0x3d5649e57458ea8692da3232] + Op.MSTORE8
        + Op.PUSH20[0x5967657e3fc6e02f6de1c0ff6cc18e051bdd52ad]
        + Op.PUSH28[0x1eb441440620426b3485ab683d44ff8d5544eb7f7fb3e1f4c3006364]
        + Op.SIGNEXTEND + Op.GAS + Op.PUSH3[0x6f341b] + Op.PUSH3[0x71dd59]
        + Op.PUSH3[0x120847] + Op.PUSH3[0x84319]
        + Op.PUSH20[0x971ab94b9c20484b37b157476a9f106f639779ed] + Op.PUSH4[0x38f86b9a]
        + Op.DELEGATECALL
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0x2c6bec15d915620a88056cc6bfb70707afa902abd52c7dfeab0864be472cb8af"
        ),
        to=None,
        data=bytes.fromhex(
            "620d15bc62074ac2f3789b4ff89d27fb5018b60a3730731819c16c8a1e6513c3c2703e63"
            "f82ce3617b9c5bdd435cc4e8eaffa5d05d45aef99b6726757bbe89b4ae0e5b9b6062855c"
            "2d525b6ca347c35412d0ab99dbc839a14f619a34621beef752635999fd987437da3edb75"
            "b58f986d9b62ffc1e6dae25c7e0c019f73922a0ab96d77aef70627e71d0a63d38d2d09af"
            "ec6a9f6dd36fff38e99a634e506f29060c4e3c3371d213d31078939857877d1780bc984b"
            "1ae1225b8dc7cc534cd080ba4b324f436d2c211b3c30889cf66d57b8f669c1be7711d782"
            "54d859636790551a4a0f6e0c06664680c8fadd1d7e7b3e887ea3cff5077d014551ed36a7"
            "2977742f6dcee4113c33297428527783529e675399ca43d5df7d9a4151fcac7093585bb8"
            "c6df7d6563faafe035226b81786f72b243bfdbc99e8fd67571df50e0ed7a8e1aaca76fcc"
            "65151e7730dee525a07c75d1b3855ae0bfbe0d79ff4905974c837e30a06fb163d89d"
        ),
        gas_limit=9840869,
        gas_price=10,
        nonce=0,
        value=4042009829,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
