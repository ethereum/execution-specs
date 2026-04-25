"""
Test_static_make_money.

Ported from:
state_tests/stStaticCall/static_makeMoneyFiller.json
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
    ["state_tests/stStaticCall/static_makeMoneyFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
@pytest.mark.pre_alloc_mutable
def test_static_make_money(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_static_make_money."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0x5F5E100)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    # Source: raw
    # 0x600160015532600255
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.SSTORE(key=0x2, value=Op.ORIGIN),
        balance=0xDE0B6B3A7640000,
        nonce=0,
    )
    # Source: lll
    # { (MSTORE 0 0x601080600c6000396000f20060003554156009570060203560003555) (STATICCALL 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffec <contract:0xaaaaaaaaace5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0,
            value=0x601080600C6000396000F20060003554156009570060203560003555,
        )
        + Op.STATICCALL(
            gas=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEC,  # noqa: E501
            address=addr,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=228500,
        value=10,
    )

    post = {
        target: Account(balance=0xDE0B6B3A764000A),
        sender: Account(balance=0x5D38038),
        addr: Account(balance=0xDE0B6B3A7640000),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
