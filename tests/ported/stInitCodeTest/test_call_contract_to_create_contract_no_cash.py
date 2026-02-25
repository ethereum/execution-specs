"""
Ported from:
tests/static/state_tests/stInitCodeTest/CallContractToCreateContractNoCashFiller.json

contract code:
    push21 0x600c60005566602060406000f060205260076039f3
    push1 0x00
    mstore
    push1 0x15
    push1 0x0b
    push3 0x0186a0
    create
    push1 0x00
    sstore
    stop
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stInitCodeTest/CallContractToCreateContractNoCashFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_contract_to_create_contract_no_cash(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xc4a2ca1058df329e5da4755f9921ddaf05cbaa06")
    contract = Address("0x985aca92559c5b1b9cd7897fec0f7c7993ad0d60")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[contract] = Account(
        balance=0x2710,
        nonce=0,
        code=(
        Op.PUSH21[0x600c60005566602060406000f060205260076039f3] + Op.PUSH1[0x0]
        + Op.MSTORE + Op.PUSH1[0x15] + Op.PUSH1[0xb] + Op.PUSH3[0x186a0] + Op.CREATE
        + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0x3b9aca00, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0xf79127a3004abde26a4cbd80c428cb10f829fa11b54d36e7b326f4f4a5927acf"
        ),
        to=contract,
        data=bytes.fromhex("00"),
        gas_limit=100000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
