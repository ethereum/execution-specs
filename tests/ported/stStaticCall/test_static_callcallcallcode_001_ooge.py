"""
Ported from:
tests/static/state_tests/stStaticCall/static_callcallcallcode_001_OOGEFiller.json

contract code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0x6f80b859ba9392b2c26e5930c330d4a7247fba4f
    push3 0x0927c0
    staticcall
    push1 0x00
    sstore
    push1 0x01
    push1 0x03
    mstore
    stop

callee code:
    push1 0x01
    push1 0x03
    mstore
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0xa3e14608664e4a0229f96c49500f83f0fdbf3dcb
    push3 0x0493e0
    staticcall
    pop
    push1 0x01
    push1 0x03
    mstore
    stop

callee_1 code:
    push1 0x01
    push1 0x03
    mstore
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0xe574f7ec5305be91332b5b8b12deb8966e05f42d
    push3 0x01d4d4
    delegatecall
    pop
    push1 0x01
    push1 0x03
    mstore
    stop

callee_2 code:
    jumpdest
    push2 0xc350
    push1 0x80
    mload
    lt
    iszero
    push1 0x1c
    jumpi
    push1 0x01
    extcodesize
    pop
    push1 0x01
    push1 0x80
    mload
    add
    push1 0x80
    mstore
    push1 0x00
    jump
    jumpdest
    ... (1 more instructions)
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
    ["tests/static/state_tests/stStaticCall/static_callcallcallcode_001_OOGEFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_static_callcallcallcode_001_ooge(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0x563f06d1277f7cb092689ac2168d6eecd1acb499")
    callee = Address("0x6f80b859ba9392b2c26e5930c330d4a7247fba4f")
    callee_1 = Address("0xa3e14608664e4a0229f96c49500f83f0fdbf3dcb")
    callee_2 = Address("0xe574f7ec5305be91332b5b8b12deb8966e05f42d")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=30000000,
    )

    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0x6f80b859ba9392b2c26e5930c330d4a7247fba4f] + Op.PUSH3[0x927c0]
        + Op.STATICCALL + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x3]
        + Op.MSTORE + Op.STOP
    ),
    )
    pre[callee] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x3] + Op.MSTORE + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0xa3e14608664e4a0229f96c49500f83f0fdbf3dcb] + Op.PUSH3[0x493e0]
        + Op.STATICCALL + Op.POP + Op.PUSH1[0x1] + Op.PUSH1[0x3] + Op.MSTORE + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x3] + Op.MSTORE + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0xe574f7ec5305be91332b5b8b12deb8966e05f42d] + Op.PUSH3[0x1d4d4]
        + Op.DELEGATECALL + Op.POP + Op.PUSH1[0x1] + Op.PUSH1[0x3] + Op.MSTORE
        + Op.STOP
    ),
    )
    pre[callee_2] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.JUMPDEST + Op.PUSH2[0xc350] + Op.PUSH1[0x80] + Op.MLOAD + Op.LT
        + Op.ISZERO + Op.PUSH1[0x1c] + Op.JUMPI + Op.PUSH1[0x1] + Op.EXTCODESIZE
        + Op.POP + Op.PUSH1[0x1] + Op.PUSH1[0x80] + Op.MLOAD + Op.ADD + Op.PUSH1[0x80]
        + Op.MSTORE + Op.PUSH1[0x0] + Op.JUMP + Op.JUMPDEST + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869"
        ),
        to=contract,
        data=b"",
        gas_limit=1720000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
