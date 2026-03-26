"""
test_sar11

Ported from:
state_tests/stShift/sar11Filler.json
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
    ["state_tests/stShift/sar11Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_sar11(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_sar11"""
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
    # 0x600160011d600055
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.SAR(0x1, 0x1)),
        storage={0: 3},
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x7362d25017f41b7d56bc5878cbb1fb9b03c39e26"),  # noqa: E501
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
        target: Account(storage={0: 0}, balance=0xde0b6b3a76586a0),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
