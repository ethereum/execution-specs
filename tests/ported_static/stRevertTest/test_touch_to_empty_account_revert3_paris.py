"""
Test_touch_to_empty_account_revert3_paris.

Ported from:
state_tests/stRevertTest/TouchToEmptyAccountRevert3_ParisFiller.json
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
    ["state_tests/stRevertTest/TouchToEmptyAccountRevert3_ParisFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_touch_to_empty_account_revert3_paris(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_touch_to_empty_account_revert3_paris."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xE8D4A51000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    addr = pre.fund_eoa(amount=10)  # noqa: F841
    # Source: lll
    # { (SELFDESTRUCT <eoa:0x1000000000000000000000000000000000000000>) }
    addr_3 = pre.deploy_contract(  # noqa: F841
        code=Op.SELFDESTRUCT(address=addr) + Op.STOP,
        nonce=0,
    )
    # Source: lll
    # { (SELFDESTRUCT <eoa:0x1000000000000000000000000000000000000000>) }
    addr_4 = pre.deploy_contract(  # noqa: F841
        code=Op.SELFDESTRUCT(address=addr) + Op.STOP,
        nonce=0,
    )
    # Source: lll
    # { [[2]](CALL 100000 <contract:0xe94f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) (KECCAK256 0x00 0x2fffff) }  # noqa: E501
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x2,
            value=Op.CALL(
                gas=0x186A0,
                address=addr_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SHA3(offset=0x0, size=0x2FFFFF)
        + Op.STOP,
        nonce=0,
    )
    # Source: lll
    # { [[0]](CALL 130000 <contract:0xd94f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) [[1]](CALL 130000 <contract:0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALL(
                gas=0x1FBD0,
                address=addr_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(
            key=0x1,
            value=Op.CALL(
                gas=0x1FBD0,
                address=addr_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.STOP,
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=200000,
    )

    post = {addr: Account(balance=10)}

    state_test(env=env, pre=pre, post=post, tx=tx)
