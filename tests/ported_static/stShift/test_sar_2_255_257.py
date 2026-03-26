"""
test_sar_2_255_257

Ported from:
state_tests/stShift/sar_2^255_257Filler.json
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
    ["state_tests/stShift/sar_2^255_257Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_sar_2_255_257(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_sar_2_255_257"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xb1f4cbc3a50042184425a6f9e996d0910f7ba879457ce5dac5c71e498ad3c005
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

    # Source: raw
    # 0x7f80000000000000000000000000000000000000000000000000000000000000006101011d600055
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.SAR(0x101, 0x8000000000000000000000000000000000000000000000000000000000000000)),  # noqa: E501
        storage={0: 3},
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0xf1b108eb4de4c7a4c0b2258442c550d23df640a0"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000)


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=400000,
        value=0x186a0,
        nonce=0,
        gas_price=10,
    )

    post = {
        target: Account(
                storage={
            0: 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff,
        },
                balance=0xde0b6b3a76586a0,
            ),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
