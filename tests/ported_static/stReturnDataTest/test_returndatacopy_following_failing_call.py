"""
Test_returndatacopy_following_failing_call.

Ported from:
state_tests/stReturnDataTest/returndatacopy_following_failing_callFiller.json
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
        "state_tests/stReturnDataTest/returndatacopy_following_failing_callFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_returndatacopy_following_failing_call(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_returndatacopy_following_failing_call."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0x834185262E53584684BF2B72C64E510013C235D0F45E462DB65900455DF45A35
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=111669149696,
    )

    # Source: raw
    # 0xfd
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.REVERT,
        nonce=0,
        address=Address(0x3141BB954E8294E47A14EBD08229F30E6294BA83),  # noqa: E501
    )
    # Source: lll
    # { (CALL 0x0900000000 <contract:0x0aabbccdd5c57f15886f9b263e2f6d2d6c7b5ec6> 0 0 0 0 0) (RETURNDATACOPY 0 1 32) (SSTORE 0 (MLOAD 0)) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.POP(
            Op.CALL(
                gas=0x900000000,
                address=0x3141BB954E8294E47A14EBD08229F30E6294BA83,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.RETURNDATACOPY(dest_offset=0x0, offset=0x1, size=0x20)
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
        + Op.STOP,
        storage={0: 1},
        nonce=0,
        address=Address(0x71A277F82C43FF98682EB8D6DB4A3ECD680407EB),  # noqa: E501
    )
    pre[sender] = Account(balance=0x6400000000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=100000,
    )

    post = {target: Account(storage={0: 1})}

    state_test(env=env, pre=pre, post=post, tx=tx)
