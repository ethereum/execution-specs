"""
The execution records the EIP-1559 transaction origin balance to make...

properly computed based on the effective gas price (not the maximum gas price
as in
the transaction validity check).

Ported from:
state_tests/stEIP1559/senderBalanceFiller.yml
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
    ["state_tests/stEIP1559/senderBalanceFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_sender_balance(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """The execution records the EIP-1559 transaction origin balance to..."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0xE04D1AC7DDDA0C98397D56A0B501E960D4CD325A39286919AC23C1A07009A869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=11,
        gas_limit=30000000,
    )

    pre[sender] = Account(balance=0xDE0B6B3A7640000)
    # Source: yul
    # london
    # {
    #   sstore(0, balance(caller()))
    # }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.BALANCE(address=Op.CALLER)) + Op.STOP,
        nonce=0,
        address=Address(0x420132F96200BA8E5C98298A85633C35C4F052EF),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=60000,
        max_fee_per_gas=1000,
        max_priority_fee_per_gas=100,
        access_list=[],
    )

    post = {target: Account(storage={0: 0xDE0B6B3A6FE6060})}

    state_test(env=env, pre=pre, post=post, tx=tx)
