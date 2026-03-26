"""
test_random_statetest184

Ported from:
state_tests/stRandom/randomStatetest184Filler.json
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
    ["state_tests/stRandom/randomStatetest184Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest184(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_random_statetest184"""
    coinbase = Address("0x6d6e40885310545835a5b582dbc23ef026404bda")
    addr_0x945304eb96065b2a98b57a48a06ae28d285a71b5 = Address("0xf377657e450772b703a269e12bb487ff421a5c6d")  # noqa: E501
    sender = EOA(
        key=0x382acd382cc7a37bb6a57c4a171f216ef77ef04ebd5e6c0744ee5c90b0d962ef
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=10000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=69449279085,
    )

    # Source: raw
    # 0x6f823a02877cef7c1afb60663009def564608c557bad2ae05769b991313726edbfa0881d9cc955b0f5154751da315696ea7ce130184b64f2507582c502d450349ff24fb8aeb2a46146687b666bd7bd0364946cb720c76d483f5afea0049251fd9793c4b0376afbb4ebcdc42fdd42edcd4b619cec787638009cea26a1abe570e3186ab790b7dc7db36e4cda2570b0847adf6e39579c7c43a4ac976cd507d493cdfaebe09936078e31c71c4665d34a4b816b8004
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x8c, value=0x823a02877cef7c1afb60663009def564)
        + Op.SUB(0xe130184b64f2507582c502d450349ff24fb8aeb2a46146687b666bd7bd, 0xad2ae05769b991313726edbfa0881d9cc955b0f5154751da315696ea)
        + Op.PUSH5[0x946cb720c7] + Op.PUSH14[0x483f5afea0049251fd9793c4b037]
        + Op.PUSH11[0xfbb4ebcdc42fdd42edcd4b] + Op.PUSH2[0x9cec]
        + Op.PUSH25[0x7638009cea26a1abe570e3186ab790b7dc7db36e4cda2570b0]
        + Op.DUP5
        + Op.DIV(0xd34a4b816b80, 0xdf6e39579c7c43a4ac976cd507d493cdfaebe09936078e31c71c46),
        balance=0x70a217c02c8f2d4,
        nonce=117,
        address=Address("0x898207f2d9b9fb11cec9647a70e9390711732daa"),  # noqa: E501
    )
    pre[addr_0x945304eb96065b2a98b57a48a06ae28d285a71b5] = Account(balance=0x9740421ff0ff3ae3, nonce=29)
    pre[sender] = Account(balance=0x10c1142f2b8e8eb058)


    tx = Transaction(
        sender=sender,
        to=target,
        data=bytes.fromhex("64dd3e4e84676723342c1dfaf9af4ef3"),
        gas_limit=100000,
        value=0x6d1dd024,
        nonce=0,
        gas_price=28,
    )

    post = {
        target: Account(
                storage={140: 0x823a02877cef7c1afb60663009def564},
                nonce=117,
            ),
        addr_0x945304eb96065b2a98b57a48a06ae28d285a71b5: Account(storage={}, code=b"", nonce=29),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
