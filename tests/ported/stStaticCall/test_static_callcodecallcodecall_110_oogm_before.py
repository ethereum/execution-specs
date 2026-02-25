"""
Ported from:
tests/static/state_tests/stStaticCall/static_callcodecallcodecall_110_OOGMBeforeFiller.json

contract code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0x401580462c2ca97fc4f16b066d6249250a227afb
    push3 0x0249f0
    delegatecall
    push1 0x00
    sstore
    push1 0x01
    push1 0x01
    sstore
    stop

callee code:
    push1 0x01
    push1 0x03
    mstore
    stop

callee_1 code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push20 0xf32619344056ad22a07f10433f70165ce82d9273
    push2 0x9c90
    delegatecall
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
    ... (8 more instructions)
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
    ["tests/static/state_tests/stStaticCall/static_callcodecallcodecall_110_OOGMBeforeFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_static_callcodecallcodecall_110_oogm_before(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0x31d06fad70e2a598413824a9bc68d80a5d2b194e")
    callee = Address("0x335c5531b84765a7626e6e76688f18b81be5259c")
    callee_1 = Address("0x401580462c2ca97fc4f16b066d6249250a227afb")
    callee_2 = Address("0xf32619344056ad22a07f10433f70165ce82d9273")

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
        + Op.PUSH20[0x401580462c2ca97fc4f16b066d6249250a227afb] + Op.PUSH3[0x249f0]
        + Op.DELEGATECALL + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee] = Account(
        balance=0,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH1[0x3] + Op.MSTORE + Op.STOP,
    )
    pre[callee_1] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0xf32619344056ad22a07f10433f70165ce82d9273] + Op.PUSH2[0x9c90]
        + Op.DELEGATECALL + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee_2] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.JUMPDEST + Op.PUSH2[0xc350] + Op.PUSH1[0x80] + Op.MLOAD + Op.LT
        + Op.ISZERO + Op.PUSH1[0x1c] + Op.JUMPI + Op.PUSH1[0x1] + Op.EXTCODESIZE
        + Op.POP + Op.PUSH1[0x1] + Op.PUSH1[0x80] + Op.MLOAD + Op.ADD + Op.PUSH1[0x80]
        + Op.MSTORE + Op.PUSH1[0x0] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x40]
        + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH20[0x335c5531b84765a7626e6e76688f18b81be5259c] + Op.PUSH2[0x4e34]
        + Op.STATICCALL + Op.STOP
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869"
        ),
        to=contract,
        data=b"",
        gas_limit=172000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
