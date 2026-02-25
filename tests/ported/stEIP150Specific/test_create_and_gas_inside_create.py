"""
Ported from:
tests/static/state_tests/stEIP150Specific/CreateAndGasInsideCreateFiller.json

contract code:
    gas
    push1 0x64
    mstore
    push4 0x5a60fd55
    push1 0x00
    mstore
    push1 0x04
    push1 0x1c
    push1 0x00
    create
    push1 0x0b
    sstore
    gas
    push1 0x64
    mload
    sub
    push1 0x09
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
    ["tests/static/state_tests/stEIP150Specific/CreateAndGasInsideCreateFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create_and_gas_inside_create(
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
        balance=0,
        nonce=0,
        code=(
        Op.GAS + Op.PUSH1[0x64] + Op.MSTORE + Op.PUSH4[0x5a60fd55] + Op.PUSH1[0x0]
        + Op.MSTORE + Op.PUSH1[0x4] + Op.PUSH1[0x1c] + Op.PUSH1[0x0] + Op.CREATE
        + Op.PUSH1[0xb] + Op.SSTORE + Op.GAS + Op.PUSH1[0x64] + Op.MLOAD + Op.SUB
        + Op.PUSH1[0x9] + Op.SSTORE + Op.STOP
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
