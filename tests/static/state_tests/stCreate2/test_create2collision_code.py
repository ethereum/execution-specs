"""
create2 generates an account that already exists and has not empty code

Ported from:
tests/static/state_tests/stCreate2/create2collisionCodeFiller.json

contract code:
    add
    mul
    sub

callee_1 code:
    add
    mul
    sub

callee_2 code:
    add
    mul
    sub
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
    ["tests/static/state_tests/stCreate2/create2collisionCodeFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "6000600060006000f500",
        "64600160015560005260006005601b6000f500",
        "6d6460016001556000526005601bf36000526000600e60126000f500",
    ],
    ids=['case0', 'case1', 'case2'],
)
@pytest.mark.pre_alloc_mutable
def test_create2collision_code(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """create2 generates an account that already exists and has not empty code."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0xaf3ecba2fe09a4f6c19f16a9d119e44e08c2da01")
    callee_1 = Address("0xe2b35478fdd26477cc576dd906e6277761246a3c")
    callee_2 = Address("0xec2c6832d00680ece8ff9254f81fdab0a5a2ac50")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(balance=0, nonce=0, code=Op.ADD + Op.MUL + Op.SUB)
    pre[callee_1] = Account(balance=0, nonce=0, code=Op.ADD + Op.MUL + Op.SUB)
    pre[callee_2] = Account(balance=0, nonce=0, code=Op.ADD + Op.MUL + Op.SUB)

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
        value=1,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
