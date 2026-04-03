"""
Test_call_data_copy_offset.

Ported from:
state_tests/stMemoryTest/callDataCopyOffsetFiller.json
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
    ["state_tests/stMemoryTest/callDataCopyOffsetFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_data_copy_offset(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_call_data_copy_offset."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0xEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE)
    contract_1 = Address(0x095E7BAEA6A6C7C4C2DFEB977EFAC326AF552D87)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
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
    # { (MSTORE 0x00 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff) (CALLDATACOPY 0x00 0xffff  0x10) (SSTORE 0x00 (MLOAD 0x00)) }  # noqa: E501
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0,
            value=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
        )
        + Op.CALLDATACOPY(dest_offset=0x0, offset=0xFFFF, size=0x10)
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=1,
        address=Address(0xEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE),  # noqa: E501
    )
    # Source: yul
    # berlin { mstore(0, 0x0123456789abcdef) pop(call(0xffff,0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee,0, 0,0x0f, 0,0))  }  # noqa: E501
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=0x123456789ABCDEF)
        + Op.CALL(
            gas=0xFFFF,
            address=0xEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE,
            value=Op.DUP1,
            args_offset=Op.DUP2,
            args_size=0xF,
            ret_offset=Op.DUP1,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=1,
        address=Address(0x095E7BAEA6A6C7C4C2DFEB977EFAC326AF552D87),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=contract_1,
        data=Bytes(""),
        gas_limit=400000,
        value=0x186A0,
    )

    post = {
        contract_0: Account(storage={0: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF})
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
