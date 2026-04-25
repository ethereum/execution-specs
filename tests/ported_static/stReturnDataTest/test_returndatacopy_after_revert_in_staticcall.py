"""
Test_returndatacopy_after_revert_in_staticcall.

Ported from:
state_tests/stReturnDataTest/returndatacopy_after_revert_in_staticcallFiller.json
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
        "state_tests/stReturnDataTest/returndatacopy_after_revert_in_staticcallFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_returndatacopy_after_revert_in_staticcall(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_returndatacopy_after_revert_in_staticcall."""
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

    addr = pre.fund_eoa(amount=0x1000000)  # noqa: F841
    # Source: lll
    # { (MSTORE 0x0 (CALLER)) (REVERT 0 32) }
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.CALLER)
        + Op.REVERT(offset=0x0, size=0x20)
        + Op.STOP,
        balance=0x6400000000,
        nonce=0,
    )
    # Source: lll
    # { (STATICCALL 60000 <contract:0x1000000000000000000000000000000000000002> 0 0 0 0) (RETURNDATACOPY 0x0 0x0 32) ( SSTORE 0 (MLOAD 0))}  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.POP(
            Op.STATICCALL(
                gas=0xEA60,
                address=addr_2,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.RETURNDATACOPY(dest_offset=0x0, offset=0x0, size=0x20)
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
        + Op.STOP,
        storage={
            0: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
        },
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=100000,
    )

    post = {target: Account(storage={0: target})}

    state_test(env=env, pre=pre, post=post, tx=tx)
