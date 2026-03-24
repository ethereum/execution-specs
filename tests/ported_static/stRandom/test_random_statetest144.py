"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stRandom/randomStatetest144Filler.json
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
    ["tests/static/state_tests/stRandom/randomStatetest144Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest144(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0xb0085a57673c8f7d78fb870418f622e42fd686e4")
    sender = EOA(
        key=0x102DA5C19454BAF64E4F417E04AC2551245F3F217FFE9197F0C1D80FC2B16CFF
    )
    callee = Address("0x19bcdbcd094c63df253c825b4b8e6dffc45c21a4")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1545160903,
    )

    pre[sender] = Account(balance=0x71E90493E6EB4C59)
    pre[callee] = Account(balance=0x2401AC5958344E85, nonce=53)
    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=(
            Op.PUSH3[0x1DA825]
            + Op.PUSH22[0xE942E4FD977ABDB407069CF700116E02B4F9B25D866B]
            + Op.PUSH14[0x13163FFF2B8EF03CF8AB5D662AFB]
            + Op.PUSH28[
                0xB5C9E68462741090BC0976C9705B40411EFE39E80C20B572C5E3D75F
            ]
            + Op.PUSH25[0x8F9BE2F0981672B8DE37F9E2D1515046CB77CC3EE74646FB09]
            + Op.PUSH15[0xADCE98908499B6FD54725F3C6A7259]
            + Op.PUSH9[0x761BA50494D1ECAF1E]
            + Op.PUSH25[0x7DB9A052952427C4F271C28D3E25728B2B76439A3166CD0ED3]
            + Op.PUSH32[
                0x30EC2421ED38EBD3B00B89BA9208391DC274E4EEFA69161A37DFFF7111756DD7  # noqa: E501
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
            + Op.PUSH1[0x1]
            + Op.PUSH1[0x1]
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
            + Op.PUSH9[0xCE21A850C04A77CEB9]
        ),
        balance=0x3255F99DE856501,
        nonce=89,
        address=Address("0xea1cd1b117b10ac33fd7bbf18889624625ede7d4"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex(
            "166e31b12700cdefa7a0591398d415023175d1e5a1eca036986533972cab6625e976572e"  # noqa: E501
            "e91c150c"
        ),
        gas_limit=100000,
        gas_price=232,
        value=1022194925,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stRandom/randomStatetest144Filler.json"],
)
@pytest.mark.valid_from("Prague")
@pytest.mark.pre_alloc_mutable
def test_random_statetest144_from_prague(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0xb0085a57673c8f7d78fb870418f622e42fd686e4")
    sender = EOA(
        key=0x102DA5C19454BAF64E4F417E04AC2551245F3F217FFE9197F0C1D80FC2B16CFF
    )
    callee = Address("0x19bcdbcd094c63df253c825b4b8e6dffc45c21a4")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1545160903,
    )

    pre[sender] = Account(balance=0x71E90493E6EB4C59)
    pre[callee] = Account(balance=0x2401AC5958344E85, nonce=53)
    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=(
            Op.PUSH3[0x1DA825]
            + Op.PUSH22[0xE942E4FD977ABDB407069CF700116E02B4F9B25D866B]
            + Op.PUSH14[0x13163FFF2B8EF03CF8AB5D662AFB]
            + Op.PUSH28[
                0xB5C9E68462741090BC0976C9705B40411EFE39E80C20B572C5E3D75F
            ]
            + Op.PUSH25[0x8F9BE2F0981672B8DE37F9E2D1515046CB77CC3EE74646FB09]
            + Op.PUSH15[0xADCE98908499B6FD54725F3C6A7259]
            + Op.PUSH9[0x761BA50494D1ECAF1E]
            + Op.PUSH25[0x7DB9A052952427C4F271C28D3E25728B2B76439A3166CD0ED3]
            + Op.PUSH32[
                0x30EC2421ED38EBD3B00B89BA9208391DC274E4EEFA69161A37DFFF7111756DD7  # noqa: E501
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
            + Op.PUSH1[0x1]
            + Op.PUSH1[0x1]
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
            + Op.PUSH9[0xCE21A850C04A77CEB9]
        ),
        balance=0x3255F99DE856501,
        nonce=89,
        address=Address("0xea1cd1b117b10ac33fd7bbf18889624625ede7d4"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex(
            "166e31b12700cdefa7a0591398d415023175d1e5a1eca036986533972cab6625e976572e"  # noqa: E501
            "e91c150c"
        ),
        gas_limit=100000,
        gas_price=232,
        value=1022194925,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
