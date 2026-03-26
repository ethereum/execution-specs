"""
Uses EXTCODECOPY to copy 32 bytes of code into a 64 byte range of memory and ensures that the last 32 bytes of the memory range are zeroed out

Ported from:
state_tests/stCodeCopyTest/ExtCodeCopyTargetRangeLongerThanCodeTestsFiller.json
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
    ["state_tests/stCodeCopyTest/ExtCodeCopyTargetRangeLongerThanCodeTestsFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_ext_code_copy_target_range_longer_than_code_tests(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Uses EXTCODECOPY to copy 32 bytes of code into a 64 byte range of m..."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xe7c72b378297589acee4e0ba3272841bcfc5e220f86de253f890274cfee9e474
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre[sender] = Account(balance=0xffffffffffffffffffffffffffffffff)
    # Source: lll
    # { (MSTORE 32 0x1234) (EXTCODECOPY <contract:0xeeef5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 64) [[0]] (MLOAD 0) [[1]] (MLOAD 32) (MSTORE 96 0x5678) (EXTCODECOPY <eoa:sender:0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b> 64 0 64) [[2]] (MLOAD 64) [[3]] (MLOAD 96)}
    target = pre.deploy_contract(
        code=Op.MSTORE(offset=0x20, value=0x1234)
        + Op.EXTCODECOPY(address=0x7ac02e797f450c7ea62753383f618e1903cd6bba, dest_offset=0x0, offset=0x0, size=0x40)
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x20))
        + Op.MSTORE(offset=0x60, value=0x5678)
        + Op.EXTCODECOPY(address=0x4768b5e50b0ebe91ae38d84a47e3179e615f9c40, dest_offset=0x40, offset=0x0, size=0x40)
        + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0x40))
        + Op.SSTORE(key=0x3, value=Op.MLOAD(offset=0x60)) + Op.STOP,
        balance=7000,
        nonce=0,
        address=Address("0x48d8f710ab8cb48f77b602d24696926e31787a17"),  # noqa: E501
    )
    # Source: raw
    # 0x1122334455667788991011121314151617181920212223242526272829303132
    addr_0xeeef5374fce5edbc8e2a8697c15331677e6ebf0b = pre.deploy_contract(
        code=bytes.fromhex("1122334455667788991011121314151617181920212223242526272829303132"),  # noqa: E501
        nonce=1,
        address=Address("0x7ac02e797f450c7ea62753383f618e1903cd6bba"),  # noqa: E501
    )


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=400000,
        nonce=0,
        gas_price=10,
    )

    post = {
        target: Account(
                storage={
            0: 0x1122334455667788991011121314151617181920212223242526272829303132,
            1: 0,
            2: 0,
            3: 0,
        },
            ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
