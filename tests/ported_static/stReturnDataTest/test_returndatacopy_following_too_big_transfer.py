"""
Test: this test tries RETURNDATACOPY with a non-zero size after a CALL...

Ported from:
state_tests/stReturnDataTest/returndatacopy_following_too_big_transferFiller.json
"""

import pytest
from execution_testing import (
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
        "state_tests/stReturnDataTest/returndatacopy_following_too_big_transferFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_returndatacopy_following_too_big_transfer(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test: tis test tries RETURNDATACOPY with a non-zero size after a CALL..."""  # noqa: E501
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0x6400000000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=111669149696,
    )

    # Source: lll
    # { (seq (MSTORE 0 0x0000111122223333444455556666777788889999aaaabbbbccccddddeeeeffff) (RETURN 0 32)) }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0,
            value=0x111122223333444455556666777788889999AAAABBBBCCCCDDDDEEEEFFFF,  # noqa: E501
        )
        + Op.RETURN(offset=0x0, size=0x20)
        + Op.STOP,
        nonce=0,
    )
    # Source: lll
    # { (seq (CALL 0x0900000000 <contract:0x0aabbccdd5c57f15886f9b263e2f6d2d6c7b5ec6> 10000000 0 0 0 0) (RETURNDATACOPY 0 0 32) (SSTORE 0 200) )}  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.POP(
            Op.CALL(
                gas=0x900000000,
                address=addr,
                value=0x989680,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.RETURNDATACOPY(dest_offset=0x0, offset=0x0, size=0x20)
        + Op.SSTORE(key=0x0, value=0xC8)
        + Op.STOP,
        storage={0: 1},
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=100000,
    )

    post = {target: Account(storage={0: 1})}

    state_test(env=env, pre=pre, post=post, tx=tx)
