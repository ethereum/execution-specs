"""
The execution records the EIP-1559 transaction origin balance to make sure its value is 
properly computed based on the effective gas price (not the maximum gas price as in 
the transaction validity check).


Ported from:
tests/static/state_tests/stEIP1559/senderBalanceFiller.yml

contract code:
    caller
    balance
    push1 0x00
    sstore
    stop
"""

import pytest
from execution_testing import (
    AccessList,
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
    ["tests/static/state_tests/stEIP1559/senderBalanceFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_sender_balance(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """The execution records the EIP-1559 transaction origin balance to make sure its value is 
properly computed based on the effective gas price (not the maximum gas price as in 
the transaction validity check).
."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0x420132f96200ba8e5c98298a85633c35c4f052ef")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=11,
        gas_limit=30000000,
    )

    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=Op.CALLER + Op.BALANCE + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP,
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869"
        ),
        to=contract,
        data=b"",
        gas_limit=60000,
        max_fee_per_gas=1000,
        max_priority_fee_per_gas=100,
        nonce=0,
        value=0,
        access_list=[],
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
