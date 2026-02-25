"""
Ported from:
tests/static/state_tests/stCreateTest/CREATE_EmptyContractAndCallIt_1weiFiller.json

contract code:
    gas
    push1 0x00
    sstore
    push1 0x20
    push1 0x00
    push1 0x00
    create
    push1 0x01
    sstore
    gas
    push1 0x02
    sstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x01
    push1 0x01
    sload
    push2 0xea60
    ... (7 more instructions)
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
    ["tests/static/state_tests/stCreateTest/CREATE_EmptyContractAndCallIt_1weiFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create_empty_contract_and_call_it_1wei(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[sender] = Account(balance=0xe8d4a51000, nonce=0)
    pre[contract] = Account(
        balance=1,
        nonce=0,
        code=(
        Op.GAS + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.CREATE + Op.PUSH1[0x1] + Op.SSTORE + Op.GAS
        + Op.PUSH1[0x2] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SLOAD + Op.PUSH2[0xea60]
        + Op.CALL + Op.PUSH1[0x3] + Op.SSTORE + Op.GAS + Op.PUSH1[0x64] + Op.SSTORE
        + Op.STOP
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=contract,
        data=b"",
        gas_limit=600000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
