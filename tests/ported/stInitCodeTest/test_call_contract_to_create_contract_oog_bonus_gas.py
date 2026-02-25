"""
Ported from:
tests/static/state_tests/stInitCodeTest/CallContractToCreateContractOOGBonusGasFiller.json

contract code:
    push21 0x600c60005566602060406000f060205260076039f3
    push1 0x00
    mstore
    push1 0x15
    push1 0x0b
    push1 0x01
    create
    push1 0x00
    sstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x0c
    push1 0x00
    sload
    push1 0x00
    call
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
    ["tests/static/state_tests/stInitCodeTest/CallContractToCreateContractOOGBonusGasFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_contract_to_create_contract_oog_bonus_gas(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0x095e7baea6a6c7c4c2dfeb977efac326af552d87")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000000,
    )

    pre[contract] = Account(
        balance=112,
        nonce=0,
        code=(
        Op.PUSH21[0x600c60005566602060406000f060205260076039f3] + Op.PUSH1[0x0]
        + Op.MSTORE + Op.PUSH1[0x15] + Op.PUSH1[0xb] + Op.PUSH1[0x1] + Op.CREATE
        + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0xc] + Op.PUSH1[0x0] + Op.SLOAD + Op.PUSH1[0x0]
        + Op.CALL + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0x3b9aca00, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=contract,
        data=bytes.fromhex("00"),
        gas_limit=200000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
