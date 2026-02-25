"""
create fails because we try to send more wei to it that we have

Ported from:
tests/static/state_tests/stCallCreateCallCodeTest/createFailBalanceTooLowFiller.json

contract code:
    push5 0x6001600255
    push1 0x00
    mstore
    push1 0x05
    push1 0x1b
    push8 0x0de0b6b3a7640018
    create
    selfdestruct
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
    ["tests/static/state_tests/stCallCreateCallCodeTest/createFailBalanceTooLowFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_value",
    [
        23,
        24,
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_create_fail_balance_too_low(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_value: int,
) -> None:
    """create fails because we try to send more wei to it that we have."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0x095e7baea6a6c7c4c2dfeb977efac326af552d87")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH5[0x6001600255] + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x5]
        + Op.PUSH1[0x1b] + Op.PUSH8[0xde0b6b3a7640018] + Op.CREATE + Op.SELFDESTRUCT
        + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=contract,
        data=b"",
        gas_limit=253021,
        gas_price=10,
        nonce=0,
        value=tx_value,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
