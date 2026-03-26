"""
test_post_to_return1

Ported from:
state_tests/stSystemOperationsTest/PostToReturn1Filler.json
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
    ["state_tests/stSystemOperationsTest/PostToReturn1Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_post_to_return1(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_post_to_return1"""
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
    # { (MSTORE 0 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff) (MSTORE 32 0xaaffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffaa ) [[1]](CALL 30000 <contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5> 23 0 64 0 0 ) [[2]] 1 }
    target = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff)
        + Op.MSTORE(offset=0x20, value=0xaaffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffaa)
        + Op.SSTORE(key=0x1, value=Op.CALL(gas=0x7530, address=0x1ec76f80449bf4d3edf503813e06c0d4373fdf3d, value=0x17, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x2, value=0x1) + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x3ae2f90d9f77554f1e03d5a4868ca5f0c4e14039"),  # noqa: E501
    )
    # Source: raw
    # 0x603760005360026000f2
    addr_0x945304eb96065b2a98b57a48a06ae28d285a71b5 = pre.deploy_contract(
        code=Op.MSTORE8(offset=0x0, value=0x37) + Op.PUSH1[0x2] + Op.PUSH1[0x0]
        + Op.CALLCODE,
        balance=23,
        nonce=0,
        address=Address("0x1ec76f80449bf4d3edf503813e06c0d4373fdf3d"),  # noqa: E501
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

    post = {target: Account(storage={1: 0, 2: 1})}

    state_test(env=env, pre=pre, post=post, tx=tx)
