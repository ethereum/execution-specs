"""
Test_touch_to_empty_account_revert_paris.

Ported from:
state_tests/stRevertTest/TouchToEmptyAccountRevert_ParisFiller.json
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
    ["state_tests/stRevertTest/TouchToEmptyAccountRevert_ParisFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_touch_to_empty_account_revert_paris(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_touch_to_empty_account_revert_paris."""
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
    # { [[1]](CALL 30000 <eoa:0x1000000000000000000000000000000000000000> 0 0 0 0 0) }  # noqa: E501
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x1,
            value=Op.CALL(
                gas=0x7530,
                address=addr,
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
    # Source: lll
    # { [[0]](CALL 30000 <contract:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) [[2]] 1 }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALL(
                gas=0x7530,
                address=addr_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x2, value=0x1)
        + Op.STOP,
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=70000,
    )

    post = {addr: Account(storage={}, code=b"", balance=10, nonce=0)}

    state_test(env=env, pre=pre, post=post, tx=tx)
