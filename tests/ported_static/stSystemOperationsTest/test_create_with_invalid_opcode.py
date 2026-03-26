"""
test_create_with_invalid_opcode

Ported from:
state_tests/stSystemOperationsTest/createWithInvalidOpcodeFiller.json
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
    ["state_tests/stSystemOperationsTest/createWithInvalidOpcodeFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create_with_invalid_opcode(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_create_with_invalid_opcode"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    # Source: raw
    # 0x444242424245434253f0
    target = pre.deploy_contract(
        code=Op.PREVRANDAO + Op.TIMESTAMP * 4 + Op.GASLIMIT
        + Op.MSTORE8(offset=Op.TIMESTAMP, value=Op.NUMBER) + Op.CREATE,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0xcc73f3508071f505fb5a5c6108b9444fe05fdd4d"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000)


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=300000,
        value=0x186a0,
        nonce=0,
        gas_price=10,
    )

    post = {target: Account(storage={}, nonce=1)}

    state_test(env=env, pre=pre, post=post, tx=tx)
