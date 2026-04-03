"""
Test_returndatasize_after_successful_delegatecall.

Ported from:
state_tests/stReturnDataTest/returndatasize_after_successful_delegatecallFiller.json
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
        "state_tests/stReturnDataTest/returndatasize_after_successful_delegatecallFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_returndatasize_after_successful_delegatecall(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_returndatasize_after_successful_delegatecall."""
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

    # Source: lll
    # { (seq (DELEGATECALL 60000 <contract:0x1000000000000000000000000000000000000002> 0 0 0 0) (SSTORE 0 (RETURNDATASIZE)))}  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.POP(
            Op.DELEGATECALL(
                gas=0xEA60,
                address=0x7C17DBBFA29DC8391BFA19022ECB4FDA54FC826A,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE)
        + Op.STOP,
        storage={
            0: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
        },
        nonce=0,
        address=Address(0x1C7CCE7753E67952A031524E6505E53F170520BE),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 0x0 (CALLER)) (RETURN 0 20) }
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.CALLER)
        + Op.RETURN(offset=0x0, size=0x14)
        + Op.STOP,
        balance=0x6400000000,
        nonce=0,
        address=Address(0x7C17DBBFA29DC8391BFA19022ECB4FDA54FC826A),  # noqa: E501
    )
    pre[sender] = Account(balance=0x6400000000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=100000,
    )

    post = {target: Account(storage={0: 20})}

    state_test(env=env, pre=pre, post=post, tx=tx)
