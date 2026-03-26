"""
test_static_log0_empty_mem

Ported from:
state_tests/stStaticCall/static_log0_emptyMemFiller.json
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
    ["state_tests/stStaticCall/static_log0_emptyMemFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_static_log0_empty_mem(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_static_log0_empty_mem"""
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

    # Source: lll
    # { [[ 0 ]] (STATICCALL 1000 <contract:0x0f572e5295c57f15886f9b263e2f6d2d6c7b5ec6> 0 0 0 0) [[ 1 ]] 1 }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.STATICCALL(gas=0x3e8, address=0xc2a943e837808399d9c1b946c6188739d4d4475e, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x1, value=0x1) + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0xde4edfb3ce6bd32637813f22447df168e9289cdd"),  # noqa: E501
    )
    # Source: lll
    # { (LOG0 0 0) }
    addr_0x0f572e5295c57f15886f9b263e2f6d2d6c7b5ec6 = pre.deploy_contract(
        code=Op.LOG0(offset=0x0, size=0x0) + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0xc2a943e837808399d9c1b946c6188739d4d4475e"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000)


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=210000,
        value=0x186a0,
        nonce=0,
        gas_price=10,
    )

    post = {target: Account(storage={0: 0, 1: 1})}

    state_test(env=env, pre=pre, post=post, tx=tx)
