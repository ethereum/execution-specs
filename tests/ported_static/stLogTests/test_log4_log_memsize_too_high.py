"""
test_log4_log_memsize_too_high

Ported from:
state_tests/stLogTests/log4_logMemsizeTooHighFiller.json
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
    ["state_tests/stLogTests/log4_logMemsizeTooHighFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_log4_log_memsize_too_high(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_log4_log_memsize_too_high"""
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
    # { [[ 0 ]] (CALL 1000 <contract:0x0f572e5295c57f15886f9b263e2f6d2d6c7b5ec6> 23 0 0 0 0) }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.CALL(gas=0x3e8, address=0x59e2f8fdf907d6e627fcafd97606824ce1fe1e2a, value=0x17, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x1e5597b6168fe79952cb2de7af91c3449bc95bd4"),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 0 0xaabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd) (LOG4 1 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff 0 0 0 0) }
    addr_0x0f572e5295c57f15886f9b263e2f6d2d6c7b5ec6 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0xaabbffffffffffffffffffffffffffffffffffffffffffffffffffffffffccdd)
        + Op.LOG4(offset=0x1, size=0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff, topic_1=0x0, topic_2=0x0, topic_3=0x0, topic_4=0x0)
        + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x59e2f8fdf907d6e627fcafd97606824ce1fe1e2a"),  # noqa: E501
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

    post = {target: Account(storage={})}

    state_test(env=env, pre=pre, post=post, tx=tx)
