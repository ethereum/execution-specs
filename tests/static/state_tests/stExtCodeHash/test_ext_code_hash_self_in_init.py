"""
EXTCODEHASH/EXTCODESIZE of the account currently being created

Ported from:
tests/static/state_tests/stExtCodeHash/extCodeHashSelfInInitFiller.json

contract code:
    push1 0x10
    push1 0x10
    dup1
    push1 0x13
    push1 0x00
    codecopy
    push1 0x00
    push1 0x00
    create2
    pop
    stop
    stop
    invalid
    address
    extcodehash
    push1 0x00
    sstore
    address
    extcodesize
    push1 0x01
    ... (5 more instructions)
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
    ["tests/static/state_tests/stExtCodeHash/extCodeHashSelfInInitFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_ext_code_hash_self_in_init(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """EXTCODEHASH/EXTCODESIZE of the account currently being created."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0xdeadbeef00000000000000000000000000000000")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x10] + Op.PUSH1[0x10] + Op.DUP1 + Op.PUSH1[0x13] + Op.PUSH1[0x0]
        + Op.CODECOPY + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CREATE2 + Op.POP + Op.STOP
        + Op.STOP + Op.INVALID + Op.ADDRESS + Op.EXTCODEHASH + Op.PUSH1[0x0]
        + Op.SSTORE + Op.ADDRESS + Op.EXTCODESIZE + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.RETURN + Op.STOP
    ),
        storage={0x0: 0xdeadbeef},
    )

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=contract,
        data=b"",
        gas_limit=400000,
        gas_price=10,
        nonce=0,
        value=1,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
