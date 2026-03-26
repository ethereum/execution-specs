"""
The execution records the EIP-1559 transaction origin balance to make sure its value is 
properly computed based on the effective gas price (not the maximum gas price as in 
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
    Environment,
    StateTestFiller,
    Transaction,
    AccessList,
    Hash,
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
    """The execution records the EIP-1559 transaction origin balance to ma..."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=1,
        base_fee_per_gas=11,
        gas_limit=30000000,
    )

    # Source: yul
    # london
    # {
    #   sstore(0, balance(caller()))
    # }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.BALANCE(address=Op.CALLER)) + Op.STOP,
        nonce=0,
        address=Address("0x420132f96200ba8e5c98298a85633c35c4f052ef"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000)


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=60000,
        max_fee_per_gas=1000,
        max_priority_fee_per_gas=100,
        nonce=0,
    )

    post = {target: Account(storage={0: 0xde0b6b3a6fe6060})}

    state_test(env=env, pre=pre, post=post, tx=tx)
