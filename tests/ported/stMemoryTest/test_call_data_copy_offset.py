"""
Ported from:
tests/static/state_tests/stMemoryTest/callDataCopyOffsetFiller.json

contract code:
    push8 0x0123456789abcdef
    push1 0x00
    mstore
    push1 0x00
    dup1
    push1 0x0f
    dup2
    dup1
    push20 0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee
    push2 0xffff
    call
    stop

callee code:
    push32 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
    push1 0x00
    mstore
    push1 0x10
    push2 0xffff
    push1 0x00
    calldatacopy
    push1 0x00
    mload
    push1 0x00
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
    ["tests/static/state_tests/stMemoryTest/callDataCopyOffsetFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_data_copy_offset(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0x095e7baea6a6c7c4c2dfeb977efac326af552d87")
    callee = Address("0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=1,
        code=(
        Op.PUSH8[0x123456789abcdef] + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0]
        + Op.DUP1 + Op.PUSH1[0xf] + Op.DUP2 + Op.DUP1
        + Op.PUSH20[0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee] + Op.PUSH2[0xffff]
        + Op.CALL + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee] = Account(
        balance=0xde0b6b3a7640000,
        nonce=1,
        code=(
        Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x10] + Op.PUSH2[0xffff]
        + Op.PUSH1[0x0] + Op.CALLDATACOPY + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x0]
        + Op.SSTORE + Op.STOP
    ),
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
        value=100000,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
