"""
Test_create_with_invalid_opcode.

Ported from:
state_tests/stSystemOperationsTest/createWithInvalidOpcodeFiller.json
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
    ["state_tests/stSystemOperationsTest/createWithInvalidOpcodeFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create_with_invalid_opcode(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_create_with_invalid_opcode."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0xE04D1AC7DDDA0C98397D56A0B501E960D4CD325A39286919AC23C1A07009A869
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
    # 0x444242424245434253f0
    target = pre.deploy_contract(  # noqa: F841
        code=Op.PREVRANDAO
        + Op.TIMESTAMP * 4
        + Op.GASLIMIT
        + Op.MSTORE8(offset=Op.TIMESTAMP, value=Op.NUMBER)
        + Op.CREATE,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0xCC73F3508071F505FB5A5C6108B9444FE05FDD4D),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=300000,
        value=0x186A0,
    )

    post = {target: Account(storage={}, nonce=1)}

    state_test(env=env, pre=pre, post=post, tx=tx)
