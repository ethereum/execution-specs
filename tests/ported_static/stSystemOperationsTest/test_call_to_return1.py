"""
test_call_to_return1

Ported from:
state_tests/stSystemOperationsTest/CallToReturn1Filler.json
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
    ["state_tests/stSystemOperationsTest/CallToReturn1Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_to_return1(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_call_to_return1"""
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
        gas_limit=10000000,
    )

    # Source: lll
    # { [[ 0 ]] (CALL 1000 <contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5> 23 0 0 31 1) [[ 1 ]] @0 }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.CALL(gas=0x3e8, address=0x64963d42a3dff7bf49ce946e12f6c9034c746888, value=0x17, args_offset=0x0, args_size=0x0, ret_offset=0x1f, ret_size=0x1))  # noqa: E501
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0)) + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0xe31afa4922f77f6c0ec198294b373d2ab9de47d2"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155602a601f536001601ff3
    addr_0x945304eb96065b2a98b57a48a06ae28d285a71b5 = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x1) + Op.MSTORE8(offset=0x1f, value=0x2a)  # noqa: E501
        + Op.RETURN(offset=0x1f, size=0x1),
        balance=23,
        nonce=0,
        address=Address("0x64963d42a3dff7bf49ce946e12f6c9034c746888"),  # noqa: E501
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

    post = {target: Account(storage={}, nonce=0)}

    state_test(env=env, pre=pre, post=post, tx=tx)
