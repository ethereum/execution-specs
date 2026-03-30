"""
Test_code_copy_offset.

Ported from:
state_tests/stMemoryTest/codeCopyOffsetFiller.json
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
    ["state_tests/stMemoryTest/codeCopyOffsetFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_code_copy_offset(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_code_copy_offset."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0xB1F4CBC3A50042184425A6F9E996D0910F7BA879457CE5DAC5C71E498AD3C005
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    # Source: lll
    # { (MSTORE 0x00 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff) (CODECOPY 0x00 0xffff  0x10) (SSTORE 0x00 (MLOAD 0x00)) }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0,
            value=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
        )
        + Op.CODECOPY(dest_offset=0x0, offset=0xFFFF, size=0x10)
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=1,
        address=Address(0x27D16E1D3CC862149F1E7162E612635FCAEF9FF4),  # noqa: E501
    )
    # Source: yul
    # berlin { mstore(0, 0x0123456789abcdef)  pop(call(0xffff, <contract:0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee>, 0, 0, 0x0f, 0, 0))  }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=0x123456789ABCDEF)
        + Op.CALL(
            gas=0xFFFF,
            address=0x27D16E1D3CC862149F1E7162E612635FCAEF9FF4,
            value=Op.DUP1,
            args_offset=Op.DUP2,
            args_size=0xF,
            ret_offset=Op.DUP1,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=1,
        address=Address(0xAF89A7504341A87E1CFDFFD483A00A4688469B3D),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=400000,
        value=0x186A0,
    )

    post = {addr: Account(storage={0: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF})}

    state_test(env=env, pre=pre, post=post, tx=tx)
