"""
Test_random_statetest144.

Ported from:
state_tests/stRandom/randomStatetest144Filler.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
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
    ["state_tests/stRandom/randomStatetest144Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest144(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest144."""
    coinbase = Address(0xB0085A57673C8F7D78FB870418F622E42FD686E4)
    addr = Address(0x19BCDBCD094C63DF253C825B4B8E6DFFC45C21A4)
    sender = EOA(
        key=0x102DA5C19454BAF64E4F417E04AC2551245F3F217FFE9197F0C1D80FC2B16CFF
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1545160903,
    )

    pre[addr] = Account(balance=0x2401AC5958344E85, nonce=53)
    pre[sender] = Account(balance=0x71E90493E6EB4C59)
    # Source: raw
    # 0x621da82575e942e4fd977abdb407069cf700116e02b4f9b25d866b6d13163fff2b8ef03cf8ab5d662afb7bb5c9e68462741090bc0976c9705b40411efe39e80c20b572c5e3d75f788f9be2f0981672b8de37f9e2d1515046cb77cc3ee74646fb096eadce98908499b6fd54725f3c6a725968761ba50494d1ecaf1e787db9a052952427c4f271c28d3e25728b2b76439a3166cd0ed37f30ec2421ed38ebd3b00b89ba9208391dc274e4eefa69161a37dfff7111756dd7971065f05aa9de4867609e7d847a290d0eeb08cde2ff294ae11dd16f8a3e32494d943fa0622cc04cd7476b6d2a1008e4ad1e2c33e2928e707c797f2a1a586bbf78658189bf58172ff77130be2ffc9bbf7f171939be260b30eb65b46a6cf107be1c9ed5c92c99d69fe0559389600e6013601c60096016601260016001600c6017016d200351654b9773409608aaa7db1f67b518d025727bdc6e0463b2bc334b658536d84dadc47a2288da62c36b9a35bf8934e3781a4c44e91637ce5c6b2f916d76706529d728b6f5ee076013601e601960086005601c6013601d96423568ce21a850c04a77ceb9  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH3[0x1DA825]
        + Op.PUSH22[0xE942E4FD977ABDB407069CF700116E02B4F9B25D866B]
        + Op.PUSH14[0x13163FFF2B8EF03CF8AB5D662AFB]
        + Op.PUSH28[0xB5C9E68462741090BC0976C9705B40411EFE39E80C20B572C5E3D75F]
        + Op.PUSH25[0x8F9BE2F0981672B8DE37F9E2D1515046CB77CC3EE74646FB09]
        + Op.PUSH15[0xADCE98908499B6FD54725F3C6A7259]
        + Op.PUSH9[0x761BA50494D1ECAF1E]
        + Op.PUSH25[0x7DB9A052952427C4F271C28D3E25728B2B76439A3166CD0ED3]
        + Op.PUSH32[
            0x30EC2421ED38EBD3B00B89BA9208391DC274E4EEFA69161A37DFFF7111756DD7
        ]
        + Op.SWAP8
        + Op.LT
        + Op.PUSH6[0xF05AA9DE4867]
        + Op.PUSH1[0x9E]
        + Op.PUSH30[
            0x847A290D0EEB08CDE2FF294AE11DD16F8A3E32494D943FA0622CC04CD747
        ]
        + Op.PUSH12[0x6D2A1008E4AD1E2C33E2928E]
        + Op.PUSH17[0x7C797F2A1A586BBF78658189BF58172FF7]
        + Op.PUSH18[0x30BE2FFC9BBF7F171939BE260B30EB65B46A]
        + Op.PUSH13[0xF107BE1C9ED5C92C99D69FE055]
        + Op.SWAP4
        + Op.DUP10
        + Op.PUSH1[0xE]
        + Op.PUSH1[0x13]
        + Op.PUSH1[0x1C]
        + Op.PUSH1[0x9]
        + Op.PUSH1[0x16]
        + Op.PUSH1[0x12]
        + Op.PUSH1[0x1] * 2
        + Op.ADD(0x17, 0xC)
        + Op.DIV(0xB518D025727BDC6E, 0x200351654B9773409608AAA7DB1F)
        + Op.PUSH4[0xB2BC334B]
        + Op.PUSH6[0x8536D84DADC4]
        + Op.SMOD(
            0x29D728B6F5EE,
            0x2288DA62C36B9A35BF8934E3781A4C44E91637CE5C6B2F916D7670,
        )
        + Op.PUSH1[0x13]
        + Op.PUSH1[0x1E]
        + Op.PUSH1[0x19]
        + Op.PUSH1[0x8]
        + Op.PUSH1[0x5]
        + Op.PUSH1[0x1C]
        + Op.PUSH1[0x13]
        + Op.PUSH1[0x1D]
        + Op.SWAP7
        + Op.CALLDATALOAD(offset=Op.TIMESTAMP)
        + Op.PUSH9[0xCE21A850C04A77CEB9],
        balance=0x3255F99DE856501,
        nonce=89,
        address=Address(0xEA1CD1B117B10AC33FD7BBF18889624625EDE7D4),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(
            "166e31b12700cdefa7a0591398d415023175d1e5a1eca036986533972cab6625e976572ee91c150c"  # noqa: E501
        ),
        gas_limit=100000,
        value=0x3CED74ED,
        gas_price=232,
    )

    post = {
        target: Account(storage={}, nonce=89),
        addr: Account(storage={}, code=b"", nonce=53),
        sender: Account(storage={}, code=b"", nonce=1),
        coinbase: Account(storage={}, code=b"", nonce=0),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
