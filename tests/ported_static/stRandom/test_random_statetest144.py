"""
test_random_statetest144

Ported from:
state_tests/stRandom/randomStatetest144Filler.json
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
    ["state_tests/stRandom/randomStatetest144Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest144(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_random_statetest144"""
    coinbase = Address("0xb0085a57673c8f7d78fb870418f622e42fd686e4")
    addr_0x945304eb96065b2a98b57a48a06ae28d285a71b5 = Address("0x19bcdbcd094c63df253c825b4b8e6dffc45c21a4")  # noqa: E501
    sender = EOA(
        key=0x102da5c19454baf64e4f417e04ac2551245f3f217ffe9197f0c1d80fc2b16cff
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=1545160903,
    )

    # Source: raw
    # 0x621da82575e942e4fd977abdb407069cf700116e02b4f9b25d866b6d13163fff2b8ef03cf8ab5d662afb7bb5c9e68462741090bc0976c9705b40411efe39e80c20b572c5e3d75f788f9be2f0981672b8de37f9e2d1515046cb77cc3ee74646fb096eadce98908499b6fd54725f3c6a725968761ba50494d1ecaf1e787db9a052952427c4f271c28d3e25728b2b76439a3166cd0ed37f30ec2421ed38ebd3b00b89ba9208391dc274e4eefa69161a37dfff7111756dd7971065f05aa9de4867609e7d847a290d0eeb08cde2ff294ae11dd16f8a3e32494d943fa0622cc04cd7476b6d2a1008e4ad1e2c33e2928e707c797f2a1a586bbf78658189bf58172ff77130be2ffc9bbf7f171939be260b30eb65b46a6cf107be1c9ed5c92c99d69fe0559389600e6013601c60096016601260016001600c6017016d200351654b9773409608aaa7db1f67b518d025727bdc6e0463b2bc334b658536d84dadc47a2288da62c36b9a35bf8934e3781a4c44e91637ce5c6b2f916d76706529d728b6f5ee076013601e601960086005601c6013601d96423568ce21a850c04a77ceb9
    target = pre.deploy_contract(
        code=Op.PUSH3[0x1da825]
        + Op.PUSH22[0xe942e4fd977abdb407069cf700116e02b4f9b25d866b]
        + Op.PUSH14[0x13163fff2b8ef03cf8ab5d662afb]
        + Op.PUSH28[0xb5c9e68462741090bc0976c9705b40411efe39e80c20b572c5e3d75f]
        + Op.PUSH25[0x8f9be2f0981672b8de37f9e2d1515046cb77cc3ee74646fb09]
        + Op.PUSH15[0xadce98908499b6fd54725f3c6a7259]
        + Op.PUSH9[0x761ba50494d1ecaf1e]
        + Op.PUSH25[0x7db9a052952427c4f271c28d3e25728b2b76439a3166cd0ed3]
        + Op.PUSH32[0x30ec2421ed38ebd3b00b89ba9208391dc274e4eefa69161a37dfff7111756dd7]
        + Op.SWAP8 + Op.LT + Op.PUSH6[0xf05aa9de4867] + Op.PUSH1[0x9e]
        + Op.PUSH30[0x847a290d0eeb08cde2ff294ae11dd16f8a3e32494d943fa0622cc04cd747]
        + Op.PUSH12[0x6d2a1008e4ad1e2c33e2928e]
        + Op.PUSH17[0x7c797f2a1a586bbf78658189bf58172ff7]
        + Op.PUSH18[0x30be2ffc9bbf7f171939be260b30eb65b46a]
        + Op.PUSH13[0xf107be1c9ed5c92c99d69fe055] + Op.SWAP4 + Op.DUP10
        + Op.PUSH1[0xe] + Op.PUSH1[0x13] + Op.PUSH1[0x1c] + Op.PUSH1[0x9]
        + Op.PUSH1[0x16] + Op.PUSH1[0x12] + Op.PUSH1[0x1] * 2 + Op.ADD(0x17, 0xc)
        + Op.DIV(0xb518d025727bdc6e, 0x200351654b9773409608aaa7db1f)
        + Op.PUSH4[0xb2bc334b] + Op.PUSH6[0x8536d84dadc4]
        + Op.SMOD(0x29d728b6f5ee, 0x2288da62c36b9a35bf8934e3781a4c44e91637ce5c6b2f916d7670)
        + Op.PUSH1[0x13] + Op.PUSH1[0x1e] + Op.PUSH1[0x19] + Op.PUSH1[0x8]
        + Op.PUSH1[0x5] + Op.PUSH1[0x1c] + Op.PUSH1[0x13] + Op.PUSH1[0x1d]
        + Op.SWAP7 + Op.CALLDATALOAD(offset=Op.TIMESTAMP)
        + Op.PUSH9[0xce21a850c04a77ceb9],
        balance=0x3255f99de856501,
        nonce=89,
        address=Address("0xea1cd1b117b10ac33fd7bbf18889624625ede7d4"),  # noqa: E501
    )
    pre[addr_0x945304eb96065b2a98b57a48a06ae28d285a71b5] = Account(balance=0x2401ac5958344e85, nonce=53)
    pre[sender] = Account(balance=0x71e90493e6eb4c59)


    tx = Transaction(
        sender=sender,
        to=target,
        data=bytes.fromhex("166e31b12700cdefa7a0591398d415023175d1e5a1eca036986533972cab6625e976572ee91c150c"),  # noqa: E501
        gas_limit=100000,
        value=0x3ced74ed,
        nonce=0,
        gas_price=232,
    )

    post = {
        target: Account(storage={}, nonce=89),
        addr_0x945304eb96065b2a98b57a48a06ae28d285a71b5: Account(storage={}, code=b"", nonce=53),
        sender: Account(storage={}, code=b"", nonce=1),
        coinbase: Account(storage={}, code=b"", nonce=0),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
