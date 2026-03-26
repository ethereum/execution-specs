"""
A test shows basefee transaction example

Ported from:
state_tests/stExample/basefeeExampleFiller.yml
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
    ["state_tests/stExample/basefeeExampleFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_basefee_example(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """A test shows basefee transaction example"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xb1f4cbc3a50042184425a6f9e996d0910f7ba879457ce5dac5c71e498ad3c005
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=70000000,
        gas_limit=68719476736,
    )

    # Source: lll
    # {
    #    ; Can also add lll style comments here
    #    [[0]] (ADD 1 1) 
    # }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.ADD(0x1, 0x1)) + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0xad21eb96c7a254c810474f7b1e1e66ca449a3426"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000)


    tx = Transaction(
        sender=sender,
        to=target,
        data=bytes.fromhex("00"),
        gas_limit=4000000,
        value=0x186a0,
        max_fee_per_gas=5000000000,
        max_priority_fee_per_gas=2,
        nonce=0,
        access_list=[
            AccessList(
                address=Address("0xad21eb96c7a254c810474f7b1e1e66ca449a3426"),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000001"  # noqa: E501
                    ),
                ],
            ),
        ],
    )

    post = {target: Account(storage={0: 2})}

    state_test(env=env, pre=pre, post=post, tx=tx)
