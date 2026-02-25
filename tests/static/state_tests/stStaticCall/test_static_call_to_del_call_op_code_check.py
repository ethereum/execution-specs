"""
Ported from:
tests/static/state_tests/stStaticCall/static_callToDelCallOpCodeCheckFiller.json

callee code:
    origin
    push20 0xebaf50debf10e08302fe4280c32df010463ca297
    eq
    push1 0x22
    jumpi
    push1 0x02
    push1 0x01
    sstore
    push1 0x28
    jump
    jumpdest
    push1 0x01
    push1 0x01
    mstore
    jumpdest
    caller
    push20 0x7ef8271e6cdb0a23220b73bf3e9697e173f9d015
    eq
    push1 0x4b
    jumpi
    ... (41 more instructions)

callee_1 code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x114ca039127835ca3472ef43e00d15e2d8623286
    push3 0x0186a0
    delegatecall
    push1 0x00
    mstore
    push1 0x00
    mload
    push1 0x01
    eq
    push1 0x36
    jumpi
    push1 0x01
    push1 0x01
    sstore
    push1 0x3c
    jump
    ... (6 more instructions)

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    calldataload
    push3 0x0186a0
    staticcall
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
    ["tests/static/state_tests/stStaticCall/static_callToDelCallOpCodeCheckFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_static_call_to_del_call_op_code_check(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0x7ef8271e6cdb0a23220b73bf3e9697e173f9d015")
    callee = Address("0x114ca039127835ca3472ef43e00d15e2d8623286")
    callee_1 = Address("0x692bdb71bf492107772d8fb07345faa13b37937b")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[callee] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.ORIGIN + Op.PUSH20[0xebaf50debf10e08302fe4280c32df010463ca297] + Op.EQ
        + Op.PUSH1[0x22] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x28] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.CALLER
        + Op.PUSH20[0x7ef8271e6cdb0a23220b73bf3e9697e173f9d015] + Op.EQ
        + Op.PUSH1[0x4b] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x51] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.ADDRESS
        + Op.PUSH20[0x692bdb71bf492107772d8fb07345faa13b37937b] + Op.EQ
        + Op.PUSH1[0x74] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x7a] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.CALLVALUE + Op.PUSH1[0x0] + Op.EQ
        + Op.PUSH1[0x8a] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x90] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x114ca039127835ca3472ef43e00d15e2d8623286] + Op.PUSH3[0x186a0]
        + Op.DELEGATECALL + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.MLOAD
        + Op.PUSH1[0x1] + Op.EQ + Op.PUSH1[0x36] + Op.JUMPI + Op.PUSH1[0x1]
        + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x3c] + Op.JUMP + Op.JUMPDEST
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.MSTORE + Op.JUMPDEST + Op.STOP
    ),
    )
    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH3[0x186a0] + Op.STATICCALL
        + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869"
        ),
        to=contract,
        data=bytes.fromhex("000000000000000000000000692bdb71bf492107772d8fb07345faa13b37937b"),
        gas_limit=1000000,
        gas_price=10,
        nonce=0,
        value=100000,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
