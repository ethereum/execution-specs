"""
EXTCODEHASH of an account during a CALLCODE

Ported from:
tests/static/state_tests/stExtCodeHash/extCodeHashCALLCODEFiller.json

callee code:
    push20 0x54b3b055779972844a92b30244148fc92092c216
    extcodehash
    push1 0x00
    mstore
    push1 0x20
    push1 0x00
    return
    stop

callee_1 code:
    slt
    callvalue

callee_2 code:
    push20 0x54b3b055779972844a92b30244148fc92092c216
    extcodesize
    push1 0x00
    mstore
    push1 0x20
    push1 0x00
    return
    stop

contract code:
    push1 0x20
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x307e5b123e61545f0ebb0f01dbcd8c6dff125788
    push3 0x0249f0
    callcode
    pop
    push1 0x20
    push1 0x00
    push1 0x00
    returndatacopy
    push1 0x00
    mload
    push1 0x00
    sstore
    push1 0x20
    push1 0x00
    push1 0x00
    ... (15 more instructions)
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
    ["tests/static/state_tests/stExtCodeHash/extCodeHashCALLCODEFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_ext_code_hash_callcode(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """EXTCODEHASH of an account during a CALLCODE."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0x7e3828b44afe2ba3c5a80b24379c51120e3ac4bd")
    callee = Address("0x307e5b123e61545f0ebb0f01dbcd8c6dff125788")
    callee_1 = Address("0x54b3b055779972844a92b30244148fc92092c216")
    callee_2 = Address("0x6e37c7a39fd79ba4cd41ad3962df174a377773fa")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[callee] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH20[0x54b3b055779972844a92b30244148fc92092c216] + Op.EXTCODEHASH
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.RETURN
        + Op.STOP
    ),
        storage={0x0: 0xdeadbeef},
    )
    pre[callee_1] = Account(balance=0xde0b6b3a7640000, nonce=0, code=Op.SLT + Op.CALLVALUE)
    pre[callee_2] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH20[0x54b3b055779972844a92b30244148fc92092c216] + Op.EXTCODESIZE
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.RETURN
        + Op.STOP
    ),
        storage={0x0: 0xdeadbeef},
    )
    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0x307e5b123e61545f0ebb0f01dbcd8c6dff125788]
        + Op.PUSH3[0x249f0] + Op.CALLCODE + Op.POP + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.RETURNDATACOPY + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x0]
        + Op.SSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0x6e37c7a39fd79ba4cd41ad3962df174a377773fa]
        + Op.PUSH3[0x249f0] + Op.CALLCODE + Op.POP + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.RETURNDATACOPY + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x1]
        + Op.SSTORE + Op.STOP
    ),
        storage={0x0: 0xdeadbeef},
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869"
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
