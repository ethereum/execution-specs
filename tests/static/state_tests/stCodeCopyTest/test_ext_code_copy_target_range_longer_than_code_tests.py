"""
Uses EXTCODECOPY to copy 32 bytes of code into a 64 byte range of memory and ensures that the last 32 bytes of the memory range are zeroed out

Ported from:
tests/static/state_tests/stCodeCopyTest/ExtCodeCopyTargetRangeLongerThanCodeTestsFiller.json

contract code:
    push2 0x1234
    push1 0x20
    mstore
    push1 0x40
    push1 0x00
    push1 0x00
    push20 0x7ac02e797f450c7ea62753383f618e1903cd6bba
    extcodecopy
    push1 0x00
    mload
    push1 0x00
    sstore
    push1 0x20
    mload
    push1 0x01
    sstore
    push2 0x5678
    push1 0x60
    mstore
    push1 0x40
    ... (13 more instructions)
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
    ["tests/static/state_tests/stCodeCopyTest/ExtCodeCopyTargetRangeLongerThanCodeTestsFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_ext_code_copy_target_range_longer_than_code_tests(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Uses EXTCODECOPY to copy 32 bytes of code into a 64 byte range of memory and ensures that the last 32 bytes of the memory range are zeroed out."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0x4768b5e50b0ebe91ae38d84a47e3179e615f9c40")
    contract = Address("0x48d8f710ab8cb48f77b602d24696926e31787a17")
    callee = Address("0x7ac02e797f450c7ea62753383f618e1903cd6bba")

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
        Op.PUSH2[0x1234] + Op.PUSH1[0x20] + Op.MSTORE + Op.PUSH1[0x40]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x7ac02e797f450c7ea62753383f618e1903cd6bba] + Op.EXTCODECOPY
        + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x20]
        + Op.MLOAD + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH2[0x5678] + Op.PUSH1[0x60]
        + Op.MSTORE + Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40]
        + Op.PUSH20[0x4768b5e50b0ebe91ae38d84a47e3179e615f9c40] + Op.EXTCODECOPY
        + Op.PUSH1[0x40] + Op.MLOAD + Op.PUSH1[0x2] + Op.SSTORE + Op.PUSH1[0x60]
        + Op.MLOAD + Op.PUSH1[0x3] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee] = Account(
        balance=0,
        nonce=1,
        code=bytes.fromhex("1122334455667788991011121314151617181920212223242526272829303132"),
    )

    tx = Transaction(
        secret_key=Hash(
            "0xe7c72b378297589acee4e0ba3272841bcfc5e220f86de253f890274cfee9e474"
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
