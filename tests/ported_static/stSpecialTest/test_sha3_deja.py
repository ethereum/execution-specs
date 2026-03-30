"""
Test_sha3_deja.

Ported from:
state_tests/stSpecialTest/sha3_dejaFiller.json
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
    ["state_tests/stSpecialTest/sha3_dejaFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_sha3_deja(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_sha3_deja."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0xB1F4CBC3A50042184425A6F9E996D0910F7BA879457CE5DAC5C71E498AD3C005
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    # Source: raw
    # 0x6042601f53600064ffffffffff2080
    target = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE8(offset=0x1F, value=0x42)
        + Op.SHA3(offset=0xFFFFFFFFFF, size=0x0)
        + Op.DUP1,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0xCC4CDC08ED5801A6C7D1D87EFB229F9556D50CE6),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=1000000,
        value=0x186A0,
    )

    post = {sender: Account(nonce=1)}

    state_test(env=env, pre=pre, post=post, tx=tx)
