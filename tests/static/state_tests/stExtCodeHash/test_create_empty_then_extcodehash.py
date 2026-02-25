"""
https://github.com/ethereum/tests/issues/652

Ported from:
tests/static/state_tests/stExtCodeHash/createEmptyThenExtcodehashFiller.json

contract code:
    push1 0x00
    push1 0x09
    dup1
    push1 0x56
    push1 0x00
    codecopy
    push1 0x00
    push1 0x00
    create2
    push1 0x00
    sstore
    push20 0x0826562ac9373818f7a055166f7b0cc87485f05d
    extcodehash
    push1 0x01
    sstore
    push1 0x09
    dup1
    push1 0x5f
    push1 0x00
    codecopy
    ... (21 more instructions)
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
    ["tests/static/state_tests/stExtCodeHash/createEmptyThenExtcodehashFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create_empty_then_extcodehash(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """https://github.com/ethereum/tests/issues/652."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0x1000000000000000000000000000000000000000")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=47244640256,
    )

    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x9] + Op.DUP1 + Op.PUSH1[0x56] + Op.PUSH1[0x0]
        + Op.CODECOPY + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CREATE2 + Op.PUSH1[0x0]
        + Op.SSTORE + Op.PUSH20[0x826562ac9373818f7a055166f7b0cc87485f05d]
        + Op.EXTCODEHASH + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x9] + Op.DUP1
        + Op.PUSH1[0x5f] + Op.PUSH1[0x0] + Op.CODECOPY + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.CREATE + Op.PUSH1[0x2] + Op.SSTORE
        + Op.PUSH20[0x7c5a2c91b22d7a9226523d4ba717db6afb741ebd] + Op.EXTCODEHASH
        + Op.PUSH1[0x3] + Op.SSTORE + Op.STOP + Op.INVALID + Op.PUSH3[0x112233]
        + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP + Op.STOP + Op.PUSH3[0x112233]
        + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP + Op.STOP
    ),
        storage={0x0: 0x1, 0x1: 0x1, 0x2: 0x1, 0x3: 0x1},
    )
    pre[sender] = Account(balance=0x6400000000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=contract,
        data=b"",
        gas_limit=300000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
