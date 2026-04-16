"""
Test_call1024_balance_too_low.

Ported from:
state_tests/stDelegatecallTestHomestead/Call1024BalanceTooLowFiller.json
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
        "state_tests/stDelegatecallTestHomestead/Call1024BalanceTooLowFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.pre_alloc_mutable
def test_call1024_balance_too_low(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_call1024_balance_too_low."""
    coinbase = Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    sender = pre.fund_eoa(amount=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    addr = pre.fund_eoa(amount=7000)  # noqa: F841
    # Source: lll
    # { [[ 0 ]] (ADD @@0 1) [[ 1 ]] (DELEGATECALL 0xfffffffffff <contract:target:0xbbbf5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
        + Op.SSTORE(
            key=0x1,
            value=Op.DELEGATECALL(
                gas=0xFFFFFFFFFFF,
                address=0xE7ADDF870A481E1A0829E5A67DEBD5B963861979,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.STOP,
        balance=1024,
        nonce=0,
        address=Address(0xE7ADDF870A481E1A0829E5A67DEBD5B963861979),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=17592186099592,
        value=10,
    )

    post = {target: Account(storage={0: 1025, 1: 1})}

    state_test(env=env, pre=pre, post=post, tx=tx)
