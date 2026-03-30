"""
Uses EXTCODECOPY to copy 32 bytes of code into a 64 byte range of...

Ported from:
state_tests/stCodeCopyTest/ExtCodeCopyTargetRangeLongerThanCodeTestsFiller.json
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
    [
        "state_tests/stCodeCopyTest/ExtCodeCopyTargetRangeLongerThanCodeTestsFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_ext_code_copy_target_range_longer_than_code_tests(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Uses EXTCODECOPY to copy 32 bytes of code into a 64 byte range of..."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0xE7C72B378297589ACEE4E0BA3272841BCFC5E220F86DE253F890274CFEE9E474
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre[sender] = Account(balance=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
    # Source: lll
    # { (MSTORE 32 0x1234) (EXTCODECOPY <contract:0xeeef5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 64) [[0]] (MLOAD 0) [[1]] (MLOAD 32) (MSTORE 96 0x5678) (EXTCODECOPY <eoa:sender:0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b> 64 0 64) [[2]] (MLOAD 64) [[3]] (MLOAD 96)}  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x20, value=0x1234)
        + Op.EXTCODECOPY(
            address=0x7AC02E797F450C7EA62753383F618E1903CD6BBA,
            dest_offset=0x0,
            offset=0x0,
            size=0x40,
        )
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x20))
        + Op.MSTORE(offset=0x60, value=0x5678)
        + Op.EXTCODECOPY(
            address=0x4768B5E50B0EBE91AE38D84A47E3179E615F9C40,
            dest_offset=0x40,
            offset=0x0,
            size=0x40,
        )
        + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0x40))
        + Op.SSTORE(key=0x3, value=Op.MLOAD(offset=0x60))
        + Op.STOP,
        balance=7000,
        nonce=0,
        address=Address(0x48D8F710AB8CB48F77B602D24696926E31787A17),  # noqa: E501
    )
    # Source: raw
    # 0x1122334455667788991011121314151617181920212223242526272829303132
    addr = pre.deploy_contract(  # noqa: F841
        code=bytes.fromhex(
            "1122334455667788991011121314151617181920212223242526272829303132"
        ),
        nonce=1,
        address=Address(0x7AC02E797F450C7EA62753383F618E1903CD6BBA),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=400000,
    )

    post = {
        target: Account(
            storage={
                0: 0x1122334455667788991011121314151617181920212223242526272829303132,  # noqa: E501
                1: 0,
                2: 0,
                3: 0,
            },
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
