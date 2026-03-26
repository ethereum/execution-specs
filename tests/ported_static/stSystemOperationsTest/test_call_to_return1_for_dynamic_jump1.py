"""
test_call_to_return1_for_dynamic_jump1

Ported from:
state_tests/stSystemOperationsTest/CallToReturn1ForDynamicJump1Filler.json
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
    ["state_tests/stSystemOperationsTest/CallToReturn1ForDynamicJump1Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_to_return1_for_dynamic_jump1(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_call_to_return1_for_dynamic_jump1"""
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

    # Source: raw
    # 0x6001601f60006000601773<contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5>6103e8f160005560005156605b6023602355
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.CALL(gas=0x3e8, address=0xd43411a40a68e9cba15440e3c34a74a4dc5f79dd, value=0x17, args_offset=0x0, args_size=0x0, ret_offset=0x1f, ret_size=0x1))  # noqa: E501
        + Op.JUMP(pc=Op.MLOAD(offset=0x0)) + Op.PUSH1[0x5b]
        + Op.SSTORE(key=0x23, value=0x23),
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x7bc307ec814ce37f4553993ac5612b763f18165d"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155602b601f536001601ff3
    addr_0x945304eb96065b2a98b57a48a06ae28d285a71b5 = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x1) + Op.MSTORE8(offset=0x1f, value=0x2b)  # noqa: E501
        + Op.RETURN(offset=0x1f, size=0x1),
        balance=23,
        nonce=0,
        address=Address("0xd43411a40a68e9cba15440e3c34a74a4dc5f79dd"),  # noqa: E501
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
