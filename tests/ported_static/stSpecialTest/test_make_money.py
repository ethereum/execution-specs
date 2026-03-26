"""
test_make_money

Ported from:
state_tests/stSpecialTest/makeMoneyFiller.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"

REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stSpecialTest/makeMoneyFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_make_money(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_make_money"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xf79127a3004abde26a4cbd80c428cb10f829fa11b54d36e7b326f4f4a5927acf
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    # Source: lll
    # { (MSTORE 0 0x601080600c6000396000f20060003554156009570060203560003555) (CALL 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffec <contract:0xaaaaaaaaace5edbc8e2a8697c15331677e6ebf0b> 23 0 0 0 0) }
    target = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0x601080600c6000396000f20060003554156009570060203560003555)
        + Op.CALL(gas=0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffec, address=0x802edccf6cde9162a05fd89cdfcd8dc4a230b978, value=0x17, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)
        + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x56f6da36928bffd1fdb9eade8a5b8baffde0dea4"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x3b9aca00)
    # Source: raw
    # 0x600160015532600255
    addr_0xaaaaaaaaace5edbc8e2a8697c15331677e6ebf0b = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x1) + Op.SSTORE(key=0x2, value=Op.ORIGIN),  # noqa: E501
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x802edccf6cde9162a05fd89cdfcd8dc4a230b978"),  # noqa: E501
    )


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=228500,
        value=10,
        nonce=0,
        gas_price=10,
    )

    post = {
        target: Account(balance=0xde0b6b3a763fff3),
        sender: Account(balance=0x3b8f6a16),
        addr_0xaaaaaaaaace5edbc8e2a8697c15331677e6ebf0b: Account(balance=0xde0b6b3a7640017),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
