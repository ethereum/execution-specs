"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stSpecialTest/makeMoneyFiller.json
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
    ["tests/static/state_tests/stSpecialTest/makeMoneyFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_make_money(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xF79127A3004ABDE26A4CBD80C428CB10F829FA11B54D36E7B326F4F4A5927ACF
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    # Source: LLL
    # { (MSTORE 0 0x601080600c6000396000f20060003554156009570060203560003555) (CALL 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffec <contract:0xaaaaaaaaace5edbc8e2a8697c15331677e6ebf0b> 23 0 0 0 0) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(
                offset=0x0,
                value=0x601080600C6000396000F20060003554156009570060203560003555,  # noqa: E501
            )
            + Op.CALL(
                gas=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEC,  # noqa: E501
                address=0x802EDCCF6CDE9162A05FD89CDFCD8DC4A230B978,
                value=0x17,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x56f6da36928bffd1fdb9eade8a5b8baffde0dea4"),  # noqa: E501
    )
    # Source: raw bytecode
    callee = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x1, value=0x1) + Op.SSTORE(key=0x2, value=Op.ORIGIN)
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x802edccf6cde9162a05fd89cdfcd8dc4a230b978"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x3B9ACA00)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=228500,
        value=10,
    )

    post = {
        callee: Account(
            storage={
                1: 1,
                2: 0xC4A2CA1058DF329E5DA4755F9921DDAF05CBAA06,
            },
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
