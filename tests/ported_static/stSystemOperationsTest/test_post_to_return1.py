"""
Test_post_to_return1.

Ported from:
state_tests/stSystemOperationsTest/PostToReturn1Filler.json
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
    ["state_tests/stSystemOperationsTest/PostToReturn1Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_post_to_return1(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_post_to_return1."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0xE04D1AC7DDDA0C98397D56A0B501E960D4CD325A39286919AC23C1A07009A869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    # Source: lll
    # { (MSTORE 0 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff) (MSTORE 32 0xaaffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffaa ) [[1]](CALL 30000 <contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5> 23 0 64 0 0 ) [[2]] 1 }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0,
            value=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
        )
        + Op.MSTORE(
            offset=0x20,
            value=0xAAFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFAA,  # noqa: E501
        )
        + Op.SSTORE(
            key=0x1,
            value=Op.CALL(
                gas=0x7530,
                address=0x1EC76F80449BF4D3EDF503813E06C0D4373FDF3D,
                value=0x17,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x2, value=0x1)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x3AE2F90D9F77554F1E03D5A4868CA5F0C4E14039),  # noqa: E501
    )
    # Source: raw
    # 0x603760005360026000f2
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE8(offset=0x0, value=0x37)
        + Op.PUSH1[0x2]
        + Op.PUSH1[0x0]
        + Op.CALLCODE,
        balance=23,
        nonce=0,
        address=Address(0x1EC76F80449BF4D3EDF503813E06C0D4373FDF3D),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=300000,
        value=0x186A0,
    )

    post = {target: Account(storage={1: 0, 2: 1})}

    state_test(env=env, pre=pre, post=post, tx=tx)
