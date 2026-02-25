"""
Ported from:
tests/static/state_tests/stCodeCopyTest/ExtCodeCopyTestsParisFiller.json

contract code:
    push1 0x02
    push1 0x0a
    push1 0x01
    push20 0xbbbf5374fce5edbc8e2a8697c15331677e6ebf0b
    extcodecopy
    push1 0x00
    mload
    push1 0x02
    sstore
    push1 0x02
    push1 0x0a
    push1 0x01
    push20 0xcccf5374fce5edbc8e2a8697c15331677e6ebf0b
    extcodecopy
    push1 0x00
    mload
    push1 0x03
    sstore
    push1 0x02
    push1 0x0a
    ... (26 more instructions)
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
    ["tests/static/state_tests/stCodeCopyTest/ExtCodeCopyTestsParisFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_ext_code_copy_tests_paris(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0xaaaf5374fce5edbc8e2a8697c15331677e6ebf0b")
    callee = Address("0xcccf5374fce5edbc8e2a8697c15331677e6ebf0b")
    callee_1 = Address("0xdddf5374fce5edbc8e2a8697c15331677e6ebf0b")
    callee_2 = Address("0xeeef5374fce5edbc8e2a8697c15331677e6ebf0b")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre[sender] = Account(balance=0xffffffffffffffffffffffffffffffff, nonce=0)
    pre[contract] = Account(
        balance=7000,
        nonce=0,
        code=(
        Op.PUSH1[0x2] + Op.PUSH1[0xa] + Op.PUSH1[0x1]
        + Op.PUSH20[0xbbbf5374fce5edbc8e2a8697c15331677e6ebf0b] + Op.EXTCODECOPY
        + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x2] + Op.SSTORE + Op.PUSH1[0x2]
        + Op.PUSH1[0xa] + Op.PUSH1[0x1]
        + Op.PUSH20[0xcccf5374fce5edbc8e2a8697c15331677e6ebf0b] + Op.EXTCODECOPY
        + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x3] + Op.SSTORE + Op.PUSH1[0x2]
        + Op.PUSH1[0xa] + Op.PUSH1[0x1]
        + Op.PUSH20[0xdddf5374fce5edbc8e2a8697c15331677e6ebf0b] + Op.EXTCODECOPY
        + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x4] + Op.SSTORE + Op.PUSH1[0x2]
        + Op.PUSH1[0xa] + Op.PUSH1[0x1]
        + Op.PUSH20[0xeeef5374fce5edbc8e2a8697c15331677e6ebf0b] + Op.EXTCODECOPY
        + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x5] + Op.SSTORE + Op.PUSH1[0xc8]
        + Op.PUSH1[0xa] + Op.PUSH1[0x1]
        + Op.PUSH20[0xeeef5374fce5edbc8e2a8697c15331677e6ebf0b] + Op.EXTCODECOPY
        + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x6] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee] = Account(balance=10, nonce=0)
    pre[callee_1] = Account(balance=0, nonce=1)
    pre[callee_2] = Account(
        balance=0,
        nonce=1,
        code=bytes.fromhex("1122334455667788991011121314151617181920212223242526272829303132"),
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
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
