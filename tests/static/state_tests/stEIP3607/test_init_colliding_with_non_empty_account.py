"""
Account attempts to send tx to create a contract on a non-empty address

Ported from:
tests/static/state_tests/stEIP3607/initCollidingWithNonEmptyAccountFiller.yml

contract code:
    push1 0x00
    push1 0x01
    sstore
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
    ["tests/static/state_tests/stEIP3607/initCollidingWithNonEmptyAccountFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "60206000f3",
        "6001600055600080808061271073d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d05af100",
        "60016000556000602081612710f500",
        "600160005560206000612710f000",
        "6001600055600080808073d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d05af400",
    ],
    ids=['case0', 'case1', 'case2', 'case3', 'case4'],
)
@pytest.mark.pre_alloc_mutable
def test_init_colliding_with_non_empty_account(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Account attempts to send tx to create a contract on a non-empty address."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0x6295ee1b4f6dd65047762f924ecd367c17eabf8f")
    callee_1 = Address("0xd0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=71794957647893862,
    )

    pre[coinbase] = Account(balance=0, nonce=1)
    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=Op.PUSH1[0x0] + Op.PUSH1[0x1] + Op.SSTORE,
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_1] = Account(balance=0, nonce=0, code=bytes.fromhex("00"))

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=None,
        data=tx_data,
        gas_limit=400000,
        gas_price=10,
        nonce=0,
        value=100000,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
